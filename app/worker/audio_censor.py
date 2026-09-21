import string
import warnings
from pathlib import Path
from typing import NotRequired, TypedDict
from uuid import UUID

from better_profanity import profanity
from celery import Task
from pydub import AudioSegment
from pydub.generators import Sine
from replicate.client import Client
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel import Session

from app.config import settings
from app.database.models import Audio, AudioStatus
from app.object_storage import storage

warnings.filterwarnings("ignore")


class Word(TypedDict):
    word: str
    start: float
    end: float
    score: float
    flagged: NotRequired[bool]


class AudioCensor(Task):
    def __init__(self) -> None:
        self.replicate_client = Client(settings.REPLICATE_API_TOKEN)

        self.punctuation_table = str.maketrans("", "", string.punctuation)

        self.engine = create_engine(
            url=settings.DB_URL.replace("asyncpg", "psycopg2"),
        )
        self.session_local = sessionmaker(
            bind=self.engine,
            class_=Session,
            expire_on_commit=False,
        )

    def transcribe_audio(self, audio_path: str) -> list[Word]:
        # Get a presigned URL for the audio file in object storage
        url = storage.get_file_url(audio_path)

        # Call the Replicate API to transcribe the audio and get transcription
        output = self.replicate_client.run(
            "victor-upmeet/whisperx:84d2ad2d6194fe98a17d2b60bef1c7f910c46b2f6fd38996ca457afd9c8abfcb",
            input={
                "audio_file": url,
                "language": "en",
                "align_output": True,
            },
        )

        # Flatten the list of word segments from the output
        return [word for segment in output["segments"] for word in segment["words"]]

    def detect_profanity(
        self,
        word_segments: list[Word],
        user_list: list[str] | None = None,
    ) -> list[Word]:
        updated_segments = []

        for segment in word_segments:
            # Remove punctuation marks from the word using string translation
            word = segment["word"].translate(self.punctuation_table)

            updated_segments.append(
                {
                    **segment,
                    "flagged": profanity.contains_profanity(word)
                    or (user_list is not None and word.lower() in user_list),
                }
            )

        return updated_segments

    def render_audio(
        self,
        input_path: str,
        output_path: str,
        word_segments: list[Word],
        beep: bool = True,
        sound_effect_path: str | None = None,
    ) -> None:
        audio = storage.download_audio(input_path)

        effect_audio: AudioSegment | None = None
        if not beep and sound_effect_path is not None:
            effect_audio = storage.download_audio(sound_effect_path)

        for segment in word_segments:
            if not segment.get("flagged", False):
                continue

            start_ms = max(0, int(segment["start"] * 1000))
            end_ms = min(len(audio), int(segment["end"] * 1000))

            if end_ms <= start_ms:
                continue

            replacement = AudioSegment.silent(duration=end_ms - start_ms)

            if beep:
                replacement = (
                    Sine(1000)
                    .to_audio_segment(duration=end_ms - start_ms)
                    .apply_gain(-6)
                )
            elif effect_audio is not None and len(effect_audio) > 0:
                segment_duration = end_ms - start_ms
                # Repeat and trim the effect to exactly match the censored segment length.
                repeats = (segment_duration // len(effect_audio)) + 1
                replacement = (effect_audio * repeats)[:segment_duration]

            audio = audio[:start_ms] + replacement + audio[end_ms:]

        output_format = Path(output_path).suffix.lstrip(".").lower() or "wav"
        storage.upload_audio(audio, output_path, format=output_format)

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        id = args[0] if args else kwargs.get("id")
        if id is not None:
            with self.session_local() as session:
                audio = session.get(Audio, UUID(id))
                if audio is not None:
                    audio.status = AudioStatus.failed
                    session.add(audio)
                    session.commit()

        return super().on_failure(exc, task_id, args, kwargs, einfo)
