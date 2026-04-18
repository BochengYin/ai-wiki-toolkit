"""Helpers for future opencode.json integration."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ai_wiki_toolkit.content import OPENCODE_KEY, default_opencode_config


def upsert_opencode_config(
    path: Path, payload: dict[str, Any] | None = None
) -> dict[str, Any]:
    if path.exists():
        current = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(current, dict):
            raise ValueError("opencode.json must contain a top-level JSON object.")
    else:
        current = {}

    current_section = current.get(OPENCODE_KEY, {})
    if not isinstance(current_section, dict):
        current_section = {}

    merged_section = {
        **default_opencode_config(),
        **current_section,
        **(payload or {}),
    }
    current[OPENCODE_KEY] = merged_section

    path.write_text(json.dumps(current, indent=2) + "\n", encoding="utf-8")
    return current


def remove_opencode_config(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None

    current = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(current, dict):
        raise ValueError("opencode.json must contain a top-level JSON object.")

    if OPENCODE_KEY not in current:
        return current

    del current[OPENCODE_KEY]

    if current:
        path.write_text(json.dumps(current, indent=2) + "\n", encoding="utf-8")
        return current

    path.unlink()
    return {}
