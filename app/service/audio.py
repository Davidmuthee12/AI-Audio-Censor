from uuid import UUID

from fastapi import UploadFile
from sqlmodel.ext.asyncio.session import AsyncSession

from app.database.models import Audio, User
from app.utils import save_file
from app.worker.tasks import censor_audio_task


class AudioService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_audio(self, id: UUID) -> Audio | None:
        return await self.session.get(Audio, id)

    async def add_audio(self, file: UploadFile, user: User) -> Audio:
        # Save the uploaded file to disk
        save_file(file)

        # Add audio record to database
        audio = Audio(
            file_path=file.filename,
            user_id=user.id,
        )
        self.session.add(audio)
        await self.session.commit()
        await self.session.refresh(audio)

        # Trigger the background task to censor the audio
        censor_audio_task.delay(str(audio.id))

        return audio
