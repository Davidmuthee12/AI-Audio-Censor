from fastapi import APIRouter

from app.api.router import audio, sound_effect, user

master_router = APIRouter()

master_router.include_router(user.router)
master_router.include_router(audio.router)
master_router.include_router(sound_effect.router)
