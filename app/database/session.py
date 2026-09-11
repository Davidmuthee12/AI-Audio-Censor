from sqlalchemy import create_engine
from sqlmodel import SQLModel

from app.config import settings

engine = create_engine(
    settings.DB_URL,
    echo=True,
)


def init_db():
    from app.database import models  # noqa: f401

    SQLModel.metadata.create_all(engine)
