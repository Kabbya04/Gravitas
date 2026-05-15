from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np


class ChromaIndex:
    def __init__(self, persist_dir: Path):
        import chromadb
        from chromadb.config import Settings as ChromaSettings

        persist_dir.mkdir(parents=True, exist_ok=True)
        self._client = chromadb.PersistentClient(
            path=str(persist_dir),
            settings=ChromaSettings(anonymized_telemetry=False),
        )
        self._collection = self._client.get_or_create_collection(
            name="chunks",
            metadata={"hnsw:space": "cosine"},
        )

    def delete_document(self, document_id: str) -> None:
        try:
            self._collection.delete(where={"document_id": document_id})
        except Exception:
            # Collection may be empty or API differences across versions
            pass

    def upsert_document(
        self,
        document_id: str,
        chunks: list[dict[str, Any]],
        embeddings: np.ndarray,
    ) -> None:
        if not chunks:
            return
        ids = [c["id"] for c in chunks]
        documents = [c["text"] for c in chunks]
        metadatas = [
            {
                "document_id": document_id,
                "chunk_id": c["id"],
                "page_start": int(c.get("page_start", 1)),
            }
            for c in chunks
        ]
        embs = embeddings.tolist() if hasattr(embeddings, "tolist") else list(embeddings)
        self._collection.upsert(ids=ids, documents=documents, embeddings=embs, metadatas=metadatas)

    def query_dense(self, document_id: str, query_embedding: list[float], k: int) -> list[str]:
        res = self._collection.query(
            query_embeddings=[query_embedding],
            n_results=k,
            where={"document_id": document_id},
            include=["metadatas", "distances"],
        )
        ids = (res.get("ids") or [[]])[0] or []
        return [str(i) for i in ids]
