from pathlib import Path
from typing import Annotated

from fastapi import Depends, File, HTTPException, UploadFile, status
from polar_sdk import Polar
from propelauth_fastapi import User as PropelauthUser
from propelauth_fastapi import init_auth_async
from pydub import AudioSegment
from pydub.exceptions import CouldntDecodeError
from sqlmodel.ext.asyncio.session import AsyncSession

from app.config import settings
from app.database.models import User
from app.database.session import get_session
from app.service.audio import AudioService
from app.service.sound_effect import SoundEffectService
from app.service.user import UserService
from app.types import AudioFileUpload
from app.utils import slugify

auth = init_auth_async(
    auth_url=settings.PROPELAUTH_AUTH_URL,
    api_key=settings.PROPELAUTH_API_KEY,
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
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid file type. Please upload an audio file.",
            )

        file_size = file.size
        if file_size is None:
            # Try to determine size by seeking to end
            file.file.seek(0, 2)
            file_size = file.file.tell()
            file.file.seek(0)

        if file_size > self.max_size_bytes:
            raise HTTPException(
                status_code=status.HTTP_413_CONTENT_TOO_LARGE,
                detail=f"File too large. Maximum allowed size is {self.max_size_bytes // (1024 * 1024)}MB.",
            )

        # Validate that the uploaded stream can actually be decoded as audio.
        try:
            file.file.seek(0)
            audio: AudioSegment = AudioSegment.from_file(file.file)
        except CouldntDecodeError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid file type. Please upload an audio file.",
            )
        finally:
            file.file.seek(0)

        if audio.duration_seconds > self.max_audio_duration_seconds:
            raise HTTPException(
                status_code=status.HTTP_413_CONTENT_TOO_LARGE,
                detail=f"Audio duration too long. Maximum allowed duration is {self.max_audio_duration_seconds // 60} minutes.",
            )

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
    user: PropelauthUser = Depends(auth.require_user),
    service: UserService = Depends(get_user_service),
) -> User:
    return await service.get_user_by_propelauth_id(user.user_id)


async def get_polar():
    async with Polar(
        access_token=settings.POLAR_API_TOKEN,
        server="sandbox",
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
