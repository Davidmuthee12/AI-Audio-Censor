from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse


class CensurException(Exception):
    status_code = status.HTTP_400_BAD_REQUEST
    default_message = "Censur error"

    def __init__(self, message: str | None = None):
        self.message = message or self.default_message
        super().__init__(self.message)


class AudioNotFound(CensurException):
    status_code = status.HTTP_404_NOT_FOUND
    default_message = "Audio not found"


class CensoredAudioNotFound(CensurException):
    status_code = status.HTTP_404_NOT_FOUND
    default_message = "Censored audio not found"


class AudioTranscriptionNotReady(CensurException):
    status_code = status.HTTP_409_CONFLICT
    default_message = "Audio transcription is not ready"


class AudioProcessingInProgress(CensurException):
    status_code = status.HTTP_409_CONFLICT
    default_message = "Audio is currently being processed."


class InvalidAudioFileType(CensurException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_message = "Invalid file type. Please upload an audio file."


class FileTooLarge(CensurException):
    status_code = status.HTTP_413_CONTENT_TOO_LARGE

    def __init__(self, max_size_bytes: int):
        max_size_mb = max_size_bytes // (1024 * 1024)
        super().__init__(
            message=f"File too large. Maximum allowed size is {max_size_mb}MB."
        )


class AudioDurationTooLong(CensurException):
    status_code = status.HTTP_413_CONTENT_TOO_LARGE

    def __init__(self, max_audio_duration_seconds: int):
        max_minutes = max_audio_duration_seconds // 60
        super().__init__(
            message=(
                "Audio duration too long. "
                f"Maximum allowed duration is {max_minutes} minutes."
            )
        )


class InsufficientCredits(CensurException):
    status_code = status.HTTP_402_PAYMENT_REQUIRED
    default_message = "Insufficient credits"


class UserNotFound(CensurException):
    status_code = status.HTTP_404_NOT_FOUND
    default_message = "User not found"


class CheckoutSessionCreationFailed(CensurException):
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    default_message = "Failed to create checkout session"


class InvalidWebhookSignature(CensurException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_message = "Invalid webhook signature"


def add_exception_handlers(app: FastAPI):
    def exception_handler(_: Request, exc: CensurException):
        return JSONResponse(
            status_code=exc.status_code,
            content={"message": exc.message},
        )

    @app.exception_handler(status.HTTP_500_INTERNAL_SERVER_ERROR)
    def internal_server_error_handler(_: Request, __: Exception):
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"message": "Internal server error"},
        )

    app.add_exception_handler(CensurException, exception_handler)
