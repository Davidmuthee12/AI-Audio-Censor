from uuid import uuid4

from sqlmodel.ext.asyncio.session import AsyncSession

from app.database.models import SoundEffect, User
from app.object_storage import storage
from app.types import AudioFileUpload


class SoundEffectService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def add_sound_effect(
        self, audio_file: AudioFileUpload, user: User
    ) -> SoundEffect:
        # Save the uploaded file to object storage
        file_key = f"users/{user.id}/sound_effects/{uuid4()}{audio_file.file_extension}"
        storage.upload_file(
            audio_file.file.file,
            key=file_key,
            content_type=audio_file.file.content_type,
        )

        # Add the sound effect record to the database
        sound_effect = SoundEffect(
            name=audio_file.sanitized_filename,
            file_path=file_key,
            user_id=user.id,
        )
        self.session.add(sound_effect)
        await self.session.commit()
        await self.session.refresh(sound_effect)

        return sound_effect
