from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4

from sqlmodel import Field, Relationship, SQLModel


class AudioStatus(Enum):
    pending = "pending"
    processing = "processing"
    completed = "completed"
    failed = "failed"


class User(SQLModel, table=True):
    __tablename__ = "user"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.now)

    email: str
    password_hash: str

    audios: list["Audio"] = Relationship(
        back_populates="user",
        sa_relationship_kwargs={"lazy": "selectin"},
    )


class Audio(SQLModel, table=True):
    __tablename__ = "audio"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.now)

    file_path: str
    censored_file_path: str | None = Field(default=None)

    status: AudioStatus = Field(default=AudioStatus.pending)

    user_id: UUID = Field(foreign_key="user.id")
    user: User = Relationship(
        back_populates="audios",
        sa_relationship_kwargs={"lazy": "selectin"},
    )
