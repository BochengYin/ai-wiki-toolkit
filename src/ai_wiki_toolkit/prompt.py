"""Managed block helpers for prompt files."""

from __future__ import annotations

from pathlib import Path

from ai_wiki_toolkit.content import (
    PROMPT_BLOCK_END,
    PROMPT_BLOCK_START,
    prompt_block_body,
)
from ai_wiki_toolkit.managed_block import (
    remove_managed_block as remove_generic_managed_block,
    remove_managed_block_file as remove_generic_managed_block_file,
    render_managed_block as render_generic_managed_block,
    upsert_managed_block as upsert_generic_managed_block,
    upsert_managed_block_file as upsert_generic_managed_block_file,
)


def _prompt_insert_after_intro(text: str, block: str) -> str:
    lines = text.splitlines()
    if not lines or not lines[0].lstrip().startswith("# "):
        return f"{text}\n\n{block}\n"

    insert_at = 1
    while insert_at < len(lines) and not lines[insert_at].strip():
        insert_at += 1

    if insert_at >= len(lines):
        return f"{text}\n\n{block}\n"

    if lines[insert_at].lstrip().startswith("#"):
        before = "\n".join(lines[:1]).rstrip()
        after = "\n".join(lines[1:]).lstrip("\n")
    else:
        while insert_at < len(lines) and lines[insert_at].strip():
            insert_at += 1
        before = "\n".join(lines[:insert_at]).rstrip()
        after = "\n".join(lines[insert_at:]).lstrip("\n")

    if after:
        return f"{before}\n\n{block}\n\n{after}\n"
    return f"{before}\n\n{block}\n"


def render_managed_block(handle: str) -> str:
    del handle
    return render_generic_managed_block(
        body=prompt_block_body(),
        start_marker=PROMPT_BLOCK_START,
        end_marker=PROMPT_BLOCK_END,
    )


def upsert_managed_block(text: str, handle: str) -> str:
    del handle
    return upsert_generic_managed_block(
        text,
        body=prompt_block_body(),
        start_marker=PROMPT_BLOCK_START,
        end_marker=PROMPT_BLOCK_END,
        insert_block=_prompt_insert_after_intro,
    )


def upsert_managed_block_file(path: Path, handle: str) -> bool:
    del handle
    return upsert_generic_managed_block_file(
        path,
        body=prompt_block_body(),
        start_marker=PROMPT_BLOCK_START,
        end_marker=PROMPT_BLOCK_END,
        insert_block=_prompt_insert_after_intro,
    )


def remove_managed_block(text: str) -> str:
    return remove_generic_managed_block(
        text,
        start_marker=PROMPT_BLOCK_START,
        end_marker=PROMPT_BLOCK_END,
    )


def remove_managed_block_file(path: Path) -> tuple[bool, bool]:
    return remove_generic_managed_block_file(
        path,
        start_marker=PROMPT_BLOCK_START,
        end_marker=PROMPT_BLOCK_END,
    )
