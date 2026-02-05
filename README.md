# MELIS ePLM — Electronics Product Lifecycle Management

A REST API for managing the full lifecycle of electronics products, from concept through production to end-of-life. Built with FastAPI, SQLAlchemy 2.0 (async), and Pydantic v2.

## Core Modules

| Module | Description |
|--------|-------------|
| **Product Management** | Create and track electronics products through lifecycle phases |
| **Component Library** | Manage electronic components with manufacturer data, packages, and RoHS status |
| **Bill of Materials** | Versioned BOMs with line items, reference designators, cost roll-ups, and cloning |
| **Engineering Changes** | ECR/ECO workflow — request, review, approve, and implement design changes |
| **Document Control** | Track schematics, PCB layouts, Gerbers, test reports with revision history |
| **Compliance Tracking** | Monitor CE, FCC, UL, RoHS, REACH certification status per product |

## Lifecycle Phases

Products move through a governed state machine:

```
CONCEPT → DESIGN → PROTOTYPE → VALIDATION → PRE_PRODUCTION → PRODUCTION → ACTIVE → END_OF_LIFE → OBSOLETE
```

Early phases (up to PRE_PRODUCTION) can also transition to CANCELLED. Backward transitions are allowed for rework (e.g. PROTOTYPE → DESIGN).

## Project Structure

```
src/eplm/
├── api/                 # FastAPI routers (REST endpoints)
│   ├── products.py      # Product CRUD + lifecycle transitions
│   ├── components.py    # Component library management
│   ├── boms.py          # BOM management + cost summaries
│   ├── changes.py       # ECR/ECO workflow endpoints
│   ├── documents.py     # Document + revision management
│   └── compliance.py    # Standards + compliance records
├── models/              # SQLAlchemy ORM models
│   ├── base.py          # Declarative base with id, timestamps
│   ├── lifecycle.py     # Phase enum + transition rules
│   ├── product.py       # Product + ProductRevision
│   ├── component.py     # Component + ComponentRevision
│   ├── bom.py           # BillOfMaterials + BomLineItem
│   ├── change.py        # ChangeRequest + ChangeOrder
│   ├── document.py      # Document + DocumentRevision
│   └── compliance.py    # ComplianceStandard + ComplianceRecord
├── schemas/             # Pydantic request/response schemas
├── services/            # Business logic layer
├── app.py               # FastAPI application factory
├── config.py            # Settings (env-based)
└── database.py          # Async engine + session
tests/                   # pytest test suite (48 tests)
scripts/seed_data.py     # Sample data loader
alembic/                 # Database migrations
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

# Run tests
pytest
```

The API will be available at `http://localhost:8000`. Interactive docs at `/docs`.

## API Overview

All endpoints are under `/api/v1`. Key operations:

### Products
- `POST /api/v1/products` — Create a product
- `GET /api/v1/products` — List products (filter by phase, category)
- `POST /api/v1/products/{id}/transition` — Advance lifecycle phase
- `POST /api/v1/products/{id}/revisions` — Create a revision snapshot

### Components
- `POST /api/v1/components` — Register a component
- `GET /api/v1/components/search?q=STM32` — Search by part number/name
- `GET /api/v1/components?rohs_only=true` — Filter RoHS-compliant parts

### Bill of Materials
- `POST /api/v1/boms` — Create a BOM for a product
- `POST /api/v1/boms/{id}/items` — Add a line item (ref designator + component)
- `GET /api/v1/boms/{id}/cost-summary` — Get cost breakdown
- `POST /api/v1/boms/{id}/clone?new_revision=2` — Clone BOM to new revision

### Engineering Changes
- `POST /api/v1/changes/ecr` — File a change request
- `PATCH /api/v1/changes/ecr/{id}` — Progress ECR through review workflow
- `POST /api/v1/changes/eco` — Create a change order (requires approved ECR)
- `POST /api/v1/changes/eco/{id}/items` — Add affected items to ECO

### Compliance
- `POST /api/v1/compliance/standards` — Define a standard (CE, FCC, etc.)
- `POST /api/v1/compliance/records` — Track a product's compliance status
- `GET /api/v1/compliance/summary/{product_id}` — Compliance dashboard

## Configuration

Environment variables (prefix `EPLM_`):

| Variable | Default | Description |
|----------|---------|-------------|
| `EPLM_DATABASE_URL` | `sqlite+aiosqlite:///./eplm.db` | Database connection string |
| `EPLM_DEBUG` | `false` | Enable debug mode + SQL logging |
| `EPLM_API_PREFIX` | `/api/v1` | API route prefix |

## Engineering Change Workflow

```
ECR: DRAFT → SUBMITTED → UNDER_REVIEW → APPROVED → (creates ECO)
ECO: DRAFT → PENDING_APPROVAL → APPROVED → IN_PROGRESS → COMPLETED
```

Both ECRs and ECOs enforce valid status transitions and reject invalid ones with descriptive errors.
