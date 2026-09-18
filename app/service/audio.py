from uuid import UUID

from celery import chain
from fastapi import UploadFile
from sqlmodel.ext.asyncio.session import AsyncSession

from app.api.schemas import CensorOptions
from app.database.models import Audio, User
from app.utils import save_file
from app.worker.tasks import (
    detect_profanity_task,
    render_audio_task,
    transcribe_audio_task,
)


class AudioService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_audio(self, id: UUID) -> Audio | None:
        return await self.session.get(Audio, id)

    async def add_audio(
        self,
        file: UploadFile,
        user: User,
        options: CensorOptions | None = None,
    ) -> Audio:
        # Save the uploaded file to disk
        save_file(file)

        # Add audio record to database
        audio = Audio(
            name=file.filename.split(".")[0],
            file_path=file.filename,
            user_id=user.id,
            user_list=options.user_list if options else None,
            use_beep=options.use_beep if options else False,
            sound_effect_id=options.sound_effect_id if options else None,
        )
        self.session.add(audio)
        await self.session.commit()
        await self.session.refresh(audio)

        # Trigger the background task to censor the audio
        chain(
            transcribe_audio_task.si(str(audio.id)),
            detect_profanity_task.si(str(audio.id)),
            render_audio_task.si(str(audio.id)),
        ).apply_async()

        return audio

    async def update_audio(
        self,
        id: UUID,
        user: User,
        options: CensorOptions,
    ) -> Audio | None:
        audio = await self.session.get(Audio, id)
        if audio is None or audio.user_id != user.id:
            return None

        user_list_changed = audio.user_list != options.user_list

        audio.user_list = options.user_list
        audio.use_beep = options.use_beep
        audio.sound_effect_id = options.sound_effect_id

        self.session.add(audio)
        await self.session.commit()
        await self.session.refresh(audio)

        if user_list_changed:
            chain(
                detect_profanity_task.si(str(audio.id)),
                render_audio_task.si(str(audio.id)),
            ).apply_async()
        else:
            render_audio_task.delay(str(audio.id))

        return audio
