"""Where-used analysis, BOM comparison, obsolescence scoring, and product analytics.

Addresses multiple IFS pain points:
- "Report generation difficulty and analytics gaps"
- "Over 30% of manufacturing respondents unable to easily access data from PLM"
- BOM change management fragility
- No component cross-referencing across products

Electronics-specific analytics for supply chain risk, cost optimization, and
design reuse.
"""

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from eplm.models.alternate import AlternateComponent, AlternateStatus
from eplm.models.bom import BillOfMaterials, BomLineItem
from eplm.models.change import ChangeOrder, ChangeOrderStatus, ChangeRequest, ChangeRequestStatus
from eplm.models.compliance import ComplianceRecord, ComplianceStatus
from eplm.models.component import Component
from eplm.models.lifecycle import LifecyclePhase
from eplm.models.mpn_xref import ManufacturerPart, ManufacturerStatus
from eplm.models.product import Product


class AnalysisService:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ── Where-Used Analysis ──────────────────────────────────────

    async def where_used(self, component_id: str) -> list[dict]:
        """Find every product and BOM that uses a specific component.

        Critical for impact assessment: before obsoleting or changing a component,
        engineers need to know exactly which products are affected.
        """
        result = await self.db.execute(
            select(BomLineItem)
            .options(selectinload(BomLineItem.bom))
            .where(BomLineItem.component_id == component_id)
        )
        line_items = result.scalars().all()

        usage = []
        for li in line_items:
            usage.append({
                "bom_id": li.bom_id,
                "bom_name": li.bom.name if li.bom else "",
                "bom_revision": li.bom.revision if li.bom else "",
                "product_id": li.bom.product_id if li.bom else "",
                "reference": li.reference,
                "quantity": li.quantity,
            })
        return usage

    # ── BOM Comparison / Diff ─────────────────────────────────────

    async def compare_boms(self, bom_id_a: str, bom_id_b: str) -> dict:
        """Compare two BOMs and return added, removed, and changed line items.

        Addresses IFS complaint: "BOM change management is fragile" and
        "if BOM is only a static list, it breaks under change."
        """
        result_a = await self.db.execute(
            select(BomLineItem).where(BomLineItem.bom_id == bom_id_a)
        )
        result_b = await self.db.execute(
            select(BomLineItem).where(BomLineItem.bom_id == bom_id_b)
        )
        items_a = {li.reference: li for li in result_a.scalars().all()}
        items_b = {li.reference: li for li in result_b.scalars().all()}

        refs_a = set(items_a.keys())
        refs_b = set(items_b.keys())

        added = []
        for ref in refs_b - refs_a:
            li = items_b[ref]
            added.append({
                "reference": ref,
                "component_id": li.component_id,
                "quantity": li.quantity,
                "unit_cost": li.unit_cost,
            })

        removed = []
        for ref in refs_a - refs_b:
            li = items_a[ref]
            removed.append({
                "reference": ref,
                "component_id": li.component_id,
                "quantity": li.quantity,
                "unit_cost": li.unit_cost,
            })

        changed = []
        for ref in refs_a & refs_b:
            a, b = items_a[ref], items_b[ref]
            diffs = {}
            if a.component_id != b.component_id:
                diffs["component_id"] = {"from": a.component_id, "to": b.component_id}
            if a.quantity != b.quantity:
                diffs["quantity"] = {"from": a.quantity, "to": b.quantity}
            if abs(a.unit_cost - b.unit_cost) > 0.0001:
                diffs["unit_cost"] = {"from": a.unit_cost, "to": b.unit_cost}
            if a.do_not_populate != b.do_not_populate:
                diffs["do_not_populate"] = {"from": a.do_not_populate, "to": b.do_not_populate}
            if diffs:
                changed.append({"reference": ref, "changes": diffs})

        cost_a = sum(li.quantity * li.unit_cost for li in items_a.values())
        cost_b = sum(li.quantity * li.unit_cost for li in items_b.values())

        return {
            "bom_a": bom_id_a,
            "bom_b": bom_id_b,
            "added": added,
            "removed": removed,
            "changed": changed,
            "summary": {
                "items_added": len(added),
                "items_removed": len(removed),
                "items_changed": len(changed),
                "cost_a": round(cost_a, 4),
                "cost_b": round(cost_b, 4),
                "cost_delta": round(cost_b - cost_a, 4),
            },
        }

    # ── Component Obsolescence Risk ──────────────────────────────

    async def obsolescence_risk_report(self, product_id: str) -> dict:
        """Assess supply chain risk for a product based on component lifecycle status.

        Checks:
        1. Manufacturer part lifecycle status (NRND, LTB, EOL, Obsolete)
        2. Availability of approved alternates
        3. Number of qualified vendors
        """
        # Get all BOMs for this product
        bom_result = await self.db.execute(
            select(BillOfMaterials)
            .options(selectinload(BillOfMaterials.line_items))
            .where(
                BillOfMaterials.product_id == product_id,
                BillOfMaterials.is_active.is_(True),
            )
            .execution_options(populate_existing=True)
        )
        boms = bom_result.scalars().all()

        component_ids = set()
        for bom in boms:
            for li in bom.line_items:
                component_ids.add(li.component_id)

        if not component_ids:
            return {
                "product_id": product_id,
                "total_components": 0,
                "at_risk": 0,
                "risk_items": [],
                "risk_score": 0.0,
            }

        # Check manufacturer lifecycle status for each component
        mpn_result = await self.db.execute(
            select(ManufacturerPart)
            .where(ManufacturerPart.component_id.in_(component_ids))
        )
        mpn_map: dict[str, list[ManufacturerPart]] = {}
        for mpn in mpn_result.scalars().all():
            mpn_map.setdefault(mpn.component_id, []).append(mpn)

        # Check alternates
        alt_result = await self.db.execute(
            select(AlternateComponent)
            .where(
                AlternateComponent.primary_component_id.in_(component_ids),
                AlternateComponent.status == AlternateStatus.APPROVED,
            )
        )
        alt_map: dict[str, int] = {}
        for alt in alt_result.scalars().all():
            alt_map[alt.primary_component_id] = alt_map.get(alt.primary_component_id, 0) + 1

        risk_items = []
        for cid in component_ids:
            mpns = mpn_map.get(cid, [])
            at_risk_mpns = [m for m in mpns if m.is_at_risk]
            if at_risk_mpns:
                risk_items.append({
                    "component_id": cid,
                    "at_risk_mpns": [
                        {
                            "manufacturer": m.manufacturer,
                            "mpn": m.mpn,
                            "status": m.status.value,
                            "eol_date": str(m.eol_date) if m.eol_date else None,
                            "replacement_mpn": m.replacement_mpn,
                        }
                        for m in at_risk_mpns
                    ],
                    "approved_alternates": alt_map.get(cid, 0),
                    "total_sources": len(mpns),
                })

        total = len(component_ids)
        at_risk_count = len(risk_items)
        risk_score = round((at_risk_count / total) * 100, 1) if total > 0 else 0.0

        return {
            "product_id": product_id,
            "total_components": total,
            "at_risk": at_risk_count,
            "risk_score": risk_score,
            "risk_items": risk_items,
        }

    # ── Product Dashboard / Analytics ────────────────────────────

    async def product_dashboard(self, product_id: str) -> dict:
        """Comprehensive product health dashboard.

        Addresses IFS complaint: "Getting reports is not very easy" and
        "Generating a report takes some time."
        Provides a single-call summary of everything relevant to a product.
        """
        # Product details
        prod_result = await self.db.execute(
            select(Product).where(Product.id == product_id)
        )
        product = prod_result.scalar_one_or_none()
        if not product:
            return {"error": f"Product '{product_id}' not found"}

        # BOM summary
        bom_result = await self.db.execute(
            select(BillOfMaterials)
            .options(selectinload(BillOfMaterials.line_items))
            .where(BillOfMaterials.product_id == product_id)
            .execution_options(populate_existing=True)
        )
        boms = bom_result.scalars().all()
        active_bom = next((b for b in boms if b.is_active), None)

        # Compliance summary
        comp_result = await self.db.execute(
            select(ComplianceRecord).where(ComplianceRecord.product_id == product_id)
        )
        compliance_records = comp_result.scalars().all()
        compliance_passed = sum(1 for r in compliance_records if r.status == ComplianceStatus.PASSED and r.is_valid)
        compliance_total = len(compliance_records)

        # Change activity
        ecr_result = await self.db.execute(
            select(func.count(ChangeRequest.id)).where(
                ChangeRequest.product_id == product_id
            )
        )
        ecr_count = ecr_result.scalar() or 0

        open_ecr_result = await self.db.execute(
            select(func.count(ChangeRequest.id)).where(
                ChangeRequest.product_id == product_id,
                ChangeRequest.status.in_([
                    ChangeRequestStatus.DRAFT,
                    ChangeRequestStatus.SUBMITTED,
                    ChangeRequestStatus.UNDER_REVIEW,
                ]),
            )
        )
        open_ecrs = open_ecr_result.scalar() or 0

        # Obsolescence risk (lightweight — just count)
        risk_report = await self.obsolescence_risk_report(product_id)

        return {
            "product": {
                "id": product.id,
                "part_number": product.part_number,
                "name": product.name,
                "phase": product.phase.value,
                "owner": product.owner,
            },
            "bom": {
                "total_bom_revisions": len(boms),
                "active_bom_id": active_bom.id if active_bom else None,
                "active_bom_revision": active_bom.revision if active_bom else None,
                "total_cost": active_bom.total_cost if active_bom else 0,
                "component_count": active_bom.component_count if active_bom else 0,
            },
            "compliance": {
                "total_standards": compliance_total,
                "passed": compliance_passed,
                "completion_pct": round((compliance_passed / compliance_total) * 100, 1) if compliance_total > 0 else 0,
            },
            "changes": {
                "total_ecrs": ecr_count,
                "open_ecrs": open_ecrs,
            },
            "obsolescence": {
                "at_risk_components": risk_report["at_risk"],
                "risk_score": risk_report["risk_score"],
            },
        }

    # ── Global Analytics ──────────────────────────────────────────

    async def global_analytics(self) -> dict:
        """System-wide PLM health metrics.

        Addresses IFS complaint about needing better reporting and analytics.
        """
        # Products by phase
        phase_result = await self.db.execute(
            select(Product.phase, func.count(Product.id)).group_by(Product.phase)
        )
        products_by_phase = {row[0].value: row[1] for row in phase_result.all()}

        # Total components
        comp_count_result = await self.db.execute(select(func.count(Component.id)))
        total_components = comp_count_result.scalar() or 0

        # Open ECRs
        open_ecr_result = await self.db.execute(
            select(func.count(ChangeRequest.id)).where(
                ChangeRequest.status.in_([
                    ChangeRequestStatus.DRAFT,
                    ChangeRequestStatus.SUBMITTED,
                    ChangeRequestStatus.UNDER_REVIEW,
                ])
            )
        )
        open_ecrs = open_ecr_result.scalar() or 0

        # In-progress ECOs
        active_eco_result = await self.db.execute(
            select(func.count(ChangeOrder.id)).where(
                ChangeOrder.status.in_([
                    ChangeOrderStatus.DRAFT,
                    ChangeOrderStatus.PENDING_APPROVAL,
                    ChangeOrderStatus.APPROVED,
                    ChangeOrderStatus.IN_PROGRESS,
                ])
            )
        )
        active_ecos = active_eco_result.scalar() or 0

        # At-risk manufacturer parts
        risk_result = await self.db.execute(
            select(func.count(ManufacturerPart.id)).where(
                ManufacturerPart.status.in_([
                    ManufacturerStatus.NRND,
                    ManufacturerStatus.LAST_TIME_BUY,
                    ManufacturerStatus.EOL,
                    ManufacturerStatus.OBSOLETE,
                ])
            )
        )
        at_risk_mpns = risk_result.scalar() or 0

        return {
            "products_by_phase": products_by_phase,
            "total_components": total_components,
            "open_ecrs": open_ecrs,
            "active_ecos": active_ecos,
            "at_risk_manufacturer_parts": at_risk_mpns,
        }
