from __future__ import annotations

import json
from typing import Any

from openai import OpenAI

from app.core.prompts import get_drafting_prompts, render_template
from app.core.settings import get_settings
from app.core.yaml_config import get_yaml_config
from app.llm.citations import draft_json_to_markdown, extract_json_object, validate_citations_in_draft
from app.rag.retrieval import EvidenceItem


class GroqDraftService:
    def __init__(self) -> None:
        self.yaml = get_yaml_config()
        self.settings = get_settings()
        g = self.yaml.get("groq", {})
        api_key = self.settings.groq_api_key
        if not api_key:
            raise RuntimeError("GROQ_API_KEY is not set")
        self.client = OpenAI(api_key=api_key, base_url=str(g.get("base_url")))
        self.model = self.settings.groq_model or str(g.get("model"))
        self.temperature = float(g.get("temperature", 0.2))
        self.max_tokens = int(g.get("max_tokens", 4096))

    def _evidence_block(self, items: list[EvidenceItem]) -> str:
        lines: list[str] = []
        for it in items:
            lines.append(f"{it.label} (chunk {it.chunk_id}, page {it.page}):\n{it.text}\n")
        return "\n".join(lines).strip()

    def generate(
        self,
        query: str,
        evidence: list[EvidenceItem],
        memory_block: str | None,
    ) -> tuple[dict[str, Any], str, list[str]]:
        prompts = get_drafting_prompts()
        labels = {it.label for it in evidence}
        evidence_block = self._evidence_block(evidence)
        system = render_template(prompts.system)
        user = render_template(
            prompts.user,
            query=query,
            evidence_block=evidence_block,
            memory_block=memory_block or "",
        )

        resp = self.client.chat.completions.create(
            model=self.model,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        )
        raw = (resp.choices[0].message.content or "").strip()
        draft = extract_json_object(raw)
        md = draft_json_to_markdown(draft)
        issues = validate_citations_in_draft(draft, labels)
        return draft, md, issues

    def repair(
        self,
        draft: dict[str, Any],
        evidence: list[EvidenceItem],
        issues: list[str],
    ) -> tuple[dict[str, Any], str, list[str]]:
        prompts = get_drafting_prompts()
        labels = sorted({it.label for it in evidence}, key=lambda x: int(x[1:]))
        n_evidence = len(evidence)
        system = render_template(prompts.repair_system, n_evidence=n_evidence)
        user = render_template(
            prompts.repair_user,
            issues="; ".join(issues) if issues else "unknown",
            labels=", ".join(labels),
            draft_json=json.dumps(draft, ensure_ascii=False),
        )
        resp = self.client.chat.completions.create(
            model=self.model,
            temperature=0.0,
            max_tokens=self.max_tokens,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        )
        raw = (resp.choices[0].message.content or "").strip()
        fixed = extract_json_object(raw)
        md = draft_json_to_markdown(fixed)
        labels_set = {it.label for it in evidence}
        new_issues = validate_citations_in_draft(fixed, labels_set)
        return fixed, md, new_issues
