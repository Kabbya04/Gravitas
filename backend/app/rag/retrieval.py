from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.yaml_config import chroma_dir, get_yaml_config
from app.db.models import Chunk
from app.rag.bm25_index import BM25Retriever
from app.rag.chroma_store import ChromaIndex
from app.rag.embedder import get_embedder
from app.rag.fusion import reciprocal_rank_fusion


@dataclass
class EvidenceItem:
    label: str
    chunk_id: str
    text: str
    page: int


class HybridRetriever:
    def __init__(self, db: Session):
        self.db = db
        self.yaml = get_yaml_config()

    def _chunks_for_doc(self, document_id: str) -> list[Chunk]:
        rows = self.db.execute(
            select(Chunk).where(Chunk.document_id == document_id).order_by(Chunk.chunk_index)
        ).scalars().all()
        return list(rows)

    def retrieve(self, document_id: str, query: str) -> tuple[list[EvidenceItem], dict[str, Any]]:
        y = self.yaml
        r_cfg = y.get("retrieval", {})
        dense_k = int(r_cfg.get("dense_top_k", 12))
        bm25_k = int(r_cfg.get("bm25_top_k", 12))
        fusion_k = int(r_cfg.get("fusion_k", 60))
        max_ctx = int(r_cfg.get("max_context_chunks", 10))
        max_ev_chars = int(r_cfg.get("max_chars_per_evidence", 900))

        chunks = self._chunks_for_doc(document_id)
        if not chunks:
            return [], {"reason": "no_chunks"}

        id_to_chunk = {c.id: c for c in chunks}
        texts = [c.text for c in chunks]
        ids = [c.id for c in chunks]

        embedder = get_embedder(str(y.get("embedding", {}).get("model")))
        q_emb = embedder.encode([query])[0].astype(float).tolist()

        chroma = ChromaIndex(chroma_dir(y))
        dense_ids = chroma.query_dense(document_id, q_emb, dense_k)

        bm25 = BM25Retriever(ids, texts)
        sparse_ids = bm25.top_k(query, bm25_k)

        fused = reciprocal_rank_fusion([dense_ids, sparse_ids], k=fusion_k)
        fused = [cid for cid in fused if cid in id_to_chunk][:max_ctx]

        evidence: list[EvidenceItem] = []
        for i, cid in enumerate(fused, start=1):
            ch = id_to_chunk[cid]
            text = ch.text if len(ch.text) <= max_ev_chars else ch.text[: max_ev_chars - 1] + "…"
            evidence.append(
                EvidenceItem(
                    label=f"E{i}",
                    chunk_id=cid,
                    text=text,
                    page=int(ch.page_start),
                )
            )

        debug = {"dense_ids": dense_ids[:5], "sparse_ids": sparse_ids[:5], "fused_ids": fused}
        return evidence, debug
