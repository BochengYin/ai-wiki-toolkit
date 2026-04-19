from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from ai_wiki_toolkit.cli import app

runner = CliRunner()


def test_doctor_is_clean_for_latest_index_structure(repo_env: dict[str, Path]) -> None:
    install_result = runner.invoke(app, ["install", "--handle", "alice"])
    assert install_result.exit_code == 0

    result = runner.invoke(app, ["doctor", "--handle", "alice", "--strict"])

    assert result.exit_code == 0
    assert "OK    ai-wiki/index.md `ai-wiki/index.md` already uses the current index-based navigation shape." in result.output
    assert "OK    ai-wiki/review-patterns/index.md `ai-wiki/review-patterns/index.md` exists." in result.output
    assert "OK    ai-wiki/trails/index.md `ai-wiki/trails/index.md` exists." in result.output
    assert "OK    ai-wiki/people/alice/index.md `ai-wiki/people/alice/index.md` exists." in result.output
    assert "OK    ai-wiki/metrics/index.md `ai-wiki/metrics/index.md` exists." in result.output


def test_doctor_suggests_index_upgrade_with_copy_paste_content(repo_env: dict[str, Path]) -> None:
    repo = repo_env["repo"]
    repo_wiki = repo / "ai-wiki"
    (repo_wiki / "review-patterns").mkdir(parents=True)
    (repo_wiki / "trails").mkdir(parents=True)
    (repo_wiki / "people" / "alice").mkdir(parents=True)
    (repo_wiki / "metrics").mkdir(parents=True)
    (repo_wiki / "_toolkit").mkdir(parents=True)
    (repo_wiki / "index.md").write_text(
        "\n".join(
            [
                "# Project AI Wiki Index",
                "",
                "## Read Order",
                "",
                "1. Read `_toolkit/system.md`.",
                "2. Read `review-patterns/` before review work.",
                "3. Read `people/<handle>/drafts/` when continuing draft notes.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (repo_wiki / "_toolkit" / "system.md").write_text("# Toolkit Managed System Rules\n", encoding="utf-8")
    (repo / "AGENT.md").write_text(
        "\n".join(
            [
                "<!-- aiwiki-toolkit:start -->",
                "Read `ai-wiki/review-patterns/` before implementation work.",
                "Read `ai-wiki/people/<handle>/drafts/` when continuing draft notes.",
                "<!-- aiwiki-toolkit:end -->",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    result = runner.invoke(app, ["doctor", "--handle", "alice", "--suggest-index-upgrade"])

    assert result.exit_code == 0
    assert "WARN  ai-wiki/index.md `ai-wiki/index.md` is missing current navigation references:" in result.output
    assert "WARN  ai-wiki/review-patterns/index.md `ai-wiki/review-patterns/index.md` is missing." in result.output
    assert "WARN  AGENT.md `AGENT.md` has a managed block but is missing index-based references:" in result.output
    assert "Suggested index updates:" in result.output
    assert "Path: ai-wiki/index.md" in result.output
    assert "Path: ai-wiki/review-patterns/index.md" in result.output
    assert "Path: ai-wiki/trails/index.md" in result.output
    assert "Path: ai-wiki/people/alice/index.md" in result.output
    assert "Path: ai-wiki/metrics/index.md" in result.output
    assert "Read `review-patterns/index.md` before individual review patterns." in result.output
    assert "This folder is user-owned evidence space for measuring whether the AI wiki is helping in real work." in result.output
