from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.database.models import AudioStatus


class UserCreate(BaseModel):
    email: str
    password: str


class UserRead(BaseModel):
    id: UUID
    created_at: datetime
    email: str


class TokenData(BaseModel):
    access_token: str
    token_type: str


class AudioRead(BaseModel):
    id: UUID
    created_at: datetime
    updated_at: datetime
    name: str
    censored_file_path: str | None
    status: AudioStatus
    user_list: list[str] | None
    use_beep: bool
    sound_effect_id: UUID | None


class CensorOptions(BaseModel):
    user_list: list[str] | None = Field(default=None)
    use_beep: bool = Field(default=False)
    sound_effect_id: UUID | None = Field(default=None)


class SoundEffectRead(BaseModel):
    id: UUID
    created_at: datetime
    name: str
    file_path: str
