from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Form, HTTPException, UploadFile, status
from fastapi.responses import PlainTextResponse
from pydantic import Json

from app.api.dependencies import AudioServiceDep, UserDep
from app.api.schemas.audio import AudioRead, CensorOptions, SubtitleOptions
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
    audio = await service.get_audio(id)

    if not audio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Audio not found",
        )

    return audio


@router.post("/")
async def submit_audio(
    audio_file: UploadFile,
    service: AudioServiceDep,
    user: UserDep,
    options: Annotated[Json[CensorOptions], Form()] = None,
):
    audio = await service.add_audio(audio_file, user, options)
    return audio


@router.patch("/{id}", response_model=AudioRead)
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


@router.post("/{id}/subtitle")
async def download_subtitle(
    id: UUID,
    options: SubtitleOptions,
    service: AudioServiceDep,
    user: UserDep,
):
    try:
        subtitle = await service.get_subtitle(id, user, options)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc

    if subtitle is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Audio not found",
        )

    return PlainTextResponse(subtitle)


@router.get("/{id}/download")
async def download_audio(
    id: UUID,
    service: AudioServiceDep,
):
    audio = await service.get_audio(id)

    if not audio.censored_file_path:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Censored audio not found",
        )

    url = storage.get_file_url(audio.censored_file_path)

    return {"file_url": url}
