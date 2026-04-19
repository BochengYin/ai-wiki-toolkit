"""Generic managed block helpers for text files."""

from __future__ import annotations

from pathlib import Path
import re


def _managed_block_re(start_marker: str, end_marker: str) -> re.Pattern[str]:
    return re.compile(
        rf"(?ms)^[ \t]*{re.escape(start_marker)}[ \t]*\n.*?^[ \t]*{re.escape(end_marker)}[ \t]*(?:\n|$)"
    )


def render_managed_block(*, body: str, start_marker: str, end_marker: str) -> str:
    return f"{start_marker}\n{body}\n{end_marker}"


def upsert_managed_block(
    text: str, *, body: str, start_marker: str, end_marker: str
) -> str:
    block = render_managed_block(body=body, start_marker=start_marker, end_marker=end_marker)
    pattern = _managed_block_re(start_marker, end_marker)
    if pattern.search(text):
        updated = pattern.sub(block, text, count=1)
        if not updated.endswith("\n"):
            updated += "\n"
        return updated

    stripped = text.rstrip()
    if stripped:
        return f"{stripped}\n\n{block}\n"
    return f"{block}\n"


def upsert_managed_block_file(
    path: Path, *, body: str, start_marker: str, end_marker: str
) -> bool:
    current = path.read_text(encoding="utf-8") if path.exists() else ""
    updated = upsert_managed_block(
        current,
        body=body,
        start_marker=start_marker,
        end_marker=end_marker,
    )
    if current == updated:
        return False
    path.write_text(updated, encoding="utf-8")
    return True


def remove_managed_block(text: str, *, start_marker: str, end_marker: str) -> str:
    pattern = _managed_block_re(start_marker, end_marker)
    match = pattern.search(text)
    if not match:
        return text

    before = text[: match.start()].rstrip("\n")
    after = text[match.end() :].lstrip("\n")

    if before and after:
        return f"{before}\n\n{after}"
    if before:
        return f"{before}\n"
    if after:
        return after if after.endswith("\n") else f"{after}\n"
    return ""


def remove_managed_block_file(
    path: Path, *, start_marker: str, end_marker: str
) -> tuple[bool, bool]:
    if not path.exists():
        return False, False

    current = path.read_text(encoding="utf-8")
    updated = remove_managed_block(
        current,
        start_marker=start_marker,
        end_marker=end_marker,
    )
    if updated == current:
        return False, False

    if not updated:
        path.unlink()
        return True, True

    path.write_text(updated, encoding="utf-8")
    return True, False
