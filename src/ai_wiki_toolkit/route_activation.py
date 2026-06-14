"""Activation reports for route-core retrieval and harness behavior evidence."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import json
from pathlib import Path
from typing import Any, Mapping

from ai_wiki_toolkit.paths import build_paths, resolve_user_handle, slugify

ROUTE_ACTIVATION_REPORT_SCHEMA_VERSION = "route-activation-report-v1"


@dataclass(frozen=True)
class RouteActivationReportResult:
    """Rendered activation report and optional managed output paths."""

    report: dict[str, Any]
    markdown: str
    json_text: str
    markdown_path: Path | None = None
    json_path: Path | None = None


def _timestamp() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Expected JSON object in {path}.")
    return payload


def _number(value: object) -> float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int | float):
        return float(value)
    return None


def _int(value: object) -> int:
    if isinstance(value, bool):
        return 0
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    return 0


def _summary(report: Mapping[str, Any], section: str) -> Mapping[str, Any]:
    value = report.get(section)
    if not isinstance(value, dict):
        return {}
    summary = value.get("summary")
    return summary if isinstance(summary, dict) else {}


def _comparison(report: Mapping[str, Any]) -> Mapping[str, Any]:
    value = report.get("comparison")
    return value if isinstance(value, dict) else {}


def _prompt_recovery(report: Mapping[str, Any]) -> Mapping[str, Any]:
    value = report.get("prompt_recovery")
    return value if isinstance(value, dict) else {}


def _replay_item_regression_counts(report: Mapping[str, Any]) -> dict[str, int]:
    summary = report.get("item_regression_summary")
    if isinstance(summary, dict):
        return {
            "precision_regressions": _int(summary.get("precision_regression_count")),
            "noise_regressions": _int(summary.get("noise_regression_count")),
        }
    precision_regressions = 0
    noise_regressions = 0
    items = report.get("items")
    if not isinstance(items, list):
        return {"precision_regressions": 0, "noise_regressions": 0}
    for item in items:
        if not isinstance(item, dict):
            continue
        comparison = item.get("comparison")
        if not isinstance(comparison, dict):
            continue
        precision_delta = _number(comparison.get("route_precision_delta"))
        if precision_delta is not None and precision_delta < 0:
            precision_regressions += 1
        noise_delta = _number(comparison.get("route_noise_delta"))
        if noise_delta is not None and noise_delta > 0:
            noise_regressions += 1
    return {
        "precision_regressions": precision_regressions,
        "noise_regressions": noise_regressions,
    }


def _criterion(
    criterion_id: str,
    *,
    passed: bool,
    observed: object,
    threshold: object,
    reason: str,
    category: str,
) -> dict[str, Any]:
    return {
        "id": criterion_id,
        "category": category,
        "status": "pass" if passed else "fail",
        "observed": observed,
        "threshold": threshold,
        "reason": reason,
        "blocks_activation": not passed,
    }


def _delta(
    after: Mapping[str, Any],
    before: Mapping[str, Any],
    field: str,
) -> int:
    return _int(after.get(field)) - _int(before.get(field))


def _route_replay_metrics(replay_report: Mapping[str, Any]) -> dict[str, Any]:
    replay_baseline = _summary(replay_report, "baseline")
    replay_summary = _summary(replay_report, "replay")
    comparison = _comparison(replay_report)
    recovery = _prompt_recovery(replay_report)
    item_regressions = _replay_item_regression_counts(replay_report)

    return {
        "replayed_trace_count": _int(recovery.get("replayed_trace_count")),
        "route_precision_delta": _number(comparison.get("route_precision_delta")),
        "route_noise_delta": _number(comparison.get("route_noise_delta")),
        "selected_useful_doc_delta": _delta(
            replay_summary,
            replay_baseline,
            "selected_useful_doc_count",
        ),
        "missed_useful_doc_delta": _delta(
            replay_summary,
            replay_baseline,
            "missed_useful_doc_count",
        ),
        "precision_regression_items": item_regressions["precision_regressions"],
        "noise_regression_items": item_regressions["noise_regressions"],
        "baseline_retrieval_precision": _number(replay_baseline.get("retrieval_precision")),
        "replay_retrieval_precision": _number(replay_summary.get("retrieval_precision")),
        "baseline_core_doc_count": _int(replay_baseline.get("core_doc_count")),
        "replay_core_doc_count": _int(replay_summary.get("core_doc_count")),
        "baseline_retrieval_selected_doc_count": _int(
            replay_baseline.get("retrieval_selected_doc_count")
        ),
        "replay_retrieval_selected_doc_count": _int(
            replay_summary.get("retrieval_selected_doc_count")
        ),
    }


def _behavior_metrics(behavior_report: Mapping[str, Any]) -> dict[str, Any]:
    behavior_summary = behavior_report.get("summary")
    if not isinstance(behavior_summary, dict):
        behavior_summary = {}
    return {
        "behavior_case_count": _int(behavior_summary.get("case_count")),
        "behavior_failed_check_count": _int(behavior_summary.get("failed_check_count")),
        "behavior_blocks_activation": bool(behavior_summary.get("blocks_activation")),
    }


def evaluate_route_activation_policy(
    *,
    replay_report: Mapping[str, Any],
    min_replayed_traces: int = 57,
    min_precision_delta: float = 0.0,
    max_noise_delta: float = 0.0,
    min_selected_useful_delta: int = 0,
    max_missed_useful_delta: int = 0,
    max_precision_regression_items: int = 0,
    max_noise_regression_items: int = 0,
) -> dict[str, Any]:
    """Evaluate route-core retrieval replay against activation criteria."""
    metrics = _route_replay_metrics(replay_report)
    criteria = [
        _criterion(
            "replayed_trace_count",
            passed=metrics["replayed_trace_count"] >= min_replayed_traces,
            observed=metrics["replayed_trace_count"],
            threshold=f">= {min_replayed_traces}",
            reason="Replay evidence must cover enough historical route traces.",
            category="route_core",
        ),
        _criterion(
            "route_precision_delta",
            passed=(
                metrics["route_precision_delta"] is not None
                and metrics["route_precision_delta"] >= min_precision_delta
            ),
            observed=metrics["route_precision_delta"],
            threshold=f">= {min_precision_delta}",
            reason="Replay precision must not regress.",
            category="route_core",
        ),
        _criterion(
            "route_noise_delta",
            passed=(
                metrics["route_noise_delta"] is not None
                and metrics["route_noise_delta"] <= max_noise_delta
            ),
            observed=metrics["route_noise_delta"],
            threshold=f"<= {max_noise_delta}",
            reason="Replay noise must not increase.",
            category="route_core",
        ),
        _criterion(
            "selected_useful_doc_delta",
            passed=metrics["selected_useful_doc_delta"] >= min_selected_useful_delta,
            observed=metrics["selected_useful_doc_delta"],
            threshold=f">= {min_selected_useful_delta}",
            reason="Replay must not lose useful selected docs by default.",
            category="route_core",
        ),
        _criterion(
            "missed_useful_doc_delta",
            passed=metrics["missed_useful_doc_delta"] <= max_missed_useful_delta,
            observed=metrics["missed_useful_doc_delta"],
            threshold=f"<= {max_missed_useful_delta}",
            reason="Replay must not increase missed useful docs by default.",
            category="route_core",
        ),
        _criterion(
            "precision_regression_items",
            passed=metrics["precision_regression_items"] <= max_precision_regression_items,
            observed=metrics["precision_regression_items"],
            threshold=f"<= {max_precision_regression_items}",
            reason="Per-trace precision regressions must stay within tolerance.",
            category="route_core",
        ),
        _criterion(
            "noise_regression_items",
            passed=metrics["noise_regression_items"] <= max_noise_regression_items,
            observed=metrics["noise_regression_items"],
            threshold=f"<= {max_noise_regression_items}",
            reason="Per-trace noise regressions must stay within tolerance.",
            category="route_core",
        ),
    ]
    failed = [item for item in criteria if item["status"] == "fail"]
    replay_evidence_insufficient = any(
        item["id"] == "replayed_trace_count" and item["status"] == "fail"
        for item in criteria
    )
    metric_failed = any(
        item["category"] == "route_core"
        and item["id"] != "replayed_trace_count"
        and item["status"] == "fail"
        for item in criteria
    )
    if not failed:
        status = "activate_recommended"
        reason = "Route-core retrieval evidence passed all activation criteria."
    elif metric_failed:
        status = "blocked"
        reason = "At least one route-core retrieval metric criterion failed."
    elif replay_evidence_insufficient:
        status = "needs_more_evidence"
        reason = "Replay evidence is insufficient for activation."
    else:
        status = "blocked"
        reason = "Route-core activation criteria failed."

    return {
        "status": status,
        "activation_allowed": status == "activate_recommended",
        "blocks_activation": status != "activate_recommended",
        "reason": reason,
        "criteria": criteria,
        "failed_criteria": failed,
        "metrics": metrics,
    }


def evaluate_harness_activation_policy(
    *,
    behavior_report: Mapping[str, Any],
    min_behavior_cases: int = 4,
) -> dict[str, Any]:
    """Evaluate Agent Harness behavior evidence against activation criteria."""
    metrics = _behavior_metrics(behavior_report)
    criteria = [
        _criterion(
            "behavior_does_not_block_activation",
            passed=(
                not metrics["behavior_blocks_activation"]
                and metrics["behavior_failed_check_count"] == 0
            ),
            observed={
                "blocks_activation": metrics["behavior_blocks_activation"],
                "failed_check_count": metrics["behavior_failed_check_count"],
            },
            threshold={"blocks_activation": False, "failed_check_count": 0},
            reason="Behavior failures must block Agent Harness activation.",
            category="agent_harness",
        ),
        _criterion(
            "behavior_case_count",
            passed=metrics["behavior_case_count"] >= min_behavior_cases,
            observed=metrics["behavior_case_count"],
            threshold=f">= {min_behavior_cases}",
            reason="Behavior coverage must include the minimum expected cases.",
            category="agent_harness",
        ),
    ]
    failed = [item for item in criteria if item["status"] == "fail"]
    if not failed:
        status = "activate_recommended"
        reason = "Agent Harness behavior evidence passed all activation criteria."
    else:
        status = "blocked"
        reason = "At least one Agent Harness behavior criterion failed."

    return {
        "status": status,
        "activation_allowed": status == "activate_recommended",
        "blocks_activation": status != "activate_recommended",
        "reason": reason,
        "criteria": criteria,
        "failed_criteria": failed,
        "metrics": metrics,
    }


def evaluate_activation_policy(
    *,
    replay_report: Mapping[str, Any],
    behavior_report: Mapping[str, Any],
    min_replayed_traces: int = 57,
    min_behavior_cases: int = 4,
    min_precision_delta: float = 0.0,
    max_noise_delta: float = 0.0,
    min_selected_useful_delta: int = 0,
    max_missed_useful_delta: int = 0,
    max_precision_regression_items: int = 0,
    max_noise_regression_items: int = 0,
) -> dict[str, Any]:
    """Evaluate route-core and Agent Harness activation policies.

    The combined policy is kept for existing CLI callers. Route-core activation
    should read the ``route_core`` layer; harness activation should read the
    ``agent_harness`` layer.
    """
    route_policy = evaluate_route_activation_policy(
        replay_report=replay_report,
        min_replayed_traces=min_replayed_traces,
        min_precision_delta=min_precision_delta,
        max_noise_delta=max_noise_delta,
        min_selected_useful_delta=min_selected_useful_delta,
        max_missed_useful_delta=max_missed_useful_delta,
        max_precision_regression_items=max_precision_regression_items,
        max_noise_regression_items=max_noise_regression_items,
    )
    harness_policy = evaluate_harness_activation_policy(
        behavior_report=behavior_report,
        min_behavior_cases=min_behavior_cases,
    )

    criteria = harness_policy["criteria"] + route_policy["criteria"]
    failed = [item for item in criteria if item["status"] == "fail"]
    route_metric_failed = any(
        item["category"] == "route_core"
        and item["id"] != "replayed_trace_count"
        and item["status"] == "fail"
        for item in criteria
    )
    harness_failed = bool(harness_policy["failed_criteria"])
    replay_evidence_insufficient = any(
        item["id"] == "replayed_trace_count" and item["status"] == "fail"
        for item in criteria
    )

    if not failed:
        status = "activate_recommended"
        reason = "Route-core retrieval and Agent Harness behavior evidence passed."
    elif harness_failed or route_metric_failed:
        status = "blocked"
        reason = "At least one route-core metric or Agent Harness criterion failed."
    elif replay_evidence_insufficient:
        status = "needs_more_evidence"
        reason = "Replay evidence is insufficient for route-core activation."
    else:
        status = "blocked"
        reason = "Activation criteria failed."

    return {
        "status": status,
        "activation_allowed": status == "activate_recommended",
        "blocks_activation": status != "activate_recommended",
        "reason": reason,
        "criteria": criteria,
        "failed_criteria": failed,
        "metrics": {
            **route_policy["metrics"],
            **harness_policy["metrics"],
        },
        "layers": {
            "route_core": route_policy,
            "agent_harness": harness_policy,
        },
    }


def build_route_activation_report(
    *,
    replay_report: Mapping[str, Any],
    behavior_report: Mapping[str, Any],
    replay_report_path: Path,
    behavior_report_path: Path,
    min_replayed_traces: int = 57,
    min_behavior_cases: int = 4,
    min_precision_delta: float = 0.0,
    max_noise_delta: float = 0.0,
    min_selected_useful_delta: int = 0,
    max_missed_useful_delta: int = 0,
    max_precision_regression_items: int = 0,
    max_noise_regression_items: int = 0,
    generated_at: str | None = None,
) -> dict[str, Any]:
    generated_at = generated_at or _timestamp()
    policy = evaluate_activation_policy(
        replay_report=replay_report,
        behavior_report=behavior_report,
        min_replayed_traces=min_replayed_traces,
        min_behavior_cases=min_behavior_cases,
        min_precision_delta=min_precision_delta,
        max_noise_delta=max_noise_delta,
        min_selected_useful_delta=min_selected_useful_delta,
        max_missed_useful_delta=max_missed_useful_delta,
        max_precision_regression_items=max_precision_regression_items,
        max_noise_regression_items=max_noise_regression_items,
    )
    return {
        "schema_version": ROUTE_ACTIVATION_REPORT_SCHEMA_VERSION,
        "generated_at": generated_at,
        "inputs": {
            "replay_report": str(replay_report_path),
            "behavior_report": str(behavior_report_path),
            "replay_schema_version": replay_report.get("schema_version"),
            "behavior_schema_version": behavior_report.get("schema_version"),
        },
        "thresholds": {
            "min_replayed_traces": min_replayed_traces,
            "min_behavior_cases": min_behavior_cases,
            "min_precision_delta": min_precision_delta,
            "max_noise_delta": max_noise_delta,
            "min_selected_useful_delta": min_selected_useful_delta,
            "max_missed_useful_delta": max_missed_useful_delta,
            "max_precision_regression_items": max_precision_regression_items,
            "max_noise_regression_items": max_noise_regression_items,
        },
        "decision": policy,
        "activation_policy": [
            "Route Core activation is based on retrieval replay metrics only.",
            "Agent Harness activation is based on behavior-test evidence only.",
            "The combined legacy decision blocks if either layer blocks.",
            "Replay must cover at least the configured minimum trace count.",
            "Replay precision and noise must not regress unless thresholds are explicitly relaxed.",
            "Selected useful docs must not decrease and missed useful docs must not increase by default.",
            "Behavior tests must have zero failed checks before Agent Harness activation.",
            "Passing this report recommends activation; it does not mutate active taxonomy, route state, or harness state.",
        ],
    }


def render_route_activation_report_json(payload: Mapping[str, Any]) -> str:
    return json.dumps(payload, indent=2, sort_keys=True) + "\n"


def _format_metric(value: object) -> str:
    number = _number(value)
    if number is not None:
        if number.is_integer():
            return str(int(number))
        return f"{number:.3f}"
    if value is None:
        return "n/a"
    if isinstance(value, dict | list | tuple):
        return json.dumps(value, sort_keys=True)
    return str(value)


def _markdown_table(headers: list[str], rows: list[list[str]]) -> str:
    if not rows:
        return "_None._"
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(row) + " |")
    return "\n".join(lines)


def render_route_activation_report(payload: Mapping[str, Any]) -> str:
    decision = payload.get("decision") if isinstance(payload.get("decision"), dict) else {}
    metrics = decision.get("metrics") if isinstance(decision.get("metrics"), dict) else {}
    layers = decision.get("layers") if isinstance(decision.get("layers"), dict) else {}
    route_layer = layers.get("route_core") if isinstance(layers.get("route_core"), dict) else {}
    harness_layer = (
        layers.get("agent_harness") if isinstance(layers.get("agent_harness"), dict) else {}
    )
    criteria_rows = []
    for criterion in decision.get("criteria", []):
        if not isinstance(criterion, dict):
            continue
        criteria_rows.append(
            [
                str(criterion.get("id")),
                str(criterion.get("category")),
                str(criterion.get("status")),
                _format_metric(criterion.get("observed")),
                str(criterion.get("threshold")),
            ]
        )
    lines = [
        "# Route Activation Decision Report",
        "",
        f"- Generated at: `{payload.get('generated_at')}`",
        f"- Decision: `{decision.get('status')}`",
        f"- Activation allowed: `{decision.get('activation_allowed')}`",
        f"- Blocks activation: `{decision.get('blocks_activation')}`",
        f"- Reason: {decision.get('reason')}",
        f"- Route Core status: `{route_layer.get('status') or 'n/a'}`",
        f"- Agent Harness status: `{harness_layer.get('status') or 'n/a'}`",
        "",
        "## Inputs",
        "",
        f"- Replay report: `{payload.get('inputs', {}).get('replay_report') if isinstance(payload.get('inputs'), dict) else ''}`",
        f"- Behavior report: `{payload.get('inputs', {}).get('behavior_report') if isinstance(payload.get('inputs'), dict) else ''}`",
        "",
        "## Metrics",
        "",
        f"- Replayed traces: `{metrics.get('replayed_trace_count')}`",
        f"- Behavior cases: `{metrics.get('behavior_case_count')}`",
        f"- Behavior failed checks: `{metrics.get('behavior_failed_check_count')}`",
        f"- Precision delta: `{_format_metric(metrics.get('route_precision_delta'))}`",
        f"- Noise delta: `{_format_metric(metrics.get('route_noise_delta'))}`",
        f"- Baseline retrieval precision: `{_format_metric(metrics.get('baseline_retrieval_precision'))}`",
        f"- Replay retrieval precision: `{_format_metric(metrics.get('replay_retrieval_precision'))}`",
        f"- Selected useful delta: `{metrics.get('selected_useful_doc_delta')}`",
        f"- Missed useful delta: `{metrics.get('missed_useful_doc_delta')}`",
        f"- Precision regression items: `{metrics.get('precision_regression_items')}`",
        f"- Noise regression items: `{metrics.get('noise_regression_items')}`",
        f"- Baseline retrieval selected docs: `{metrics.get('baseline_retrieval_selected_doc_count')}`",
        f"- Replay retrieval selected docs: `{metrics.get('replay_retrieval_selected_doc_count')}`",
        f"- Baseline core docs: `{metrics.get('baseline_core_doc_count')}`",
        f"- Replay core docs: `{metrics.get('replay_core_doc_count')}`",
        "",
        "## Criteria",
        "",
        _markdown_table(["criterion", "category", "status", "observed", "threshold"], criteria_rows),
        "",
        "## Activation Policy",
        "",
    ]
    lines.extend(f"- {item}" for item in payload.get("activation_policy", []))
    lines.append("")
    return "\n".join(lines)


def generate_route_activation_report(
    *,
    replay_report_path: Path,
    behavior_report_path: Path,
    repo_root: Path | None = None,
    handle: str | None = None,
    min_replayed_traces: int = 57,
    min_behavior_cases: int = 4,
    min_precision_delta: float = 0.0,
    max_noise_delta: float = 0.0,
    min_selected_useful_delta: int = 0,
    max_missed_useful_delta: int = 0,
    max_precision_regression_items: int = 0,
    max_noise_regression_items: int = 0,
    write: bool = False,
) -> RouteActivationReportResult:
    paths = build_paths(repo_root)
    replay_report = _load_json(replay_report_path)
    behavior_report = _load_json(behavior_report_path)
    report = build_route_activation_report(
        replay_report=replay_report,
        behavior_report=behavior_report,
        replay_report_path=replay_report_path,
        behavior_report_path=behavior_report_path,
        min_replayed_traces=min_replayed_traces,
        min_behavior_cases=min_behavior_cases,
        min_precision_delta=min_precision_delta,
        max_noise_delta=max_noise_delta,
        min_selected_useful_delta=min_selected_useful_delta,
        max_missed_useful_delta=max_missed_useful_delta,
        max_precision_regression_items=max_precision_regression_items,
        max_noise_regression_items=max_noise_regression_items,
    )
    resolved_handle = resolve_user_handle(paths.repo_root, explicit_handle=handle)
    json_text = render_route_activation_report_json(report)
    markdown = render_route_activation_report(report)
    report_dir = (
        paths.repo_wiki_dir
        / "_toolkit"
        / "reports"
        / "route-activation"
        / slugify(resolved_handle)
    )
    markdown_path = report_dir / "latest.md" if write else None
    json_path = report_dir / "latest.json" if write else None
    if write:
        report_dir.mkdir(parents=True, exist_ok=True)
        assert markdown_path is not None
        assert json_path is not None
        markdown_path.write_text(markdown, encoding="utf-8")
        json_path.write_text(json_text, encoding="utf-8")
    return RouteActivationReportResult(
        report=report,
        markdown=markdown,
        json_text=json_text,
        markdown_path=markdown_path,
        json_path=json_path,
    )
