"""Tests for the product service layer."""

import pytest

from eplm.models.lifecycle import LifecyclePhase
from eplm.schemas.product import (
    PhaseTransitionRequest,
    ProductCreate,
    ProductRevisionCreate,
    ProductUpdate,
)
from eplm.services.product_service import (
    DuplicatePartNumberError,
    InvalidTransitionError,
    ProductNotFoundError,
    ProductService,
)


@pytest.fixture
def svc(db_session):
    return ProductService(db_session)


@pytest.fixture
async def sample_product(svc):
    return await svc.create(
        ProductCreate(
            part_number="TEST-001",
            name="Test Product",
            description="A test product",
            category="Test",
        )
    )


class TestProductCreate:
    async def test_create_product(self, svc):
        product = await svc.create(
            ProductCreate(part_number="PRD-001", name="Widget")
        )
        assert product.part_number == "PRD-001"
        assert product.name == "Widget"
        assert product.phase == LifecyclePhase.CONCEPT

    async def test_duplicate_part_number_rejected(self, svc, sample_product):
        with pytest.raises(DuplicatePartNumberError):
            await svc.create(
                ProductCreate(part_number="TEST-001", name="Duplicate")
            )


class TestProductGet:
    async def test_get_existing(self, svc, sample_product):
        fetched = await svc.get(sample_product.id)
        assert fetched.part_number == "TEST-001"

    async def test_get_nonexistent_raises(self, svc):
        with pytest.raises(ProductNotFoundError):
            await svc.get("nonexistent-id")


class TestProductUpdate:
    async def test_update_name(self, svc, sample_product):
        updated = await svc.update(
            sample_product.id, ProductUpdate(name="Renamed")
        )
        assert updated.name == "Renamed"

    async def test_partial_update(self, svc, sample_product):
        updated = await svc.update(
            sample_product.id, ProductUpdate(category="Updated Category")
        )
        assert updated.category == "Updated Category"
        assert updated.name == "Test Product"  # unchanged


class TestPhaseTransition:
    async def test_valid_transition(self, svc, sample_product):
        result = await svc.transition_phase(
            sample_product.id,
            PhaseTransitionRequest(target_phase=LifecyclePhase.DESIGN),
        )
        assert result.phase == LifecyclePhase.DESIGN

    async def test_invalid_transition_raises(self, svc, sample_product):
        with pytest.raises(InvalidTransitionError):
            await svc.transition_phase(
                sample_product.id,
                PhaseTransitionRequest(target_phase=LifecyclePhase.PRODUCTION),
            )


class TestProductRevision:
    async def test_create_revision(self, svc, sample_product):
        rev = await svc.create_revision(
            sample_product.id,
            ProductRevisionCreate(revision="A", change_summary="Initial release"),
        )
        assert rev.revision == "A"
        assert rev.phase_at_creation == LifecyclePhase.CONCEPT

    async def test_list_revisions(self, svc, sample_product):
        await svc.create_revision(
            sample_product.id, ProductRevisionCreate(revision="A")
        )
        await svc.create_revision(
            sample_product.id, ProductRevisionCreate(revision="B")
        )
        revisions = await svc.get_revisions(sample_product.id)
        assert len(revisions) == 2


class TestProductDelete:
    async def test_delete_product(self, svc, sample_product):
        await svc.delete(sample_product.id)
        with pytest.raises(ProductNotFoundError):
            await svc.get(sample_product.id)
