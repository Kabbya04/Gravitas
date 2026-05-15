from __future__ import annotations

from rank_bm25 import BM25Okapi


def tokenize(text: str) -> list[str]:
    return [t for t in "".join(ch.lower() if ch.isalnum() else " " for ch in text).split() if t]


class BM25Retriever:
    def __init__(self, chunk_ids: list[str], corpus: list[str]):
        self.chunk_ids = chunk_ids
        tokenized_corpus = [tokenize(c) for c in corpus]
        self._bm25 = BM25Okapi(tokenized_corpus) if tokenized_corpus else None

    def top_k(self, query: str, k: int) -> list[str]:
        if not self._bm25 or not self.chunk_ids:
            return []
        scores = self._bm25.get_scores(tokenize(query))
        ranked = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)
        return [self.chunk_ids[i] for i in ranked[:k]]
