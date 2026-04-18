"""Helpers for working with a Homebrew tap repository."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from ai_wiki_toolkit.homebrew_formula import FORMULA_FILENAME


@dataclass(frozen=True)
class TapSyncResult:
    formula_path: Path
    changed: bool


def default_tap_repository(repository_owner: str) -> str:
    owner = repository_owner.strip()
    if not owner:
        raise ValueError("repository_owner must not be empty")
    return f"{owner}/homebrew-tap"


def tap_formula_path(tap_root: Path) -> Path:
    return tap_root / "Formula" / FORMULA_FILENAME


def release_commit_message(version: str) -> str:
    return f"Update aiwiki-toolkit to {version}"


def sync_formula_into_tap(formula_text: str, tap_root: Path) -> TapSyncResult:
    formula_path = tap_formula_path(tap_root)
    formula_path.parent.mkdir(parents=True, exist_ok=True)
    current = formula_path.read_text(encoding="utf-8") if formula_path.exists() else None
    if current == formula_text:
        return TapSyncResult(formula_path=formula_path, changed=False)
    formula_path.write_text(formula_text, encoding="utf-8")
    return TapSyncResult(formula_path=formula_path, changed=True)
