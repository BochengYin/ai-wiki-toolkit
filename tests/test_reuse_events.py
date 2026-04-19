from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from ai_wiki_toolkit.cli import app

runner = CliRunner()


def test_record_reuse_appends_event_and_refreshes_stats(repo_env: dict[str, Path]) -> None:
    install_result = runner.invoke(app, ["install", "--handle", "alice"])
    assert install_result.exit_code == 0

    result = runner.invoke(
        app,
        [
            "record-reuse",
            "--doc-id",
            "review-patterns/shared-prompt-files-must-be-user-agnostic",
            "--task-id",
            "task-release-followup",
            "--retrieval-mode",
            "lookup",
            "--evidence-mode",
            "explicit",
            "--reuse-outcome",
            "resolved",
            "--reuse-effect",
            "avoided_retry",
            "--reuse-effect",
            "faster_resolution",
            "--agent-name",
            "codex",
            "--model",
            "gpt-5",
            "--saved-tokens",
            "1200",
            "--saved-seconds",
            "45",
            "--notes",
            "Found the release rule after checking the wiki.",
            "--observed-at",
            "2026-04-19T22:00:00+10:00",
            "--handle",
            "alice",
        ],
    )

    assert result.exit_code == 0
    event_log_path = repo_env["repo"] / "ai-wiki" / "metrics" / "reuse-events" / "alice.jsonl"
    lines = event_log_path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1
    event = json.loads(lines[0])
    assert event == {
        "agent_name": "codex",
        "author_handle": "alice",
        "doc_id": "review-patterns/shared-prompt-files-must-be-user-agnostic",
        "doc_kind": "review_pattern",
        "estimated_savings": {"saved_seconds": 45, "saved_tokens": 1200},
        "event_id": event["event_id"],
        "evidence_mode": "explicit",
        "model": "gpt-5",
        "notes": "Found the release rule after checking the wiki.",
        "observed_at": "2026-04-19T22:00:00+10:00",
        "retrieval_mode": "lookup",
        "reuse_effects": ["avoided_retry", "faster_resolution"],
        "reuse_outcome": "resolved",
        "schema_version": "reuse-v1",
        "task_id": "task-release-followup",
    }
    assert event["event_id"].startswith("evt_")

    document_stats = json.loads(
        (repo_env["repo"] / "ai-wiki" / "_toolkit" / "metrics" / "document-stats.json").read_text(
            encoding="utf-8"
        )
    )
    assert document_stats["documents"] == {
        "review-patterns/shared-prompt-files-must-be-user-agnostic": {
            "effective_reuse_count": 1,
            "last_effective_at": "2026-04-19T22:00:00+10:00",
            "last_observed_at": "2026-04-19T22:00:00+10:00",
            "lookup_reuse_count": 1,
            "preloaded_reuse_count": 0,
            "total_events": 1,
        }
    }

    task_stats = json.loads(
        (repo_env["repo"] / "ai-wiki" / "_toolkit" / "metrics" / "task-stats.json").read_text(
            encoding="utf-8"
        )
    )
    assert task_stats["tasks"] == {
        "task-release-followup": {
            "check_count": 0,
            "effective_reuse_count": 1,
            "estimated_seconds_saved": 45,
            "estimated_token_savings": 1200,
            "last_check_outcome": None,
            "last_checked_at": None,
            "lookup_reuse_count": 1,
            "preloaded_reuse_count": 0,
            "reuse_checked": False,
            "reused_docs": 1,
            "total_events": 1,
        }
    }
    assert task_stats["summary"] == {
        "checked_tasks": 0,
        "tasks_with_events_but_no_check": 1,
        "tasks_with_wiki_use": 0,
        "tasks_without_wiki_use": 0,
    }


def test_record_reuse_requires_initialized_repo_wiki(repo_env: dict[str, Path]) -> None:
    result = runner.invoke(
        app,
        [
            "record-reuse",
            "--doc-id",
            "review-patterns/example",
            "--task-id",
            "task-1",
            "--retrieval-mode",
            "preloaded",
            "--evidence-mode",
            "inferred",
            "--reuse-outcome",
            "partial",
        ],
    )

    assert result.exit_code == 1
    assert "Run `aiwiki-toolkit install` first." in result.output


def test_record_reuse_rejects_managed_toolkit_docs(repo_env: dict[str, Path]) -> None:
    install_result = runner.invoke(app, ["install", "--handle", "alice"])
    assert install_result.exit_code == 0

    result = runner.invoke(
        app,
        [
            "record-reuse",
            "--doc-id",
            "_toolkit/system",
            "--task-id",
            "task-1",
            "--retrieval-mode",
            "preloaded",
            "--evidence-mode",
            "explicit",
            "--reuse-outcome",
            "resolved",
            "--handle",
            "alice",
        ],
    )

    assert result.exit_code == 1
    assert "must not be recorded with `record-reuse`" in result.output


def test_record_reuse_check_appends_task_check_and_refreshes_stats(repo_env: dict[str, Path]) -> None:
    install_result = runner.invoke(app, ["install", "--handle", "alice"])
    assert install_result.exit_code == 0

    reuse_result = runner.invoke(
        app,
        [
            "record-reuse",
            "--doc-id",
            "workflows",
            "--task-id",
            "task-branch-push",
            "--retrieval-mode",
            "preloaded",
            "--evidence-mode",
            "explicit",
            "--reuse-outcome",
            "resolved",
            "--handle",
            "alice",
        ],
    )
    assert reuse_result.exit_code == 0

    result = runner.invoke(
        app,
        [
            "record-reuse-check",
            "--task-id",
            "task-branch-push",
            "--check-outcome",
            "wiki_used",
            "--agent-name",
            "codex",
            "--model",
            "gpt-5",
            "--notes",
            "The branch policy came from the AI wiki workflow doc.",
            "--checked-at",
            "2026-04-19T22:05:00+10:00",
            "--handle",
            "alice",
        ],
    )

    assert result.exit_code == 0
    check_log_path = repo_env["repo"] / "ai-wiki" / "metrics" / "task-checks" / "alice.jsonl"
    lines = check_log_path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1
    check = json.loads(lines[0])
    assert check == {
        "agent_name": "codex",
        "author_handle": "alice",
        "check_id": check["check_id"],
        "check_outcome": "wiki_used",
        "checked_at": "2026-04-19T22:05:00+10:00",
        "model": "gpt-5",
        "notes": "The branch policy came from the AI wiki workflow doc.",
        "schema_version": "reuse-v1",
        "task_id": "task-branch-push",
    }
    assert check["check_id"].startswith("chk_")

    task_stats = json.loads(
        (repo_env["repo"] / "ai-wiki" / "_toolkit" / "metrics" / "task-stats.json").read_text(
            encoding="utf-8"
        )
    )
    assert task_stats["tasks"] == {
        "task-branch-push": {
            "check_count": 1,
            "effective_reuse_count": 1,
            "estimated_seconds_saved": 0,
            "estimated_token_savings": 0,
            "last_check_outcome": "wiki_used",
            "last_checked_at": "2026-04-19T22:05:00+10:00",
            "lookup_reuse_count": 0,
            "preloaded_reuse_count": 1,
            "reuse_checked": True,
            "reused_docs": 1,
            "total_events": 1,
        }
    }
    assert task_stats["summary"] == {
        "checked_tasks": 1,
        "tasks_with_events_but_no_check": 0,
        "tasks_with_wiki_use": 1,
        "tasks_without_wiki_use": 0,
    }
