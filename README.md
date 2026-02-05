# MELIS ePLM — Electronics Product Lifecycle Management

A REST API for managing the full lifecycle of electronics products, from concept through production to end-of-life. Built with FastAPI, SQLAlchemy 2.0 (async), and Pydantic v2.

Designed specifically for electronics product development workflows, addressing common pain points reported by users of legacy PLM/ERP systems (rigid customization, poor search, missing approval automation, BOM fragility, limited analytics, weak integration).

## Modules

### Core PLM

| Module | Description |
|--------|-------------|
| **Product Management** | Products with governed lifecycle state machine (concept → obsolete) |
| **Component Library** | Electronic components with manufacturer data, packages, RoHS, and search |
| **Bill of Materials** | Multi-level hierarchical BOMs, eBOM/mBOM types, cost roll-ups, cloning |
| **Engineering Changes** | ECR/ECO workflow with status transition enforcement |
| **Document Control** | Schematics, PCB layouts, Gerbers, test reports with revision history |
| **Compliance Tracking** | CE, FCC, UL, RoHS, REACH certification status per product |

### New — Addressing Legacy PLM Pain Points

| Module | IFS Pain Point Addressed | What It Does |
|--------|--------------------------|-------------|
| **Approval Workflows** | "No automatic approval routines", rigid permissions | Reusable multi-step approval templates with role-based chains |
| **Audit Trail** | No change history, no accountability | Immutable log of every create/update/delete/transition |
| **Supply Chain (Alternates + AVL)** | eBOM-to-mBOM friction, single-source risk | Alternate components, approved vendor list per part |
| **Manufacturer Part Tracking** | CAD-to-ERP integration fragility | MPN cross-reference, lifecycle tracking (NRND/LTB/EOL/Obsolete) |
| **Where-Used Analysis** | No component impact visibility | Find all products/BOMs using a specific component |
| **BOM Comparison** | "BOM change management is fragile" | Diff between BOM revisions — added/removed/changed items |
| **Obsolescence Risk Scoring** | No proactive supply chain risk | Per-product risk report based on MPN lifecycle + alternate availability |
| **Product Dashboard** | "Getting reports is not very easy" | Single-call comprehensive product health summary |
| **Global Analytics** | Analytics gaps vs Oracle/SAP | System-wide metrics (products by phase, open ECRs, at-risk parts) |
| **Webhooks** | "Integration options with third-party solutions are limited" | Event-driven notifications for external systems (CAD, ERP, Slack) |

## Lifecycle Phases

Products move through a governed state machine:

```
CONCEPT → DESIGN → PROTOTYPE → VALIDATION → PRE_PRODUCTION → PRODUCTION → ACTIVE → END_OF_LIFE → OBSOLETE
```

Early phases (up to PRE_PRODUCTION) can also transition to CANCELLED. Backward transitions are allowed for rework (e.g. PROTOTYPE → DESIGN).

## Project Structure

```
src/eplm/
├── api/                    # FastAPI routers (12 modules)
│   ├── products.py         # Product CRUD + lifecycle transitions
│   ├── components.py       # Component library + search
│   ├── boms.py             # Multi-level BOM management
│   ├── changes.py          # ECR/ECO workflow
│   ├── documents.py        # Document + revision management
│   ├── compliance.py       # Standards + compliance records
│   ├── approvals.py        # Approval workflow engine
│   ├── alternates.py       # Alternate components + AVL
│   ├── mpn.py              # Manufacturer part cross-reference
│   ├── analysis.py         # Where-used, BOM diff, dashboards
│   ├── audit.py            # Audit trail queries
│   └── webhooks.py         # Webhook subscription management
├── models/                 # SQLAlchemy ORM models (22 tables)
│   ├── base.py             # Declarative base with id, timestamps
│   ├── lifecycle.py        # Phase enum + transition rules
│   ├── product.py          # Product + ProductRevision
│   ├── component.py        # Component + ComponentRevision
│   ├── bom.py              # BillOfMaterials (multi-level) + BomLineItem
│   ├── change.py           # ChangeRequest + ChangeOrder + ChangeOrderItem
│   ├── document.py         # Document + DocumentRevision
│   ├── compliance.py       # ComplianceStandard + ComplianceRecord
│   ├── approval.py         # ApprovalTemplate + ApprovalRequest + decisions
│   ├── alternate.py        # AlternateComponent + ApprovedVendor
│   ├── mpn_xref.py         # ManufacturerPart (lifecycle tracking)
│   ├── audit.py            # AuditLog (immutable)
│   └── webhook.py          # WebhookSubscription
├── schemas/                # Pydantic v2 request/response schemas
├── services/               # Business logic (9 service classes)
├── app.py                  # FastAPI application factory
├── config.py               # Settings (env-based)
└── database.py             # Async engine + session
tests/                      # pytest test suite (79 tests)
scripts/seed_data.py        # Sample data loader
alembic/                    # Database migrations
```

## Quick Start

```bash
# Install
pip install -e ".[dev]"

# Run the server (auto-creates tables on startup)
python -m eplm

# Or with uvicorn directly
uvicorn eplm.app:app --reload

# Seed sample data
python scripts/seed_data.py

# Run tests (79 tests)
pytest
```

The API is available at `http://localhost:8000`. Interactive docs at `/docs`.

## API Overview

All endpoints are under `/api/v1`.

### Products
- `POST /products` — Create a product
- `GET /products` — List (filter by phase, category)
- `POST /products/{id}/transition` — Advance lifecycle phase
- `POST /products/{id}/revisions` — Create a revision snapshot

### Components
- `POST /components` — Register a component
- `GET /components/search?q=STM32` — Search by part number/name/MPN
- `GET /components?rohs_only=true&category=ic` — Filter by attributes

### Bill of Materials (Multi-Level)
- `POST /boms` — Create a BOM (eBOM, mBOM, sBOM, or prototype type)
- `POST /boms` — Create sub-assembly BOM (set `parent_bom_id` + `level`)
- `POST /boms/{id}/items` — Add a line item (ref designator + component)
- `GET /boms/{id}/cost-summary` — Cost breakdown
- `POST /boms/{id}/clone?new_revision=2` — Clone BOM to new revision

### Engineering Changes
- `POST /changes/ecr` — File a change request
- `PATCH /changes/ecr/{id}` — Progress ECR through review
- `POST /changes/eco` — Create a change order (requires approved ECR)

### Approval Workflows
- `POST /approvals/templates` — Create reusable approval chain
- `POST /approvals/requests` — Launch approval for any entity
- `POST /approvals/requests/{id}/decide` — Approve/reject current step
- `GET /approvals/requests/pending` — View all pending approvals

### Supply Chain
- `POST /supply-chain/alternates` — Register alternate component
- `GET /supply-chain/alternates/component/{id}` — List approved alternates
- `POST /supply-chain/vendors` — Add vendor to AVL
- `GET /supply-chain/vendors/component/{id}` — List approved vendors

### Manufacturer Parts
- `POST /manufacturer-parts` — Register MPN cross-reference
- `GET /manufacturer-parts/search?q=TPS6307` — Search by MPN
- `GET /manufacturer-parts/at-risk` — All NRND/LTB/EOL/Obsolete parts
- `GET /manufacturer-parts/component/{id}` — Sources for a component

### Analysis & Reporting
- `GET /analysis/where-used/{component_id}` — All products using a component
- `GET /analysis/bom-compare?bom_a=X&bom_b=Y` — Diff between BOM revisions
- `GET /analysis/obsolescence-risk/{product_id}` — Supply chain risk report
- `GET /analysis/product-dashboard/{product_id}` — Comprehensive product health
- `GET /analysis/global` — System-wide PLM metrics

### Audit Trail
- `GET /audit/history/{entity_type}/{entity_id}` — Change history for entity
- `GET /audit/recent` — Recent system activity
- `GET /audit/actor/{actor}` — Activity by person

### Webhooks
- `POST /webhooks` — Subscribe to events (19 event types)
- `GET /webhooks` — List active subscriptions
- `DELETE /webhooks/{id}` — Remove subscription

### Compliance
- `POST /compliance/standards` — Define a standard (CE, FCC, etc.)
- `POST /compliance/records` — Track a product's compliance status
- `GET /compliance/summary/{product_id}` — Compliance dashboard

## Configuration

Environment variables (prefix `EPLM_`):

| Variable | Default | Description |
|----------|---------|-------------|
| `EPLM_DATABASE_URL` | `sqlite+aiosqlite:///./eplm.db` | Database connection string |
| `EPLM_DEBUG` | `false` | Enable debug mode + SQL logging |
| `EPLM_API_PREFIX` | `/api/v1` | API route prefix |

## Key Design Decisions

### Why Multi-Level BOMs?
Electronics products are naturally hierarchical (main board → power module → individual components). IFS and many PLM tools treat BOMs as flat lists, breaking under complex assemblies. Our BOMs support `parent_bom_id` and `level` for proper sub-assembly nesting.

### Why eBOM vs mBOM?
Engineering designs every screw and washer. Manufacturing needs kits, phantoms, and routings. The `bom_type` field (engineering/manufacturing/service/prototype) allows parallel BOM structures for the same product, addressing the eBOM-to-mBOM handoff friction that IFS users consistently report.

### Why Approval Templates?
IFS users complain about rigid, one-off permission workflows. Our approval engine uses reusable templates with ordered steps, role-based routing, and auto-approve timers — define once, reuse across all ECRs/ECOs/phase gates.

### Why Manufacturer Lifecycle Tracking?
Electronic components go through manufacturer lifecycle stages (Active → NRND → Last Time Buy → EOL → Obsolete) that directly impact product viability. Tracking this separately from internal lifecycle lets engineers proactively manage supply chain risk.

## Engineering Change Workflow

```
ECR: DRAFT → SUBMITTED → UNDER_REVIEW → APPROVED → (creates ECO)
ECO: DRAFT → PENDING_APPROVAL → APPROVED → IN_PROGRESS → COMPLETED
```

Both ECRs and ECOs enforce valid status transitions and reject invalid ones with descriptive errors.

## Webhook Events

Subscribe to any of these events for real-time integration:

```
product.created, product.updated, product.phase_changed
component.created, component.updated, component.obsolescence_alert
bom.created, bom.line_item_added, bom.line_item_removed, bom.cloned
ecr.created, ecr.status_changed, eco.created, eco.status_changed
document.created, document.revision_added
compliance.status_changed
approval.requested, approval.decided
```
