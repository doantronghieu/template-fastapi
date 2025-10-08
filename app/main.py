from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi
from fastapi.staticfiles import StaticFiles
from scalar_fastapi import get_scalar_api_reference

# Load .env file into os.environ before any imports that need env vars
load_dotenv()

from app.api import pages  # noqa: E402
from app.api.router import api_router  # noqa: E402
from app.core.admin import setup_admin  # noqa: E402
from app.core.config import settings  # noqa: E402
from app.core.database import init_db  # noqa: E402
from app.core.openapi_tags import get_openapi_tags, get_tag_groups  # noqa: E402
from app.core.templates import BASE_DIR  # noqa: E402


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup/shutdown events."""
    _ = app  # Unused but required by FastAPI signature
    # Startup: Initialize database tables
    await init_db()
    yield
    # Shutdown: cleanup if needed


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    lifespan=lifespan,
    openapi_tags=get_openapi_tags(
        extension_tags=[
            ext.replace("_", " ").title() for ext in settings.ENABLED_EXTENSIONS
        ]
    ),
)

# Mount static files
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")

# Setup page routes (templates)
app.include_router(pages.router)

# Setup API routes
app.include_router(api_router, prefix="/api")

# Setup admin interface
setup_admin(app)


def custom_openapi():
    """Customize OpenAPI schema with x-tagGroups for nested navigation."""
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        openapi_version=app.openapi_version,
        description=app.description,
        routes=app.routes,
        tags=app.openapi_tags,
    )

    # Add x-tagGroups for nested navigation in Scalar
    extension_tags = [
        ext.replace("_", " ").title() for ext in settings.ENABLED_EXTENSIONS
    ]
    openapi_schema["x-tagGroups"] = get_tag_groups(
        extension_tags=extension_tags if extension_tags else None
    )

    app.openapi_schema = openapi_schema
    return app.openapi_schema


# Override default OpenAPI schema generator
app.openapi = custom_openapi


@app.get("/scalar", include_in_schema=False)
async def scalar_html():
    return get_scalar_api_reference(
        openapi_url=app.openapi_url,
        title=app.title,
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=settings.PORT,
        reload=True,
    )
