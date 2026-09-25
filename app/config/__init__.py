from pydantic import Field

from .api import APISettings, api_settings
from .base import AppBaseSettings
from .shared import (
    DatabaseSettings,
    ObjectStorageSettings,
    db_settings,
    storage_settings,
)
from .worker import WorkerSettings, worker_settings


class Settings(AppBaseSettings):
    DB_URL: str
    BROKER_URL: str
    JWT_SECRET: str | None = None
    JWT_ALGORITHM: str | None = None
    R2_ACCESS_KEY_ID: str
    R2_SECRET_ACCESS_KEY: str
    R2_ENDPOINT_URL: str
    R2_BUCKET_NAME: str
    REPLICATE_API_TOKEN: str
    POLAR_SERVER: str
    POLAR_PRODUCT_ID: str
    POLAR_API_TOKEN: str
    POLAR_WEBHOOK_SECRET: str
    PROPELAUTH_AUTH_URL: str
    PROPELAUTH_API_KEY: str
    PROPELAUTH_WEBHOOK_SECRET: str
    TELEMETRY_SOURCE_TOKEN: str
    TELEMETRY_HOST_URL: str
    FRONTEND_URL: str
    ENABLE_DOCS: bool = False


settings = Settings()

__all__ = [
    "APISettings",
    "DatabaseSettings",
    "ObjectStorageSettings",
    "WorkerSettings",
    "api_settings",
    "db_settings",
    "storage_settings",
    "worker_settings",
    "settings",
]
