"""Minimal frontmatter helpers for ai-wiki-toolkit note templates."""

from __future__ import annotations

from typing import Mapping


def _render_value(value: object) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if value is None:
        return "null"
    if isinstance(value, int):
        return str(value)
    escaped = str(value).replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


def render_frontmatter(metadata: Mapping[str, object]) -> str:
    lines = ["---"]
    for key, value in metadata.items():
        lines.append(f"{key}: {_render_value(value)}")
    lines.append("---")
    return "\n".join(lines)


def _parse_value(raw: str) -> object:
    if raw == "true":
        return True
    if raw == "false":
        return False
    if raw == "null":
        return None
    if raw.startswith('"') and raw.endswith('"'):
        inner = raw[1:-1]
        return inner.replace('\\"', '"').replace("\\\\", "\\")
    try:
        return int(raw)
    except ValueError:
        return raw


def parse_frontmatter(text: str) -> tuple[dict[str, object], str]:
    if not text.startswith("---\n"):
        return {}, text

    lines = text.splitlines()
    end_index = None
    for index in range(1, len(lines)):
        if lines[index] == "---":
            end_index = index
            break

    if end_index is None:
        return {}, text

    metadata: dict[str, object] = {}
    for line in lines[1:end_index]:
        key, sep, value = line.partition(":")
        if not sep:
            continue
        metadata[key.strip()] = _parse_value(value.strip())

    body = "\n".join(lines[end_index + 1 :])
    if text.endswith("\n"):
        body += "\n"
    return metadata, body


def replace_frontmatter(text: str, metadata: Mapping[str, object]) -> str:
    _, body = parse_frontmatter(text)
    frontmatter = render_frontmatter(metadata)
    return f"{frontmatter}\n{body.lstrip()}"
