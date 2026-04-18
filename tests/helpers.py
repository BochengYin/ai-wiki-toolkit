from __future__ import annotations

from pathlib import Path
from textwrap import dedent


def write_git_config(
    repo: Path, *, email: str | None = None, name: str | None = None
) -> None:
    lines = ["[core]", "\trepositoryformatversion = 0"]
    if email or name:
        lines.extend(["[user]"])
        if name:
            lines.append(f"\tname = {name}")
        if email:
            lines.append(f"\temail = {email}")
    (repo / ".git" / "config").write_text("\n".join(lines) + "\n", encoding="utf-8")


def snapshot_tree(root: Path) -> list[str]:
    entries: list[str] = []
    for path in sorted(root.rglob("*")):
        relative = path.relative_to(root).as_posix()
        entries.append(f"{relative}/" if path.is_dir() else relative)
    return entries


def strip_margin(text: str) -> str:
    return dedent(text).lstrip("\n")
