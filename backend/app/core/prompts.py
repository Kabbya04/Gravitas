from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml
from jinja2 import Environment, StrictUndefined

from app.core.paths import BACKEND_DIR
from app.core.yaml_config import get_yaml_config


@dataclass
class DraftingPrompts:
    system: str
    user: str
    repair_system: str
    repair_user: str


@dataclass
class OcrRefinePrompts:
    system: str
    user: str


@lru_cache
def _load_prompt_file(path: str) -> dict[str, Any]:
    p = Path(path)
    if not p.is_absolute():
        p = BACKEND_DIR / p
    with p.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def _prompt_path_from_config(key: str, default: str) -> Path:
    y = get_yaml_config()
    rel = y.get("prompts", {}).get(key, default)
    p = Path(rel)
    if not p.is_absolute():
        p = BACKEND_DIR / p
    return p


def get_drafting_prompts() -> DraftingPrompts:
    raw = _load_prompt_file(str(_prompt_path_from_config("drafting_file", "prompts/drafting.yaml")))
    return DraftingPrompts(
        system=raw.get("system", "").strip(),
        user=raw.get("user", "").strip(),
        repair_system=raw.get("repair_system", "").strip(),
        repair_user=raw.get("repair_user", "").strip(),
    )


def get_ocr_refine_prompts() -> OcrRefinePrompts:
    raw = _load_prompt_file(str(_prompt_path_from_config("ocr_refine_file", "prompts/ocr_refine.yaml")))
    return OcrRefinePrompts(
        system=raw.get("system", "").strip(),
        user=raw.get("user", "").strip(),
    )


def render_template(template_str: str, **kwargs: Any) -> str:
    env = Environment(undefined=StrictUndefined, autoescape=False)
    return env.from_string(template_str).render(**kwargs)
