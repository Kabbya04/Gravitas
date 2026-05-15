from __future__ import annotations

import json
import re
from typing import Any


def extract_json_object(text: str) -> dict[str, Any]:
    t = text.strip()
    try:
        return json.loads(t)
    except json.JSONDecodeError:
        m = re.search(r"\{[\s\S]*\}\s*$", t)
        if not m:
            m = re.search(r"\{[\s\S]*\}", t)
        if m:
            return json.loads(m.group(0))
        raise


def draft_json_to_markdown(draft: dict[str, Any]) -> str:
    title = str(draft.get("title", "")).strip()
    lines = [f"# {title}" if title else "# Draft", ""]
    for sec in draft.get("sections", []) or []:
        h = str(sec.get("heading", "")).strip()
        if h:
            lines.append(f"## {h}")
            lines.append("")
        for b in sec.get("bullets", []) or []:
            lines.append(f"- {str(b).strip()}")
        lines.append("")
    return "\n".join(lines).strip()


_CIT_RE = re.compile(r"\[E(\d+)\]")


def collect_citation_labels(text: str) -> set[str]:
    return {f"E{int(m.group(1))}" for m in _CIT_RE.finditer(text)}


def validate_citations_in_draft(draft: dict[str, Any], valid_labels: set[str]) -> list[str]:
    issues: list[str] = []
    blob = json.dumps(draft)
    found = collect_citation_labels(blob)
    for lab in sorted(found, key=lambda x: int(x[1:])):
        if lab not in valid_labels:
            issues.append(f"Unknown citation tag [{lab}]")
    # substantive check: each bullet should have a citation
    for si, sec in enumerate(draft.get("sections", []) or []):
        for bi, b in enumerate(sec.get("bullets", []) or []):
            bs = str(b)
            if len(bs) > 40 and not _CIT_RE.search(bs):
                issues.append(f"Missing citation in section {si} bullet {bi}")
    return issues
