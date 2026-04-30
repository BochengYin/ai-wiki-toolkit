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


def test_diagnose_memory_writes_managed_reports(repo_env: dict[str, Path]) -> None:
    install_result = runner.invoke(app, ["install", "--handle", "alice"])
    assert install_result.exit_code == 0

    repo_wiki = repo_env["repo"] / "ai-wiki"
    _write_doc(repo_wiki / "review-patterns" / "high-roi.md", "# High ROI\n")
    _write_doc(repo_wiki / "review-patterns" / "noisy.md", "# Noisy\n")
    _write_doc(repo_wiki / "review-patterns" / "conflict.md", "# Conflict\n")
    _write_doc(
        repo_wiki / "people" / "alice" / "drafts" / "old-guidance.md",
        "---\n"
        'title: "Old Guidance"\n'
        'status: "superseded"\n'
        "---\n"
        "# Old Guidance\n",
    )

    _write_jsonl(
        repo_wiki / "metrics" / "reuse-events" / "alice.jsonl",
        [
            {
                "author_handle": "alice",
                "doc_id": "review-patterns/high-roi",
                "doc_kind": "review_pattern",
                "estimated_savings": {"saved_seconds": 120, "saved_tokens": 2500},
                "event_id": "evt_1",
                "evidence_mode": "explicit",
                "observed_at": "2026-04-20T10:00:00+00:00",
                "retrieval_mode": "lookup",
                "reuse_effects": ["avoided_retry"],
                "reuse_outcome": "resolved",
                "schema_version": "reuse-v1",
                "task_id": "task-high-1",
            },
            {
                "author_handle": "alice",
                "doc_id": "review-patterns/high-roi",
                "doc_kind": "review_pattern",
                "event_id": "evt_2",
                "evidence_mode": "explicit",
                "observed_at": "2026-04-21T10:00:00+00:00",
                "retrieval_mode": "preloaded",
                "reuse_outcome": "resolved",
                "schema_version": "reuse-v1",
                "task_id": "task-high-2",
            },
            {
                "author_handle": "alice",
                "doc_id": "review-patterns/noisy",
                "doc_kind": "review_pattern",
                "event_id": "evt_3",
                "evidence_mode": "explicit",
                "observed_at": "2026-04-21T11:00:00+00:00",
                "retrieval_mode": "lookup",
                "reuse_outcome": "not_helpful",
                "schema_version": "reuse-v1",
                "task_id": "task-noisy",
            },
            {
                "author_handle": "alice",
                "doc_id": "review-patterns/noisy",
                "doc_kind": "review_pattern",
                "event_id": "evt_4",
                "evidence_mode": "explicit",
                "observed_at": "2026-04-21T12:00:00+00:00",
                "retrieval_mode": "lookup",
                "reuse_outcome": "not_helpful",
                "schema_version": "reuse-v1",
                "task_id": "task-noisy",
            },
            {
                "author_handle": "alice",
                "doc_id": "people/alice/drafts/old-guidance",
                "doc_kind": "draft",
                "event_id": "evt_5",
                "evidence_mode": "explicit",
                "observed_at": "2026-04-22T10:00:00+00:00",
                "retrieval_mode": "lookup",
                "reuse_outcome": "resolved",
                "schema_version": "reuse-v1",
                "task_id": "task-stale",
            },
            {
                "author_handle": "alice",
                "doc_id": "review-patterns/conflict",
                "doc_kind": "review_pattern",
                "event_id": "evt_6",
                "evidence_mode": "explicit",
                "notes": "This conflicts with another convention and should have used the newer memory.",
                "observed_at": "2026-04-23T10:00:00+00:00",
                "retrieval_mode": "lookup",
                "reuse_outcome": "partial",
                "schema_version": "reuse-v1",
                "task_id": "task-conflict",
            },
            {
                "author_handle": "alice",
                "doc_id": "review-patterns/high-roi",
                "doc_kind": "review_pattern",
                "event_id": "evt_7",
                "evidence_mode": "explicit",
                "observed_at": "2026-04-24T10:00:00+00:00",
                "retrieval_mode": "lookup",
                "reuse_outcome": "resolved",
                "schema_version": "reuse-v1",
                "task_id": "task-unchecked",
            },
        ],
    )
    _write_jsonl(
        repo_wiki / "metrics" / "task-checks" / "alice.jsonl",
        [
            {
                "author_handle": "alice",
                "check_id": "chk_1",
                "check_outcome": "wiki_used",
                "checked_at": "2026-04-21T13:00:00+00:00",
                "schema_version": "reuse-v1",
                "task_id": "task-noisy",
            },
            {
                "author_handle": "alice",
                "check_id": "chk_2",
                "check_outcome": "no_wiki_use",
                "checked_at": "2026-04-23T13:00:00+00:00",
                "schema_version": "reuse-v1",
                "task_id": "task-conflict",
            },
        ],
    )

    result = runner.invoke(
        app,
        [
            "diagnose",
            "memory",
            "--handle",
            "alice",
            "--since",
            "2026-04-01T00:00:00+00:00",
        ],
    )

    assert result.exit_code == 0
    assert "# AI Wiki Memory Diagnostics" in result.output
    assert "## High-ROI Memory" in result.output
    assert "`review-patterns/high-roi`" in result.output
    assert "## Noisy Memory" in result.output
    assert "`review-patterns/noisy`" in result.output
    assert "## Stale Memory" in result.output
    assert "`people/alice/drafts/old-guidance` - Old Guidance" in result.output
    assert "## Conflicting Memory" in result.output
    assert "`review-patterns/conflict`" in result.output
    assert "## Missed Memory Signals" in result.output
    assert "## Coverage Gaps" in result.output
    assert "`task-conflict`" in result.output
    assert "`task-unchecked`" in result.output

    markdown_path = repo_wiki / "_toolkit" / "diagnostics" / "memory-report.md"
    json_path = repo_wiki / "_toolkit" / "diagnostics" / "memory-report.json"
    assert markdown_path.read_text(encoding="utf-8") == result.output
    report = json.loads(json_path.read_text(encoding="utf-8"))
    assert report["schema_version"] == "diagnostics-v1"
    assert report["summary"]["reuse_events"] == 7
    assert report["summary"]["task_checks"] == 2
    assert report["high_roi_memory"][0]["doc_id"] == "review-patterns/high-roi"
    assert report["noisy_memory"][0]["doc_id"] == "review-patterns/noisy"
    assert report["stale_memory"][0]["doc_id"] == "people/alice/drafts/old-guidance"
    assert report["conflicting_memory"][0]["doc_id"] == "review-patterns/conflict"


def test_diagnose_memory_json_no_write_filters_handle_and_since(
    repo_env: dict[str, Path],
) -> None:
    install_result = runner.invoke(app, ["install", "--handle", "alice"])
    assert install_result.exit_code == 0

    repo_wiki = repo_env["repo"] / "ai-wiki"
    _write_doc(repo_wiki / "workflows.md", "# Workflows\n")
    _write_jsonl(
        repo_wiki / "metrics" / "reuse-events" / "alice.jsonl",
        [
            {
                "author_handle": "alice",
                "doc_id": "workflows",
                "doc_kind": "workflows",
                "event_id": "evt_old",
                "evidence_mode": "explicit",
                "observed_at": "2026-04-01T00:00:00+00:00",
                "retrieval_mode": "lookup",
                "reuse_outcome": "resolved",
                "schema_version": "reuse-v1",
                "task_id": "old-task",
            },
            {
                "author_handle": "alice",
                "doc_id": "workflows",
                "doc_kind": "workflows",
                "event_id": "evt_new",
                "evidence_mode": "explicit",
                "observed_at": "2026-04-20T00:00:00+00:00",
                "retrieval_mode": "lookup",
                "reuse_outcome": "resolved",
                "schema_version": "reuse-v1",
                "task_id": "new-task",
            },
        ],
    )
    _write_jsonl(
        repo_wiki / "metrics" / "reuse-events" / "bob.jsonl",
        [
            {
                "author_handle": "bob",
                "doc_id": "workflows",
                "doc_kind": "workflows",
                "event_id": "evt_bob",
                "evidence_mode": "explicit",
                "observed_at": "2026-04-20T00:00:00+00:00",
                "retrieval_mode": "lookup",
                "reuse_outcome": "resolved",
                "schema_version": "reuse-v1",
                "task_id": "bob-task",
            }
        ],
    )

    result = runner.invoke(
        app,
        [
            "diagnose",
            "memory",
            "--format",
            "json",
            "--no-write",
            "--handle",
            "alice",
            "--since",
            "2026-04-15T00:00:00+00:00",
            "--high-roi-min-events",
            "1",
        ],
    )

    assert result.exit_code == 0
    report = json.loads(result.output)
    assert report["filters"]["handle"] == "alice"
    assert report["summary"]["reuse_events"] == 1
    assert report["high_roi_memory"][0]["tasks"] == ["new-task"]
    assert not (repo_wiki / "_toolkit" / "diagnostics" / "memory-report.md").exists()
    assert not (repo_wiki / "_toolkit" / "diagnostics" / "memory-report.json").exists()


def test_diagnose_memory_trial_error_focus_reports_existing_evidence(
    repo_env: dict[str, Path],
) -> None:
    install_result = runner.invoke(app, ["install", "--handle", "alice"])
    assert install_result.exit_code == 0

    repo_wiki = repo_env["repo"] / "ai-wiki"
    _write_doc(repo_wiki / "problems" / "retry-loop.md", "# Retry Loop\n")
    _write_doc(repo_wiki / "conventions" / "plain-style.md", "# Plain Style\n")
    _write_jsonl(
        repo_wiki / "metrics" / "reuse-events" / "alice.jsonl",
        [
            {
                "author_handle": "alice",
                "doc_id": "problems/retry-loop",
                "doc_kind": "problem",
                "event_id": "evt_retry",
                "evidence_mode": "explicit",
                "notes": "Used existing memory to avoid repeating the failed attempt.",
                "observed_at": "2026-04-20T10:00:00+00:00",
                "retrieval_mode": "lookup",
                "reuse_effects": ["avoided_retry", "blocked_wrong_path"],
                "reuse_outcome": "resolved",
                "schema_version": "reuse-v1",
                "task_id": "task-avoided-retry",
            },
            {
                "author_handle": "alice",
                "doc_id": "conventions/plain-style",
                "doc_kind": "convention",
                "event_id": "evt_unproven",
                "evidence_mode": "explicit",
                "observed_at": "2026-04-21T10:00:00+00:00",
                "retrieval_mode": "lookup",
                "reuse_effects": ["reused_convention"],
                "reuse_outcome": "resolved",
                "schema_version": "reuse-v1",
                "task_id": "task-used-wiki",
            },
        ],
    )
    _write_jsonl(
        repo_wiki / "metrics" / "task-checks" / "alice.jsonl",
        [
            {
                "author_handle": "alice",
                "check_id": "chk_retry",
                "check_outcome": "wiki_used",
                "checked_at": "2026-04-20T11:00:00+00:00",
                "schema_version": "reuse-v1",
                "task_id": "task-avoided-retry",
            },
            {
                "author_handle": "alice",
                "check_id": "chk_used",
                "check_outcome": "wiki_used",
                "checked_at": "2026-04-21T11:00:00+00:00",
                "schema_version": "reuse-v1",
                "task_id": "task-used-wiki",
            },
            {
                "author_handle": "alice",
                "check_id": "chk_missed",
                "check_outcome": "no_wiki_use",
                "checked_at": "2026-04-22T11:00:00+00:00",
                "notes": "Missed relevant memory caused a repeated error and extra iteration.",
                "schema_version": "reuse-v1",
                "task_id": "task-missed-memory",
            },
        ],
    )

    result = runner.invoke(
        app,
        [
            "diagnose",
            "memory",
            "--handle",
            "alice",
            "--focus",
            "trial-error",
            "--format",
            "json",
        ],
    )

    assert result.exit_code == 0
    report = json.loads(result.output)
    section = report["trial_error_reduction"]
    assert report["filters"]["focus"] == "trial-error"
    assert section["summary"]["tasks_with_trial_error_effect"] == 1
    assert section["positive_evidence"][0]["doc_id"] == "problems/retry-loop"
    assert section["positive_evidence"][0]["trial_error_effects"] == {
        "avoided_retry": 1,
        "blocked_wrong_path": 1,
    }
    assert section["replay_candidates"][0]["doc_id"] == "problems/retry-loop"
    assert section["unproven_wiki_use"][0]["task_id"] == "task-used-wiki"
    assert section["missed_or_repeated_issue_signals"][0]["task_id"] == "task-missed-memory"

    markdown_path = repo_wiki / "_toolkit" / "diagnostics" / "trial-error-report.md"
    json_path = repo_wiki / "_toolkit" / "diagnostics" / "trial-error-report.json"
    assert markdown_path.exists()
    assert json_path.exists()
    assert "AI Wiki Trial/Error Reduction Diagnostics" in markdown_path.read_text(
        encoding="utf-8"
    )


def test_diagnose_memory_requires_initialized_repo_wiki(repo_env: dict[str, Path]) -> None:
    result = runner.invoke(app, ["diagnose", "memory"])

    assert result.exit_code == 1
    assert "Run `aiwiki-toolkit install` first." in result.output
