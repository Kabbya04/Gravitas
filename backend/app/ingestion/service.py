from __future__ import annotations

import shutil
import uuid
from pathlib import Path

import numpy as np
from sqlalchemy.orm import Session

from app.core.settings import get_settings
from app.core.yaml_config import chroma_dir, data_dir, get_yaml_config
from app.db.models import Chunk, Document
from app.ingestion.chunking import chunk_pages
from app.ingestion.extract import extract_document
from app.ingestion.ocr_refine import refine_ocr_pages
from app.rag.chroma_store import ChromaIndex
from app.rag.embedder import get_embedder


def _safe_filename(name: str) -> str:
    return Path(name).name.replace("..", "_")[:200] or "upload"


def create_document_record(db: Session, filename: str, content_type: str | None, data: bytes) -> Document:
    y = get_yaml_config()
    s = get_settings()
    root = data_dir(y, s)
    doc_id = str(uuid.uuid4())
    dest_dir = root / "files" / doc_id
    dest_dir.mkdir(parents=True, exist_ok=True)
    ext = Path(filename).suffix or ""
    storage = dest_dir / f"original{ext}"
    storage.write_bytes(data)

    doc = Document(
        id=doc_id,
        filename=_safe_filename(filename),
        content_type=content_type,
        storage_path=str(storage),
        status="pending",
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)
    return doc


def process_document(db: Session, document_id: str) -> Document:
    y = get_yaml_config()
    s = get_settings()
    doc = db.get(Document, document_id)
    if not doc:
        raise ValueError("document not found")

    path = Path(doc.storage_path)
    try:
        pages = extract_document(
            path,
            doc.content_type,
            float(y.get("chunking", {}).get("ocr_text_threshold", 40)),
        )
        pages = refine_ocr_pages(pages, y)
        max_chars = int(y.get("chunking", {}).get("max_chars", 1200))
        overlap = int(y.get("chunking", {}).get("overlap_chars", 150))
        raw_chunks = chunk_pages(pages, max_chars=max_chars, overlap=overlap)

        # Replace old chunks / vectors
        db.query(Chunk).filter(Chunk.document_id == doc.id).delete()
        chroma = ChromaIndex(chroma_dir(y))
        chroma.delete_document(doc.id)

        embedder = get_embedder(str(y.get("embedding", {}).get("model")))
        texts = [c["text"] for c in raw_chunks]
        if not texts:
            doc.status = "failed"
            doc.error_message = "No extractable text"
            db.commit()
            return doc

        vectors = embedder.encode(texts)

        orm_chunks: list[Chunk] = []
        for i, c in enumerate(raw_chunks):
            ch = Chunk(
                document_id=doc.id,
                chunk_index=i,
                text=c["text"],
                page_start=c["page_start"],
                page_end=c["page_end"],
                source=c["source"],
                ocr_confidence=c.get("ocr_confidence"),
            )
            db.add(ch)
            orm_chunks.append(ch)
        db.commit()
        for ch in orm_chunks:
            db.refresh(ch)

        chroma.upsert_document(
            doc.id,
            [{"id": ch.id, "text": ch.text, "page_start": ch.page_start} for ch in orm_chunks],
            np.asarray(vectors, dtype=np.float32),
        )

        doc.status = "ready"
        doc.error_message = None
        db.commit()
        db.refresh(doc)
        return doc
    except Exception as e:  # noqa: BLE001
        doc.status = "failed"
        doc.error_message = str(e)[:2000]
        db.commit()
        db.refresh(doc)
        return doc


def delete_document_files(doc: Document) -> None:
    folder = Path(doc.storage_path).parent
    if folder.exists():
        shutil.rmtree(folder, ignore_errors=True)


def purge_document(db: Session, document_id: str) -> bool:
    """Remove document row (cascades chunks/drafts), on-disk files, and Chroma vectors."""
    doc = db.get(Document, document_id)
    if not doc:
        return False
    y = get_yaml_config()
    s = get_settings()
    chroma = ChromaIndex(chroma_dir(y))
    chroma.delete_document(document_id)
    delete_document_files(doc)
    db.delete(doc)
    db.commit()
    return True
