from __future__ import annotations

from typing import Any


def _split_paragraphs(text: str) -> list[str]:
    parts = [p.strip() for p in text.replace("\r\n", "\n").split("\n\n")]
    return [p for p in parts if p]


def _windows(text: str, max_chars: int, overlap: int) -> list[str]:
    if len(text) <= max_chars:
        return [text] if text else []
    out: list[str] = []
    step = max(1, max_chars - overlap)
    start = 0
    while start < len(text):
        chunk = text[start : start + max_chars].strip()
        if chunk:
            out.append(chunk)
        start += step
    return out


def chunk_pages(
    pages: list[dict[str, Any]],
    max_chars: int,
    overlap: int,
) -> list[dict[str, Any]]:
    """Turn page-level extraction into overlapping chunks with provenance."""
    chunks: list[dict[str, Any]] = []
    idx = 0
    for p in pages:
        page = int(p.get("page") or 1)
        text = (p.get("text") or "").strip()
        source = str(p.get("source") or "native")
        ocr_conf = p.get("ocr_confidence")
        if not text:
            continue
        paras = _split_paragraphs(text)
        buf: list[str] = []
        buf_len = 0

        def flush():
            nonlocal idx, buf, buf_len
            if not buf:
                return
            merged = "\n\n".join(buf).strip()
            for piece in _windows(merged, max_chars, overlap):
                chunks.append(
                    {
                        "chunk_index": idx,
                        "page_start": page,
                        "page_end": page,
                        "text": piece,
                        "source": source,
                        "ocr_confidence": float(ocr_conf) if ocr_conf is not None else None,
                    }
                )
                idx += 1
            buf = []
            buf_len = 0

        for para in paras:
            if buf_len + len(para) + 2 > max_chars and buf:
                flush()
            buf.append(para)
            buf_len += len(para) + 2
        flush()
    return chunks
