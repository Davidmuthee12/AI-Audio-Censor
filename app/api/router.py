from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Form, HTTPException, UploadFile, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import Json

from app.api.dependencies import (
    AudioServiceDep,
    SoundEffectServiceDep,
    UserDep,
    UserServiceDep,
)
from app.api.schemas import (
    AudioRead,
    CensorOptions,
    SoundEffectRead,
    TokenData,
    UserCreate,
    UserRead,
)

router = APIRouter()


# Register a new user
@router.post(
    "/signup",
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
)
async def register_user(user_data: UserCreate, service: UserServiceDep):
    user = await service.add_user(user_data)
    return user


@router.post("/token", response_model=TokenData)
async def login_user(
    service: UserServiceDep,
    credentials: OAuth2PasswordRequestForm = Depends(),
):
    token = await service.generate_token(
        email=credentials.username,
        password=credentials.password,
    )
    if token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return {
        "access_token": token,
        "token_type": "bearer",
    }


# Read all audios uploaded by a user
@router.get("/audio", response_model=list[AudioRead])
async def read_all_audios(user: UserDep):
    return user.audios


# Read an audio by ID
@router.get("/audio/{id}", response_model=AudioRead)
async def read_audio(
    id: UUID,
    service: AudioServiceDep,
    user: UserDep,
):
    audio = await service.get_audio(id)

    if not audio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Audio not found",
        )

    return audio


# Submit a new audio to censor
@router.post("/audio", response_model=AudioRead)
async def submit_audio(
    audio_file: UploadFile,
    service: AudioServiceDep,
    user: UserDep,
    options: Annotated[Json[CensorOptions], Form()] = None,
):
    audio = await service.add_audio(audio_file, user, options)
    return audio


# Update censoring options for an existing audio
@router.patch("/audio/{id}", response_model=AudioRead)
async def update_audio(
    id: UUID,
    options: CensorOptions,
    service: AudioServiceDep,
    user: UserDep,
):
    audio = await service.update_audio(
        id=id,
        user=user,
        options=options,
    )

    if audio is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Audio not found",
        )

    return audio


# Upload a new sound effect
@router.post(
    "/sfx",
    response_model=SoundEffectRead,
    status_code=status.HTTP_201_CREATED,
)
async def add_sound_effect(
    file: UploadFile,
    service: SoundEffectServiceDep,
    user: UserDep,
):
    sound_effect = await service.add_sound_effect(file, user)
    return sound_effect


# Read all sound effects uploaded by a user
@router.get("/sfx", response_model=list[SoundEffectRead])
async def read_all_sound_effects(user: UserDep):
    return user.sound_effects
