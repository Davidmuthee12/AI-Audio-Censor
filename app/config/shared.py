from .base import AppBaseSettings


class DatabaseSettings(AppBaseSettings):
    DB_URL: str
    BROKER_URL: str


class ObjectStorageSettings(AppBaseSettings):
    R2_ACCESS_KEY_ID: str
    R2_SECRET_ACCESS_KEY: str
    R2_ENDPOINT_URL: str
    R2_BUCKET_NAME: str


db_settings = DatabaseSettings()
storage_settings = ObjectStorageSettings()
