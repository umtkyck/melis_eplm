"""Document management API endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from eplm.database import get_db
from eplm.schemas.document import (
    DocumentCreate,
    DocumentResponse,
    DocumentRevisionCreate,
    DocumentRevisionResponse,
)
from eplm.services.document_service import DocumentNotFoundError, DocumentService

router = APIRouter(prefix="/documents", tags=["documents"])


def _svc(db: AsyncSession = Depends(get_db)) -> DocumentService:
    return DocumentService(db)


@router.post("", response_model=DocumentResponse, status_code=201)
async def create_document(
    data: DocumentCreate, svc: DocumentService = Depends(_svc)
):
    return await svc.create(data)


@router.get("/product/{product_id}", response_model=list[DocumentResponse])
async def list_documents_for_product(
    product_id: str, svc: DocumentService = Depends(_svc)
):
    return await svc.list_for_product(product_id)


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: str, svc: DocumentService = Depends(_svc)
):
    try:
        return await svc.get(document_id)
    except DocumentNotFoundError as e:
        raise HTTPException(404, str(e))


@router.post(
    "/{document_id}/revisions",
    response_model=DocumentRevisionResponse,
    status_code=201,
)
async def add_revision(
    document_id: str,
    data: DocumentRevisionCreate,
    svc: DocumentService = Depends(_svc),
):
    try:
        return await svc.add_revision(document_id, data)
    except DocumentNotFoundError as e:
        raise HTTPException(404, str(e))


@router.get(
    "/{document_id}/revisions",
    response_model=list[DocumentRevisionResponse],
)
async def list_revisions(
    document_id: str, svc: DocumentService = Depends(_svc)
):
    try:
        return await svc.get_revisions(document_id)
    except DocumentNotFoundError as e:
        raise HTTPException(404, str(e))


@router.delete("/{document_id}", status_code=204)
async def delete_document(
    document_id: str, svc: DocumentService = Depends(_svc)
):
    try:
        await svc.delete(document_id)
    except DocumentNotFoundError as e:
        raise HTTPException(404, str(e))
