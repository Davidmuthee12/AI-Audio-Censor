from typing import Annotated

from fastapi import Depends
from polar_sdk import Polar
from propelauth_fastapi import User as PropelauthUser
from propelauth_fastapi import init_auth_async
from sqlmodel.ext.asyncio.session import AsyncSession

from app.config import settings
from app.database.models import User
from app.database.session import get_session
from app.service.audio import AudioService
from app.service.sound_effect import SoundEffectService
from app.service.user import UserService

auth = init_auth_async(
    auth_url=settings.PROPELAUTH_AUTH_URL,
    api_key=settings.PROPELAUTH_API_KEY,
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


AudioServiceDep = Annotated[AudioService, Depends(get_audio_service)]
SoundEffectServiceDep = Annotated[SoundEffectService, Depends(get_sound_effect_service)]
UserServiceDep = Annotated[UserService, Depends(get_user_service)]
UserDep = Annotated[User, Depends(get_current_user)]
PolarDep = Annotated[Polar, Depends(get_polar)]
