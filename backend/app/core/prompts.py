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


@lru_cache
def _load_prompt_file(path: str) -> dict[str, Any]:
    p = Path(path)
    if not p.is_absolute():
        p = BACKEND_DIR / p
    with p.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def get_drafting_prompts() -> DraftingPrompts:
    y = get_yaml_config()
    rel = y.get("prompts", {}).get("drafting_file", "prompts/drafting.yaml")
    raw = _load_prompt_file(str(BACKEND_DIR / rel) if not Path(rel).is_absolute() else rel)
    return DraftingPrompts(
        system=raw.get("system", "").strip(),
        user=raw.get("user", "").strip(),
        repair_system=raw.get("repair_system", "").strip(),
        repair_user=raw.get("repair_user", "").strip(),
    )


def render_template(template_str: str, **kwargs: Any) -> str:
    env = Environment(undefined=StrictUndefined, autoescape=False)
    return env.from_string(template_str).render(**kwargs)
