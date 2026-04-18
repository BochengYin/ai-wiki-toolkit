"""Managed block helpers for prompt files."""

from __future__ import annotations

import re
from pathlib import Path

from ai_wiki_toolkit.content import (
    PROMPT_BLOCK_END,
    PROMPT_BLOCK_START,
    prompt_block_body,
)

_MANAGED_BLOCK_RE = re.compile(
    rf"{re.escape(PROMPT_BLOCK_START)}.*?{re.escape(PROMPT_BLOCK_END)}",
    re.DOTALL,
)


def render_managed_block(handle: str) -> str:
    del handle
    return f"{PROMPT_BLOCK_START}\n{prompt_block_body()}\n{PROMPT_BLOCK_END}"


def upsert_managed_block(text: str, handle: str) -> str:
    block = render_managed_block(handle)
    if _MANAGED_BLOCK_RE.search(text):
        updated = _MANAGED_BLOCK_RE.sub(block, text, count=1)
        if not updated.endswith("\n"):
            updated += "\n"
        return updated

    stripped = text.rstrip()
    if stripped:
        return f"{stripped}\n\n{block}\n"
    return f"{block}\n"


def upsert_managed_block_file(path: Path, handle: str) -> bool:
    current = path.read_text(encoding="utf-8") if path.exists() else ""
    updated = upsert_managed_block(current, handle)
    if current == updated:
        return False
    path.write_text(updated, encoding="utf-8")
    return True


def remove_managed_block(text: str) -> str:
    match = _MANAGED_BLOCK_RE.search(text)
    if not match:
        return text

    before = text[: match.start()].rstrip("\n")
    after = text[match.end() :].lstrip("\n")

    if before and after:
        result = f"{before}\n\n{after}"
    elif before:
        result = f"{before}\n"
    elif after:
        result = after if after.endswith("\n") else f"{after}\n"
    else:
        result = ""

    return result


def remove_managed_block_file(path: Path) -> tuple[bool, bool]:
    if not path.exists():
        return False, False

    current = path.read_text(encoding="utf-8")
    updated = remove_managed_block(current)
    if updated == current:
        return False, False

    if not updated:
        path.unlink()
        return True, True

    path.write_text(updated, encoding="utf-8")
    return True, False
