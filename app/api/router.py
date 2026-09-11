from uuid import UUID

from fastapi import APIRouter, HTTPException, UploadFile, status

from app.api.dependencies import AudioServiceDep
from app.api.schemas import AudioRead

router = APIRouter()


@router.get("/audio/{id}", response_model=AudioRead)
def read_audio(id: UUID, service: AudioServiceDep):
    audio = service.get_audio(id)

    if not audio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Audio not found",
        )

    return audio


@router.post("/audio", response_model=AudioRead)
def submit_audio(
    audio_file: UploadFile,
    service: AudioServiceDep,
):
    audio = service.add_audio(audio_file)

    return audio
