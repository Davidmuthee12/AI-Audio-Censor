from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from scalar_fastapi import get_scalar_api_reference

from app.api.router.router import master_router
from app.utils import UPLOADS_DIR

# Main FastAPI instance
app = FastAPI(docs_url=None)

# Serve uploaded files
app.mount(
    "/uploads",
    StaticFiles(directory=UPLOADS_DIR),
    name="uploads",
)

# Include API routes
app.include_router(master_router)


# Scalar docs endpoint
@app.get("/docs", include_in_schema=False)
def scalar_docs():
    return get_scalar_api_reference(
        openapi_url=app.openapi_url,
        title="API Docs",
    )
