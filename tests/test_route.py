from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from ai_wiki_toolkit.cli import app
from helpers import strip_margin

runner = CliRunner()


def test_route_generates_context_packet_with_cited_sources(repo_env: dict[str, Path]) -> None:
    install_result = runner.invoke(app, ["install", "--handle", "alice"])
    assert install_result.exit_code == 0

    convention_path = (
        repo_env["repo"]
        / "ai-wiki"
        / "conventions"
        / "package-managed-vs-user-owned-docs.md"
    )
    convention_path.write_text(
        strip_margin(
            """
            ---
            title: "Package-managed vs user-owned docs"
            ---
            # Package-Managed Vs User-Owned Docs

            ## Rule

            Put evolving package-controlled guidance in `ai-wiki/_toolkit/**`.
            Keep user-owned docs stable unless a contributor intentionally edits them.
            Do not rewrite user-owned AI wiki docs during install.
            """
        ),
        encoding="utf-8",
    )

    result = runner.invoke(
        app,
        [
            "route",
            "--task",
            "Update scaffold prompt routing without overwriting user-owned AI wiki docs.",
            "--changed-path",
            "src/ai_wiki_toolkit/content.py",
            "--format",
            "json",
        ],
    )

    assert result.exit_code == 0
    packet = json.loads(result.output)
    assert packet["schema_version"] == "route-v1"
    assert packet["route"]["task_type"] == "scaffold_prompt_workflow"
    assert "user_owned_docs" in packet["route"]["risk_tags"]
    assert "managed_prompt_block" in packet["route"]["risk_tags"]

    must_load_ids = {doc["doc_id"] for doc in packet["must_load"]}
    assert "constraints" in must_load_ids
    assert "conventions/package-managed-vs-user-owned-docs" in must_load_ids

    rules = packet["must_follow"]
    assert rules
    assert all(rule["source"].startswith("ai-wiki/") for rule in rules)
    assert any(
        rule["rule"] == "Do not rewrite user-owned AI wiki docs during install."
        and rule["source"] == "ai-wiki/conventions/package-managed-vs-user-owned-docs.md"
        for rule in rules
    )


def test_route_text_packet_is_agent_readable(repo_env: dict[str, Path]) -> None:
    install_result = runner.invoke(app, ["install", "--handle", "alice"])
    assert install_result.exit_code == 0

    result = runner.invoke(
        app,
        [
            "route",
            "--task",
            "Diagnose a failing release smoke workflow.",
            "--changed-path",
            ".github/workflows/release.yml",
            "--max-docs",
            "3",
        ],
    )

    assert result.exit_code == 0
    assert "# AI Wiki Context Packet" in result.output
    assert "Task Type: `release_distribution`" in result.output
    assert "## Must Load" in result.output
    assert "## Trust Model" in result.output


def test_route_requires_initialized_repo_wiki(repo_env: dict[str, Path]) -> None:
    result = runner.invoke(
        app,
        [
            "route",
            "--task",
            "Update prompt routing.",
        ],
    )

    assert result.exit_code == 1
    assert "Run `aiwiki-toolkit install` first." in result.output


def test_route_rejects_task_and_task_file_together(repo_env: dict[str, Path]) -> None:
    install_result = runner.invoke(app, ["install", "--handle", "alice"])
    assert install_result.exit_code == 0
    task_file = repo_env["repo"] / "task.md"
    task_file.write_text("Update prompt routing.\n", encoding="utf-8")

    result = runner.invoke(
        app,
        [
            "route",
            "--task",
            "Update prompt routing.",
            "--task-file",
            str(task_file),
        ],
    )

    assert result.exit_code == 1
    assert "Use either --task or --task-file" in result.output
