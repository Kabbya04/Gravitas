from __future__ import annotations

import difflib
import json

import numpy as np
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.yaml_config import get_yaml_config
from app.db.models import Draft, OperatorCorrection
from app.rag.embedder import get_embedder


def _mean_embedding(texts: list[str], model_name: str) -> np.ndarray:
    emb = get_embedder(model_name)
    usable = [t for t in texts if t.strip()]
    if not usable:
        return emb.encode([" "])[0]
    v = emb.encode(usable)
    return np.mean(v, axis=0)


def cosine_sim(a: np.ndarray, b: np.ndarray) -> float:
    denom = float(np.linalg.norm(a) * np.linalg.norm(b)) or 1.0
    return float(np.dot(a, b) / denom)


def build_memory_block(db: Session, document_id: str, query: str) -> str:
    y = get_yaml_config()
    model_name = str(y.get("embedding", {}).get("model"))
    top_k = int(y.get("learning", {}).get("memory_top_k", 4))
    max_chars = int(y.get("learning", {}).get("max_memory_chars", 2000))

    rows = db.execute(
        select(OperatorCorrection).where(OperatorCorrection.document_id == document_id)
    ).scalars().all()
    if not rows:
        return ""

    q_emb = get_embedder(model_name).encode([query])[0]
    scored: list[tuple[float, OperatorCorrection]] = []
    for r in rows:
        try:
            vec = np.asarray(json.loads(r.embedding_json), dtype=np.float32)
        except (json.JSONDecodeError, TypeError):
            continue
        scored.append((cosine_sim(q_emb, vec), r))
    scored.sort(key=lambda x: x[0], reverse=True)

    parts: list[str] = []
    used = 0
    for _, r in scored[:top_k]:
        block = f"- Prefer replacing:\n  FROM: {r.before_snippet[:400]}\n  TO: {r.after_snippet[:400]}\n"
        if used + len(block) > max_chars:
            break
        parts.append(block)
        used += len(block)
    return "\n".join(parts).strip()


def record_operator_edit(db: Session, draft: Draft, operator_text: str) -> None:
    y = get_yaml_config()
    model_name = str(y.get("embedding", {}).get("model"))
    before = (draft.model_output or "").strip()
    after = operator_text.strip()
    draft.operator_output = after
    db.add(draft)
    db.commit()
    db.refresh(draft)

    if not before or before == after:
        return

    # Chunk-level-ish edits: split by lines, pair simple replacements
    before_lines = before.splitlines()
    after_lines = after.splitlines()
    sm = difflib.SequenceMatcher(a=before_lines, b=after_lines)
    count = 0
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "replace":
            b = "\n".join(before_lines[i1:i2]).strip()
            a = "\n".join(after_lines[j1:j2]).strip()
            if len(b) < 8 and len(a) < 8:
                continue
            vec = _mean_embedding([b, a], model_name)
            cor = OperatorCorrection(
                document_id=draft.document_id,
                draft_id=draft.id,
                before_snippet=b[:4000],
                after_snippet=a[:4000],
                embedding_json=json.dumps(vec.astype(float).tolist()),
            )
            db.add(cor)
            count += 1
            if count >= 12:
                break
    db.commit()
