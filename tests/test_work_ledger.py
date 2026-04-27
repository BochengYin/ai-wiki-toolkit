from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from ai_wiki_toolkit.cli import app

runner = CliRunner()


def test_work_capture_records_event_and_generated_views(repo_env: dict[str, Path]) -> None:
    install_result = runner.invoke(app, ["install", "--handle", "alice"])
    assert install_result.exit_code == 0

    result = runner.invoke(
        app,
        [
            "work",
            "capture",
            "--work-id",
            "Framework Ledger MVP",
            "--title",
            "Build routeable work ledger",
            "--status",
            "processing",
            "--epic-id",
            "Agent Framework",
            "--link",
            "ai-wiki/people/alice/drafts/framework-roadmap.md",
            "--notes",
            "Captured from conversation todo.",
            "--occurred-at",
            "2026-04-27T10:00:00+10:00",
            "--handle",
            "alice",
        ],
    )

    assert result.exit_code == 0
    repo_wiki = repo_env["repo"] / "ai-wiki"
    event_log = repo_wiki / "work" / "events" / "alice.jsonl"
    payload = json.loads(event_log.read_text(encoding="utf-8").splitlines()[0])
    assert payload["schema_version"] == "work-v1"
    assert payload["event_type"] == "captured"
    assert payload["work_id"] == "framework-ledger-mvp"
    assert payload["epic_id"] == "agent-framework"

    state = json.loads((repo_wiki / "_toolkit" / "work" / "state.json").read_text(encoding="utf-8"))
    task = state["tasks"]["framework-ledger-mvp"]
    assert task["status"] == "processing"
    assert task["title"] == "Build routeable work ledger"
    assert task["event_count"] == 1
    assert task["links"] == ["ai-wiki/people/alice/drafts/framework-roadmap.md"]
    assert state["summary"]["open_task_count"] == 1

    report = (repo_wiki / "_toolkit" / "work" / "report.md").read_text(encoding="utf-8")
    assert "# AI Wiki Work Report" in report
    assert "Build routeable work ledger" in report
    assert "`framework-ledger-mvp`" in report


def test_work_status_updates_current_state_without_rewriting_events(repo_env: dict[str, Path]) -> None:
    install_result = runner.invoke(app, ["install", "--handle", "alice"])
    assert install_result.exit_code == 0

    capture_result = runner.invoke(
        app,
        [
            "work",
            "capture",
            "--work-id",
            "work-ledger",
            "--title",
            "Build work ledger",
            "--status",
            "active",
            "--occurred-at",
            "2026-04-27T10:00:00+10:00",
            "--handle",
            "alice",
        ],
    )
    assert capture_result.exit_code == 0

    status_result = runner.invoke(
        app,
        [
            "work",
            "status",
            "--work-id",
            "work-ledger",
            "--status",
            "done",
            "--notes",
            "Merged and released.",
            "--occurred-at",
            "2026-04-27T11:00:00+10:00",
            "--handle",
            "alice",
        ],
    )

    assert status_result.exit_code == 0
    repo_wiki = repo_env["repo"] / "ai-wiki"
    assert len((repo_wiki / "work" / "events" / "alice.jsonl").read_text(encoding="utf-8").splitlines()) == 2

    state = json.loads((repo_wiki / "_toolkit" / "work" / "state.json").read_text(encoding="utf-8"))
    task = state["tasks"]["work-ledger"]
    assert task["status"] == "done"
    assert task["last_notes"] == "Merged and released."
    assert state["summary"]["open_task_count"] == 0
    assert state["summary"]["tasks_by_status"] == {"done": 1}


def test_work_report_requires_initialized_repo_wiki(repo_env: dict[str, Path]) -> None:
    result = runner.invoke(app, ["work", "report"])

    assert result.exit_code == 1
    assert "Run `aiwiki-toolkit install` first." in result.output


def test_work_capture_rejects_invalid_status(repo_env: dict[str, Path]) -> None:
    install_result = runner.invoke(app, ["install", "--handle", "alice"])
    assert install_result.exit_code == 0

    result = runner.invoke(
        app,
        [
            "work",
            "capture",
            "--work-id",
            "work-ledger",
            "--title",
            "Build work ledger",
            "--status",
            "invalid-status",
        ],
    )

    assert result.exit_code == 1
    assert "Invalid work status" in result.output
