from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from ai_wiki_toolkit.cli import app

runner = CliRunner()


def test_route_records_trace_by_default(repo_env: dict[str, Path]) -> None:
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
    assert trace["author_handle"] == "alice"
    assert trace["packet_words"] > 0
    assert trace["selected_doc_count"] == len(trace["selected_doc_ids"])
    assert "constraints" in trace["selected_doc_ids"]
    assert isinstance(trace["route_scores"], dict)


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
