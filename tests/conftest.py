from uuid import uuid4

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel import Session, SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession

from app.api.dependencies import get_current_user
from app.api.router import audio as audio_router
from app.database.models import User
from app.database.session import get_session
from app.main import app
from app.service import audio as audio_service
from app.service import sound_effect as sound_effect_service
from app.worker import audio_censor as audio_censor_module
from app.worker.audio_censor import AudioCensor
from app.worker.tasks import (
    celery_app,
    detect_profanity_task,
    render_audio_task,
    transcribe_audio_task,
)

from .object_storage import test_storage

_test_user_id = uuid4()
_sample_audio_transcription = [
    {
        "end": 0.37,
        "word": "I've",
        "score": 0.697,
        "start": 0.27,
    },
    {
        "end": 0.511,
        "word": "been",
        "score": 0.529,
        "start": 0.391,
    },
    {
        "end": 0.571,
        "word": "in",
        "score": 0.97,
        "start": 0.531,
    },
    {
        "end": 0.752,
        "word": "this",
        "score": 0.818,
        "start": 0.611,
    },
    {
        "end": 1.134,
        "word": "business",
        "score": 0.86,
        "start": 0.792,
    },
    {
        "end": 2.09,
        "word": "15",
        "score": 0.81,
        "start": 1.21,
    },
    {
        "end": 2.258,
        "word": "years.",
        "score": 0.789,
        "start": 1.856,
    },
    {
        "end": 2.479,
        "word": "What's",
        "score": 0.338,
        "start": 2.298,
    },
    {
        "end": 2.599,
        "word": "your",
        "score": 0.118,
        "start": 2.499,
    },
    {
        "end": 2.881,
        "word": "name?",
        "score": 0.682,
        "start": 2.64,
    },
    {
        "end": 3.443,
        "word": "Fuck",
        "score": 0.788,
        "start": 3.162,
    },
    {
        "end": 3.985,
        "word": "you.",
        "score": 0.854,
        "start": 3.664,
    },
    {
        "end": 4.567,
        "word": "That's",
        "score": 0.913,
        "start": 4.226,
    },
    {
        "end": 4.889,
        "word": "my",
        "score": 0.99,
        "start": 4.688,
    },
    {
        "end": 5.15,
        "word": "name.",
        "score": 0.977,
        "start": 4.949,
    },
]


@pytest_asyncio.fixture(scope="session")
async def async_engine():
    engine = create_async_engine(
        "postgresql+asyncpg://postgres:very$trong@localhost:5432/censur_test",
    )

    # create tables before tests run
    async with engine.begin() as conn:
        from app.database import models  # noqa: F401

        await conn.run_sync(SQLModel.metadata.create_all)

    # add a test user to the database
    async with AsyncSession(engine) as session:
        session.add(
            User(
                id=_test_user_id,
                propelauth_id="test_id",
                email="user@test.site",
            )
        )
        await session.commit()
        print("(🧑) Added test user to database with ID:", _test_user_id)

    yield engine

    # remove tables after tests are done
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)

    # dispose of the engine to close
    # all connections after tests are done
    await engine.dispose()


@pytest_asyncio.fixture
async def patch_cloud_services(monkeypatch):
    sync_engine = create_engine(
        "postgresql+psycopg2://postgres:very$trong@localhost:5432/censur_test",
    )

    test_session_local = sessionmaker(
        bind=sync_engine,
        class_=Session,
        expire_on_commit=False,
    )

    # patch session local on AudioCensor
    monkeypatch.setattr(AudioCensor, "session_local", test_session_local, raising=False)
    # patch session local on tasks
    for task in (transcribe_audio_task, detect_profanity_task, render_audio_task):
        monkeypatch.setattr(task, "session_local", test_session_local, raising=False)

    # trancribe audio override
    def _transcribe_audio_stub(self, audio_path: str):
        print("(🔉 patch) Transcribed audio")
        return _sample_audio_transcription

    # patch transcribe_audio method
    monkeypatch.setattr(AudioCensor, "transcribe_audio", _transcribe_audio_stub)

    # patch storage on routers, services, and worker
    monkeypatch.setattr(audio_router, "storage", test_storage)
    monkeypatch.setattr(audio_service, "storage", test_storage)
    monkeypatch.setattr(sound_effect_service, "storage", test_storage)
    monkeypatch.setattr(audio_censor_module, "storage", test_storage)


@pytest_asyncio.fixture(scope="session")
async def client(async_engine):
    # set celery app to eager mode for testing
    celery_app.conf.update(
        task_always_eager=True,
        task_eager_propagates=True,
    )

    # override dependencies
    async def get_session_override():
        async with AsyncSession(async_engine, expire_on_commit=False) as session:
            print("(🗄️ patch) Overriding session")
            yield session

    async def get_current_user_override():
        async with AsyncSession(async_engine, expire_on_commit=False) as session:
            print("(🧑 patch) Overriding current user")
            return await session.get(User, _test_user_id)

    app.dependency_overrides[get_session] = get_session_override
    app.dependency_overrides[get_current_user] = get_current_user_override

    # test client
    async with AsyncClient(
        transport=ASGITransport(app), base_url="http://testserver"
    ) as client:
        yield client

    # reset celery app to default after tests are done
    celery_app.conf.update(
        task_always_eager=False,
        task_eager_propagates=False,
    )

    # clear dependency overrides after tests are done
    app.dependency_overrides.clear()
