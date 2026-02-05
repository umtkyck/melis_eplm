"""Tests for where-used analysis, BOM comparison, obsolescence, and analytics."""

import pytest

from eplm.models.alternate import AlternateStatus
from eplm.models.mpn_xref import ManufacturerStatus
from eplm.schemas.alternate import AlternateComponentCreate
from eplm.schemas.bom import BomCreate, BomLineItemCreate
from eplm.schemas.component import ComponentCreate
from eplm.schemas.mpn_xref import ManufacturerPartCreate
from eplm.schemas.product import ProductCreate
from eplm.services.alternate_service import AlternateService
from eplm.services.analysis_service import AnalysisService
from eplm.services.bom_service import BomService
from eplm.services.component_service import ComponentService
from eplm.services.mpn_service import MpnService
from eplm.services.product_service import ProductService


@pytest.fixture
async def setup_data(db_session):
    """Create a product with components, BOM, MPN data, and alternates."""
    prod_svc = ProductService(db_session)
    comp_svc = ComponentService(db_session)
    bom_svc = BomService(db_session)
    mpn_svc = MpnService(db_session)
    alt_svc = AlternateService(db_session)

    product = await prod_svc.create(
        ProductCreate(part_number="ANAL-PRD-001", name="Analysis Test Product")
    )
    resistor = await comp_svc.create(
        ComponentCreate(part_number="ANAL-R1", name="Test Resistor")
    )
    cap = await comp_svc.create(
        ComponentCreate(part_number="ANAL-C1", name="Test Capacitor")
    )
    alt_resistor = await comp_svc.create(
        ComponentCreate(part_number="ANAL-R1-ALT", name="Alt Resistor")
    )

    bom = await bom_svc.create(
        BomCreate(product_id=product.id, revision="1", name="Test BOM")
    )
    await bom_svc.add_line_item(
        bom.id,
        BomLineItemCreate(
            component_id=resistor.id, reference="R1", quantity=4, unit_cost=0.01
        ),
    )
    await bom_svc.add_line_item(
        bom.id,
        BomLineItemCreate(
            component_id=cap.id, reference="C1", quantity=2, unit_cost=0.05
        ),
    )

    # Add an at-risk MPN
    await mpn_svc.create(
        ManufacturerPartCreate(
            component_id=resistor.id,
            manufacturer="Yageo",
            mpn="RC0402-10K",
            status=ManufacturerStatus.NRND,
        )
    )

    # Add an approved alternate
    alt = await alt_svc.add_alternate(
        AlternateComponentCreate(
            primary_component_id=resistor.id,
            alternate_component_id=alt_resistor.id,
            form_fit_function=True,
        )
    )
    # Approve it
    from eplm.schemas.alternate import AlternateComponentUpdate
    await alt_svc.update_alternate(
        alt.id, AlternateComponentUpdate(status=AlternateStatus.APPROVED)
    )

    return {
        "product": product,
        "resistor": resistor,
        "cap": cap,
        "bom": bom,
    }


@pytest.fixture
def svc(db_session):
    return AnalysisService(db_session)


class TestWhereUsed:
    async def test_where_used_finds_component(self, svc, setup_data):
        usage = await svc.where_used(setup_data["resistor"].id)
        assert len(usage) == 1
        assert usage[0]["reference"] == "R1"
        assert usage[0]["product_id"] == setup_data["product"].id

    async def test_where_used_empty_for_unused(self, svc, setup_data):
        usage = await svc.where_used("nonexistent-id")
        assert len(usage) == 0


class TestBomComparison:
    async def test_compare_identical_boms(self, svc, db_session, setup_data):
        bom_svc = BomService(db_session)
        cloned = await bom_svc.clone_bom(setup_data["bom"].id, "2")
        diff = await svc.compare_boms(setup_data["bom"].id, cloned.id)
        assert diff["summary"]["items_added"] == 0
        assert diff["summary"]["items_removed"] == 0
        assert diff["summary"]["items_changed"] == 0
        assert diff["summary"]["cost_delta"] == 0

    async def test_compare_boms_with_changes(self, svc, db_session, setup_data):
        bom_svc = BomService(db_session)
        comp_svc = ComponentService(db_session)

        # Create a second BOM with different items
        new_comp = await comp_svc.create(
            ComponentCreate(part_number="ANAL-NEW-1", name="New Component")
        )
        bom_b = await bom_svc.create(
            BomCreate(
                product_id=setup_data["product"].id, revision="3", name="Modified BOM"
            )
        )
        # Same R1 but different quantity
        await bom_svc.add_line_item(
            bom_b.id,
            BomLineItemCreate(
                component_id=setup_data["resistor"].id,
                reference="R1",
                quantity=8,
                unit_cost=0.01,
            ),
        )
        # New component added
        await bom_svc.add_line_item(
            bom_b.id,
            BomLineItemCreate(
                component_id=new_comp.id,
                reference="U1",
                quantity=1,
                unit_cost=5.00,
            ),
        )

        diff = await svc.compare_boms(setup_data["bom"].id, bom_b.id)
        assert diff["summary"]["items_added"] == 1  # U1 added
        assert diff["summary"]["items_removed"] == 1  # C1 removed
        assert diff["summary"]["items_changed"] == 1  # R1 quantity changed


class TestObsolescenceRisk:
    async def test_risk_report(self, svc, setup_data):
        report = await svc.obsolescence_risk_report(setup_data["product"].id)
        assert report["total_components"] == 2
        assert report["at_risk"] == 1  # resistor has NRND MPN
        assert report["risk_score"] == 50.0
        assert report["risk_items"][0]["approved_alternates"] == 1

    async def test_risk_report_empty_product(self, svc, db_session):
        prod_svc = ProductService(db_session)
        product = await prod_svc.create(
            ProductCreate(part_number="EMPTY-PRD", name="Empty Product")
        )
        report = await svc.obsolescence_risk_report(product.id)
        assert report["total_components"] == 0
        assert report["risk_score"] == 0.0


class TestProductDashboard:
    async def test_dashboard(self, svc, setup_data):
        dashboard = await svc.product_dashboard(setup_data["product"].id)
        assert dashboard["product"]["part_number"] == "ANAL-PRD-001"
        assert dashboard["bom"]["total_bom_revisions"] >= 1
        assert dashboard["bom"]["component_count"] == 2
        assert dashboard["obsolescence"]["at_risk_components"] == 1


class TestGlobalAnalytics:
    async def test_global_analytics(self, svc, setup_data):
        analytics = await svc.global_analytics()
        assert analytics["total_components"] >= 2
        assert "concept" in analytics["products_by_phase"]
        assert analytics["at_risk_manufacturer_parts"] >= 1
