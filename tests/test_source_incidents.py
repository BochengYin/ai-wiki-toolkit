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


def _write_doc(path: Path, text: str = "# Retry Loop\n") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _write_session(
    path: Path,
    *,
    session_id: str,
    cwd: Path,
    writeback_path: str,
    final_duration_ms: int = 60000,
) -> None:
    rows: list[dict[str, object]] = [
        {
            "timestamp": "2026-05-24T00:00:00Z",
            "type": "session_meta",
            "payload": {"id": session_id, "cwd": cwd.as_posix()},
        },
        {
            "timestamp": "2026-05-24T00:00:10Z",
            "type": "event_msg",
            "payload": {
                "type": "task_complete",
                "turn_id": "turn-unrelated",
                "duration_ms": 111000,
            },
        },
        {
            "timestamp": "2026-05-24T00:00:30Z",
            "type": "event_msg",
            "payload": {
                "type": "user_message",
                "message": "Fix the retry loop and write back the memory.",
            },
        },
        {
            "timestamp": "2026-05-24T00:01:00Z",
            "type": "event_msg",
            "payload": {
                "type": "task_complete",
                "turn_id": "turn-before",
                "duration_ms": 120000,
            },
        },
        {
            "timestamp": "2026-05-24T00:02:00Z",
            "type": "event_msg",
            "payload": {
                "type": "turn_aborted",
                "turn_id": "turn-failed",
                "duration_ms": 30000,
            },
        },
        {
            "timestamp": "2026-05-24T00:03:00Z",
            "type": "response_item",
            "payload": {
                "type": "function_call_output",
                "output": f"AI Wiki Write-Back Path: {writeback_path}",
            },
        },
        {
            "timestamp": "2026-05-24T00:04:00Z",
            "type": "event_msg",
            "payload": {
                "type": "task_complete",
                "turn_id": "turn-writeback",
                "duration_ms": final_duration_ms,
                "last_agent_message": (
                    "Done.\n\n"
                    "AI Wiki Write-Back: draft recorded\n"
                    f"AI Wiki Write-Back Path: {writeback_path}\n"
                ),
            },
        },
        {
            "timestamp": "2026-05-24T00:05:00Z",
            "type": "event_msg",
            "payload": {
                "type": "task_complete",
                "turn_id": "turn-after",
                "duration_ms": 999000,
            },
        },
    ]
    _write_jsonl(path, rows)


def _write_simple_writeback_session(
    path: Path,
    *,
    session_id: str,
    cwd: Path,
    doc_path: str,
    task_start_timestamp: str,
    cutoff_timestamp: str,
    first_duration_ms: int,
    final_duration_ms: int,
) -> None:
    rows: list[dict[str, object]] = [
        {
            "timestamp": task_start_timestamp,
            "type": "session_meta",
            "payload": {"id": session_id, "cwd": cwd.as_posix()},
        },
        {
            "timestamp": task_start_timestamp,
            "type": "event_msg",
            "payload": {"type": "user_message", "message": "Write back a memory."},
        },
        {
            "timestamp": task_start_timestamp,
            "type": "event_msg",
            "payload": {
                "type": "task_complete",
                "turn_id": f"{session_id}-before",
                "duration_ms": first_duration_ms,
            },
        },
        {
            "timestamp": cutoff_timestamp,
            "type": "event_msg",
            "payload": {
                "type": "task_complete",
                "turn_id": f"{session_id}-writeback",
                "duration_ms": final_duration_ms,
                "last_agent_message": (
                    "Done.\n\n"
                    "AI Wiki Write-Back: draft recorded\n"
                    f"AI Wiki Write-Back Path: {doc_path}\n"
                ),
            },
        },
    ]
    _write_jsonl(path, rows)


def test_source_incident_backfill_writeback_counts_first_writeback_cutoff(
    repo_env: dict[str, Path],
    tmp_path: Path,
) -> None:
    install_result = runner.invoke(app, ["install", "--handle", "alice"])
    assert install_result.exit_code == 0

    repo = repo_env["repo"]
    repo_wiki = repo / "ai-wiki"
    writeback_path = "ai-wiki/problems/retry-loop.md"
    _write_doc(repo_wiki / "problems" / "retry-loop.md")

    sessions_root = tmp_path / "codex-sessions"
    _write_session(
        sessions_root / "2026" / "05" / "24" / "rollout-current.jsonl",
        session_id="source-session",
        cwd=repo,
        writeback_path=writeback_path,
    )
    _write_session(
        sessions_root / "2026" / "05" / "24" / "rollout-other-repo.jsonl",
        session_id="other-session",
        cwd=tmp_path / "other-repo",
        writeback_path=writeback_path,
        final_duration_ms=500000,
    )

    result = runner.invoke(
        app,
        [
            "source-incident",
            "backfill-writeback",
            "--writeback-path",
            writeback_path,
            "--sessions-root",
            str(sessions_root),
            "--handle",
            "alice",
            "--apply",
            "--format",
            "json",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["candidate_count"] == 1
    assert payload["written_count"] == 1
    candidate = payload["candidates"][0]
    assert candidate["doc_id"] == "problems/retry-loop"
    assert candidate["duration_ms"] == 210000
    assert candidate["active_seconds"] == 210
    assert candidate["task_complete_count"] == 2
    assert candidate["turn_aborted_count"] == 1
    assert candidate["source_task_start_timestamp"] == "2026-05-24T00:00:30Z"
    assert candidate["cutoff_turn_id"] == "turn-writeback"
    assert candidate["policy"] == "first_writeback_user_task_inclusive"
    assert candidate["status"] == "written"

    ledger_path = repo_wiki / "metrics" / "source-incidents" / "alice.jsonl"
    ledger_events = [json.loads(line) for line in ledger_path.read_text(encoding="utf-8").splitlines()]
    assert len(ledger_events) == 1
    assert ledger_events[0]["timing_source"] == "codex_writeback_footer"
    assert ledger_events[0]["session_id"] == "source-session"

    duplicate = runner.invoke(
        app,
        [
            "source-incident",
            "backfill-writeback",
            "--writeback-path",
            writeback_path,
            "--sessions-root",
            str(sessions_root),
            "--handle",
            "alice",
            "--apply",
            "--format",
            "json",
        ],
    )

    assert duplicate.exit_code == 0
    duplicate_payload = json.loads(duplicate.output)
    assert duplicate_payload["written_count"] == 0
    assert duplicate_payload["skipped_existing_count"] == 1
    assert len(ledger_path.read_text(encoding="utf-8").splitlines()) == 1


def test_source_incident_capture_post_turn_uses_latest_repo_writeback(
    repo_env: dict[str, Path],
    tmp_path: Path,
) -> None:
    install_result = runner.invoke(app, ["install", "--handle", "alice"])
    assert install_result.exit_code == 0

    repo = repo_env["repo"]
    repo_wiki = repo / "ai-wiki"
    _write_doc(repo_wiki / "problems" / "older.md", "# Older\n")
    _write_doc(repo_wiki / "problems" / "newer.md", "# Newer\n")

    sessions_root = tmp_path / "codex-sessions"
    _write_simple_writeback_session(
        sessions_root / "2026" / "05" / "24" / "rollout-older.jsonl",
        session_id="older-session",
        cwd=repo,
        doc_path="ai-wiki/problems/older.md",
        task_start_timestamp="2026-05-24T00:00:00Z",
        cutoff_timestamp="2026-05-24T00:01:00Z",
        first_duration_ms=10000,
        final_duration_ms=20000,
    )
    _write_simple_writeback_session(
        sessions_root / "2026" / "05" / "24" / "rollout-newer.jsonl",
        session_id="newer-session",
        cwd=repo,
        doc_path="ai-wiki/problems/newer.md",
        task_start_timestamp="2026-05-24T00:02:00Z",
        cutoff_timestamp="2026-05-24T00:03:00Z",
        first_duration_ms=40000,
        final_duration_ms=50000,
    )
    _write_simple_writeback_session(
        sessions_root / "2026" / "05" / "24" / "rollout-other-repo.jsonl",
        session_id="other-session",
        cwd=tmp_path / "other-repo",
        doc_path="ai-wiki/problems/older.md",
        task_start_timestamp="2026-05-24T00:04:00Z",
        cutoff_timestamp="2026-05-24T00:05:00Z",
        first_duration_ms=70000,
        final_duration_ms=80000,
    )

    result = runner.invoke(
        app,
        [
            "source-incident",
            "capture-post-turn",
            "--sessions-root",
            str(sessions_root),
            "--handle",
            "alice",
            "--apply",
            "--format",
            "json",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["candidate_count"] == 1
    assert payload["written_count"] == 1
    candidate = payload["candidates"][0]
    assert candidate["doc_id"] == "problems/newer"
    assert candidate["duration_ms"] == 90000
    assert candidate["session_id"] == "newer-session"
    assert candidate["source_kind"] == "writeback_post_turn_capture"
    assert candidate["status"] == "written"

    duplicate = runner.invoke(
        app,
        [
            "source-incident",
            "capture-post-turn",
            "--sessions-root",
            str(sessions_root),
            "--handle",
            "alice",
            "--apply",
            "--format",
            "json",
        ],
    )

    assert duplicate.exit_code == 0
    duplicate_payload = json.loads(duplicate.output)
    assert duplicate_payload["written_count"] == 0
    assert duplicate_payload["skipped_existing_count"] == 1


def test_source_incident_capture_post_turn_can_scope_to_session_id(
    repo_env: dict[str, Path],
    tmp_path: Path,
) -> None:
    install_result = runner.invoke(app, ["install", "--handle", "alice"])
    assert install_result.exit_code == 0

    repo = repo_env["repo"]
    repo_wiki = repo / "ai-wiki"
    _write_doc(repo_wiki / "problems" / "older.md", "# Older\n")
    _write_doc(repo_wiki / "problems" / "newer.md", "# Newer\n")

    sessions_root = tmp_path / "codex-sessions"
    _write_simple_writeback_session(
        sessions_root / "2026" / "05" / "24" / "rollout-older.jsonl",
        session_id="older-session",
        cwd=repo,
        doc_path="ai-wiki/problems/older.md",
        task_start_timestamp="2026-05-24T00:00:00Z",
        cutoff_timestamp="2026-05-24T00:01:00Z",
        first_duration_ms=10000,
        final_duration_ms=20000,
    )
    _write_simple_writeback_session(
        sessions_root / "2026" / "05" / "24" / "rollout-newer.jsonl",
        session_id="newer-session",
        cwd=repo,
        doc_path="ai-wiki/problems/newer.md",
        task_start_timestamp="2026-05-24T00:02:00Z",
        cutoff_timestamp="2026-05-24T00:03:00Z",
        first_duration_ms=40000,
        final_duration_ms=50000,
    )

    result = runner.invoke(
        app,
        [
            "source-incident",
            "capture-post-turn",
            "--session-id",
            "older-session",
            "--sessions-root",
            str(sessions_root),
            "--handle",
            "alice",
            "--apply",
            "--format",
            "json",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["candidate_count"] == 1
    assert payload["written_count"] == 1
    assert payload["candidates"][0]["doc_id"] == "problems/older"
    assert payload["candidates"][0]["duration_ms"] == 30000


def test_diagnose_trial_error_reads_source_incident_backfill_ledger(
    repo_env: dict[str, Path],
) -> None:
    install_result = runner.invoke(app, ["install", "--handle", "alice"])
    assert install_result.exit_code == 0

    repo_wiki = repo_env["repo"] / "ai-wiki"
    _write_doc(repo_wiki / "problems" / "retry-loop.md")
    _write_jsonl(
        repo_wiki / "metrics" / "reuse-events" / "alice.jsonl",
        [
            {
                "author_handle": "alice",
                "doc_id": "problems/retry-loop",
                "doc_kind": "problem",
                "event_id": "evt_retry",
                "evidence_mode": "explicit",
                "observed_at": "2026-05-24T01:00:00+00:00",
                "retrieval_mode": "lookup",
                "reuse_effects": ["avoided_retry"],
                "reuse_outcome": "resolved",
                "schema_version": "reuse-v1",
                "task_id": "task-avoided-retry",
            }
        ],
    )
    _write_jsonl(
        repo_wiki / "metrics" / "source-incidents" / "alice.jsonl",
        [
            {
                "schema_version": "source-incident-v1",
                "evidence_id": "srcinc_retry",
                "recorded_at": "2026-05-24T02:00:00+00:00",
                "author_handle": "alice",
                "doc_id": "problems/retry-loop",
                "writeback_path": "ai-wiki/problems/retry-loop.md",
                "source_kind": "writeback_backfill",
                "timing_label": "source active-turn estimate",
                "timing_source": "codex_writeback_footer",
                "policy": "first_writeback_user_task_inclusive",
                "active_seconds": 210,
                "duration_ms": 210000,
                "included_events": ["task_complete", "turn_aborted"],
                "session_id": "source-session",
                "session_file": "rollout-current.jsonl",
                "session_relpath": "2026/05/24/rollout-current.jsonl",
                "task_complete_count": 2,
                "turn_aborted_count": 1,
            }
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
    assert report["summary"]["source_incident_events"] == 1
    assert section["summary"]["replay_candidates_with_source_incident_timing"] == 1
    timing = section["replay_candidates"][0]["source_incident_timing"]
    assert timing["status"] == "measured"
    assert timing["active_seconds"] == 210
    assert timing["sources"][0]["source_session_id"] == "source-session"
    assert timing["sources"][0]["timing_source"] == "codex_writeback_footer"
