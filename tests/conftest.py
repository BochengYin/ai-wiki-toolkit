from __future__ import annotations

import sys
from pathlib import Path
from textwrap import dedent

import pytest

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
TESTS = ROOT / "tests"

if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))
if str(TESTS) not in sys.path:
    sys.path.insert(0, str(TESTS))


@pytest.fixture
def repo_env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> dict[str, Path]:
    repo = tmp_path / "repo"
    repo.mkdir()
    git_dir = repo / ".git"
    git_dir.mkdir()
    (git_dir / "config").write_text("[core]\n\trepositoryformatversion = 0\n", encoding="utf-8")

    home_dir = tmp_path / "home" / "ai-wiki"
    monkeypatch.setenv("AIWIKI_TOOLKIT_HOME_DIR", str(home_dir))
    monkeypatch.chdir(repo)

    return {"repo": repo, "home_dir": home_dir, "system_dir": home_dir / "system"}


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
    entries = [
        f"{path.relative_to(root).as_posix()}/"
        if path.is_dir()
        else path.relative_to(root).as_posix()
        for path in root.rglob("*")
    ]
    return sorted(entries)


def strip_margin(text: str) -> str:
    return dedent(text).lstrip("\n")
