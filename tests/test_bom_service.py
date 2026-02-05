"""Tests for BOM service layer."""

import pytest

from eplm.models.component import ComponentCategoryEnum
from eplm.models.lifecycle import LifecyclePhase
from eplm.schemas.bom import BomCreate, BomLineItemCreate
from eplm.schemas.component import ComponentCreate
from eplm.schemas.product import ProductCreate
from eplm.services.bom_service import BomNotFoundError, BomService, LineItemConflictError
from eplm.services.component_service import ComponentService
from eplm.services.product_service import ProductService


@pytest.fixture
async def product(db_session):
    svc = ProductService(db_session)
    return await svc.create(ProductCreate(part_number="BOM-TEST-PRD", name="BOM Test Product"))


@pytest.fixture
async def component(db_session):
    svc = ComponentService(db_session)
    return await svc.create(
        ComponentCreate(
            part_number="BOM-TEST-CMP",
            name="Test Resistor",
            category=ComponentCategoryEnum.RESISTOR,
            value="10kΩ",
        )
    )


@pytest.fixture
def bom_svc(db_session):
    return BomService(db_session)


@pytest.fixture
async def sample_bom(bom_svc, product):
    return await bom_svc.create(
        BomCreate(product_id=product.id, revision="1", name="Test BOM")
    )


class TestBomCreate:
    async def test_create_bom(self, bom_svc, product):
        bom = await bom_svc.create(
            BomCreate(product_id=product.id, revision="1", name="Rev 1 BOM")
        )
        assert bom.product_id == product.id
        assert bom.revision == "1"
        assert bom.phase == LifecyclePhase.DESIGN


class TestBomLineItems:
    async def test_add_line_item(self, bom_svc, sample_bom, component):
        item = await bom_svc.add_line_item(
            sample_bom.id,
            BomLineItemCreate(
                component_id=component.id,
                reference="R1",
                quantity=2,
                unit_cost=0.01,
            ),
        )
        assert item.reference == "R1"
        assert item.quantity == 2

    async def test_duplicate_reference_rejected(self, bom_svc, sample_bom, component):
        await bom_svc.add_line_item(
            sample_bom.id,
            BomLineItemCreate(component_id=component.id, reference="R1"),
        )
        with pytest.raises(LineItemConflictError):
            await bom_svc.add_line_item(
                sample_bom.id,
                BomLineItemCreate(component_id=component.id, reference="R1"),
            )

    async def test_remove_line_item(self, bom_svc, sample_bom, component):
        item = await bom_svc.add_line_item(
            sample_bom.id,
            BomLineItemCreate(component_id=component.id, reference="R1"),
        )
        await bom_svc.remove_line_item(item.id)
        bom = await bom_svc.get(sample_bom.id)
        assert len(bom.line_items) == 0


class TestBomCostSummary:
    async def test_cost_summary(self, bom_svc, sample_bom, component):
        await bom_svc.add_line_item(
            sample_bom.id,
            BomLineItemCreate(
                component_id=component.id, reference="R1", quantity=10, unit_cost=0.05
            ),
        )
        summary = await bom_svc.get_cost_summary(sample_bom.id)
        assert summary["total_cost"] == pytest.approx(0.5)
        assert summary["component_count"] == 1


class TestBomClone:
    async def test_clone_bom(self, bom_svc, sample_bom, component):
        await bom_svc.add_line_item(
            sample_bom.id,
            BomLineItemCreate(component_id=component.id, reference="R1", quantity=5),
        )
        cloned = await bom_svc.clone_bom(sample_bom.id, "2")
        assert cloned.revision == "2"
        assert len(cloned.line_items) == 1
        assert cloned.line_items[0].reference == "R1"
        assert cloned.line_items[0].quantity == 5
        assert cloned.id != sample_bom.id
