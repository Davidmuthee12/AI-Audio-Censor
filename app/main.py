from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from scalar_fastapi import get_scalar_api_reference

from app.api.router.router import master_router
from app.config import api_settings
from app.core.exceptions import add_exception_handlers

# Main FastAPI instance
app = FastAPI(
    docs_url=None,
    redoc_url=None,
    openapi_url="/openapi.json" if api_settings.ENABLE_DOCS else None,
    generate_unique_id_function=lambda route: route.name,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[api_settings.FRONTEND_URL],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "OPTIONS"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(master_router)

# Add exception handlers
add_exception_handlers(app)


@app.get("/health", include_in_schema=False)
def health_check():
    return {"status": "ok"}


# Scalar docs endpoint
if api_settings.ENABLE_DOCS:

    @app.get("/docs", include_in_schema=False)
    def scalar_docs():
        return get_scalar_api_reference(
            openapi_url=app.openapi_url,
            title="API Docs",
        )
