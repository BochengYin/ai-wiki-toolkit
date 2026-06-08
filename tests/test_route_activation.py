from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from ai_wiki_toolkit.cli import app
from ai_wiki_toolkit.route_activation import (
    evaluate_harness_activation_policy,
    evaluate_route_activation_policy,
    render_route_activation_report,
)

runner = CliRunner()


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def _install(repo_env: dict[str, Path]) -> Path:
    result = runner.invoke(app, ["install", "--handle", "alice"])
    assert result.exit_code == 0
    return repo_env["repo"] / "ai-wiki"


def _behavior_report(*, failed_check_count: int = 0, case_count: int = 4) -> dict[str, object]:
    failed = failed_check_count > 0
    return {
        "schema_version": "route-behavior-report-v1",
        "summary": {
            "case_count": case_count,
            "passed_case_count": case_count - min(failed_check_count, case_count),
            "failed_case_count": 1 if failed else 0,
            "check_count": case_count + failed_check_count,
            "failed_check_count": failed_check_count,
            "blocks_activation": failed,
            "failure_sources": ["codex_runtime_control"] if failed else [],
        },
        "activation": {
            "status": "blocked" if failed else "eligible_for_shadow_validation",
            "blocked": failed,
            "reason": "fixture",
        },
        "items": [],
    }


def _replay_report(
    *,
    replayed_trace_count: int = 57,
    precision_delta: float = 0.02,
    noise_delta: float = -0.02,
    selected_useful_delta: int = 2,
    missed_useful_delta: int = -1,
    precision_regression_items: int = 0,
    item_regression_summary: dict[str, object] | None = None,
) -> dict[str, object]:
    items = [
        {
            "task_id": f"trace-{index}",
            "comparison": {
                "route_precision_delta": -0.01 if index < precision_regression_items else 0.01,
                "route_noise_delta": 0.01 if index < precision_regression_items else -0.01,
            },
        }
        for index in range(max(precision_regression_items, 1))
    ]
    payload: dict[str, object] = {
        "schema_version": "impact-eval-route-replay-report-v1",
        "prompt_recovery": {
            "target_trace_count": replayed_trace_count,
            "recovered_trace_count": replayed_trace_count,
            "replayed_trace_count": replayed_trace_count,
            "unmatched_trace_count": 0,
            "confidence_counts": {"high": replayed_trace_count},
        },
        "baseline": {
            "summary": {
                "trace_count": replayed_trace_count,
                "selected_useful_doc_count": 100,
                "missed_useful_doc_count": 50,
            }
        },
        "replay": {
            "summary": {
                "trace_count": replayed_trace_count,
                "selected_useful_doc_count": 100 + selected_useful_delta,
                "missed_useful_doc_count": 50 + missed_useful_delta,
            }
        },
        "comparison": {
            "route_precision_delta": precision_delta,
            "route_noise_delta": noise_delta,
        },
        "items": items,
    }
    if item_regression_summary is not None:
        payload["item_regression_summary"] = item_regression_summary
    return payload


def _run_activation(
    repo_env: dict[str, Path],
    *,
    replay: dict[str, object],
    behavior: dict[str, object],
    write: bool = False,
) -> tuple[dict[str, object], Path]:
    repo_wiki = _install(repo_env)
    replay_path = repo_env["repo"] / "replay.json"
    behavior_path = repo_env["repo"] / "behavior.json"
    _write_json(replay_path, replay)
    _write_json(behavior_path, behavior)
    args = [
        "eval",
        "impact",
        "route-noise",
        "activation",
        "--replay-report",
        str(replay_path),
        "--behavior-report",
        str(behavior_path),
        "--handle",
        "alice",
        "--format",
        "json",
    ]
    if write:
        args.append("--write")
    result = runner.invoke(app, args)
    assert result.exit_code == 0, result.output
    return json.loads(result.output), repo_wiki


def test_route_activation_report_recommends_activation_when_all_gates_pass(
    repo_env: dict[str, Path],
) -> None:
    payload, repo_wiki = _run_activation(
        repo_env,
        replay=_replay_report(),
        behavior=_behavior_report(),
        write=True,
    )

    assert payload["schema_version"] == "route-activation-report-v1"
    assert payload["decision"]["status"] == "activate_recommended"
    assert payload["decision"]["activation_allowed"] is True
    assert payload["decision"]["blocks_activation"] is False
    assert payload["decision"]["layers"]["route_core"]["status"] == "activate_recommended"
    assert payload["decision"]["layers"]["agent_harness"]["status"] == "activate_recommended"
    assert all(item["status"] == "pass" for item in payload["decision"]["criteria"])
    assert "Route Activation Decision Report" in render_route_activation_report(payload)
    assert (
        repo_wiki
        / "_toolkit"
        / "reports"
        / "route-activation"
        / "alice"
        / "latest.json"
    ).exists()


def test_route_activation_report_blocks_on_behavior_failures(
    repo_env: dict[str, Path],
) -> None:
    payload, _repo_wiki = _run_activation(
        repo_env,
        replay=_replay_report(),
        behavior=_behavior_report(failed_check_count=1),
    )

    assert payload["decision"]["status"] == "blocked"
    assert payload["decision"]["activation_allowed"] is False
    assert payload["decision"]["layers"]["route_core"]["activation_allowed"] is True
    assert payload["decision"]["layers"]["agent_harness"]["activation_allowed"] is False
    failed_ids = {item["id"] for item in payload["decision"]["failed_criteria"]}
    assert "behavior_does_not_block_activation" in failed_ids


def test_route_activation_report_needs_more_evidence_when_replay_sample_is_small(
    repo_env: dict[str, Path],
) -> None:
    payload, _repo_wiki = _run_activation(
        repo_env,
        replay=_replay_report(replayed_trace_count=12),
        behavior=_behavior_report(),
    )

    assert payload["decision"]["status"] == "needs_more_evidence"
    assert payload["decision"]["activation_allowed"] is False
    assert payload["decision"]["layers"]["route_core"]["status"] == "needs_more_evidence"
    assert payload["decision"]["layers"]["agent_harness"]["activation_allowed"] is True
    failed_ids = {item["id"] for item in payload["decision"]["failed_criteria"]}
    assert failed_ids == {"replayed_trace_count"}


def test_route_activation_report_blocks_on_replay_metric_regression(
    repo_env: dict[str, Path],
) -> None:
    payload, _repo_wiki = _run_activation(
        repo_env,
        replay=_replay_report(
            precision_delta=0.01,
            noise_delta=-0.01,
            selected_useful_delta=-1,
            missed_useful_delta=1,
            precision_regression_items=1,
        ),
        behavior=_behavior_report(),
    )

    assert payload["decision"]["status"] == "blocked"
    assert payload["decision"]["layers"]["route_core"]["status"] == "blocked"
    assert payload["decision"]["layers"]["agent_harness"]["activation_allowed"] is True
    failed_ids = {item["id"] for item in payload["decision"]["failed_criteria"]}
    assert "selected_useful_doc_delta" in failed_ids
    assert "missed_useful_doc_delta" in failed_ids
    assert "precision_regression_items" in failed_ids


def test_route_activation_report_uses_full_item_regression_summary(
    repo_env: dict[str, Path],
) -> None:
    payload, _repo_wiki = _run_activation(
        repo_env,
        replay=_replay_report(
            item_regression_summary={
                "compared_item_count": 57,
                "precision_regression_count": 2,
                "noise_regression_count": 2,
            }
        ),
        behavior=_behavior_report(),
    )

    assert payload["decision"]["status"] == "blocked"
    metrics = payload["decision"]["metrics"]
    assert metrics["precision_regression_items"] == 2
    assert metrics["noise_regression_items"] == 2
    failed_ids = {item["id"] for item in payload["decision"]["failed_criteria"]}
    assert "precision_regression_items" in failed_ids
    assert "noise_regression_items" in failed_ids


def test_route_core_activation_policy_ignores_harness_behavior() -> None:
    policy = evaluate_route_activation_policy(replay_report=_replay_report())

    assert policy["status"] == "activate_recommended"
    assert "behavior_case_count" not in policy["metrics"]
    assert {item["category"] for item in policy["criteria"]} == {"route_core"}


def test_harness_activation_policy_ignores_route_replay() -> None:
    policy = evaluate_harness_activation_policy(
        behavior_report=_behavior_report(failed_check_count=1)
    )

    assert policy["status"] == "blocked"
    assert "replayed_trace_count" not in policy["metrics"]
    assert {item["category"] for item in policy["criteria"]} == {"agent_harness"}
