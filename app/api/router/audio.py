from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Form
from fastapi.responses import PlainTextResponse
from pydantic import Json

from app.api.dependencies import AudioFileDep, AudioServiceDep, UserDep
from app.api.schemas.audio import (
    AudioFileData,
    AudioRead,
    CensorOptions,
    SubtitleOptions,
)
from app.core.logger import logger
from app.object_storage import storage

router = APIRouter(prefix="/audio", tags=["Audio"])


@router.get("/", response_model=list[AudioRead])
async def read_all_audios(user: UserDep):
    return user.audios


@router.get("/{id}", response_model=AudioRead)
async def read_audio(
    id: UUID,
    service: AudioServiceDep,
    user: UserDep,
):
    audio = await service.get_audio(id, user)
    logger.info(
        "Audio read",
        extra={"data": {"audio_id": str(audio.id), "user_id": str(user.id)}},
    )
    return audio


@router.post("/")
async def submit_audio(
    audio_file: AudioFileDep,
    service: AudioServiceDep,
    user: UserDep,
    options: Annotated[Json[CensorOptions], Form()] = None,
):
    return await service.add_audio(audio_file, user, options)


@router.patch("/{id}", response_model=AudioRead)
async def update_audio(
    id: UUID,
    options: CensorOptions,
    service: AudioServiceDep,
    user: UserDep,
):
    return await service.update_audio(
        id=id,
        user=user,
        options=options,
    )


@router.post("/{id}/subtitle")
async def download_subtitle(
    id: UUID,
    options: SubtitleOptions,
    service: AudioServiceDep,
    user: UserDep,
):
    subtitle = await service.get_subtitle(id, user, options)
    return PlainTextResponse(subtitle)


@router.get("/{id}/download", response_model=AudioFileData)
async def download_audio(
    id: UUID,
    service: AudioServiceDep,
    user: UserDep,
):
    audio = await service.get_audio(id, user)
    url = storage.get_file_url(audio.censored_file_path)
    return {
        "file_url": url,
    }
