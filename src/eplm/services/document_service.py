"""Document and revision management service."""

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from eplm.models.document import Document, DocumentRevision
from eplm.schemas.document import DocumentCreate, DocumentRevisionCreate


class DocumentServiceError(Exception):
    pass


class DocumentNotFoundError(DocumentServiceError):
    pass


class DocumentService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, data: DocumentCreate) -> Document:
        doc = Document(**data.model_dump())
        self.db.add(doc)
        await self.db.commit()
        await self.db.refresh(doc)
        return doc

    async def get(self, document_id: str) -> Document:
        result = await self.db.execute(
            select(Document)
            .options(selectinload(Document.revisions))
            .where(Document.id == document_id)
        )
        doc = result.scalar_one_or_none()
        if not doc:
            raise DocumentNotFoundError(f"Document '{document_id}' not found")
        return doc

    async def list_for_product(self, product_id: str) -> list[Document]:
        result = await self.db.execute(
            select(Document)
            .where(Document.product_id == product_id)
            .order_by(Document.document_number)
        )
        return list(result.scalars().all())

    async def add_revision(
        self, document_id: str, data: DocumentRevisionCreate
    ) -> DocumentRevision:
        doc = await self.get(document_id)

        # Determine next revision number
        max_rev_result = await self.db.execute(
            select(func.max(DocumentRevision.revision_number)).where(
                DocumentRevision.document_id == document_id
            )
        )
        max_rev = max_rev_result.scalar() or 0

        revision = DocumentRevision(
            document_id=document_id,
            revision_number=max_rev + 1,
            file_path=data.file_path,
            change_summary=data.change_summary,
            uploaded_by=data.uploaded_by,
        )
        self.db.add(revision)
        await self.db.commit()
        await self.db.refresh(revision)
        return revision

    async def get_revisions(self, document_id: str) -> list[DocumentRevision]:
        doc = await self.get(document_id)
        return list(doc.revisions)

    async def delete(self, document_id: str) -> None:
        doc = await self.get(document_id)
        await self.db.delete(doc)
        await self.db.commit()
