from uuid import UUID

from fastapi import UploadFile
from sqlmodel import Session

from app.audio_censor import AudioCensor
from app.database.models import Audio
from app.utils import get_file_path, save_file


class AudioService:
    def __init__(self, session: Session):
        self.session = session
        self.ac = AudioCensor()

    def get_audio(self, id: UUID) -> Audio | None:
        return self.session.get(Audio, id)

    def add_audio(self, file: UploadFile) -> Audio:
        # Get file paths
        file_path = save_file(file)
        output_path = get_file_path(f"censored_{file.filename}")

        # Add audio record to database
        audio = Audio(
            file_path=file.filename,
            censored_file_path=f"censored_{file.filename}",
        )
        self.session.add(audio)
        self.session.commit()
        self.session.refresh(audio)

        # Censor audio
        words = self.ac.transcribe_audio(file_path)
        self.ac.mute_audio(
            input_path=file_path,
            output_path=output_path,
            word_segments=self.ac.detect_profanity(words),
        )

        return audio
