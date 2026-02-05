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
        version="0.2.0",
        description=(
            "Product Lifecycle Management API for electronics product development. "
            "Manages products, components, BOMs, engineering changes, documents, "
            "regulatory compliance, approval workflows, supply chain (alternates/AVL), "
            "manufacturer part tracking, and provides analytics dashboards. "
            "Designed to address common PLM pain points reported by IFS users."
        ),
        lifespan=lifespan,
    )

    # Import models so they are registered with Base.metadata
    import eplm.models  # noqa: F401

    # Core modules
    from eplm.api.boms import router as boms_router
    from eplm.api.changes import router as changes_router
    from eplm.api.compliance import router as compliance_router
    from eplm.api.components import router as components_router
    from eplm.api.documents import router as documents_router
    from eplm.api.products import router as products_router

    # New modules — addressing IFS pain points
    from eplm.api.alternates import router as alternates_router
    from eplm.api.analysis import router as analysis_router
    from eplm.api.approvals import router as approvals_router
    from eplm.api.audit import router as audit_router
    from eplm.api.mpn import router as mpn_router
    from eplm.api.webhooks import router as webhooks_router

    prefix = settings.api_prefix
    app.include_router(products_router, prefix=prefix)
    app.include_router(components_router, prefix=prefix)
    app.include_router(boms_router, prefix=prefix)
    app.include_router(changes_router, prefix=prefix)
    app.include_router(documents_router, prefix=prefix)
    app.include_router(compliance_router, prefix=prefix)
    app.include_router(approvals_router, prefix=prefix)
    app.include_router(alternates_router, prefix=prefix)
    app.include_router(mpn_router, prefix=prefix)
    app.include_router(analysis_router, prefix=prefix)
    app.include_router(audit_router, prefix=prefix)
    app.include_router(webhooks_router, prefix=prefix)

    @app.get("/health")
    async def health():
        return {"status": "ok", "service": settings.app_name, "version": "0.2.0"}

    return app


app = create_app()
