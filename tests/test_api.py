"""Integration tests for the REST API endpoints."""

import pytest


class TestHealthEndpoint:
    async def test_health(self, client):
        resp = await client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"


class TestProductAPI:
    async def test_create_product(self, client):
        resp = await client.post(
            "/api/v1/products",
            json={"part_number": "API-PRD-001", "name": "API Test Product"},
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["part_number"] == "API-PRD-001"
        assert data["phase"] == "concept"

    async def test_list_products(self, client):
        await client.post(
            "/api/v1/products",
            json={"part_number": "LIST-001", "name": "Product 1"},
        )
        await client.post(
            "/api/v1/products",
            json={"part_number": "LIST-002", "name": "Product 2"},
        )
        resp = await client.get("/api/v1/products")
        assert resp.status_code == 200
        assert len(resp.json()) == 2

    async def test_get_product(self, client):
        create_resp = await client.post(
            "/api/v1/products",
            json={"part_number": "GET-001", "name": "Get Test"},
        )
        product_id = create_resp.json()["id"]
        resp = await client.get(f"/api/v1/products/{product_id}")
        assert resp.status_code == 200
        assert resp.json()["part_number"] == "GET-001"

    async def test_get_nonexistent_product(self, client):
        resp = await client.get("/api/v1/products/nonexistent")
        assert resp.status_code == 404

    async def test_update_product(self, client):
        create_resp = await client.post(
            "/api/v1/products",
            json={"part_number": "UPD-001", "name": "Original"},
        )
        product_id = create_resp.json()["id"]
        resp = await client.patch(
            f"/api/v1/products/{product_id}",
            json={"name": "Updated"},
        )
        assert resp.status_code == 200
        assert resp.json()["name"] == "Updated"

    async def test_phase_transition(self, client):
        create_resp = await client.post(
            "/api/v1/products",
            json={"part_number": "PHASE-001", "name": "Phase Test"},
        )
        product_id = create_resp.json()["id"]
        resp = await client.post(
            f"/api/v1/products/{product_id}/transition",
            json={"target_phase": "design"},
        )
        assert resp.status_code == 200
        assert resp.json()["phase"] == "design"

    async def test_invalid_phase_transition(self, client):
        create_resp = await client.post(
            "/api/v1/products",
            json={"part_number": "PHASE-002", "name": "Phase Test 2"},
        )
        product_id = create_resp.json()["id"]
        resp = await client.post(
            f"/api/v1/products/{product_id}/transition",
            json={"target_phase": "production"},
        )
        assert resp.status_code == 400

    async def test_duplicate_part_number(self, client):
        await client.post(
            "/api/v1/products",
            json={"part_number": "DUP-001", "name": "First"},
        )
        resp = await client.post(
            "/api/v1/products",
            json={"part_number": "DUP-001", "name": "Second"},
        )
        assert resp.status_code == 409

    async def test_delete_product(self, client):
        create_resp = await client.post(
            "/api/v1/products",
            json={"part_number": "DEL-001", "name": "Delete Me"},
        )
        product_id = create_resp.json()["id"]
        resp = await client.delete(f"/api/v1/products/{product_id}")
        assert resp.status_code == 204
        resp = await client.get(f"/api/v1/products/{product_id}")
        assert resp.status_code == 404


class TestComponentAPI:
    async def test_create_component(self, client):
        resp = await client.post(
            "/api/v1/components",
            json={
                "part_number": "CMP-API-001",
                "name": "Test Resistor",
                "category": "resistor",
                "value": "4.7kΩ",
                "package": "0402",
            },
        )
        assert resp.status_code == 201
        assert resp.json()["category"] == "resistor"

    async def test_search_components(self, client):
        await client.post(
            "/api/v1/components",
            json={"part_number": "SRCH-001", "name": "Special MCU"},
        )
        resp = await client.get("/api/v1/components/search", params={"q": "Special"})
        assert resp.status_code == 200
        assert len(resp.json()) >= 1


class TestBomAPI:
    async def test_create_bom_and_add_items(self, client):
        # Create product
        prod_resp = await client.post(
            "/api/v1/products",
            json={"part_number": "BOM-API-PRD", "name": "BOM Product"},
        )
        product_id = prod_resp.json()["id"]

        # Create component
        comp_resp = await client.post(
            "/api/v1/components",
            json={"part_number": "BOM-API-CMP", "name": "Capacitor"},
        )
        component_id = comp_resp.json()["id"]

        # Create BOM
        bom_resp = await client.post(
            "/api/v1/boms",
            json={"product_id": product_id, "revision": "1", "name": "Rev 1"},
        )
        assert bom_resp.status_code == 201
        bom_id = bom_resp.json()["id"]

        # Add line item
        item_resp = await client.post(
            f"/api/v1/boms/{bom_id}/items",
            json={
                "component_id": component_id,
                "reference": "C1",
                "quantity": 3,
                "unit_cost": 0.05,
            },
        )
        assert item_resp.status_code == 201
        assert item_resp.json()["quantity"] == 3

        # Check cost summary
        cost_resp = await client.get(f"/api/v1/boms/{bom_id}/cost-summary")
        assert cost_resp.status_code == 200
        assert cost_resp.json()["total_cost"] == pytest.approx(0.15)
