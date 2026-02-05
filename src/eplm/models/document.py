"""Document management models for design files, datasheets, test reports, etc."""

import enum

from sqlalchemy import Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from eplm.models.base import Base


class DocumentType(str, enum.Enum):
    SCHEMATIC = "schematic"
    PCB_LAYOUT = "pcb_layout"
    GERBER = "gerber"
    DATASHEET = "datasheet"
    TEST_REPORT = "test_report"
    MANUFACTURING_SPEC = "manufacturing_spec"
    ASSEMBLY_DRAWING = "assembly_drawing"
    USER_MANUAL = "user_manual"
    COMPLIANCE_CERT = "compliance_cert"
    OTHER = "other"


class Document(Base):
    """A document associated with a product (schematic, layout, test report, etc.)."""

    __tablename__ = "documents"

    product_id: Mapped[str] = mapped_column(ForeignKey("products.id"), index=True)
    document_number: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    title: Mapped[str] = mapped_column(String(300))
    doc_type: Mapped[DocumentType] = mapped_column(
        Enum(DocumentType), default=DocumentType.OTHER
    )
    description: Mapped[str] = mapped_column(Text, default="")
    file_path: Mapped[str] = mapped_column(String(500), default="")

    product: Mapped["Product"] = relationship(back_populates="documents")  # noqa: F821
    revisions: Mapped[list["DocumentRevision"]] = relationship(
        back_populates="document", cascade="all, delete-orphan",
        order_by="DocumentRevision.revision_number"
    )

    @property
    def latest_revision(self) -> "DocumentRevision | None":
        return self.revisions[-1] if self.revisions else None

    def __repr__(self) -> str:
        return f"<Document {self.document_number} '{self.title}'>"


class DocumentRevision(Base):
    """A specific revision of a document."""

    __tablename__ = "document_revisions"

    document_id: Mapped[str] = mapped_column(ForeignKey("documents.id"), index=True)
    revision_number: Mapped[int] = mapped_column(Integer, default=1)
    file_path: Mapped[str] = mapped_column(String(500), default="")
    change_summary: Mapped[str] = mapped_column(Text, default="")
    uploaded_by: Mapped[str] = mapped_column(String(200), default="")

    document: Mapped["Document"] = relationship(back_populates="revisions")

    def __repr__(self) -> str:
        return f"<DocumentRevision {self.document_id} rev={self.revision_number}>"
