from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from ai_wiki_toolkit.cli import app

runner = CliRunner()


def test_route_records_trace_by_default(repo_env: dict[str, Path], monkeypatch) -> None:
    monkeypatch.setenv("CODEX_THREAD_ID", "thread-route-trace-test")
    monkeypatch.setenv("CODEX_STATE_DB", str(repo_env["repo"] / "missing-state.sqlite"))
    install_result = runner.invoke(app, ["install", "--handle", "alice"])
    assert install_result.exit_code == 0

    result = runner.invoke(
        app,
        [
            "route",
            "--task",
            "Update scaffold prompt routing without overwriting user-owned docs.",
            "--task-id",
            "task-route-trace",
            "--changed-path",
            "src/ai_wiki_toolkit/scaffold.py",
            "--format",
            "json",
        ],
    )

    assert result.exit_code == 0
    packet = json.loads(result.output)
    assert packet["task_id"] == "task-route-trace"
    trace_log = repo_env["repo"] / "ai-wiki" / "metrics" / "route-traces" / "alice.jsonl"
    lines = trace_log.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1
    trace = json.loads(lines[0])
    assert trace["schema_version"] == "route-trace-v1"
    assert trace["task_id"] == "task-route-trace"
    assert trace["task"] == "Update scaffold prompt routing without overwriting user-owned docs."
    assert trace["author_handle"] == "alice"
    assert "managed_prompt_block" in trace["guardrail_tags"]
    assert "user_owned_docs" in trace["guardrail_tags"]
    assert isinstance(trace["domain_tags"], list)
    assert trace["packet_words"] > 0
    assert trace["selected_doc_count"] == len(trace["selected_doc_ids"])
    assert "constraints" in trace["selected_doc_ids"]
    assert isinstance(trace["route_scores"], dict)
    assert isinstance(trace["base_route_scores"], dict)
    assert isinstance(trace["route_rerank_adjustments"], dict)
    assert isinstance(trace["route_multi_signal_adjustments"], dict)
    assert trace["reranker"]["mode"] == "deterministic_index_card"
    assert isinstance(trace["route_quality_adjustments"], dict)
    assert isinstance(trace["route_quality_signals"], dict)
    assert isinstance(trace["route_multi_signals"], dict)
    assert isinstance(trace["language_signals"], dict)
    assert isinstance(trace["intent_signals"], dict)
    assert isinstance(trace["route_mode"], dict)
    assert trace["route_mode"]["name"] == "code"
    assert trace["workflow_contract"] is None
    assert isinstance(trace["intent_buckets"], list)
    assert isinstance(trace["behavior_contract"], dict)
    assert isinstance(trace["selector"], dict)
    assert isinstance(trace["route_applies_when_adjustments"], dict)
    assert isinstance(trace["route_applies_when_signals"], dict)
    assert isinstance(trace["route_doc_slots"], dict)
    assert isinstance(trace["route_selection_reason_types"], dict)
    assert trace["changed_path_signal_source"] == "explicit"
    assert trace["changed_path_signal_used"] is True
    assert trace["source_session_id"] == "thread-route-trace-test"
    assert trace["source_session_env"] == "CODEX_THREAD_ID"
    assert trace["source_session_lookup"] == "env_only"


def test_route_can_skip_trace_recording(repo_env: dict[str, Path]) -> None:
    install_result = runner.invoke(app, ["install", "--handle", "alice"])
    assert install_result.exit_code == 0

    result = runner.invoke(
        app,
        [
            "route",
            "--task",
            "Push PR.",
            "--task-id",
            "task-no-trace",
            "--no-record-trace",
        ],
    )

    assert result.exit_code == 0
    trace_log = repo_env["repo"] / "ai-wiki" / "metrics" / "route-traces" / "alice.jsonl"
    assert not trace_log.exists()
