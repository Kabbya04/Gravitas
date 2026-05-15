from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

from app.core.paths import BACKEND_DIR


def load_yaml_config(path: Path | None = None) -> dict[str, Any]:
    cfg_path = path or (BACKEND_DIR / "config.yaml")
    with cfg_path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


@lru_cache
def get_yaml_config() -> dict[str, Any]:
    return load_yaml_config()


def data_dir(yaml_cfg: dict[str, Any], settings) -> Path:
    if settings.data_dir:
        return Path(settings.data_dir).expanduser().resolve()
    base = BACKEND_DIR / "data"
    base.mkdir(parents=True, exist_ok=True)
    return base.resolve()


def chroma_dir(yaml_cfg: dict[str, Any]) -> Path:
    rel = yaml_cfg.get("paths", {}).get("chroma_dir", "chroma_data")
    p = (BACKEND_DIR / rel).resolve() if not Path(rel).is_absolute() else Path(rel)
    p.mkdir(parents=True, exist_ok=True)
    return p


def sqlite_url(yaml_cfg: dict[str, Any], settings) -> str:
    db_name = yaml_cfg.get("paths", {}).get("sqlite_filename", "gravitas.sqlite3")
    db_path = data_dir(yaml_cfg, settings) / db_name
    return f"sqlite:///{db_path}"
