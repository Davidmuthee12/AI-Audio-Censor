from __future__ import annotations

import whisperx
from rich import print_json


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

    def transcribe_audio(self, audio_path: str) -> list[dict]:
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


ac = AudioCensor()
result = ac.transcribe_audio("./sample.wav")

print_json(data=result)
