from fastapi import FastAPI
from scalar_fastapi import get_scalar_api_reference

from app.api.router.router import master_router
from app.core.exceptions import add_exception_handlers

# Main FastAPI instance
app = FastAPI(docs_url=None)

# Include API routes
app.include_router(master_router)

# Add exception handlers
add_exception_handlers(app)


# Scalar docs endpoint
@app.get("/docs", include_in_schema=False)
def scalar_docs():
    return get_scalar_api_reference(
        openapi_url=app.openapi_url,
        title="API Docs",
    )
