from __future__ import annotations

import io
import re
from pathlib import Path
from typing import Any

import pymupdf
import pytesseract
from PIL import Image


def _avg_confidence_from_data(data: dict) -> float | None:
    """Average confidence from pytesseract image_to_data (0-100 scale)."""
    confs: list[float] = []
    for c in data.get("conf", []) or []:
        try:
            v = int(float(str(c)))
        except (TypeError, ValueError):
            continue
        if v > 0:
            confs.append(float(v))
    if not confs:
        return None
    return sum(confs) / len(confs)


def extract_pdf_native(path: Path) -> list[dict[str, Any]]:
    from pypdf import PdfReader

    reader = PdfReader(str(path))
    out: list[dict[str, Any]] = []
    for i, page in enumerate(reader.pages):
        text = (page.extract_text() or "").strip()
        out.append({"page": i + 1, "text": text, "source": "native"})
    return out


def _should_ocr_pages(pages: list[dict[str, Any]], threshold: float) -> bool:
    if not pages:
        return True
    lengths = [len((p.get("text") or "").strip()) for p in pages]
    avg = sum(lengths) / max(len(lengths), 1)
    return avg < threshold


def extract_pdf_ocr(path: Path, dpi_scale: float = 2.0) -> list[dict[str, Any]]:
    doc = pymupdf.open(str(path))
    out: list[dict[str, Any]] = []
    mat = pymupdf.Matrix(dpi_scale, dpi_scale)
    for i in range(doc.page_count):
        page = doc.load_page(i)
        pix = page.get_pixmap(matrix=mat, alpha=False)
        img = Image.open(io.BytesIO(pix.tobytes("png"))).convert("L")
        text = pytesseract.image_to_string(img)
        data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT)
        conf = _avg_confidence_from_data(data)
        out.append({"page": i + 1, "text": text.strip(), "source": "ocr", "ocr_confidence": conf})
    doc.close()
    return out


def extract_image_ocr(path: Path) -> list[dict[str, Any]]:
    img = Image.open(path).convert("L")
    text = pytesseract.image_to_string(img)
    data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT)
    conf = _avg_confidence_from_data(data)
    return [{"page": 1, "text": text.strip(), "source": "ocr", "ocr_confidence": conf}]


def extract_with_markitdown(path: Path) -> list[dict[str, Any]]:
    try:
        from markitdown import MarkItDown
    except ImportError:
        return [{"page": 1, "text": "", "source": "markitdown", "ocr_confidence": None}]
    md = MarkItDown()
    result = md.convert(str(path))
    text = (result.text_content or "").strip()
    return [{"page": 1, "text": text, "source": "markitdown", "ocr_confidence": None}]


def extract_pdf_smart(path: Path, ocr_threshold: float) -> list[dict[str, Any]]:
    native = extract_pdf_native(path)
    if _should_ocr_pages(native, ocr_threshold):
        return extract_pdf_ocr(path)
    return native


def extract_document(path: Path, content_type: str | None, ocr_threshold: float) -> list[dict[str, Any]]:
    ct = (content_type or "").lower()
    suf = path.suffix.lower()

    if ct.startswith("image/") or suf in {".png", ".jpg", ".jpeg", ".tif", ".tiff", ".webp"}:
        return extract_image_ocr(path)

    if suf == ".pdf" or ct == "application/pdf":
        return extract_pdf_smart(path, ocr_threshold)

    if suf in {".docx", ".doc"} or "wordprocessingml" in ct:
        return extract_with_markitdown(path)

    if suf in {".html", ".htm", ".pptx", ".xlsx"}:
        return extract_with_markitdown(path)

    # Fallback: try MarkItDown, else read as utf-8 text
    try:
        pages = extract_with_markitdown(path)
        if pages and pages[0].get("text"):
            return pages
    except Exception:
        pass
    try:
        raw = path.read_text(encoding="utf-8", errors="ignore")
        return [{"page": 1, "text": raw, "source": "native", "ocr_confidence": None}]
    except OSError:
        return [{"page": 1, "text": "", "source": "native", "ocr_confidence": None}]


def heuristic_flags(text: str) -> dict[str, Any]:
    """Lightweight structured hints for downstream (not NLP-heavy)."""
    dates = re.findall(
        r"\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)[a-z]*\.?\s+\d{1,2},?\s+\d{4}\b|\b\d{1,2}/\d{1,2}/\d{2,4}\b",
        text,
        flags=re.I,
    )
    return {"approx_date_mentions": len(dates), "char_len": len(text)}
