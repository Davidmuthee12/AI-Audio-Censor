from app.config.base import AppBaseSettings


class APISettings(AppBaseSettings):
    ENABLE_DOCS: bool = False
    FRONTEND_URL: str

    POLAR_SERVER: str
    POLAR_PRODUCT_ID: str
    POLAR_API_TOKEN: str
    POLAR_WEBHOOK_SECRET: str

    PROPELAUTH_AUTH_URL: str
    PROPELAUTH_API_KEY: str
    PROPELAUTH_WEBHOOK_SECRET: str

    TELEMETRY_SOURCE_TOKEN: str
    TELEMETRY_HOST_URL: str


api_settings = APISettings()
