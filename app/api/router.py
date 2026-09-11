from fastapi import APIRouter, Depends, UploadFile
from sqlmodel import Session

from app.database.session import get_session
from app.service.audio import AudioService

router = APIRouter()


@router.post("/censor")
def censor_audio(
    audio_file: UploadFile,
    session: Session = Depends(get_session),
):
    audio = AudioService(session).add_audio(audio_file)

    return {
        "id": audio.id,
        "url": f"/uploads/censored_{audio_file.filename}",
    }
