from dataclasses import dataclass

from fastapi import UploadFile


@dataclass
class AudioFileUpload:
    file: UploadFile
    duration: int
    sanitized_filename: str
    file_extension: str
