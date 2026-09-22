import io
from datetime import timedelta
from typing import BinaryIO

import boto3
from botocore.config import Config
from pydub import AudioSegment

from app.config import settings


class ObjectStorage:
    def __init__(self):
        self.client = boto3.client(
            service_name="s3",
            aws_access_key_id=settings.R2_ACCESS_KEY_ID,
            aws_secret_access_key=settings.R2_SECRET_ACCESS_KEY,
            endpoint_url=settings.R2_ENDPOINT_URL,
            region_name="auto",
            config=Config(signature_version="s3v4"),
        )
        self.bucket_name = settings.R2_BUCKET_NAME

    def get_file_url(self, key: str, expiry: timedelta = timedelta(hours=1)) -> str:
        return self.client.generate_presigned_url(
            "get_object",
            Params={"Bucket": self.bucket_name, "Key": key},
            ExpiresIn=int(expiry.total_seconds()),
        )

    def upload_file(self, file: BinaryIO, key: str, content_type: str | None) -> None:
        file.seek(0)
        self.client.upload_fileobj(
            file,
            self.bucket_name,
            key,
            ExtraArgs={"ContentType": content_type} if content_type else {},
        )

    def download_file(self, key: str) -> BinaryIO:
        buf = io.BytesIO()
        self.client.download_fileobj(self.bucket_name, key, buf)
        buf.seek(0)
        return buf

    def upload_audio(self, audio: AudioSegment, key: str, format: str) -> None:
        content_type_by_format = {
            "mp3": "audio/mpeg",
            "wav": "audio/wav",
            "ogg": "audio/ogg",
            "flac": "audio/flac",
            "m4a": "audio/mp4",
        }
        content_type = content_type_by_format.get(
            format.lower(), f"audio/{format.lower()}"
        )

        buf = io.BytesIO()
        audio.export(buf, format=format)
        buf.seek(0)
        self.upload_file(buf, key, content_type)

    def download_audio(self, key: str) -> AudioSegment:
        buf = self.download_file(key)
        return AudioSegment.from_file(buf)


storage = ObjectStorage()
