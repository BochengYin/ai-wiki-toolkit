from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from ai_wiki_toolkit.cli import app

runner = CliRunner()


def _write_jsonl(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )


def _write_doc(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def test_report_usefulness_writes_referenced_files_and_time_impact(
    repo_env: dict[str, Path],
) -> None:
    install_result = runner.invoke(app, ["install", "--handle", "alice"])
    assert install_result.exit_code == 0

    repo_wiki = repo_env["repo"] / "ai-wiki"
    _write_doc(
        repo_wiki / "problems" / "release-check.md",
        "---\n"
        'title: "Release Check"\n'
        "---\n"
        "# Release Check\n",
    )
    _write_jsonl(
        repo_wiki / "metrics" / "reuse-events" / "alice.jsonl",
        [
            {
                "author_handle": "alice",
                "doc_id": "problems/release-check",
                "doc_kind": "problem",
                "estimated_savings": {"saved_seconds": 120, "saved_tokens": 2500},
                "event_id": "evt_1",
                "evidence_mode": "explicit",
                "observed_at": "2026-04-20T10:00:00+00:00",
                "retrieval_mode": "lookup",
                "reuse_effects": ["avoided_retry"],
                "reuse_outcome": "resolved",
                "schema_version": "reuse-v1",
                "task_id": "task-1",
            },
            {
                "author_handle": "alice",
                "doc_id": "problems/release-check",
                "doc_kind": "problem",
                "event_id": "evt_2",
                "evidence_mode": "explicit",
                "observed_at": "2026-04-21T10:00:00+00:00",
                "retrieval_mode": "preloaded",
                "reuse_outcome": "partial",
                "schema_version": "reuse-v1",
                "task_id": "task-2",
            },
            {
                "author_handle": "bob",
                "doc_id": "problems/release-check",
                "doc_kind": "problem",
                "estimated_savings": {"saved_seconds": 999, "saved_tokens": 999},
                "event_id": "evt_bob",
                "evidence_mode": "explicit",
                "observed_at": "2026-04-21T11:00:00+00:00",
                "retrieval_mode": "lookup",
                "reuse_outcome": "resolved",
                "schema_version": "reuse-v1",
                "task_id": "task-bob",
            },
        ],
    )
    _write_jsonl(
        repo_wiki / "metrics" / "task-checks" / "alice.jsonl",
        [
            {
                "author_handle": "alice",
                "check_id": "check_1",
                "check_outcome": "wiki_used",
                "checked_at": "2026-04-21T12:00:00+00:00",
                "schema_version": "reuse-v1",
                "task_id": "task-1",
            }
        ],
    )

    result = runner.invoke(app, ["report", "usefulness", "--handle", "alice", "--format", "json"])

    assert result.exit_code == 0
    report = json.loads(result.output)
    assert report["schema_version"] == "usefulness-report-v1"
    assert report["summary"]["reuse_events"] == 2
    assert report["summary"]["task_checks"] == 1
    assert report["summary"]["documents_referenced"] == 1
    assert report["summary"]["total_estimated_seconds_saved"] == 120
    assert report["timing"]["first_trial_error_seconds"] is None
    assert report["timing"]["current_elapsed_seconds"] is None
    assert report["timing"]["remaining_seconds"] is None
    assert report["referenced_documents"][0]["path"] == "ai-wiki/problems/release-check.md"

    markdown_path = repo_wiki / "_toolkit" / "reports" / "usefulness" / "alice" / "latest.md"
    json_path = repo_wiki / "_toolkit" / "reports" / "usefulness" / "alice" / "latest.json"
    assert markdown_path.exists()
    assert json.loads(json_path.read_text(encoding="utf-8"))["summary"][
        "total_estimated_seconds_saved"
    ] == 120
    markdown = markdown_path.read_text(encoding="utf-8")
    assert "`ai-wiki/problems/release-check.md` - Release Check" in markdown
    assert "First trial/error time: unknown" in markdown


def test_report_usefulness_no_write_requires_initialized_repo_wiki(
    repo_env: dict[str, Path],
) -> None:
    result = runner.invoke(app, ["report", "usefulness", "--handle", "alice", "--no-write"])

    assert result.exit_code == 1
    assert "Repo AI wiki is not initialized. Run `aiwiki-toolkit install` first." in result.output
