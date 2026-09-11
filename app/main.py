from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, UploadFile
from fastapi.staticfiles import StaticFiles
from scalar_fastapi import get_scalar_api_reference
from sqlmodel import Session

from app.audio_censor import AudioCensor
from app.database.models import Audio
from app.database.session import get_session, init_db

UPLOADS_DIR = "uploads"


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    print("🟢 Starting up...")
    yield
    print("🔴 ...shutting down!")


app = FastAPI(docs_url=None, lifespan=lifespan)
app.mount(
    "/uploads",
    StaticFiles(directory=UPLOADS_DIR),
    name="uploads",
)

ac = AudioCensor()


def save_file(upload_file: UploadFile, path: str):
    with open(path, "wb") as buffer:
        buffer.write(upload_file.file.read())


@app.post("/censor")
def censor_audio(audio_file: UploadFile, session: Session = Depends(get_session)):
    file_path = f"{UPLOADS_DIR}/{audio_file.filename}"
    output_path = f"{UPLOADS_DIR}/censored_{audio_file.filename}"

    audio = Audio(
        file_path=file_path,
        censored_file_path=output_path,
    )
    session.add(audio)
    session.commit()
    session.refresh(audio)

    save_file(audio_file, file_path)

    words = ac.transcribe_audio(file_path)
    ac.mute_audio(
        input_path=file_path,
        output_path=output_path,
        word_segments=ac.detect_profanity(words),
    )

    return {
        "id": audio.id,
        "url": f"/uploads/censored_{audio_file.filename}",
    }


@app.get("/docs", include_in_schema=False)
def scalar_docs():
    return get_scalar_api_reference(
        openapi_url=app.openapi_url,
        title="API Docs",
    )
