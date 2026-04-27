"""Managed `.gitignore` helpers."""

from __future__ import annotations

from pathlib import Path

from ai_wiki_toolkit.content import (
    GITIGNORE_BLOCK_END,
    GITIGNORE_BLOCK_START,
    TELEMETRY_IGNORE_PATHS,
    gitignore_block_body,
)
from ai_wiki_toolkit.managed_block import (
    remove_managed_block_file,
    upsert_managed_block_file,
)


def upsert_gitignore_block_file(path: Path) -> bool:
    return upsert_managed_block_file(
        path,
        body=gitignore_block_body(),
        start_marker=GITIGNORE_BLOCK_START,
        end_marker=GITIGNORE_BLOCK_END,
    )


def remove_gitignore_block_file(path: Path) -> tuple[bool, bool]:
    return remove_managed_block_file(
        path,
        start_marker=GITIGNORE_BLOCK_START,
        end_marker=GITIGNORE_BLOCK_END,
    )


def gitignore_has_current_telemetry_block(text: str) -> bool:
    if GITIGNORE_BLOCK_START not in text or GITIGNORE_BLOCK_END not in text:
        return False
    return all(path in text for path in TELEMETRY_IGNORE_PATHS)


def telemetry_untrack_command() -> str:
    untrack_targets = (
        "ai-wiki/metrics/reuse-events",
        "ai-wiki/metrics/task-checks",
        "ai-wiki/_toolkit/metrics",
        "ai-wiki/_toolkit/work",
        "ai-wiki/_toolkit/catalog.json",
    )
    return "git rm -r --cached --ignore-unmatch " + " ".join(untrack_targets)
