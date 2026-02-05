"""FastAPI application factory."""

from contextlib import asynccontextmanager

from fastapi import FastAPI

from eplm.config import settings
from eplm.database import engine
from eplm.models.base import Base


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Create database tables on startup."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        description=(
            "Product Lifecycle Management API for electronics product development. "
            "Manages products, components, BOMs, engineering changes, documents, "
            "and regulatory compliance throughout the product lifecycle."
        ),
        lifespan=lifespan,
    )

    # Import models so they are registered with Base.metadata
    import eplm.models  # noqa: F401

    from eplm.api.boms import router as boms_router
    from eplm.api.changes import router as changes_router
    from eplm.api.compliance import router as compliance_router
    from eplm.api.components import router as components_router
    from eplm.api.documents import router as documents_router
    from eplm.api.products import router as products_router

    prefix = settings.api_prefix
    app.include_router(products_router, prefix=prefix)
    app.include_router(components_router, prefix=prefix)
    app.include_router(boms_router, prefix=prefix)
    app.include_router(changes_router, prefix=prefix)
    app.include_router(documents_router, prefix=prefix)
    app.include_router(compliance_router, prefix=prefix)

    @app.get("/health")
    async def health():
        return {"status": "ok", "service": settings.app_name}

    return app


app = create_app()
