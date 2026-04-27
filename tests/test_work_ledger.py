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
    assert payload["author_handle"] == "alice"
    assert payload["reporter_handle"] == "alice"
    assert payload["assignee_handles"] == ["alice"]

    state = json.loads((repo_wiki / "_toolkit" / "work" / "state.json").read_text(encoding="utf-8"))
    task = state["tasks"]["framework-ledger-mvp"]
    assert task["status"] == "processing"
    assert task["title"] == "Build routeable work ledger"
    assert task["reporter_handle"] == "alice"
    assert task["assignee_handles"] == ["alice"]
    assert task["event_count"] == 1
    assert task["links"] == ["ai-wiki/people/alice/drafts/framework-roadmap.md"]
    assert state["summary"]["open_task_count"] == 1

    report = (repo_wiki / "_toolkit" / "work" / "report.md").read_text(encoding="utf-8")
    assert "# AI Wiki Work Report" in report
    assert "Build routeable work ledger" in report
    assert "`framework-ledger-mvp`" in report

    by_assignee = (
        repo_wiki / "_toolkit" / "work" / "by-assignee" / "alice.md"
    ).read_text(encoding="utf-8")
    assert "# Assigned Work: alice" in by_assignee
    assert "`framework-ledger-mvp`" in by_assignee

    by_reporter = (
        repo_wiki / "_toolkit" / "work" / "by-reporter" / "alice.md"
    ).read_text(encoding="utf-8")
    assert "# Reported Work: alice" in by_reporter
    assert "`framework-ledger-mvp`" in by_reporter


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


def test_work_capture_uses_env_aiwiki_actor_by_default(repo_env: dict[str, Path]) -> None:
    install_result = runner.invoke(app, ["install", "--handle", "Alice Reviewer"])
    assert install_result.exit_code == 0

    result = runner.invoke(
        app,
        [
            "work",
            "capture",
            "--work-id",
            "identity-scoped-work",
            "--title",
            "Use local identity for work ownership",
            "--occurred-at",
            "2026-04-27T10:00:00+10:00",
        ],
    )

    assert result.exit_code == 0
    event_log = repo_env["repo"] / "ai-wiki" / "work" / "events" / "alice-reviewer.jsonl"
    payload = json.loads(event_log.read_text(encoding="utf-8").splitlines()[0])
    assert payload["author_handle"] == "alice-reviewer"
    assert payload["reporter_handle"] == "alice-reviewer"
    assert payload["assignee_handles"] == ["alice-reviewer"]


def test_work_capture_accepts_reporter_and_assignee_overrides(repo_env: dict[str, Path]) -> None:
    install_result = runner.invoke(app, ["install", "--handle", "alice"])
    assert install_result.exit_code == 0

    result = runner.invoke(
        app,
        [
            "work",
            "capture",
            "--work-id",
            "delegated-work",
            "--title",
            "Let Bob own this task",
            "--reporter",
            "Alice",
            "--assignee",
            "Bob",
            "--assignee",
            "Carol",
        ],
    )

    assert result.exit_code == 0
    event_log = repo_env["repo"] / "ai-wiki" / "work" / "events" / "alice.jsonl"
    payload = json.loads(event_log.read_text(encoding="utf-8").splitlines()[0])
    assert payload["author_handle"] == "alice"
    assert payload["reporter_handle"] == "alice"
    assert payload["assignee_handles"] == ["bob", "carol"]


def test_work_mine_uses_local_actor_and_excludes_closed_tasks(repo_env: dict[str, Path]) -> None:
    install_result = runner.invoke(app, ["install", "--handle", "bob"])
    assert install_result.exit_code == 0

    alice_result = runner.invoke(
        app,
        [
            "work",
            "capture",
            "--work-id",
            "alice-task",
            "--title",
            "Alice owns this task",
            "--assignee",
            "alice",
            "--handle",
            "alice",
        ],
    )
    assert alice_result.exit_code == 0

    bob_result = runner.invoke(
        app,
        [
            "work",
            "capture",
            "--work-id",
            "bob-task",
            "--title",
            "Bob owns this task",
            "--assignee",
            "bob",
            "--handle",
            "bob",
        ],
    )
    assert bob_result.exit_code == 0

    closed_result = runner.invoke(
        app,
        [
            "work",
            "capture",
            "--work-id",
            "bob-done-task",
            "--title",
            "Bob already finished this task",
            "--status",
            "done",
            "--assignee",
            "bob",
            "--handle",
            "bob",
        ],
    )
    assert closed_result.exit_code == 0

    result = runner.invoke(app, ["work", "mine"])

    assert result.exit_code == 0
    assert "# My Work: bob" in result.output
    assert "`bob-task`" in result.output
    assert "`alice-task`" not in result.output
    assert "`bob-done-task`" not in result.output

    include_closed_result = runner.invoke(app, ["work", "mine", "--include-closed"])

    assert include_closed_result.exit_code == 0
    assert "`bob-task`" in include_closed_result.output
    assert "`bob-done-task`" in include_closed_result.output


def test_work_list_filters_by_assignee_and_reporter(repo_env: dict[str, Path]) -> None:
    install_result = runner.invoke(app, ["install", "--handle", "alice"])
    assert install_result.exit_code == 0

    first_result = runner.invoke(
        app,
        [
            "work",
            "capture",
            "--work-id",
            "delegated-work",
            "--title",
            "Bob owns delegated work",
            "--reporter",
            "alice",
            "--assignee",
            "bob",
            "--handle",
            "alice",
        ],
    )
    assert first_result.exit_code == 0

    second_result = runner.invoke(
        app,
        [
            "work",
            "capture",
            "--work-id",
            "alice-work",
            "--title",
            "Alice owns local work",
            "--reporter",
            "alice",
            "--assignee",
            "alice",
            "--handle",
            "alice",
        ],
    )
    assert second_result.exit_code == 0

    assignee_result = runner.invoke(app, ["work", "list", "--assignee", "bob"])

    assert assignee_result.exit_code == 0
    assert "# Work assignee=bob" in assignee_result.output
    assert "`delegated-work`" in assignee_result.output
    assert "`alice-work`" not in assignee_result.output

    reporter_result = runner.invoke(app, ["work", "list", "--reporter", "alice"])

    assert reporter_result.exit_code == 0
    assert "`delegated-work`" in reporter_result.output
    assert "`alice-work`" in reporter_result.output


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
