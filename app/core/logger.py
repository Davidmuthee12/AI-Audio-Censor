import logging

from logtail import LogtailHandler

from app.config import api_settings

handler = LogtailHandler(
    source_token=api_settings.TELEMETRY_SOURCE_TOKEN,
    host=api_settings.TELEMETRY_HOST_URL,
)
handler.setFormatter(logging.Formatter(fmt="%(levelname)s: %(message)s"))

logger = logging.getLogger("censur")

logger.setLevel(logging.INFO)

logger.handlers.clear()
logger.addHandler(handler)
