from __future__ import annotations

from typing import NotRequired, TypedDict

import whisperx
from better_profanity import profanity
from rich import print_json


class Word(TypedDict):
    word: str
    start: float
    end: float
    score: float
    flagged: NotRequired[bool]


class AudioCensor:
    def __init__(self) -> None:
        self.device = "cpu"
        self.compute_type = "int8"
        self.model_name = "small"
        self.language = "en"

        self.model = whisperx.load_model(
            self.model_name, device=self.device, compute_type=self.compute_type
        )
        self.align_model, self.align_metadata = whisperx.load_align_model(
            language_code=self.language, device=self.device
        )

    def transcribe_audio(self, audio_path: str) -> list[Word]:
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


ac = AudioCensor()
words = ac.transcribe_audio("./sample.wav")

print_json(data=ac.detect_profanity(words))
