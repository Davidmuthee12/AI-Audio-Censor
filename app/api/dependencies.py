from typing import Annotated

from fastapi import Depends
from sqlmodel import Session

from app.database.session import get_session
from app.service.audio import AudioService


def get_audio_service(session: Session = Depends(get_session)) -> AudioService:
    return AudioService(session)


AudioServiceDep = Annotated[AudioService, Depends(get_audio_service)]
