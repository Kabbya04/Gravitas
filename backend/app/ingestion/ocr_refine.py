from __future__ import annotations

from typing import Any

from app.core.prompts import get_ocr_refine_prompts, render_template
from app.core.yaml_config import get_yaml_config
from app.llm.groq_client import GroqRuntime, get_groq_runtime


def _ocr_refine_config(yaml: dict[str, Any]) -> dict[str, Any]:
    return dict(yaml.get("ocr_refine") or {})


def pages_need_ocr_refine(pages: list[dict[str, Any]]) -> bool:
    return any((p.get("source") or "") == "ocr" and (p.get("text") or "").strip() for p in pages)


def _refine_page_text(
    runtime: GroqRuntime,
    *,
    system: str,
    user_template: str,
    page_number: int,
    ocr_text: str,
    temperature: float,
    max_tokens: int,
) -> str:
    user = render_template(
        user_template,
        page_number=page_number,
        ocr_text=ocr_text,
    )
    resp = runtime.client.chat.completions.create(
        model=runtime.model,
        temperature=temperature,
        max_tokens=max_tokens,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
    )
    cleaned = (resp.choices[0].message.content or "").strip()
    return cleaned or ocr_text


def refine_ocr_pages(
    pages: list[dict[str, Any]],
    yaml: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """
  Run Groq cleanup on pages produced by OCR before chunking.
  Non-OCR pages pass through unchanged. Preserves page numbers and ocr_confidence.
  """
    y = yaml if yaml is not None else get_yaml_config()
    cfg = _ocr_refine_config(y)
    if not cfg.get("enabled", True):
        return pages
    if not pages_need_ocr_refine(pages):
        return pages

    runtime = get_groq_runtime()
    prompts = get_ocr_refine_prompts()
    temperature = float(cfg.get("temperature", runtime.temperature))
    max_tokens = int(cfg.get("max_tokens", min(runtime.max_tokens, 8192)))
    max_chars = int(cfg.get("max_chars_per_page", 14000))

    refined: list[dict[str, Any]] = []
    for p in pages:
        source = str(p.get("source") or "")
        if source != "ocr":
            refined.append(p)
            continue

        text = (p.get("text") or "").strip()
        if not text:
            refined.append(p)
            continue

        page_number = int(p.get("page") or 1)
        payload = text[:max_chars] if len(text) > max_chars else text
        cleaned = _refine_page_text(
            runtime,
            system=prompts.system,
            user_template=prompts.user,
            page_number=page_number,
            ocr_text=payload,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        refined.append(
            {
                **p,
                "text": cleaned,
                "source": "ocr_refined",
            }
        )
    return refined
