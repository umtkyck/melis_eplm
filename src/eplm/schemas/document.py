"""Pydantic schemas for document management."""

from datetime import datetime

from pydantic import BaseModel, Field

from eplm.models.document import DocumentType


class DocumentCreate(BaseModel):
    product_id: str
    document_number: str = Field(..., min_length=1, max_length=50)
    title: str = Field(..., min_length=1, max_length=300)
    doc_type: DocumentType = DocumentType.OTHER
    description: str = ""
    file_path: str = ""


class DocumentResponse(BaseModel):
    id: str
    product_id: str
    document_number: str
    title: str
    doc_type: DocumentType
    description: str
    file_path: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class DocumentRevisionCreate(BaseModel):
    file_path: str = ""
    change_summary: str = ""
    uploaded_by: str = ""


class DocumentRevisionResponse(BaseModel):
    id: str
    document_id: str
    revision_number: int
    file_path: str
    change_summary: str
    uploaded_by: str
    created_at: datetime

    model_config = {"from_attributes": True}
