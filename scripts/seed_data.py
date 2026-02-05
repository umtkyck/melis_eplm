"""Seed the database with sample electronics product data for demonstration."""

import asyncio

from sqlalchemy.ext.asyncio import AsyncSession

from eplm.database import async_session, engine
from eplm.models import (
    Base,
    BillOfMaterials,
    BomLineItem,
    ComplianceRecord,
    ComplianceStandard,
    Component,
    Document,
    Product,
)
from eplm.models.compliance import ComplianceStatus
from eplm.models.component import ComponentCategoryEnum
from eplm.models.document import DocumentType
from eplm.models.lifecycle import LifecyclePhase


async def seed(session: AsyncSession) -> None:
    # ── Compliance standards ──────────────────────────────────
    ce = ComplianceStandard(code="CE", name="CE Marking", issuing_body="EU", region="EU")
    fcc = ComplianceStandard(code="FCC", name="FCC Part 15", issuing_body="FCC", region="US")
    rohs = ComplianceStandard(
        code="RoHS", name="RoHS 3 (EU 2015/863)", issuing_body="EU", region="EU"
    )
    ul = ComplianceStandard(code="UL", name="UL 62368-1", issuing_body="UL", region="Global")
    reach = ComplianceStandard(code="REACH", name="REACH Regulation", issuing_body="ECHA", region="EU")
    session.add_all([ce, fcc, rohs, ul, reach])
    await session.flush()

    # ── Components ────────────────────────────────────────────
    mcu = Component(
        part_number="CMP-MCU-001",
        manufacturer_pn="STM32F407VGT6",
        manufacturer="STMicroelectronics",
        name="ARM Cortex-M4 MCU",
        category=ComponentCategoryEnum.IC,
        package="LQFP-100",
        unit_cost=8.50,
        lead_time_days=14,
        rohs_compliant=True,
        phase=LifecyclePhase.ACTIVE,
    )
    cap_100n = Component(
        part_number="CMP-CAP-001",
        manufacturer_pn="GRM155R71C104KA88D",
        manufacturer="Murata",
        name="100nF MLCC Capacitor",
        category=ComponentCategoryEnum.CAPACITOR,
        package="0402",
        value="100nF",
        unit_cost=0.02,
        lead_time_days=7,
        rohs_compliant=True,
        phase=LifecyclePhase.ACTIVE,
    )
    res_10k = Component(
        part_number="CMP-RES-001",
        manufacturer_pn="RC0402FR-0710KL",
        manufacturer="Yageo",
        name="10kΩ Resistor",
        category=ComponentCategoryEnum.RESISTOR,
        package="0402",
        value="10kΩ",
        unit_cost=0.01,
        lead_time_days=5,
        rohs_compliant=True,
        phase=LifecyclePhase.ACTIVE,
    )
    usb_conn = Component(
        part_number="CMP-CONN-001",
        manufacturer_pn="10118192-0001LF",
        manufacturer="Amphenol",
        name="USB Type-C Connector",
        category=ComponentCategoryEnum.CONNECTOR,
        package="SMD",
        unit_cost=0.45,
        lead_time_days=10,
        rohs_compliant=True,
        phase=LifecyclePhase.ACTIVE,
    )
    ldo = Component(
        part_number="CMP-PWR-001",
        manufacturer_pn="AMS1117-3.3",
        manufacturer="Advanced Monolithic Systems",
        name="3.3V LDO Regulator",
        category=ComponentCategoryEnum.POWER,
        package="SOT-223",
        value="3.3V",
        unit_cost=0.25,
        lead_time_days=7,
        rohs_compliant=True,
        phase=LifecyclePhase.ACTIVE,
    )
    crystal = Component(
        part_number="CMP-XTAL-001",
        manufacturer_pn="ABM8-8.000MHZ",
        manufacturer="Abracon",
        name="8MHz Crystal",
        category=ComponentCategoryEnum.CRYSTAL,
        package="ABM8",
        value="8MHz",
        unit_cost=0.30,
        lead_time_days=10,
        rohs_compliant=True,
        phase=LifecyclePhase.ACTIVE,
    )
    session.add_all([mcu, cap_100n, res_10k, usb_conn, ldo, crystal])
    await session.flush()

    # ── Product ───────────────────────────────────────────────
    product = Product(
        part_number="PRD-IOT-001",
        name="IoT Sensor Hub v1",
        description="Multi-sensor IoT hub with WiFi/BLE connectivity for industrial monitoring",
        category="IoT Devices",
        phase=LifecyclePhase.DESIGN,
        owner="engineering@example.com",
    )
    session.add(product)
    await session.flush()

    # ── BOM ───────────────────────────────────────────────────
    bom = BillOfMaterials(
        product_id=product.id,
        revision="1",
        name="IoT Sensor Hub BOM Rev 1",
        description="Initial design BOM",
        phase=LifecyclePhase.DESIGN,
    )
    session.add(bom)
    await session.flush()

    line_items = [
        BomLineItem(bom_id=bom.id, component_id=mcu.id, reference="U1", quantity=1, unit_cost=8.50),
        BomLineItem(bom_id=bom.id, component_id=cap_100n.id, reference="C1", quantity=1, unit_cost=0.02),
        BomLineItem(bom_id=bom.id, component_id=cap_100n.id, reference="C2", quantity=1, unit_cost=0.02),
        BomLineItem(bom_id=bom.id, component_id=cap_100n.id, reference="C3", quantity=1, unit_cost=0.02),
        BomLineItem(bom_id=bom.id, component_id=res_10k.id, reference="R1", quantity=1, unit_cost=0.01),
        BomLineItem(bom_id=bom.id, component_id=res_10k.id, reference="R2", quantity=1, unit_cost=0.01),
        BomLineItem(bom_id=bom.id, component_id=usb_conn.id, reference="J1", quantity=1, unit_cost=0.45),
        BomLineItem(bom_id=bom.id, component_id=ldo.id, reference="U2", quantity=1, unit_cost=0.25),
        BomLineItem(bom_id=bom.id, component_id=crystal.id, reference="Y1", quantity=1, unit_cost=0.30),
    ]
    session.add_all(line_items)

    # ── Documents ─────────────────────────────────────────────
    schematic = Document(
        product_id=product.id,
        document_number="DOC-SCH-001",
        title="IoT Sensor Hub Schematic",
        doc_type=DocumentType.SCHEMATIC,
        description="Top-level schematic for the IoT Sensor Hub",
    )
    pcb = Document(
        product_id=product.id,
        document_number="DOC-PCB-001",
        title="IoT Sensor Hub PCB Layout",
        doc_type=DocumentType.PCB_LAYOUT,
        description="4-layer PCB layout",
    )
    session.add_all([schematic, pcb])

    # ── Compliance records ────────────────────────────────────
    session.add_all(
        [
            ComplianceRecord(
                product_id=product.id,
                standard_id=ce.id,
                status=ComplianceStatus.NOT_STARTED,
            ),
            ComplianceRecord(
                product_id=product.id,
                standard_id=fcc.id,
                status=ComplianceStatus.NOT_STARTED,
            ),
            ComplianceRecord(
                product_id=product.id,
                standard_id=rohs.id,
                status=ComplianceStatus.IN_PROGRESS,
                notes="Component-level RoHS verified, board-level pending",
            ),
        ]
    )

    await session.commit()
    print("Seed data inserted successfully.")


async def main():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with async_session() as session:
        await seed(session)
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
