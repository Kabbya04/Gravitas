from __future__ import annotations

from typing import Any

from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, UploadFile
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import Chunk, Document
from app.ingestion.service import create_document_record, process_document

router = APIRouter(prefix="/api/documents", tags=["documents"])


class DocumentSummary(BaseModel):
    id: str
    filename: str
    status: str
    error_message: str | None = None


class ChunkOut(BaseModel):
    id: str
    chunk_index: int
    page_start: int
    page_end: int
    source: str
    ocr_confidence: float | None
    text_preview: str


def _process_job(document_id: str) -> None:
    from app.db.database import get_session_factory

    SessionLocal = get_session_factory()
    db = SessionLocal()
    try:
        process_document(db, document_id)
    finally:
        db.close()


@router.post("", response_model=DocumentSummary)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
) -> Any:
    data = await file.read()
    if not data:
        raise HTTPException(status_code=400, detail="empty file")
    doc = create_document_record(db, file.filename or "upload", file.content_type, data)
    background_tasks.add_task(_process_job, doc.id)
    return DocumentSummary(id=doc.id, filename=doc.filename, status=doc.status, error_message=doc.error_message)


@router.get("", response_model=list[DocumentSummary])
def list_documents(db: Session = Depends(get_db)) -> Any:
    rows = db.execute(select(Document).order_by(Document.created_at.desc())).scalars().all()
    return [
        DocumentSummary(id=r.id, filename=r.filename, status=r.status, error_message=r.error_message)
        for r in rows
    ]


@router.get("/{document_id}", response_model=DocumentSummary)
def get_document(document_id: str, db: Session = Depends(get_db)) -> Any:
    doc = db.get(Document, document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="not found")
    return DocumentSummary(id=doc.id, filename=doc.filename, status=doc.status, error_message=doc.error_message)


@router.get("/{document_id}/chunks", response_model=list[ChunkOut])
def list_chunks(document_id: str, db: Session = Depends(get_db)) -> Any:
    doc = db.get(Document, document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="not found")
    rows = db.execute(select(Chunk).where(Chunk.document_id == document_id).order_by(Chunk.chunk_index)).scalars().all()
    out: list[ChunkOut] = []
    for c in rows:
        preview = c.text if len(c.text) <= 500 else c.text[:499] + "…"
        out.append(
            ChunkOut(
                id=c.id,
                chunk_index=c.chunk_index,
                page_start=c.page_start,
                page_end=c.page_end,
                source=c.source,
                ocr_confidence=c.ocr_confidence,
                text_preview=preview,
            )
        )
    return out
