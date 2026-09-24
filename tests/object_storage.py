import io
from datetime import timedelta

from pydub import AudioSegment


class TestObjectStorage:
    def __init__(self):
        self.files: dict[str, tuple[bytes, str | None]] = {}

    def get_file_url(self, key: str, expiry: timedelta = timedelta(hours=1)) -> str:
        print("(🧊 patch) Retrieving file URL for key:", key)
        return f"memory://{key}"

    def upload_file(self, file, key: str, content_type: str | None) -> None:
        print("(🧊 patch) Uploading file with key:", key)
        file.seek(0)
        self.files[key] = (file.read(), content_type)

    def download_file(self, key: str):
        print("(🧊 patch) Downloading file with key:", key)
        file_bytes, _ = self.files[key]
        return io.BytesIO(file_bytes)

    def upload_audio(self, audio: AudioSegment, key: str, format: str) -> None:
        buf = io.BytesIO()
        audio.export(buf, format=format)
        buf.seek(0)
        self.upload_file(buf, key, f"audio/{format.lower()}")

    def download_audio(self, key: str) -> AudioSegment:
        buf = self.download_file(key)
        return AudioSegment.from_file(buf)


test_storage = TestObjectStorage()
