"""Integration tests for new API endpoints (approvals, supply chain, analysis, audit)."""

import pytest


class TestApprovalAPI:
    async def test_create_template_and_start_approval(self, client):
        # Create template
        template_resp = await client.post(
            "/api/v1/approvals/templates",
            json={
                "name": "Test Approval",
                "entity_type": "ecr",
                "steps": [
                    {"step_order": 1, "role": "lead"},
                    {"step_order": 2, "role": "manager"},
                ],
            },
        )
        assert template_resp.status_code == 201
        template_id = template_resp.json()["id"]
        assert len(template_resp.json()["steps"]) == 2

        # Start approval request
        req_resp = await client.post(
            "/api/v1/approvals/requests",
            json={
                "entity_type": "ecr",
                "entity_id": "some-ecr-id",
                "template_id": template_id,
                "title": "Approve test ECR",
            },
        )
        assert req_resp.status_code == 201
        request_id = req_resp.json()["id"]
        assert req_resp.json()["is_complete"] is False

        # Submit approval decision
        decide_resp = await client.post(
            f"/api/v1/approvals/requests/{request_id}/decide",
            json={
                "decided_by": "alice@example.com",
                "status": "approved",
                "comment": "LGTM",
            },
        )
        assert decide_resp.status_code == 200
        assert decide_resp.json()["current_step"] == 2

    async def test_list_pending_approvals(self, client):
        resp = await client.get("/api/v1/approvals/requests/pending")
        assert resp.status_code == 200


class TestSupplyChainAPI:
    async def test_alternate_component_lifecycle(self, client):
        # Create two components
        primary = await client.post(
            "/api/v1/components",
            json={"part_number": "SC-PRI-001", "name": "Primary Cap"},
        )
        alternate = await client.post(
            "/api/v1/components",
            json={"part_number": "SC-ALT-001", "name": "Alternate Cap"},
        )
        primary_id = primary.json()["id"]
        alt_id = alternate.json()["id"]

        # Add alternate
        resp = await client.post(
            "/api/v1/supply-chain/alternates",
            json={
                "primary_component_id": primary_id,
                "alternate_component_id": alt_id,
                "form_fit_function": True,
            },
        )
        assert resp.status_code == 201
        assert resp.json()["status"] == "proposed"

        # List alternates
        list_resp = await client.get(
            f"/api/v1/supply-chain/alternates/component/{primary_id}"
        )
        assert list_resp.status_code == 200
        assert len(list_resp.json()) == 1

    async def test_approved_vendor_lifecycle(self, client):
        comp = await client.post(
            "/api/v1/components",
            json={"part_number": "SC-VEND-001", "name": "Vendor Test"},
        )
        comp_id = comp.json()["id"]

        resp = await client.post(
            "/api/v1/supply-chain/vendors",
            json={
                "component_id": comp_id,
                "vendor_name": "Digi-Key",
                "vendor_pn": "DK-12345",
                "unit_cost": 0.50,
                "lead_time_days": 3,
            },
        )
        assert resp.status_code == 201
        assert resp.json()["vendor_name"] == "Digi-Key"


class TestManufacturerPartAPI:
    async def test_create_and_search_mpn(self, client):
        comp = await client.post(
            "/api/v1/components",
            json={"part_number": "MPN-TEST-001", "name": "MPN Test IC"},
        )
        comp_id = comp.json()["id"]

        resp = await client.post(
            "/api/v1/manufacturer-parts",
            json={
                "component_id": comp_id,
                "manufacturer": "Texas Instruments",
                "mpn": "TPS63070RNMR",
                "status": "active",
            },
        )
        assert resp.status_code == 201
        assert resp.json()["is_at_risk"] is False

        # Search by MPN
        search_resp = await client.get(
            "/api/v1/manufacturer-parts/search", params={"q": "TPS6307"}
        )
        assert search_resp.status_code == 200
        assert len(search_resp.json()) >= 1

    async def test_at_risk_mpn(self, client):
        comp = await client.post(
            "/api/v1/components",
            json={"part_number": "MPN-RISK-001", "name": "EOL IC"},
        )
        comp_id = comp.json()["id"]

        await client.post(
            "/api/v1/manufacturer-parts",
            json={
                "component_id": comp_id,
                "manufacturer": "NXP",
                "mpn": "LPC1768FBD100",
                "status": "eol",
            },
        )

        resp = await client.get("/api/v1/manufacturer-parts/at-risk")
        assert resp.status_code == 200
        assert len(resp.json()) >= 1
        assert any(m["mpn"] == "LPC1768FBD100" for m in resp.json())


class TestAnalysisAPI:
    async def test_where_used(self, client):
        # Create product, component, BOM, line item
        prod = await client.post(
            "/api/v1/products",
            json={"part_number": "WU-PRD-001", "name": "Where Used Product"},
        )
        comp = await client.post(
            "/api/v1/components",
            json={"part_number": "WU-CMP-001", "name": "Where Used Cap"},
        )
        bom = await client.post(
            "/api/v1/boms",
            json={
                "product_id": prod.json()["id"],
                "revision": "1",
                "name": "WU BOM",
            },
        )
        await client.post(
            f"/api/v1/boms/{bom.json()['id']}/items",
            json={
                "component_id": comp.json()["id"],
                "reference": "C1",
                "quantity": 1,
            },
        )

        resp = await client.get(
            f"/api/v1/analysis/where-used/{comp.json()['id']}"
        )
        assert resp.status_code == 200
        assert len(resp.json()) == 1

    async def test_bom_compare(self, client):
        prod = await client.post(
            "/api/v1/products",
            json={"part_number": "CMP-PRD-001", "name": "Compare Product"},
        )
        comp = await client.post(
            "/api/v1/components",
            json={"part_number": "CMP-CMP-001", "name": "Compare Resistor"},
        )
        bom_a = await client.post(
            "/api/v1/boms",
            json={
                "product_id": prod.json()["id"],
                "revision": "1",
                "name": "BOM A",
            },
        )
        await client.post(
            f"/api/v1/boms/{bom_a.json()['id']}/items",
            json={
                "component_id": comp.json()["id"],
                "reference": "R1",
                "quantity": 2,
                "unit_cost": 0.01,
            },
        )
        # Clone and compare
        bom_b = await client.post(
            f"/api/v1/boms/{bom_a.json()['id']}/clone",
            params={"new_revision": "2"},
        )

        resp = await client.get(
            "/api/v1/analysis/bom-compare",
            params={"bom_a": bom_a.json()["id"], "bom_b": bom_b.json()["id"]},
        )
        assert resp.status_code == 200
        assert resp.json()["summary"]["cost_delta"] == 0

    async def test_global_analytics(self, client):
        resp = await client.get("/api/v1/analysis/global")
        assert resp.status_code == 200
        assert "products_by_phase" in resp.json()
        assert "total_components" in resp.json()


class TestWebhookAPI:
    async def test_create_and_list_webhooks(self, client):
        resp = await client.post(
            "/api/v1/webhooks",
            json={
                "url": "https://example.com/hook",
                "event": "product.created",
                "description": "Notify on new products",
            },
        )
        assert resp.status_code == 201

        list_resp = await client.get("/api/v1/webhooks")
        assert list_resp.status_code == 200
        assert len(list_resp.json()) >= 1

    async def test_delete_webhook(self, client):
        create_resp = await client.post(
            "/api/v1/webhooks",
            json={
                "url": "https://example.com/delete-me",
                "event": "ecr.created",
            },
        )
        webhook_id = create_resp.json()["id"]

        del_resp = await client.delete(f"/api/v1/webhooks/{webhook_id}")
        assert del_resp.status_code == 204


class TestAuditAPI:
    async def test_recent_activity(self, client):
        resp = await client.get("/api/v1/audit/recent")
        assert resp.status_code == 200

    async def test_entity_history(self, client):
        resp = await client.get("/api/v1/audit/history/product/some-id")
        assert resp.status_code == 200


class TestMultiLevelBomAPI:
    async def test_create_sub_assembly_bom(self, client):
        prod = await client.post(
            "/api/v1/products",
            json={"part_number": "ML-PRD-001", "name": "Multi-Level Product"},
        )
        # Create top-level engineering BOM
        top_bom = await client.post(
            "/api/v1/boms",
            json={
                "product_id": prod.json()["id"],
                "revision": "1",
                "name": "Top-Level eBOM",
                "bom_type": "engineering",
                "level": 0,
            },
        )
        assert top_bom.status_code == 201
        assert top_bom.json()["bom_type"] == "engineering"
        assert top_bom.json()["level"] == 0

        # Create sub-assembly BOM
        sub_bom = await client.post(
            "/api/v1/boms",
            json={
                "product_id": prod.json()["id"],
                "parent_bom_id": top_bom.json()["id"],
                "revision": "1",
                "name": "Power Module Sub-Assembly",
                "bom_type": "engineering",
                "level": 1,
            },
        )
        assert sub_bom.status_code == 201
        assert sub_bom.json()["parent_bom_id"] == top_bom.json()["id"]
        assert sub_bom.json()["level"] == 1

    async def test_create_manufacturing_bom(self, client):
        prod = await client.post(
            "/api/v1/products",
            json={"part_number": "ML-PRD-002", "name": "mBOM Product"},
        )
        mbom = await client.post(
            "/api/v1/boms",
            json={
                "product_id": prod.json()["id"],
                "revision": "1",
                "name": "Manufacturing BOM",
                "bom_type": "manufacturing",
            },
        )
        assert mbom.status_code == 201
        assert mbom.json()["bom_type"] == "manufacturing"
