from __future__ import annotations

from pathlib import Path
import shutil
import subprocess

import pytest
from typer.testing import CliRunner

from ai_wiki_toolkit.cli import app

runner = CliRunner()


def test_doctor_is_clean_for_latest_navigation_and_rule_structure(
    repo_env: dict[str, Path],
) -> None:
    install_result = runner.invoke(app, ["install", "--handle", "alice"])
    assert install_result.exit_code == 0

    result = runner.invoke(app, ["doctor", "--handle", "alice", "--strict"])

    assert result.exit_code == 0
    assert "OK    ai-wiki/_toolkit/index.md `ai-wiki/_toolkit/index.md` exists." in result.output
    assert "OK    ai-wiki/_toolkit/workflows.md `ai-wiki/_toolkit/workflows.md` exists." in result.output
    assert "OK    ai-wiki/_toolkit/schema/work-v1.md `ai-wiki/_toolkit/schema/work-v1.md` exists." in result.output
    assert "OK    ai-wiki/_toolkit/schema/team-memory-v1.md `ai-wiki/_toolkit/schema/team-memory-v1.md` exists." in result.output
    assert "OK    .gitignore `.gitignore` already contains the current managed local-state ignore block." in result.output
    assert "OK    ai-wiki/index.md `ai-wiki/index.md` exists. It is repo-owned and is not compared against starter navigation drift." in result.output
    assert "OK    ai-wiki/workflows.md `ai-wiki/workflows.md` points to the managed baseline workflow doc." in result.output
    assert "OK    AGENT.md `AGENT.md` already references the current managed-system prompt entrypoint." in result.output


def test_doctor_suggests_starter_updates_for_repo_docs(repo_env: dict[str, Path]) -> None:
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
    (repo_wiki / "workflows.md").write_text("# Project Workflows\n\nCustom repo workflow.\n", encoding="utf-8")
    (repo_wiki / "_toolkit" / "system.md").write_text("# Toolkit Managed System Rules\n", encoding="utf-8")
    (repo / "AGENT.md").write_text(
        "\n".join(
            [
                "<!-- aiwiki-toolkit:start -->",
                "Read `ai-wiki/index.md`.",
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
    assert "WARN  ai-wiki/_toolkit/index.md `ai-wiki/_toolkit/index.md` is missing." in result.output
    assert "WARN  ai-wiki/_toolkit/workflows.md `ai-wiki/_toolkit/workflows.md` is missing." in result.output
    assert "WARN  ai-wiki/_toolkit/schema/work-v1.md `ai-wiki/_toolkit/schema/work-v1.md` is missing." in result.output
    assert "WARN  ai-wiki/_toolkit/schema/team-memory-v1.md `ai-wiki/_toolkit/schema/team-memory-v1.md` is missing." in result.output
    assert "WARN  .gitignore `.gitignore` is missing the `aiwiki-toolkit` managed local-state ignore block." in result.output
    assert "WARN  ai-wiki/workflows.md `ai-wiki/workflows.md` is missing the pointer to `_toolkit/workflows.md`." in result.output
    assert "WARN  AGENT.md `AGENT.md` has a managed block but is missing current managed-system references:" in result.output
    assert "Suggested starter updates:" in result.output
    assert "Path: ai-wiki/conventions/index.md" in result.output
    assert "Path: ai-wiki/workflows.md" in result.output
    assert "Path: ai-wiki/review-patterns/index.md" in result.output
    assert "Path: ai-wiki/problems/index.md" in result.output
    assert "Path: ai-wiki/features/index.md" in result.output
    assert "Path: ai-wiki/work/index.md" in result.output
    assert "Create this file with the starter content below, then customize it as needed." in result.output
    assert "See also `_toolkit/workflows.md` for package-managed baseline workflows" in result.output
    assert "`ai-wiki/index.md` exists. It is repo-owned and is not compared against starter navigation drift." in result.output


def test_doctor_warns_on_same_scope_duplicate_rule_sections(repo_env: dict[str, Path]) -> None:
    install_result = runner.invoke(app, ["install", "--handle", "alice"])
    assert install_result.exit_code == 0

    repo_workflows = repo_env["repo"] / "ai-wiki" / "workflows.md"
    repo_workflows.write_text(
        "\n".join(
            [
                "# Project Workflows",
                "",
                "See also `_toolkit/workflows.md` for package-managed baseline workflows that ship with `ai-wiki-toolkit`.",
                "",
                "## AI Wiki Maintenance",
                "",
                "1. Run one AI wiki reuse check at the end of every completed task, even when no AI wiki docs were used.",
                "2. If any user-owned repo or system AI wiki docs were consulted, record one `aiwiki-toolkit record-reuse` event per consulted doc.",
                "3. Do not log managed `_toolkit/**` docs with `record-reuse`; if they changed the plan or behavior, cite their paths in a progress update or the final note instead.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    managed_workflows = repo_env["repo"] / "ai-wiki" / "_toolkit" / "workflows.md"
    managed_workflows.write_text(
        "\n".join(
            [
                "# Toolkit Managed Workflows",
                "",
                "## AI Wiki Maintenance",
                "",
                "1. Run one AI wiki reuse check at the end of every completed task, even when no AI wiki docs were used.",
                "2. If any user-owned repo or system AI wiki docs were consulted, record one `aiwiki-toolkit record-reuse` event per consulted doc.",
                "3. Do not log managed `_toolkit/**` docs with `record-reuse`; if they changed the plan or behavior, cite their paths in a progress update or the final note instead.",
                "",
                "## Repo Overlay",
                "",
                "Use `ai-wiki/workflows.md` only for repo-specific additions.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    result = runner.invoke(app, ["doctor", "--handle", "alice", "--strict"])

    assert result.exit_code == 1
    assert "WARN  ai-wiki/_toolkit/workflows.md `ai-wiki/_toolkit/workflows.md` and `ai-wiki/workflows.md` repeat the same same-scope rule sections: AI Wiki Maintenance." in result.output


def test_doctor_warns_on_same_scope_conflicting_rule_sections(repo_env: dict[str, Path]) -> None:
    install_result = runner.invoke(app, ["install", "--handle", "alice"])
    assert install_result.exit_code == 0

    repo_workflows = repo_env["repo"] / "ai-wiki" / "workflows.md"
    repo_workflows.write_text(
        "\n".join(
            [
                "# Project Workflows",
                "",
                "See also `_toolkit/workflows.md` for package-managed baseline workflows that ship with `ai-wiki-toolkit`.",
                "",
                "## AI Wiki Maintenance",
                "",
                "1. Run one AI wiki reuse check only after release tasks are complete.",
                "2. If repo docs were consulted, record one `aiwiki-toolkit record-reuse` event.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    result = runner.invoke(app, ["doctor", "--handle", "alice", "--strict"])

    assert result.exit_code == 1
    assert "WARN  ai-wiki/_toolkit/workflows.md `ai-wiki/_toolkit/workflows.md` and `ai-wiki/workflows.md` define overlapping rule sections with different content: AI Wiki Maintenance." in result.output


def test_doctor_ignores_cross_scope_duplicate_rules(repo_env: dict[str, Path]) -> None:
    install_result = runner.invoke(app, ["install", "--handle", "alice"])
    assert install_result.exit_code == 0

    repo_pattern = repo_env["repo"] / "ai-wiki" / "review-patterns" / "rank-options.md"
    repo_pattern.write_text(
        "\n".join(
            [
                "# Rank Options By Impact",
                "",
                "## Preferred Pattern",
                "",
                "Name the best option first and order the rest by impact.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    home_playbook = repo_env["home_dir"] / "system" / "playbooks" / "rank-options.md"
    home_playbook.write_text(
        "\n".join(
            [
                "# Rank Options By Impact",
                "",
                "## Preferred Pattern",
                "",
                "Name the best option first and order the rest by impact.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    result = runner.invoke(app, ["doctor", "--handle", "alice", "--strict"])

    assert result.exit_code == 0
    assert "rank-options.md" not in result.output


def test_doctor_reports_cross_scope_conflicts_as_info(repo_env: dict[str, Path]) -> None:
    install_result = runner.invoke(app, ["install", "--handle", "alice"])
    assert install_result.exit_code == 0

    repo_pattern = repo_env["repo"] / "ai-wiki" / "review-patterns" / "rank-options.md"
    repo_pattern.write_text(
        "\n".join(
            [
                "# Rank Options By Impact",
                "",
                "## Preferred Pattern",
                "",
                "Name the best option first and order the rest by impact.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    home_playbook = repo_env["home_dir"] / "system" / "playbooks" / "rank-options.md"
    home_playbook.write_text(
        "\n".join(
            [
                "# Rank Options By Impact",
                "",
                "## Preferred Pattern",
                "",
                "List the safe options alphabetically and let the reader choose.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    result = runner.invoke(app, ["doctor", "--handle", "alice", "--strict"])

    assert result.exit_code == 0
    assert "INFO  ai-wiki/review-patterns/rank-options.md `ai-wiki/review-patterns/rank-options.md` overlaps with `<home>/ai-wiki/system/playbooks/rank-options.md` but differs in sections: Preferred Pattern. Repo-local guidance takes precedence." in result.output


def test_doctor_warns_when_telemetry_paths_are_still_tracked(repo_env: dict[str, Path]) -> None:
    if shutil.which("git") is None:
        pytest.skip("git is required for tracked-telemetry doctor coverage")

    repo = repo_env["repo"]
    subprocess.run(
        ["git", "init", "-b", "main"],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
    )

    install_result = runner.invoke(app, ["install", "--handle", "alice"])
    assert install_result.exit_code == 0

    tracked_event = repo / "ai-wiki" / "metrics" / "reuse-events" / "alice.jsonl"
    tracked_event.write_text('{"event_id": "evt_123"}\n', encoding="utf-8")
    tracked_stats = repo / "ai-wiki" / "_toolkit" / "metrics" / "task-stats.json"
    tracked_stats.write_text("{}\n", encoding="utf-8")
    subprocess.run(
        ["git", "add", "-f", tracked_event.as_posix(), tracked_stats.as_posix()],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
    )

    result = runner.invoke(app, ["doctor", "--handle", "alice", "--strict"])

    assert result.exit_code == 1
    assert "WARN  .gitignore Git still tracks AI wiki local-state paths despite the ignore rules." in result.output
    assert "Untrack legacy local-state paths once:" in result.output
    assert "git rm -r --cached --ignore-unmatch .env.aiwiki ai-wiki/metrics/reuse-events ai-wiki/metrics/task-checks ai-wiki/_toolkit/metrics ai-wiki/_toolkit/work ai-wiki/_toolkit/catalog.json" in result.output
