from __future__ import annotations

from functools import lru_cache
from typing import NamedTuple

from openai import OpenAI

from app.core.settings import get_settings
from app.core.yaml_config import get_yaml_config


class GroqRuntime(NamedTuple):
    client: OpenAI
    model: str
    temperature: float
    max_tokens: int


@lru_cache
def get_groq_runtime() -> GroqRuntime:
    """Shared Groq OpenAI-compatible client and default generation settings."""
    yaml = get_yaml_config()
    settings = get_settings()
    g = yaml.get("groq", {})
    api_key = settings.groq_api_key
    if not api_key:
        raise RuntimeError("GROQ_API_KEY is not set")
    client = OpenAI(api_key=api_key, base_url=str(g.get("base_url")))
    model = settings.groq_model or str(g.get("model"))
    return GroqRuntime(
        client=client,
        model=model,
        temperature=float(g.get("temperature", 0.2)),
        max_tokens=int(g.get("max_tokens", 4096)),
    )
