from uuid import UUID

from celery import Celery

from app.config import settings
from app.database.models import Audio, AudioStatus
from app.utils import get_file_path
from app.worker.audio_censor import AudioCensor

celery_app = Celery("tasks", broker=settings.BROKER_URL)


@celery_app.task(base=AudioCensor, bind=True)
def censor_audio_task(self: AudioCensor, id: str):

    with self.session_local() as session:
        audio = session.get(Audio, UUID(id))
        audio.status = AudioStatus.processing

        session.add(audio)
        session.commit()

        input_path = get_file_path(audio.file_path)
        output_path = get_file_path(f"censored_{audio.file_path}")

        try:
            words = self.transcribe_audio(input_path)
            self.mute_audio(
                input_path=input_path,
                output_path=output_path,
                word_segments=self.detect_profanity(words),
            )
        except Exception:
            audio.status = AudioStatus.failed

        audio.censored_file_path = f"censored_{audio.file_path}"
        audio.status = AudioStatus.completed

        session.add(audio)
        session.commit()
