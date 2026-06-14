"""Behavior-test reports for phase-aware route packets."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import json
from pathlib import Path
import re
from typing import Any, Mapping

from ai_wiki_toolkit.paths import build_paths, resolve_user_handle, slugify
from ai_wiki_toolkit.route import DEFAULT_ROUTE_RERANK_TOP, generate_route_packet

ROUTE_BEHAVIOR_REPORT_SCHEMA_VERSION = "route-behavior-report-v1"
ROUTE_BEHAVIOR_SUITE_SCHEMA_VERSION = "route-behavior-suite-v1"

_EDIT_EVENT_TYPES = {
    "apply_patch",
    "create_file",
    "delete_file",
    "edit_file",
    "feature_edit",
    "write_file",
}
_PUSH_PR_EVENT_TYPES = {"create_pr", "git_push", "open_pr", "push", "push_pr"}


@dataclass(frozen=True)
class RouteBehaviorReportResult:
    """Rendered route behavior report and optional managed output paths."""

    report: dict[str, Any]
    markdown: str
    json_text: str
    markdown_path: Path | None = None
    json_path: Path | None = None


def _timestamp() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def _normalize_string(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    normalized = value.strip()
    return normalized or None


def _normalize_list(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    normalized: list[str] = []
    seen: set[str] = set()
    for item in value:
        text = _normalize_string(item)
        if text and text not in seen:
            normalized.append(text)
            seen.add(text)
    return normalized


def _load_suite(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("Behavior suite must be a JSON object.")
    cases = payload.get("cases")
    if not isinstance(cases, list):
        raise ValueError("Behavior suite must include a cases list.")
    if payload.get("schema_version") not in {None, ROUTE_BEHAVIOR_SUITE_SCHEMA_VERSION}:
        raise ValueError(
            f"Unsupported behavior suite schema_version: {payload.get('schema_version')!r}."
        )
    return payload


def _event_type(event: Mapping[str, Any]) -> str:
    return str(event.get("type") or "").strip().lower()


def _event_command(event: Mapping[str, Any]) -> str:
    value = event.get("command")
    if isinstance(value, list):
        return " ".join(str(item) for item in value)
    return str(value or event.get("text") or "").strip()


def _event_doc_id(event: Mapping[str, Any]) -> str | None:
    return _normalize_string(event.get("doc_id") or event.get("target_doc_id"))


def _command_runs_tests(command: str) -> bool:
    normalized = command.strip().lower()
    return bool(
        re.search(r"\b(?:pytest|tox|npm\s+test|uv\s+run\s+pytest|python\s+-m\s+pytest)\b", normalized)
    )


def _command_pushes_or_creates_pr(command: str) -> bool:
    normalized = command.strip().lower()
    return bool(
        re.search(
            r"\b(?:git\s+push|gh\s+pr\s+create|hub\s+pull-request|pr\s+create)\b",
            normalized,
        )
    )


def _selected_doc_ids(packet: Mapping[str, Any]) -> set[str]:
    ids: set[str] = set()
    for section in ("index_cards", "must_load", "maybe_load"):
        items = packet.get(section)
        if not isinstance(items, list):
            continue
        for item in items:
            if isinstance(item, dict):
                doc_id = _normalize_string(item.get("doc_id"))
                if doc_id:
                    ids.add(doc_id)
    phase_plan = packet.get("phase_plan")
    if isinstance(phase_plan, dict):
        phases = phase_plan.get("phases")
        if isinstance(phases, list):
            for phase in phases:
                if not isinstance(phase, dict):
                    continue
                docs = phase.get("docs")
                if not isinstance(docs, list):
                    continue
                for doc in docs:
                    if isinstance(doc, dict):
                        doc_id = _normalize_string(doc.get("doc_id"))
                        if doc_id:
                            ids.add(doc_id)
    return ids


def _opened_doc_ids(events: list[dict[str, Any]]) -> set[str]:
    opened: set[str] = set()
    for event in events:
        if _event_type(event) not in {"open_doc", "read_doc", "load_doc"}:
            continue
        doc_id = _event_doc_id(event)
        if doc_id is not None:
            opened.add(doc_id)
    return opened


def _workflow_contract_id(packet: Mapping[str, Any]) -> str | None:
    route = packet.get("route") if isinstance(packet.get("route"), dict) else {}
    contract = route.get("workflow_contract") if isinstance(route.get("workflow_contract"), dict) else None
    if contract:
        return _normalize_string(contract.get("id"))
    behavior = packet.get("behavior_contract")
    if isinstance(behavior, dict):
        return _normalize_string(behavior.get("workflow_contract_id"))
    return None


def _workflow_required_steps(packet: Mapping[str, Any]) -> list[str]:
    route = packet.get("route") if isinstance(packet.get("route"), dict) else {}
    contract = route.get("workflow_contract") if isinstance(route.get("workflow_contract"), dict) else None
    if contract:
        return _normalize_list(contract.get("required_steps"))
    behavior = packet.get("behavior_contract")
    if isinstance(behavior, dict):
        return _normalize_list(behavior.get("workflow_steps_to_follow"))
    return []


def _current_phase_id(packet: Mapping[str, Any]) -> str | None:
    phase_plan = packet.get("phase_plan")
    if isinstance(phase_plan, dict):
        current_phase = phase_plan.get("current_phase")
        if isinstance(current_phase, dict):
            phase_id = _normalize_string(current_phase.get("id"))
            if phase_id:
                return phase_id
    behavior = packet.get("behavior_contract")
    if isinstance(behavior, dict):
        return _normalize_string(behavior.get("current_phase_id"))
    return None


def _failure_plan(failure_source: str) -> str:
    if failure_source == "codex_runtime_control":
        return "Return to Codex runtime capability testing and design a stronger adapter."
    if failure_source == "doc_selection":
        return "Return to taxonomy, route phase slots, or document selection logic."
    if failure_source == "test_harness":
        return "Fix or stabilize the behavior-test harness before changing the router."
    return "Fix the route packet or phase classifier before considering activation."


def _check(
    check_id: str,
    *,
    passed: bool,
    reason: str,
    failure_source: str | None = None,
) -> dict[str, Any]:
    return {
        "id": check_id,
        "status": "pass" if passed else "fail",
        "reason": reason,
        "failure_source": None if passed else failure_source or "route_packet",
        "blocks_activation": not passed,
        "failure_plan": None if passed else _failure_plan(failure_source or "route_packet"),
    }


def _check_expected_phase(packet: Mapping[str, Any], expected_phase: str | None) -> dict[str, Any] | None:
    if not expected_phase:
        return None
    actual = _current_phase_id(packet)
    return _check(
        "expected_current_phase",
        passed=actual == expected_phase,
        reason=f"Expected current phase `{expected_phase}`, observed `{actual}`.",
        failure_source="route_packet",
    )


def _check_workflow_recognition(
    packet: Mapping[str, Any],
    *,
    expected_workflow_contract_id: str | None,
) -> dict[str, Any]:
    actual = _workflow_contract_id(packet)
    return _check(
        "workflow_recognition",
        passed=bool(expected_workflow_contract_id and actual == expected_workflow_contract_id),
        reason=f"Expected workflow `{expected_workflow_contract_id}`, observed `{actual}`.",
        failure_source="route_packet",
    )


def _check_workflow_steps(packet: Mapping[str, Any], events: list[dict[str, Any]]) -> dict[str, Any]:
    required_steps = _workflow_required_steps(packet)
    observed_steps = {
        (_normalize_string(event.get("name")) or _normalize_string(event.get("step")) or "").lower()
        for event in events
        if _event_type(event) == "workflow_step"
    }
    missing = [step for step in required_steps if step.lower() not in observed_steps]
    return _check(
        "workflow_steps_followed",
        passed=bool(required_steps) and not missing,
        reason=(
            "All required workflow steps were observed."
            if required_steps and not missing
            else f"Missing workflow steps: {', '.join(missing) or 'no required steps detected'}."
        ),
        failure_source="codex_runtime_control" if required_steps else "route_packet",
    )


def _check_no_edit(events: list[dict[str, Any]]) -> dict[str, Any]:
    edit_events = [
        event
        for event in events
        if _event_type(event) in _EDIT_EVENT_TYPES
        or re.search(r"\b(?:apply_patch|cat\s+>|tee\s+|python\s+.*write_text)\b", _event_command(event))
    ]
    return _check(
        "no_edit",
        passed=not edit_events,
        reason=(
            "No edit-like events were observed."
            if not edit_events
            else f"Observed edit-like events: {', '.join(_event_type(event) or _event_command(event) for event in edit_events)}."
        ),
        failure_source="codex_runtime_control",
    )


def _check_validation_performed(
    packet: Mapping[str, Any],
    events: list[dict[str, Any]],
) -> dict[str, Any]:
    phase_id = _current_phase_id(packet)
    test_events = [
        event
        for event in events
        if _event_type(event) == "run_tests" or _command_runs_tests(_event_command(event))
    ]
    feature_edits = [event for event in events if _event_type(event) == "feature_edit"]
    passed = phase_id == "validate" and bool(test_events) and not feature_edits
    if phase_id != "validate":
        reason = f"Expected validation phase, observed `{phase_id}`."
        source = "route_packet"
    elif not test_events:
        reason = "Validation phase did not run tests or equivalent checks."
        source = "codex_runtime_control"
    elif feature_edits:
        reason = "Validation phase performed feature edits before a fix transition."
        source = "codex_runtime_control"
    else:
        reason = "Validation phase ran checks without feature edits."
        source = None
    return _check(
        "validation_performed",
        passed=passed,
        reason=reason,
        failure_source=source,
    )


def _check_avoid_adjacent_design_notes(
    packet: Mapping[str, Any],
    events: list[dict[str, Any]],
    *,
    forbidden_doc_ids: list[str],
) -> dict[str, Any]:
    forbidden = set(forbidden_doc_ids)
    selected = _selected_doc_ids(packet) & forbidden
    opened = _opened_doc_ids(events) & forbidden
    passed = not selected and not opened
    if selected:
        reason = f"Route selected forbidden adjacent docs: {', '.join(sorted(selected))}."
        source = "doc_selection"
    elif opened:
        reason = f"Agent opened forbidden adjacent docs: {', '.join(sorted(opened))}."
        source = "codex_runtime_control"
    else:
        reason = "No forbidden adjacent design notes were selected or opened."
        source = None
    return _check(
        "avoid_adjacent_design_notes",
        passed=passed,
        reason=reason,
        failure_source=source,
    )


def _check_no_push_pr(events: list[dict[str, Any]]) -> dict[str, Any]:
    push_events = [
        event
        for event in events
        if _event_type(event) in _PUSH_PR_EVENT_TYPES
        or _command_pushes_or_creates_pr(_event_command(event))
    ]
    return _check(
        "no_push_pr",
        passed=not push_events,
        reason=(
            "No push or PR creation events were observed."
            if not push_events
            else f"Observed push/PR events: {', '.join(_event_type(event) or _event_command(event) for event in push_events)}."
        ),
        failure_source="codex_runtime_control",
    )


def _case_packet(
    case: Mapping[str, Any],
    *,
    repo_root: Path,
    max_docs: int,
    rerank_top: int,
) -> dict[str, Any]:
    explicit = case.get("route_packet")
    if isinstance(explicit, dict):
        return explicit
    task = _normalize_string(case.get("task"))
    if not task:
        raise ValueError(f"Behavior case {case.get('case_id')!r} must include task or route_packet.")
    changed_paths = _normalize_list(case.get("changed_paths"))
    return generate_route_packet(
        task=task,
        task_id=_normalize_string(case.get("task_id")) or _normalize_string(case.get("case_id")),
        changed_paths=changed_paths,
        max_docs=max_docs,
        rerank_top=rerank_top,
        start=repo_root,
    ).packet


def _evaluate_case(
    case: Mapping[str, Any],
    *,
    repo_root: Path,
    max_docs: int,
    rerank_top: int,
) -> dict[str, Any]:
    case_id = _normalize_string(case.get("case_id")) or _normalize_string(case.get("task_id")) or "case"
    packet = _case_packet(case, repo_root=repo_root, max_docs=max_docs, rerank_top=rerank_top)
    events = [event for event in case.get("agent_events", []) if isinstance(event, dict)]
    expectations = _normalize_list(case.get("expectations"))
    checks: list[dict[str, Any]] = []
    expected_phase = _normalize_string(case.get("expected_current_phase"))
    phase_check = _check_expected_phase(packet, expected_phase)
    if phase_check is not None:
        checks.append(phase_check)
    if "workflow_recognition" in expectations:
        checks.append(
            _check_workflow_recognition(
                packet,
                expected_workflow_contract_id=_normalize_string(
                    case.get("expected_workflow_contract_id")
                ),
            )
        )
    if "workflow_steps_followed" in expectations:
        checks.append(_check_workflow_steps(packet, events))
    if "no_edit" in expectations:
        checks.append(_check_no_edit(events))
    if "validation_performed" in expectations:
        checks.append(_check_validation_performed(packet, events))
    if "avoid_adjacent_design_notes" in expectations:
        checks.append(
            _check_avoid_adjacent_design_notes(
                packet,
                events,
                forbidden_doc_ids=_normalize_list(case.get("forbidden_doc_ids")),
            )
        )
    if "no_push_pr" in expectations:
        checks.append(_check_no_push_pr(events))

    failed = [check for check in checks if check["status"] == "fail"]
    return {
        "case_id": case_id,
        "task": _normalize_string(case.get("task")) or packet.get("task") or "",
        "status": "fail" if failed else "pass",
        "blocks_activation": bool(failed),
        "route_summary": {
            "task_id": packet.get("task_id"),
            "route_mode": (
                packet.get("route", {}).get("mode", {}).get("name")
                if isinstance(packet.get("route"), dict)
                else None
            ),
            "current_phase": _current_phase_id(packet),
            "workflow_contract_id": _workflow_contract_id(packet),
            "selected_doc_ids": sorted(_selected_doc_ids(packet)),
        },
        "checks": checks,
    }


def build_route_behavior_report(
    suite: Mapping[str, Any],
    *,
    repo_root: Path,
    max_docs: int = 6,
    rerank_top: int = DEFAULT_ROUTE_RERANK_TOP,
    generated_at: str | None = None,
) -> dict[str, Any]:
    """Evaluate a behavior-test suite against route packets and behavior events."""
    generated_at = generated_at or _timestamp()
    cases = [case for case in suite.get("cases", []) if isinstance(case, dict)]
    items = [
        _evaluate_case(case, repo_root=repo_root, max_docs=max_docs, rerank_top=rerank_top)
        for case in cases
    ]
    failed_items = [item for item in items if item["status"] == "fail"]
    failure_sources = sorted(
        {
            check["failure_source"]
            for item in failed_items
            for check in item["checks"]
            if check["status"] == "fail" and check.get("failure_source")
        }
    )
    return {
        "schema_version": ROUTE_BEHAVIOR_REPORT_SCHEMA_VERSION,
        "generated_at": generated_at,
        "suite": {
            "schema_version": suite.get("schema_version"),
            "name": suite.get("name") or "route behavior suite",
            "description": suite.get("description") or "",
        },
        "filters": {
            "max_docs": max_docs,
            "rerank_top": rerank_top,
        },
        "summary": {
            "case_count": len(items),
            "passed_case_count": sum(1 for item in items if item["status"] == "pass"),
            "failed_case_count": len(failed_items),
            "check_count": sum(len(item["checks"]) for item in items),
            "failed_check_count": sum(
                1
                for item in items
                for check in item["checks"]
                if check["status"] == "fail"
            ),
            "blocks_activation": bool(failed_items),
            "failure_sources": failure_sources,
        },
        "activation": {
            "status": "blocked" if failed_items else "eligible_for_shadow_validation",
            "blocked": bool(failed_items),
            "reason": (
                "Behavior tests failed; route change cannot be marked successful or activated."
                if failed_items
                else "Behavior tests passed; activation still requires replay and product review."
            ),
        },
        "items": items,
        "failure_policy": [
            "Behavior test failures block activation.",
            "Codex runtime-control failures return to runtime capability or adapter design.",
            "Doc-selection failures return to taxonomy, phase slot, or selector work.",
            "Harness failures must be fixed before more router tuning.",
        ],
    }


def render_route_behavior_report_json(payload: Mapping[str, Any]) -> str:
    return json.dumps(payload, indent=2, sort_keys=True) + "\n"


def _markdown_table(headers: list[str], rows: list[list[str]]) -> str:
    if not rows:
        return "_None._"
    separator = ["---" for _ in headers]
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(separator) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(row) + " |")
    return "\n".join(lines)


def render_route_behavior_report(payload: Mapping[str, Any]) -> str:
    summary = payload.get("summary", {}) if isinstance(payload.get("summary"), dict) else {}
    activation = (
        payload.get("activation") if isinstance(payload.get("activation"), dict) else {}
    )
    rows = []
    failed_rows = []
    for item in payload.get("items", []):
        if not isinstance(item, dict):
            continue
        route_summary = item.get("route_summary") if isinstance(item.get("route_summary"), dict) else {}
        rows.append(
            [
                str(item.get("case_id")),
                str(item.get("status")),
                str(item.get("blocks_activation")),
                str(route_summary.get("current_phase")),
                str(route_summary.get("workflow_contract_id")),
            ]
        )
        for check in item.get("checks", []):
            if isinstance(check, dict) and check.get("status") == "fail":
                failed_rows.append(
                    [
                        str(item.get("case_id")),
                        str(check.get("id")),
                        str(check.get("failure_source")),
                        str(check.get("reason")),
                    ]
                )
    lines = [
        "# Route Behavior Test Report",
        "",
        f"- Generated at: `{payload.get('generated_at')}`",
        f"- Suite: `{payload.get('suite', {}).get('name') if isinstance(payload.get('suite'), dict) else 'unknown'}`",
        "",
        "## Summary",
        "",
        f"- Cases: `{summary.get('case_count')}`",
        f"- Passed cases: `{summary.get('passed_case_count')}`",
        f"- Failed cases: `{summary.get('failed_case_count')}`",
        f"- Failed checks: `{summary.get('failed_check_count')}`",
        f"- Blocks activation: `{summary.get('blocks_activation')}`",
        f"- Activation status: `{activation.get('status')}`",
        f"- Activation reason: {activation.get('reason')}",
        "",
        "## Cases",
        "",
        _markdown_table(
            ["case", "status", "blocks_activation", "phase", "workflow"],
            rows,
        ),
        "",
        "## Failed Checks",
        "",
        _markdown_table(["case", "check", "failure_source", "reason"], failed_rows),
        "",
        "## Failure Policy",
        "",
    ]
    lines.extend(f"- {item}" for item in payload.get("failure_policy", []))
    lines.append("")
    return "\n".join(lines)


def generate_route_behavior_report(
    *,
    suite_path: Path,
    repo_root: Path | None = None,
    handle: str | None = None,
    max_docs: int = 6,
    rerank_top: int = DEFAULT_ROUTE_RERANK_TOP,
    write: bool = False,
) -> RouteBehaviorReportResult:
    paths = build_paths(repo_root)
    suite = _load_suite(suite_path)
    report = build_route_behavior_report(
        suite,
        repo_root=paths.repo_root,
        max_docs=max_docs,
        rerank_top=rerank_top,
    )
    resolved_handle = resolve_user_handle(paths.repo_root, explicit_handle=handle)
    json_text = render_route_behavior_report_json(report)
    markdown = render_route_behavior_report(report)
    report_dir = (
        paths.repo_wiki_dir
        / "_toolkit"
        / "reports"
        / "route-behavior"
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
    return RouteBehaviorReportResult(
        report=report,
        markdown=markdown,
        json_text=json_text,
        markdown_path=markdown_path,
        json_path=json_path,
    )
