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
    )


def upsert_managed_block_file(path: Path, handle: str) -> bool:
    del handle
    return upsert_generic_managed_block_file(
        path,
        body=prompt_block_body(),
        start_marker=PROMPT_BLOCK_START,
        end_marker=PROMPT_BLOCK_END,
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
