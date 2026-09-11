from datetime import datetime
from uuid import UUID, uuid4

from sqlmodel import Field, SQLModel


class Audio(SQLModel, table=True):
    __tablename__ = "audio"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.now)

    file_path: str
    censored_file_path: str
