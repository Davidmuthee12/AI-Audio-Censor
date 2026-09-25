from pathlib import Path
from typing import Annotated

from fastapi import Depends, File, UploadFile
from polar_sdk import Polar
from propelauth_fastapi import User as PropelauthUser
from propelauth_fastapi import init_auth_async
from pydub import AudioSegment
from pydub.exceptions import CouldntDecodeError
from sqlmodel.ext.asyncio.session import AsyncSession

from app.config import api_settings
from app.core.exceptions import (
    AudioDurationTooLong,
    FileTooLarge,
    InvalidAudioFileType,
    UserNotFound,
)
from app.database.models import User
from app.database.session import get_session
from app.service.audio import AudioService
from app.service.sound_effect import SoundEffectService
from app.service.user import UserService
from app.types import AudioFileUpload
from app.utils import slugify

auth = init_auth_async(
    auth_url=api_settings.PROPELAUTH_AUTH_URL,
    api_key=api_settings.PROPELAUTH_API_KEY,
)


_ALLOWED_AUDIO_EXTENSIONS = {
    ".mp3",
    ".wav",
    ".ogg",
    ".flac",
    ".m4a",
    ".aac",
    ".wma",
    ".aiff",
    ".opus",
    ".webm",
}


class AudioFileValidator:
    def __init__(
        self,
        max_size_bytes: int = 100 * 1024 * 1024,
        max_audio_duration_seconds: int = 15 * 60,
    ):
        self.max_size_bytes = max_size_bytes
        self.max_audio_duration_seconds = max_audio_duration_seconds

    def __call__(self, file: UploadFile = File(...)) -> AudioFileUpload:
        content_type = (file.content_type or "").lower()
        extension = Path(file.filename or "").suffix.lower()

        # Check if the content type is an audio MIME type
        # and if the file extension is in the allowed list of audio extensions.
        is_audio_mime = content_type.startswith("audio/")
        is_allowed_extension = extension in _ALLOWED_AUDIO_EXTENSIONS

        if not (is_audio_mime or is_allowed_extension):
            raise InvalidAudioFileType()

        # Validate the file size
        file_size = file.size
        if file_size is None:
            # Try to determine size by seeking to end
            file.file.seek(0, 2)
            file_size = file.file.tell()
            file.file.seek(0)  # Reset pointer

        if file_size > self.max_size_bytes:
            raise FileTooLarge(self.max_size_bytes)

        # Validate that the uploaded stream can actually be decoded as audio.
        try:
            file.file.seek(0)
            audio: AudioSegment = AudioSegment.from_file(file.file)
        except CouldntDecodeError:
            raise InvalidAudioFileType()
        finally:
            file.file.seek(0)  # Reset pointer

        # Validate the audio duration
        if audio.duration_seconds > self.max_audio_duration_seconds:
            raise AudioDurationTooLong(self.max_audio_duration_seconds)

        return AudioFileUpload(
            file=file,
            duration=round(audio.duration_seconds),
            sanitized_filename=slugify(Path(file.filename or "unknown").name),
            file_extension=extension,
        )


SessionDep = Annotated[AsyncSession, Depends(get_session)]


def get_audio_service(session: SessionDep) -> AudioService:
    return AudioService(session, UserService(session))


def get_user_service(session: SessionDep) -> UserService:
    return UserService(session)


def get_sound_effect_service(session: SessionDep) -> SoundEffectService:
    return SoundEffectService(session)


async def get_current_user(
    auth_user: PropelauthUser = Depends(auth.require_user),
    service: UserService = Depends(get_user_service),
) -> User:
    user = await service.get_user_by_propelauth_id(auth_user.user_id)
    if user is None:
        raise UserNotFound(
            message="Authenticated user not found in database",
            details={"propelauth_user_id": auth_user.user_id},
        )
    return user


async def get_polar():
    async with Polar(
        access_token=api_settings.POLAR_API_TOKEN,
        server=api_settings.POLAR_SERVER,
    ) as polar:
        yield polar


AudioFileDep = Annotated[
    AudioFileUpload,
    Depends(
        AudioFileValidator(
            max_size_bytes=100 * 1024 * 1024,  # 100MB
            max_audio_duration_seconds=15 * 60,
        )
    ),
]
SoundEffectFileDep = Annotated[
    AudioFileUpload,
    Depends(
        AudioFileValidator(
            max_size_bytes=10 * 1024 * 1024,  # 10MB
            max_audio_duration_seconds=10,
        )
    ),
]
AudioServiceDep = Annotated[
    AudioService,
    Depends(get_audio_service),
]
SoundEffectServiceDep = Annotated[
    SoundEffectService,
    Depends(get_sound_effect_service),
]
UserServiceDep = Annotated[
    UserService,
    Depends(get_user_service),
]
UserDep = Annotated[User, Depends(get_current_user)]
PolarDep = Annotated[Polar, Depends(get_polar)]
