from fastapi import APIRouter, status

from app.api.dependencies import SoundEffectFileDep, SoundEffectServiceDep, UserDep
from app.api.schemas.sound_effect import SoundEffectRead

router = APIRouter(prefix="/sfx", tags=["Sound Effects"])


@router.post(
    "/",
    response_model=SoundEffectRead,
    status_code=status.HTTP_201_CREATED,
)
async def add_sound_effect(
    file: SoundEffectFileDep,
    service: SoundEffectServiceDep,
    user: UserDep,
):
    sound_effect = await service.add_sound_effect(file, user)
    return sound_effect


@router.get("/", response_model=list[SoundEffectRead])
async def read_all_sound_effects(user: UserDep):
    return user.sound_effects
