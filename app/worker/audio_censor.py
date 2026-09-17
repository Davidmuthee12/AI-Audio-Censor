import warnings
from pathlib import Path
from typing import NotRequired, TypedDict

import whisperx
from better_profanity import profanity
from celery import Task
from pydub import AudioSegment
from pydub.generators import Sine
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel import Session

from app.config import settings

warnings.filterwarnings("ignore")


class Word(TypedDict):
    word: str
    start: float
    end: float
    score: float
    flagged: NotRequired[bool]


class AudioCensor(Task):
    def __init__(self) -> None:
        self.device = "cpu"
        self.compute_type = "int8"
        self.model_name = "small"
        self.language = "en"

        self.model = None
        self.align_model, self.align_metadata = None, None

        self.engine = create_engine(
            url=settings.DB_URL.replace("asyncpg", "psycopg2"),
        )
        self.session_local = sessionmaker(
            bind=self.engine,
            class_=Session,
            expire_on_commit=False,
        )

    def transcribe_audio(self, audio_path: str) -> list[Word]:
        if self.model is None:
            self.model = whisperx.load_model(
                self.model_name, device=self.device, compute_type=self.compute_type
            )

        if self.align_model is None or self.align_metadata is None:
            self.align_model, self.align_metadata = whisperx.load_align_model(
                language_code=self.language, device=self.device
            )

        audio = whisperx.load_audio(audio_path)

        result = self.model.transcribe(audio, language=self.language)
        aligned_result = whisperx.align(
            result["segments"],
            self.align_model,
            self.align_metadata,
            audio,
            self.device,
            return_char_alignments=False,
        )

        return aligned_result["word_segments"]

    def detect_profanity(self, word_segments: list[Word]) -> list[Word]:
        for segment in word_segments:
            segment["flagged"] = profanity.contains_profanity(segment["word"])

        return word_segments

    def mute_audio(
        self,
        input_path: str,
        output_path: str,
        word_segments: list[Word],
        beep: bool = True,
    ) -> None:
        audio = AudioSegment.from_file(input_path)

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

            audio = audio[:start_ms] + replacement + audio[end_ms:]

        output_format = Path(output_path).suffix.lstrip(".").lower() or "wav"
        audio.export(output_path, format=output_format)
