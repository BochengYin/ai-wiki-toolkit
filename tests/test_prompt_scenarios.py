from __future__ import annotations

from pathlib import Path

import pytest
from typer.testing import CliRunner

from ai_wiki_toolkit.cli import app
from ai_wiki_toolkit.content import PROMPT_BLOCK_END, PROMPT_BLOCK_START

runner = CliRunner()


@pytest.mark.parametrize(
    ("existing_files", "expected_files"),
    [
        (["AGENTS.md"], ["AGENTS.md"]),
        (["AGENT.md"], ["AGENT.md"]),
        (["CLAUDE.md"], ["CLAUDE.md"]),
        (["AGENTS.md", "CLAUDE.md"], ["AGENTS.md", "CLAUDE.md"]),
    ],
)
def test_init_updates_only_existing_prompt_files(
    repo_env: dict[str, Path], existing_files: list[str], expected_files: list[str]
) -> None:
    repo = repo_env["repo"]
    for filename in existing_files:
        (repo / filename).write_text("# Existing\n", encoding="utf-8")

    result = runner.invoke(app, ["init", "--handle", "alice"])

    assert result.exit_code == 0
    for filename in expected_files:
        text = (repo / filename).read_text(encoding="utf-8")
        assert PROMPT_BLOCK_START in text
        assert "ai-wiki/_toolkit/system.md" in text

    for filename in {"AGENTS.md", "AGENT.md", "CLAUDE.md"} - set(expected_files):
        assert not (repo / filename).exists()


def test_init_replaces_existing_managed_block_and_preserves_surrounding_text(
    repo_env: dict[str, Path],
) -> None:
    agent = repo_env["repo"] / "AGENT.md"
    agent.write_text(
        "Before\n\n"
        f"{PROMPT_BLOCK_START}\nold block\n{PROMPT_BLOCK_END}\n\n"
        "After\n",
        encoding="utf-8",
    )

    result = runner.invoke(app, ["init", "--handle", "alice"])

    assert result.exit_code == 0
    updated = agent.read_text(encoding="utf-8")
    assert updated.startswith("Before\n\n")
    assert updated.endswith("After\n")
    assert "old block" not in updated
    assert updated.count(PROMPT_BLOCK_START) == 1
    assert updated.count(PROMPT_BLOCK_END) == 1


def test_init_appends_managed_block_when_prompt_file_has_no_managed_section(
    repo_env: dict[str, Path],
) -> None:
    claude = repo_env["repo"] / "CLAUDE.md"
    claude.write_text("# Existing Claude prompt\n", encoding="utf-8")

    result = runner.invoke(app, ["init", "--handle", "alice"])

    assert result.exit_code == 0
    text = claude.read_text(encoding="utf-8")
    assert text.startswith("# Existing Claude prompt\n\n")
    assert PROMPT_BLOCK_START in text
    assert "ai-wiki/_toolkit/system.md" in text


def test_init_creates_agent_when_no_prompt_files_exist(
    repo_env: dict[str, Path],
) -> None:
    result = runner.invoke(app, ["init", "--handle", "alice"])

    assert result.exit_code == 0
    assert (repo_env["repo"] / "AGENT.md").exists()
    assert not (repo_env["repo"] / "CLAUDE.md").exists()


def test_init_does_not_churn_prompt_block_across_different_handles(
    repo_env: dict[str, Path],
) -> None:
    first = runner.invoke(app, ["init", "--handle", "alice"])
    assert first.exit_code == 0
    agent_path = repo_env["repo"] / "AGENT.md"
    first_text = agent_path.read_text(encoding="utf-8")

    second = runner.invoke(app, ["init", "--handle", "bob"])

    assert second.exit_code == 0
    assert agent_path.read_text(encoding="utf-8") == first_text


def test_init_appends_managed_block_when_marker_strings_appear_inline(
    repo_env: dict[str, Path],
) -> None:
    agents = repo_env["repo"] / "AGENTS.md"
    agents.write_text(
        "Keep edits inside the `<!-- aiwiki-toolkit:start -->` and "
        "`<!-- aiwiki-toolkit:end -->` markers.\n",
        encoding="utf-8",
    )

    result = runner.invoke(app, ["init", "--handle", "alice"])

    assert result.exit_code == 0
    updated = agents.read_text(encoding="utf-8")
    assert updated.startswith(
        "Keep edits inside the `<!-- aiwiki-toolkit:start -->` and "
        "`<!-- aiwiki-toolkit:end -->` markers.\n\n"
    )
    assert updated.count(PROMPT_BLOCK_START) == 2
    assert updated.count(PROMPT_BLOCK_END) == 2
