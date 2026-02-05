"""Analysis, reporting, and analytics API endpoints.

Addresses IFS complaints:
- "Getting reports is not very easy"
- "If you require a manual to download a report, something is plainly wrong with UX"
- Analytics gaps vs Oracle/SAP
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from eplm.database import get_db
from eplm.services.analysis_service import AnalysisService

router = APIRouter(prefix="/analysis", tags=["analysis"])


def _svc(db: AsyncSession = Depends(get_db)) -> AnalysisService:
    return AnalysisService(db)


@router.get("/where-used/{component_id}")
async def where_used(
    component_id: str, svc: AnalysisService = Depends(_svc)
):
    """Find all products and BOMs that use a specific component."""
    return await svc.where_used(component_id)


@router.get("/bom-compare")
async def compare_boms(
    bom_a: str,
    bom_b: str,
    svc: AnalysisService = Depends(_svc),
):
    """Compare two BOMs and return added, removed, and changed line items."""
    return await svc.compare_boms(bom_a, bom_b)


@router.get("/obsolescence-risk/{product_id}")
async def obsolescence_risk(
    product_id: str, svc: AnalysisService = Depends(_svc)
):
    """Assess component obsolescence risk for a product."""
    return await svc.obsolescence_risk_report(product_id)


@router.get("/product-dashboard/{product_id}")
async def product_dashboard(
    product_id: str, svc: AnalysisService = Depends(_svc)
):
    """Single-call comprehensive product health dashboard."""
    return await svc.product_dashboard(product_id)


@router.get("/global")
async def global_analytics(svc: AnalysisService = Depends(_svc)):
    """System-wide PLM health metrics."""
    return await svc.global_analytics()
