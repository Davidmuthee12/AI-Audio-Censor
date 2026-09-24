import logging

from logtail import LogtailHandler

from app.config import settings

handler = LogtailHandler(
    source_token=settings.TELEMETRY_SOURCE_TOKEN,
    host=settings.TELEMETRY_HOST_URL,
)
handler.setFormatter(logging.Formatter(fmt="%(levelname)s: %(message)s"))

logger = logging.getLogger("censur")

logger.setLevel(logging.INFO)

logger.handlers.clear()
logger.addHandler(handler)
