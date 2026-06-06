"""Project A coding-agent eval harness diagnostics."""

from __future__ import annotations

from datetime import datetime
import json
from pathlib import Path
import subprocess
from typing import Any

from ai_wiki_toolkit.diagnostics import (
    DEFAULT_DIAGNOSTICS_MAX_ITEMS,
    build_memory_diagnostics_report,
)
from ai_wiki_toolkit.impact_eval import (
    discover_impact_eval_families,
    generate_impact_eval_schedule_report,
)
from ai_wiki_toolkit.paths import build_paths, resolve_user_handle
from ai_wiki_toolkit.repo_evaluation import (
    DEFAULT_REPO_EVALUATION_SINCE,
    generate_repo_evaluation,
)

PROJECT_A_DIAGNOSTICS_SCHEMA_VERSION = "project-a-diagnostics-v1"


def _now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def _default_report_stem(now_iso: str) -> str:
    return f"project_a_diagnostics_{now_iso[:10]}"


def _tail(value: str, *, max_chars: int = 4000) -> str:
    if len(value) <= max_chars:
        return value
    return value[-max_chars:]


def _run_check(command: list[str], *, cwd: Path) -> dict[str, Any]:
    started_at = _now_iso()
    try:
        result = subprocess.run(
            command,
            cwd=cwd,
            capture_output=True,
            check=False,
            text=True,
        )
        return {
            "command": command,
            "started_at": started_at,
            "finished_at": _now_iso(),
            "returncode": result.returncode,
            "ok": result.returncode == 0,
            "stdout_tail": _tail(result.stdout),
            "stderr_tail": _tail(result.stderr),
        }
    except OSError as exc:
        return {
            "command": command,
            "started_at": started_at,
            "finished_at": _now_iso(),
            "returncode": None,
            "ok": False,
            "stdout_tail": "",
            "stderr_tail": str(exc),
        }


def _run_local_checks(repo_root: Path) -> list[dict[str, Any]]:
    return [
        _run_check(["uv", "run", "pytest"], cwd=repo_root),
        _run_check(["npm", "pack", "--dry-run", "--ignore-scripts"], cwd=repo_root),
        _run_check(["git", "diff", "--check"], cwd=repo_root),
    ]


def _family_diagnostics(families: dict[str, Any]) -> dict[str, Any]:
    family_rows = [
        family
        for family in families.get("families", [])
        if isinstance(family, dict)
    ]
    missing_rubrics = [
        str(family.get("name"))
        for family in family_rows
        if not family.get("rubric_present")
    ]
    return {
        "family_count": families.get("family_count"),
        "runnable_count": families.get("runnable_count"),
        "rubrics_present": len(family_rows) - len(missing_rubrics),
        "rubrics_missing": missing_rubrics,
        "families": [
            {
                "name": family.get("name"),
                "status": family.get("status"),
                "rubric_present": family.get("rubric_present"),
                "baseline_ref": family.get("baseline_ref"),
            }
            for family in family_rows
        ],
    }


def _route_summary(route_report: dict[str, Any]) -> dict[str, Any]:
    route = route_report.get("route_diagnostics")
    if not isinstance(route, dict):
        return {}
    summary = route.get("summary")
    return summary if isinstance(summary, dict) else {}


def _repo_evaluation_summary(repo_evaluation: dict[str, Any]) -> dict[str, Any]:
    workflow = repo_evaluation.get("workflow_coverage")
    if not isinstance(workflow, dict):
        workflow = {}
    route_quality = repo_evaluation.get("route_quality")
    if not isinstance(route_quality, dict):
        route_quality = {}
    summary = repo_evaluation.get("summary")
    if not isinstance(summary, dict):
        summary = {}
    return {
        "overall_status": summary.get("overall_status"),
        "top_opportunities": summary.get("top_opportunities", []),
        "workflow_coverage": {
            "checked_tasks": workflow.get("checked_tasks"),
            "task_checks": workflow.get("task_checks"),
            "reuse_events": workflow.get("reuse_events"),
            "coverage_gaps": workflow.get("coverage_gaps"),
            "source_incident_events": workflow.get("source_incident_events"),
        },
        "route_quality": {
            "route_traces": route_quality.get("route_traces"),
            "route_precision": route_quality.get("route_precision"),
            "route_recall_proxy": route_quality.get("route_recall_proxy"),
            "route_noise_rate": route_quality.get("route_noise_rate"),
            "selected_but_unused_docs": route_quality.get("selected_but_unused_docs"),
            "missed_useful_docs": route_quality.get("missed_useful_docs"),
        },
    }


def _runnable_family_names(family_diagnostics: dict[str, Any]) -> set[str]:
    names: set[str] = set()
    for family in family_diagnostics.get("families", []):
        if not isinstance(family, dict):
            continue
        if family.get("status") != "runnable":
            continue
        name = family.get("name")
        if isinstance(name, str) and name:
            names.add(name)
    return names


def _successful_rubric_run_families(payload: dict[str, Any]) -> set[str]:
    recent_runs = payload.get("schedule_report", {}).get("recent_runs", [])
    if not isinstance(recent_runs, list):
        return set()
    families: set[str] = set()
    for run in recent_runs:
        if not isinstance(run, dict):
            continue
        if run.get("score_policy") != "rubric":
            continue
        if run.get("runner_success") is not True:
            continue
        family = run.get("family")
        if isinstance(family, str) and family:
            families.add(family)
    return families


def _latest_rubric_outcomes(payload: dict[str, Any]) -> dict[str, str]:
    recent_runs = payload.get("schedule_report", {}).get("recent_runs", [])
    if not isinstance(recent_runs, list):
        return {}
    outcomes: dict[str, str] = {}
    for run in recent_runs:
        if not isinstance(run, dict):
            continue
        if run.get("score_policy") != "rubric":
            continue
        if run.get("runner_success") is not True:
            continue
        family = run.get("family")
        outcome = run.get("primary_outcome")
        if isinstance(family, str) and isinstance(outcome, str):
            outcomes[family] = outcome
    return outcomes


def _optimization_backlog(payload: dict[str, Any]) -> list[dict[str, str]]:
    family = payload["family_diagnostics"]
    schedule = payload["schedule_report"]["summary"]
    route_quality = payload["repo_evaluation_summary"]["route_quality"]
    items: list[dict[str, str]] = []
    if family["rubrics_missing"]:
        items.append(
            {
                "priority": "P0",
                "title": "Add or fix machine-readable rubrics",
                "reason": f"{len(family['rubrics_missing'])} runnable families are missing rubric files.",
            }
        )
    indexed_runs = schedule.get("indexed_run_count")
    runnable = family.get("runnable_count")
    if isinstance(indexed_runs, int) and isinstance(runnable, int) and indexed_runs < runnable:
        items.append(
            {
                "priority": "P0",
                "title": "Backfill historical run index",
                "reason": f"Schedule index has {indexed_runs} runs for {runnable} runnable families.",
            }
        )
    noise_rate = route_quality.get("route_noise_rate")
    precision = route_quality.get("route_precision")
    if isinstance(noise_rate, float) and noise_rate > 0.5:
        items.append(
            {
                "priority": "P1",
                "title": "Reduce route noise before adding more memory",
                "reason": f"Route precision is {precision:.3f} and noise rate is {noise_rate:.3f}.",
            }
        )
    runnable_families = _runnable_family_names(family)
    rubric_run_families = _successful_rubric_run_families(payload)
    missing_rerun_families = sorted(runnable_families - rubric_run_families)
    if missing_rerun_families:
        family_list = ", ".join(missing_rerun_families[:4])
        if len(missing_rerun_families) > 4:
            family_list += ", ..."
        items.append(
            {
                "priority": "P2",
                "title": "Rerun selected benchmark families after scoring/index gates",
                "reason": (
                    f"{len(missing_rerun_families)} runnable families lack a recent "
                    f"successful rubric run: {family_list}."
                ),
            }
        )
    elif runnable_families:
        rubric_outcomes = _latest_rubric_outcomes(payload)
        neutral_families = sorted(
            family
            for family, outcome in rubric_outcomes.items()
            if outcome == "neutral_signal"
        )
        if neutral_families:
            family_list = ", ".join(neutral_families[:4])
            if len(neutral_families) > 4:
                family_list += ", ..."
            items.append(
                {
                    "priority": "P2",
                    "title": "Analyze neutral benchmark families before adding memory",
                    "reason": (
                        f"All runnable families have successful rubric runs; "
                        f"{len(neutral_families)} latest outcomes are neutral: {family_list}."
                    ),
                }
            )
        items.append(
            {
                "priority": "P2",
                "title": "Add per-slot timeout and heartbeat artifacts",
                "reason": (
                    "Recent rubric runs are indexed only after completion; long Codex slots "
                    "need elapsed-time, timeout, and heartbeat evidence for production-style ops."
                ),
            }
        )
    return items


def generate_project_a_diagnostics(
    *,
    repo_root: Path | None = None,
    repo_wiki_dir: Path | None = None,
    handle: str | None = None,
    since: str | None = DEFAULT_REPO_EVALUATION_SINCE,
    candidate_max_items: int = DEFAULT_DIAGNOSTICS_MAX_ITEMS,
    period_id: str | None = None,
    run_checks: bool = False,
    write: bool = True,
) -> dict[str, Any]:
    """Generate a single Project A harness diagnostic report."""

    paths = build_paths(repo_root)
    selected_repo_root = paths.repo_root
    selected_repo_wiki_dir = repo_wiki_dir or selected_repo_root / "ai-wiki"
    selected_handle = handle or resolve_user_handle(selected_repo_root)
    generated_at = _now_iso()

    check_results = _run_local_checks(selected_repo_root) if run_checks else []
    families = discover_impact_eval_families(repo_root=selected_repo_root)
    schedule_report = generate_impact_eval_schedule_report(
        repo_root=selected_repo_root,
        repo_wiki_dir=selected_repo_wiki_dir,
        period_id=period_id,
        refresh_candidates=True,
        handle=selected_handle,
        since=since,
        candidate_max_items=candidate_max_items,
    )
    repo_evaluation = generate_repo_evaluation(
        repo_root=selected_repo_root,
        repo_wiki_dir=selected_repo_wiki_dir,
        handle=selected_handle,
        since=since,
        max_items=candidate_max_items,
        write=False,
    )
    repo_evaluation_payload = json.loads(repo_evaluation.json_text)
    route_report = build_memory_diagnostics_report(
        selected_repo_wiki_dir,
        handle=selected_handle,
        since=since,
        focus="route",
        max_items=candidate_max_items,
    )
    payload: dict[str, Any] = {
        "schema_version": PROJECT_A_DIAGNOSTICS_SCHEMA_VERSION,
        "generated_at": generated_at,
        "repo_root": str(selected_repo_root),
        "repo_wiki_dir": str(selected_repo_wiki_dir),
        "filters": {
            "handle": selected_handle,
            "since": since,
            "candidate_max_items": candidate_max_items,
            "period_id": period_id,
            "run_checks": run_checks,
        },
        "check_results": check_results,
        "family_diagnostics": _family_diagnostics(families),
        "schedule_report": {
            "summary": schedule_report.get("summary", {}),
            "recent_runs": schedule_report.get("recent_runs", []),
            "outputs": schedule_report.get("outputs", {}),
        },
        "repo_evaluation_summary": _repo_evaluation_summary(repo_evaluation_payload),
        "route_diagnostics_summary": _route_summary(route_report),
        "outputs": {},
    }
    payload["optimization_backlog"] = _optimization_backlog(payload)
    if write:
        stem = _default_report_stem(generated_at)
        report_dir = selected_repo_root / "evals" / "impact" / "reports"
        markdown_path = report_dir / f"{stem}.md"
        json_path = report_dir / f"{stem}.json"
        payload["outputs"] = {
            "markdown": str(markdown_path),
            "json": str(json_path),
        }
        markdown = render_project_a_diagnostics(payload)
        json_text = render_project_a_diagnostics_json(payload)
        markdown_path.parent.mkdir(parents=True, exist_ok=True)
        markdown_path.write_text(markdown, encoding="utf-8")
        json_path.write_text(json_text, encoding="utf-8")
    return payload


def _format_float(value: Any) -> str:
    if not isinstance(value, float):
        return "-"
    return f"{value:.3f}"


def _markdown_table(headers: list[str], rows: list[list[str]]) -> str:
    if not rows:
        return "_No rows._"
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]
    lines.extend("| " + " | ".join(cell.replace("|", "\\|") for cell in row) + " |" for row in rows)
    return "\n".join(lines)


def render_project_a_diagnostics(payload: dict[str, Any]) -> str:
    families = payload.get("family_diagnostics", {})
    schedule = payload.get("schedule_report", {})
    schedule_summary = schedule.get("summary", {}) if isinstance(schedule, dict) else {}
    repo_summary = payload.get("repo_evaluation_summary", {})
    if not isinstance(repo_summary, dict):
        repo_summary = {}
    workflow = repo_summary.get("workflow_coverage", {})
    route = repo_summary.get("route_quality", {})
    check_rows = [
        [
            " ".join(str(part) for part in item.get("command", [])),
            str(item.get("returncode")),
            "yes" if item.get("ok") else "no",
        ]
        for item in payload.get("check_results", [])
        if isinstance(item, dict)
    ]
    family_rows = [
        [
            str(item.get("name")),
            str(item.get("status")),
            "yes" if item.get("rubric_present") else "no",
            str(item.get("baseline_ref") or "-"),
        ]
        for item in families.get("families", [])
        if isinstance(item, dict)
    ]
    run_rows = [
        [
            str(item.get("period_id", "")),
            str(item.get("family", "")),
            str(item.get("score_policy", "")),
            str(item.get("primary_outcome", "")),
            str(item.get("artifact_status", item.get("runner_success", ""))),
        ]
        for item in schedule.get("recent_runs", [])
        if isinstance(item, dict)
    ]
    backlog_rows = [
        [str(item.get("priority", "")), str(item.get("title", "")), str(item.get("reason", ""))]
        for item in payload.get("optimization_backlog", [])
        if isinstance(item, dict)
    ]
    lines = [
        "# Project A Coding-Agent Eval Harness Diagnostics",
        "",
        f"- Generated at: `{payload.get('generated_at')}`",
        f"- Repo root: `{payload.get('repo_root')}`",
        f"- Handle: `{payload.get('filters', {}).get('handle')}`",
        f"- Since: `{payload.get('filters', {}).get('since')}`",
        f"- Local checks run: `{'yes' if payload.get('check_results') else 'no'}`",
        "",
        "## Local Checks",
        "",
        _markdown_table(["command", "returncode", "ok"], check_rows),
        "",
        "## Harness State",
        "",
        f"- Runnable families: `{families.get('runnable_count')}`",
        f"- Rubrics present: `{families.get('rubrics_present')}`",
        f"- Rubrics missing: `{', '.join(families.get('rubrics_missing', [])) or 'none'}`",
        f"- Indexed runs: `{schedule_summary.get('indexed_run_count')}`",
        f"- Recent runs: `{schedule_summary.get('recent_run_count')}`",
        "",
        _markdown_table(["family", "status", "rubric", "baseline"], family_rows),
        "",
        "## Recent Runs",
        "",
        _markdown_table(["period", "family", "score_policy", "outcome", "artifact_status"], run_rows),
        "",
        "## Repo Evaluation",
        "",
        f"- Overall status: `{repo_summary.get('overall_status')}`",
        f"- Checked tasks: `{workflow.get('checked_tasks')}`",
        f"- Task checks: `{workflow.get('task_checks')}`",
        f"- Reuse events: `{workflow.get('reuse_events')}`",
        f"- Coverage gaps: `{workflow.get('coverage_gaps')}`",
        f"- Route traces: `{route.get('route_traces')}`",
        f"- Route precision: `{_format_float(route.get('route_precision'))}`",
        f"- Route recall proxy: `{_format_float(route.get('route_recall_proxy'))}`",
        f"- Route noise rate: `{_format_float(route.get('route_noise_rate'))}`",
        f"- Selected-but-unused docs: `{route.get('selected_but_unused_docs')}`",
        f"- Missed useful docs: `{route.get('missed_useful_docs')}`",
        "",
        "## Optimization Backlog",
        "",
        _markdown_table(["priority", "title", "reason"], backlog_rows),
        "",
        "## Claim Boundary",
        "",
        "This report is a local diagnostic over repo artifacts and telemetry. It is not itself a fresh "
        "multi-slot Codex benchmark rerun unless `--run-checks` and a separate `schedule run` command "
        "were executed successfully.",
        "",
    ]
    return "\n".join(lines)


def render_project_a_diagnostics_json(payload: dict[str, Any]) -> str:
    return json.dumps(payload, indent=2, sort_keys=True) + "\n"
