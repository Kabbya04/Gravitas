from __future__ import annotations

import json
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import Draft, Document
from app.learning.edits import build_memory_block, record_operator_edit
from app.llm.groq_service import GroqDraftService
from app.rag.retrieval import HybridRetriever

router = APIRouter(tags=["drafts"])


class DraftRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=4000)
    use_memory: bool = True


class EvidenceOut(BaseModel):
    e_label: str
    chunk_id: str
    text: str
    page: int


class DraftResponse(BaseModel):
    draft_id: str
    content: str
    draft_json: dict[str, Any]
    evidence: list[EvidenceOut]
    citation_issues: list[str]


class DraftListItem(BaseModel):
    draft_id: str
    query: str
    created_at: datetime
    has_operator_version: bool


class OperatorSaveRequest(BaseModel):
    text: str = Field(..., min_length=1)


def _draft_row_to_response(row: Draft) -> DraftResponse:
    text_out = (row.operator_output or row.model_output or "").strip()
    dj: dict[str, Any] = {}
    if row.draft_json:
        try:
            dj = json.loads(row.draft_json)
            if not isinstance(dj, dict):
                dj = {}
        except (json.JSONDecodeError, TypeError):
            dj = {}
    ev_raw: list[dict[str, Any]] = []
    if row.evidence_json:
        try:
            parsed = json.loads(row.evidence_json)
            if isinstance(parsed, list):
                ev_raw = [x for x in parsed if isinstance(x, dict)]
        except (json.JSONDecodeError, TypeError):
            pass
    ev_payload: list[EvidenceOut] = []
    for x in ev_raw:
        try:
            ev_payload.append(
                EvidenceOut(
                    e_label=str(x.get("e_label", "")),
                    chunk_id=str(x.get("chunk_id", "")),
                    text=str(x.get("text", "")),
                    page=int(x["page"]) if x.get("page") is not None else 0,
                )
            )
        except (TypeError, ValueError, KeyError):
            continue
    return DraftResponse(
        draft_id=row.id,
        content=text_out,
        draft_json=dj,
        evidence=ev_payload,
        citation_issues=[],
    )


@router.get("/api/documents/{document_id}/drafts", response_model=list[DraftListItem])
def list_drafts_for_document(document_id: str, db: Session = Depends(get_db)) -> Any:
    doc = db.get(Document, document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="document not found")
    rows = db.execute(
        select(Draft).where(Draft.document_id == document_id).order_by(Draft.created_at.desc())
    ).scalars().all()
    return [
        DraftListItem(
            draft_id=r.id,
            query=r.query,
            created_at=r.created_at,
            has_operator_version=bool((r.operator_output or "").strip()),
        )
        for r in rows
    ]


@router.get("/api/drafts/{draft_id}", response_model=DraftResponse)
def get_draft(draft_id: str, db: Session = Depends(get_db)) -> Any:
    row = db.get(Draft, draft_id)
    if not row:
        raise HTTPException(status_code=404, detail="draft not found")
    return _draft_row_to_response(row)


@router.post("/api/documents/{document_id}/draft", response_model=DraftResponse)
def create_draft(document_id: str, body: DraftRequest, db: Session = Depends(get_db)) -> Any:
    doc = db.get(Document, document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="document not found")
    if doc.status != "ready":
        raise HTTPException(status_code=400, detail=f"document not ready: {doc.status}")

    retriever = HybridRetriever(db)
    evidence, _ = retriever.retrieve(document_id, body.query)
    if not evidence:
        raise HTTPException(status_code=400, detail="no chunks to retrieve")

    memory = ""
    if body.use_memory:
        memory = build_memory_block(db, document_id, body.query)

    try:
        svc = GroqDraftService()
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e)) from e

    draft, md, issues = svc.generate(body.query, evidence, memory or None)
    if issues:
        draft, md, issues = svc.repair(draft, evidence, issues)

    ev_payload = [
        {"e_label": e.label, "chunk_id": e.chunk_id, "text": e.text, "page": e.page} for e in evidence
    ]
    row = Draft(
        document_id=document_id,
        query=body.query,
        model_output=md,
        draft_json=json.dumps(draft, ensure_ascii=False),
        evidence_json=json.dumps(ev_payload, ensure_ascii=False),
    )
    db.add(row)
    db.commit()
    db.refresh(row)

    return DraftResponse(
        draft_id=row.id,
        content=md,
        draft_json=draft,
        evidence=[EvidenceOut(**x) for x in ev_payload],
        citation_issues=issues,
    )


@router.post("/api/drafts/{draft_id}/operator")
def save_operator_draft(draft_id: str, body: OperatorSaveRequest, db: Session = Depends(get_db)) -> dict[str, str]:
    draft = db.get(Draft, draft_id)
    if not draft:
        raise HTTPException(status_code=404, detail="draft not found")
    record_operator_edit(db, draft, body.text)
    return {"status": "saved"}
