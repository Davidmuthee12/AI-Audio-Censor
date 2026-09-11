from sqlalchemy import create_engine
from sqlmodel import Session, SQLModel

from app.config import settings

engine = create_engine(
    settings.DB_URL,
    echo=True,
)


def get_session():
    with Session(bind=engine, expire_on_commit=False) as session:
        yield session


def init_db():
    from app.database import models  # noqa: f401

    SQLModel.metadata.create_all(engine)
