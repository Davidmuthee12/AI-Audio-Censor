from pathlib import Path
from uuid import UUID, uuid4

from celery import Celery

from app.config import settings
from app.database.models import Audio, AudioStatus
from app.worker.audio_censor import AudioCensor, Word

celery_app = Celery("tasks", broker=settings.BROKER_URL)


@celery_app.task(base=AudioCensor, bind=True)
def transcribe_audio_task(self: AudioCensor, id: str) -> None:
    with self.session_local() as session:
        audio = session.get(Audio, UUID(id))

        # Set audio status to processing
        audio.status = AudioStatus.processing
        session.add(audio)
        session.commit()

        # Transcribe the audio and save the transcription to the database
        audio.transcription = self.transcribe_audio(audio.file_path)

        audio.credits_reserved -= audio.duration
        audio.credits_used += audio.duration

        session.add(audio)
        session.commit()


@celery_app.task(base=AudioCensor, bind=True)
def detect_profanity_task(self: AudioCensor, id: str) -> None:
    with self.session_local() as session:
        audio = session.get(Audio, UUID(id))

        # Set audio status to processing if it's not already set
        if audio.status != AudioStatus.processing:
            audio.status = AudioStatus.processing
            session.add(audio)
            session.commit()

        # Run profanity detection and update the transcription with censored words
        word_segments: list[Word] = audio.transcription or []
        audio.transcription = self.detect_profanity(
            word_segments, user_list=audio.user_list
        )

        audio.credits_reserved -= audio.duration
        audio.credits_used += audio.duration

        session.add(audio)
        session.commit()


@celery_app.task(base=AudioCensor, bind=True)
def render_audio_task(self: AudioCensor, id: str) -> None:
    with self.session_local() as session:
        audio = session.get(Audio, UUID(id))

        # Set audio status to processing if it's not already set
        if audio.status != AudioStatus.processing:
            audio.status = AudioStatus.processing
            session.add(audio)
            session.commit()

        # Get file paths
        input_path = audio.file_path

        output_path = (
            f"users/{audio.user_id}/audios/{uuid4()}{Path(audio.file_path).suffix}"
            if audio.censored_file_path is None
            else audio.censored_file_path
        )

        sound_effect_path = (
            audio.sound_effect.file_path if audio.sound_effect is not None else None
        )

        # Render the censored audio
        word_segments: list[Word] = audio.transcription or []
        self.render_audio(
            input_path,
            output_path,
            word_segments,
            audio.use_beep,
            sound_effect_path,
        )

        # Set the censored file path and update the audio status to completed
        audio.censored_file_path = output_path
        audio.status = AudioStatus.completed

        audio.credits_reserved -= audio.duration
        audio.credits_used += audio.duration

        session.add(audio)
        session.commit()
