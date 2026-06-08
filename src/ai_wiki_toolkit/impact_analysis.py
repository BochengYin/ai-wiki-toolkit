"""Analysis reports for impact-eval diagnostics."""

from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import shlex
import sqlite3
from typing import Any

from ai_wiki_toolkit.diagnostics import (
    DEFAULT_DIAGNOSTICS_MAX_ITEMS,
    build_memory_diagnostics_report,
)
from ai_wiki_toolkit.impact_eval import (
    RUN_INDEX_SCHEMA_VERSION,
    generate_impact_eval_report,
    impact_eval_report_to_dict,
)
from ai_wiki_toolkit.paths import build_paths, resolve_user_handle, slugify
from ai_wiki_toolkit.repo_evaluation import DEFAULT_REPO_EVALUATION_SINCE
from ai_wiki_toolkit.route import (
    DEFAULT_ROUTE_RERANK_TOP,
    DEFAULT_ROUTE_SAFETY_CAP_WORDS,
    generate_route_packet,
    render_route_packet_text,
)
from ai_wiki_toolkit.route_traces import load_route_traces
from ai_wiki_toolkit.wiki_schema import build_repo_catalog, load_reuse_events

ROUTE_NOISE_REPORT_SCHEMA_VERSION = "impact-eval-route-noise-report-v1"
ROUTE_COHORT_REPORT_SCHEMA_VERSION = "impact-eval-route-cohort-report-v1"
ROUTE_REPLAY_REPORT_SCHEMA_VERSION = "impact-eval-route-replay-report-v1"
ROUTE_ABLATION_REPORT_SCHEMA_VERSION = "impact-eval-route-ablation-report-v1"
NEUTRAL_REPORT_SCHEMA_VERSION = "impact-eval-neutral-report-v1"
ROUTE_REPLAY_CATALOG_CUTOFF_MODES = {"current", "trace-routed-at"}
CORE_ROUTE_DOC_IDS = {"constraints", "decisions", "workflows"}
RETRIEVAL_EXCLUDED_REASON_TYPES = {"mandatory_contract", "safety_guardrail"}
EVAL_STAGE_SLOT_IDS = {
    "artifact_capture",
    "manifest_or_runner",
    "prompt_design",
    "public_metrics",
    "report_quality",
    "route_usefulness",
    "rubric_scoring",
    "source_incident_timing",
}
ROUTE_ABLATION_VARIANTS = (
    "current",
    "eval_stage_shadow",
    "eval_stage_soft_scoring",
    "stage_compatible_doc_slots",
    "no_eval_bucket_selector",
    "no_reranker",
    "no_route_quality_history",
)

_SESSION_ID_RE = re.compile(
    r"([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})\.jsonl$",
    re.IGNORECASE,
)
_COMMAND_SEPARATORS = {"&&", "||", ";", "|"}


def _now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _read_json_or_empty(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return _read_json(path)


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, str) and item]


def _ordered_unique_string_list(value: Any) -> list[str]:
    return list(dict.fromkeys(_string_list(value)))


def _int_or_none(value: Any) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    return None


def _selection_reason_type_for_doc(
    doc_id: str,
    selection_reason_types: dict[str, Any] | None,
) -> str:
    if selection_reason_types:
        reason_type = selection_reason_types.get(doc_id)
        if isinstance(reason_type, str) and reason_type:
            return reason_type
    if doc_id in CORE_ROUTE_DOC_IDS:
        return "safety_guardrail"
    return "topical_memory"


def _selection_reason_type_counts(
    selected_doc_ids: set[str],
    selection_reason_types: dict[str, Any] | None,
) -> dict[str, int]:
    counts: Counter[str] = Counter()
    for doc_id in selected_doc_ids:
        counts[_selection_reason_type_for_doc(doc_id, selection_reason_types)] += 1
    return dict(sorted(counts.items()))


def _parse_timestamp(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        parsed = datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _repo_wiki_dir(repo_root: Path, repo_wiki_dir: Path | None) -> Path:
    return repo_wiki_dir.resolve() if repo_wiki_dir is not None else repo_root / "ai-wiki"


def _run_index_path(repo_root: Path, repo_wiki_dir: Path) -> Path:
    return repo_wiki_dir / "_toolkit" / "evals" / "runs" / "index.json"


def _load_run_index(repo_root: Path, repo_wiki_dir: Path) -> dict[str, Any]:
    path = _run_index_path(repo_root, repo_wiki_dir)
    payload = _read_json_or_empty(path)
    if payload.get("schema_version") != RUN_INDEX_SCHEMA_VERSION:
        payload = {"schema_version": RUN_INDEX_SCHEMA_VERSION, "runs": []}
    runs = payload.get("runs")
    if not isinstance(runs, list):
        payload["runs"] = []
    payload["path"] = str(path)
    return payload


def _format_metric(value: Any) -> str:
    if isinstance(value, float):
        return f"{value:.3f}"
    if isinstance(value, int):
        return str(value)
    return "-"


def _markdown_table(headers: list[str], rows: list[list[str]]) -> str:
    if not rows:
        return "_No rows._"
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]
    lines.extend("| " + " | ".join(cell.replace("|", "\\|") for cell in row) + " |" for row in rows)
    return "\n".join(lines)


def _aggregate_route_task_types(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    buckets: dict[str, dict[str, Any]] = {}
    for item in items:
        task_type = str(item.get("task_type") or "unknown")
        bucket = buckets.setdefault(
            task_type,
            {
                "task_type": task_type,
                "trace_count": 0,
                "selected_doc_count": 0,
                "selected_useful_doc_count": 0,
                "noisy_selected_doc_count": 0,
                "selected_but_unused_doc_count": 0,
                "missed_useful_doc_count": 0,
            },
        )
        bucket["trace_count"] += 1
        bucket["selected_doc_count"] += int(item.get("selected_doc_count") or 0)
        bucket["selected_useful_doc_count"] += int(item.get("selected_useful_doc_count") or 0)
        bucket["noisy_selected_doc_count"] += int(item.get("noisy_selected_doc_count") or 0)
        bucket["selected_but_unused_doc_count"] += int(
            item.get("selected_but_unused_doc_count") or 0
        )
        missed = item.get("missed_useful_doc_ids")
        bucket["missed_useful_doc_count"] += len(missed) if isinstance(missed, list) else 0

    result: list[dict[str, Any]] = []
    for bucket in buckets.values():
        selected = bucket["selected_doc_count"]
        useful = bucket["selected_useful_doc_count"]
        noisy = bucket["noisy_selected_doc_count"]
        bucket["route_precision"] = useful / selected if selected else None
        bucket["route_noise_rate"] = noisy / selected if selected else None
        result.append(bucket)
    return sorted(
        result,
        key=lambda item: (
            -(item["route_noise_rate"] or 0),
            -item["selected_but_unused_doc_count"],
            item["task_type"],
        ),
    )


def _route_doc_hotspots(items: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    noisy: Counter[str] = Counter()
    not_helpful: Counter[str] = Counter()
    missed: Counter[str] = Counter()
    for item in items:
        noisy.update(str(doc_id) for doc_id in item.get("selected_but_unused_doc_ids", []))
        not_helpful.update(str(doc_id) for doc_id in item.get("selected_not_helpful_doc_ids", []))
        missed.update(str(doc_id) for doc_id in item.get("missed_useful_doc_ids", []))
    noisy_rows = [
        {
            "doc_id": doc_id,
            "selected_but_unused_count": count,
            "selected_not_helpful_count": not_helpful.get(doc_id, 0),
        }
        for doc_id, count in noisy.most_common()
    ]
    missed_rows = [
        {"doc_id": doc_id, "missed_useful_count": count}
        for doc_id, count in missed.most_common()
    ]
    return noisy_rows, missed_rows


def _load_route_cohort_inputs(
    repo_wiki_dir: Path,
    *,
    handle: str,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], int]:
    traces, skipped_trace_lines = load_route_traces(repo_wiki_dir / "metrics" / "route-traces")
    traces = [
        trace
        for trace in traces
        if trace.get("author_handle") == handle or not trace.get("author_handle")
    ]
    legacy_events, legacy_skipped = load_reuse_events(repo_wiki_dir / "metrics" / "reuse-events.jsonl")
    sharded_events, sharded_skipped = load_reuse_events(repo_wiki_dir / "metrics" / "reuse-events")
    events = [
        event
        for event in legacy_events + sharded_events
        if event.get("author_handle") == handle or not event.get("author_handle")
    ]
    return traces, events, skipped_trace_lines + legacy_skipped + sharded_skipped


def _events_by_task(events: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for event in events:
        task_id = event.get("task_id")
        if isinstance(task_id, str) and task_id:
            grouped[task_id].append(event)
    return grouped


def _route_trace_sort_key(trace: dict[str, Any]) -> tuple[datetime, str]:
    return (
        _parse_timestamp(trace.get("routed_at")) or datetime.min.replace(tzinfo=timezone.utc),
        str(trace.get("trace_id") or ""),
    )


def _cohort_trace_item(
    trace: dict[str, Any],
    task_events: list[dict[str, Any]],
) -> dict[str, Any]:
    selection_reason_types = None
    if isinstance(trace.get("selection_reason_types"), dict):
        selection_reason_types = trace.get("selection_reason_types")
    elif isinstance(trace.get("route_selection_reason_types"), dict):
        selection_reason_types = trace.get("route_selection_reason_types")
    candidate_doc_ids = (
        _string_list(trace.get("candidate_doc_ids"))
        if isinstance(trace.get("candidate_doc_ids"), list)
        else None
    )
    metrics = _selection_metrics(
        _string_list(trace.get("selected_doc_ids")),
        task_events,
        selection_reason_types=selection_reason_types,
        maybe_doc_ids=_string_list(trace.get("maybe_load_doc_ids")),
        candidate_doc_ids=candidate_doc_ids,
        packet_words=_int_or_none(trace.get("packet_words")),
    )
    return {
        "trace_id": trace.get("trace_id"),
        "task_id": trace.get("task_id"),
        "task": trace.get("task"),
        "task_type": trace.get("task_type"),
        "routed_at": trace.get("routed_at"),
        **metrics,
        "has_task_text": isinstance(trace.get("task"), str) and bool(str(trace.get("task")).strip()),
    }


def _summarize_cohort_items(items: list[dict[str, Any]]) -> dict[str, Any]:
    task_types = Counter(str(item.get("task_type") or "unknown") for item in items)
    summary = _summarize_metric_dicts(items, trace_count=len(items))
    summary.update(
        {
            "unique_task_id_count": len(
                {item.get("task_id") for item in items if item.get("task_id")}
            ),
            "traces_with_task_text": sum(1 for item in items if item.get("has_task_text")),
            "task_type_counts": dict(sorted(task_types.items())),
        }
    )
    return summary


def _cohort_items_for_traces(
    traces: list[dict[str, Any]],
    events_by_task: dict[str, list[dict[str, Any]]],
    *,
    only_evaluable: bool,
) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for trace in sorted(traces, key=_route_trace_sort_key):
        task_id = trace.get("task_id")
        task_events = events_by_task.get(task_id, []) if isinstance(task_id, str) else []
        if only_evaluable and not task_events:
            continue
        items.append(_cohort_trace_item(trace, task_events))
    return items


def generate_route_cohort_report(
    *,
    post_change_since: str,
    repo_root: Path | None = None,
    repo_wiki_dir: Path | None = None,
    handle: str | None = None,
    target_evaluable_traces: int = 57,
    baseline_evaluable_traces: int = 57,
    only_evaluable: bool = True,
    max_items: int = DEFAULT_DIAGNOSTICS_MAX_ITEMS,
) -> dict[str, Any]:
    """Compare pre-change and post-change route precision cohorts."""

    paths = build_paths(repo_root)
    selected_repo_root = paths.repo_root
    selected_repo_wiki_dir = _repo_wiki_dir(selected_repo_root, repo_wiki_dir)
    selected_handle = handle or resolve_user_handle(selected_repo_root)
    cutoff = _parse_timestamp(post_change_since)
    if cutoff is None:
        raise ValueError("Invalid --post-change-since value. Use an ISO timestamp.")

    traces, events, skipped_lines = _load_route_cohort_inputs(
        selected_repo_wiki_dir,
        handle=selected_handle,
    )
    grouped_events = _events_by_task(events)
    pre_traces = [
        trace
        for trace in traces
        if (parsed := _parse_timestamp(trace.get("routed_at"))) is not None and parsed < cutoff
    ]
    post_traces = [
        trace
        for trace in traces
        if (parsed := _parse_timestamp(trace.get("routed_at"))) is not None and parsed >= cutoff
    ]
    pre_items = _cohort_items_for_traces(
        pre_traces,
        grouped_events,
        only_evaluable=only_evaluable,
    )
    post_items = _cohort_items_for_traces(
        post_traces,
        grouped_events,
        only_evaluable=only_evaluable,
    )
    if baseline_evaluable_traces > 0 and len(pre_items) > baseline_evaluable_traces:
        pre_items = pre_items[-baseline_evaluable_traces:]
    if target_evaluable_traces > 0 and len(post_items) > target_evaluable_traces:
        post_items = post_items[:target_evaluable_traces]

    baseline_summary = _summarize_cohort_items(pre_items)
    post_summary = _summarize_cohort_items(post_items)
    target_remaining = max(0, target_evaluable_traces - int(post_summary["trace_count"]))
    baseline_precision = baseline_summary.get("route_precision")
    post_precision = post_summary.get("route_precision")
    baseline_noise = baseline_summary.get("route_noise_rate")
    post_noise = post_summary.get("route_noise_rate")
    payload: dict[str, Any] = {
        "schema_version": ROUTE_COHORT_REPORT_SCHEMA_VERSION,
        "generated_at": _now_iso(),
        "repo_root": str(selected_repo_root),
        "repo_wiki_dir": str(selected_repo_wiki_dir),
        "filters": {
            "handle": selected_handle,
            "post_change_since": post_change_since,
            "target_evaluable_traces": target_evaluable_traces,
            "baseline_evaluable_traces": baseline_evaluable_traces,
            "only_evaluable": only_evaluable,
            "max_items": max_items,
        },
        "baseline": {
            "summary": baseline_summary,
            "items": pre_items[-max_items:],
        },
        "post_change": {
            "summary": post_summary,
            "items": post_items[:max_items],
        },
        "progress": {
            "target_evaluable_traces": target_evaluable_traces,
            "current_evaluable_traces": post_summary["trace_count"],
            "remaining_evaluable_traces": target_remaining,
            "complete": target_remaining == 0,
        },
        "comparison": {
            "route_precision_delta": (
                post_precision - baseline_precision
                if isinstance(post_precision, float) and isinstance(baseline_precision, float)
                else None
            ),
            "route_noise_delta": (
                post_noise - baseline_noise
                if isinstance(post_noise, float) and isinstance(baseline_noise, float)
                else None
            ),
        },
        "warnings": [
            "Historical route-trace-v1 rows before this change may not include original task text."
        ]
        if any(not item.get("has_task_text") for item in pre_items)
        else [],
        "skipped_lines": skipped_lines,
    }
    return payload


def _route_task_id_from_task(task: str | None) -> str:
    if not task or not task.strip():
        return "current-task"
    return slugify(task)[:80].strip("-") or "current-task"


def _selected_doc_ids_from_packet(packet: dict[str, Any]) -> list[str]:
    maybe_doc_ids = set(_string_list([item.get("doc_id") for item in packet.get("maybe_load", []) if isinstance(item, dict)]))
    selected: list[str] = []
    for item in packet.get("index_cards", []):
        if not isinstance(item, dict):
            continue
        doc_id = item.get("doc_id")
        if isinstance(doc_id, str) and doc_id and doc_id not in maybe_doc_ids:
            selected.append(doc_id)
    return selected


def _packet_doc_field(
    packet: dict[str, Any],
    field: str,
    *,
    selected_doc_ids: list[str],
) -> dict[str, Any]:
    selected = set(selected_doc_ids)
    values: dict[str, Any] = {}
    for section in ("index_cards", "must_load"):
        items = packet.get(section)
        if not isinstance(items, list):
            continue
        for item in items:
            if not isinstance(item, dict):
                continue
            doc_id = item.get("doc_id")
            if not isinstance(doc_id, str) or doc_id not in selected:
                continue
            if field in item:
                values[doc_id] = item[field]
    return values


def _selection_metrics(
    selected_doc_ids: list[str],
    task_events: list[dict[str, Any]],
    selection_reason_types: dict[str, Any] | None = None,
    *,
    maybe_doc_ids: list[str] | None = None,
    candidate_doc_ids: list[str] | None = None,
    packet_words: int | None = None,
) -> dict[str, Any]:
    selected_doc_ids = _ordered_unique_string_list(selected_doc_ids)
    selected = set(selected_doc_ids)
    maybe_doc_ids = _ordered_unique_string_list(maybe_doc_ids or [])
    maybe = set(maybe_doc_ids) - selected
    selected_plus_maybe = selected | maybe
    candidate20_available = candidate_doc_ids is not None
    candidate20_doc_ids = (
        _ordered_unique_string_list(candidate_doc_ids or [])[:20]
        if candidate20_available
        else []
    )
    candidate20 = set(candidate20_doc_ids)
    event_doc_ids = {
        doc_id
        for event in task_events
        if isinstance((doc_id := event.get("doc_id")), str) and doc_id
    }
    useful_doc_ids = {
        str(event["doc_id"])
        for event in task_events
        if event.get("reuse_outcome") in {"resolved", "partial"}
        and isinstance(event.get("doc_id"), str)
    }
    not_helpful_doc_ids = {
        str(event["doc_id"])
        for event in task_events
        if event.get("reuse_outcome") == "not_helpful"
        and isinstance(event.get("doc_id"), str)
    }
    lookup_doc_ids = {
        str(event["doc_id"])
        for event in task_events
        if event.get("retrieval_mode") == "lookup" and isinstance(event.get("doc_id"), str)
    }
    selected_useful_doc_ids = sorted(selected & useful_doc_ids)
    maybe_useful_doc_ids = sorted(maybe & useful_doc_ids)
    selected_plus_maybe_useful_doc_ids = sorted(selected_plus_maybe & useful_doc_ids)
    candidate20_useful_doc_ids = sorted(candidate20 & useful_doc_ids)
    maybe_recovered_doc_ids = sorted((maybe & useful_doc_ids) - selected)
    selected_but_unused_doc_ids = sorted(selected - event_doc_ids)
    selected_not_helpful_doc_ids = sorted((selected & not_helpful_doc_ids) - useful_doc_ids)
    missed_useful_doc_ids = sorted(
        doc_id for doc_id in useful_doc_ids if doc_id in lookup_doc_ids and doc_id not in selected
    )
    reason_type_by_doc = {
        doc_id: _selection_reason_type_for_doc(doc_id, selection_reason_types)
        for doc_id in selected
    }
    retrieval_selected = {
        doc_id
        for doc_id in selected
        if reason_type_by_doc.get(doc_id) not in RETRIEVAL_EXCLUDED_REASON_TYPES
    }
    mandatory_selected = {
        doc_id for doc_id in selected if reason_type_by_doc.get(doc_id) == "mandatory_contract"
    }
    safety_selected = {
        doc_id for doc_id in selected if reason_type_by_doc.get(doc_id) == "safety_guardrail"
    }
    background_selected = {
        doc_id for doc_id in selected if reason_type_by_doc.get(doc_id) == "background_reference"
    }
    core_selected = mandatory_selected | safety_selected
    retrieval_selected_useful_doc_ids = sorted(retrieval_selected & useful_doc_ids)
    retrieval_selected_but_unused_doc_ids = sorted(retrieval_selected - event_doc_ids)
    retrieval_selected_not_helpful_doc_ids = sorted(
        (retrieval_selected & not_helpful_doc_ids) - useful_doc_ids
    )
    mandatory_selected_but_unused_doc_ids = sorted(mandatory_selected - event_doc_ids)
    safety_selected_but_unused_doc_ids = sorted(safety_selected - event_doc_ids)
    core_selected_but_unused_doc_ids = sorted(core_selected - event_doc_ids)
    selected_count = len(selected)
    selected_useful_count = len(selected_useful_doc_ids)
    useful_count = len(useful_doc_ids)
    noisy_count = len(selected - useful_doc_ids)
    retrieval_selected_count = len(retrieval_selected)
    retrieval_selected_useful_count = len(retrieval_selected_useful_doc_ids)
    retrieval_noisy_count = len(retrieval_selected - useful_doc_ids)
    normalized_packet_words = packet_words if isinstance(packet_words, int) and packet_words >= 0 else None
    failed_route_at_selected = bool(useful_doc_ids and not selected_useful_doc_ids)
    failed_route_at_selected_plus_maybe = bool(
        useful_doc_ids and not selected_plus_maybe_useful_doc_ids
    )
    failed_route_at_candidate20 = (
        bool(useful_doc_ids and not candidate20_useful_doc_ids)
        if candidate20_available
        else None
    )
    return {
        "selected_doc_count": selected_count,
        "selected_useful_doc_count": selected_useful_count,
        "useful_doc_count": useful_count,
        "noisy_selected_doc_count": noisy_count,
        "selected_but_unused_doc_count": len(selected_but_unused_doc_ids),
        "selected_not_helpful_doc_count": len(selected_not_helpful_doc_ids),
        "missed_useful_doc_count": len(missed_useful_doc_ids),
        "route_precision": selected_useful_count / selected_count if selected_count else None,
        "route_noise_rate": noisy_count / selected_count if selected_count else None,
        "useful_coverage_at_selected": (
            selected_useful_count / useful_count if useful_count else None
        ),
        "maybe_load_doc_count": len(maybe),
        "maybe_load_useful_doc_count": len(maybe_useful_doc_ids),
        "selected_plus_maybe_doc_count": len(selected_plus_maybe),
        "selected_plus_maybe_useful_doc_count": len(selected_plus_maybe_useful_doc_ids),
        "useful_coverage_at_selected_plus_maybe": (
            len(selected_plus_maybe_useful_doc_ids) / useful_count
            if useful_count
            else None
        ),
        "candidate20_available": candidate20_available,
        "candidate20_doc_count": len(candidate20_doc_ids) if candidate20_available else None,
        "candidate20_useful_doc_count": (
            len(candidate20_useful_doc_ids) if candidate20_available else None
        ),
        "useful_coverage_at_candidate20": (
            len(candidate20_useful_doc_ids) / useful_count
            if candidate20_available and useful_count
            else None
        ),
        "failed_route_at_selected": failed_route_at_selected,
        "failed_route_at_selected_plus_maybe": failed_route_at_selected_plus_maybe,
        "failed_route_at_candidate20": failed_route_at_candidate20,
        "maybe_recovered_doc_count": len(maybe_recovered_doc_ids),
        "maybe_recovered": bool(failed_route_at_selected and maybe_recovered_doc_ids),
        "packet_word_count": normalized_packet_words,
        "retrieval_selected_doc_count": retrieval_selected_count,
        "retrieval_selected_useful_doc_count": retrieval_selected_useful_count,
        "retrieval_selected_but_unused_doc_count": len(retrieval_selected_but_unused_doc_ids),
        "retrieval_selected_not_helpful_doc_count": len(retrieval_selected_not_helpful_doc_ids),
        "retrieval_precision": (
            retrieval_selected_useful_count / retrieval_selected_count
            if retrieval_selected_count
            else None
        ),
        "retrieval_noise_rate": (
            retrieval_noisy_count / retrieval_selected_count
            if retrieval_selected_count
            else None
        ),
        "mandatory_contract_doc_count": len(mandatory_selected),
        "mandatory_contract_but_unused_doc_count": len(mandatory_selected_but_unused_doc_ids),
        "safety_guardrail_doc_count": len(safety_selected),
        "safety_guardrail_but_unused_doc_count": len(safety_selected_but_unused_doc_ids),
        "background_reference_doc_count": len(background_selected),
        "core_doc_count": len(core_selected),
        "core_selected_but_unused_doc_count": len(core_selected_but_unused_doc_ids),
        "selection_reason_type_counts": _selection_reason_type_counts(
            selected,
            selection_reason_types,
        ),
        "selected_doc_ids": sorted(selected),
        "useful_selected_doc_ids": selected_useful_doc_ids,
        "maybe_load_doc_ids": sorted(maybe),
        "maybe_load_useful_doc_ids": maybe_useful_doc_ids,
        "selected_plus_maybe_doc_ids": sorted(selected_plus_maybe),
        "selected_plus_maybe_useful_doc_ids": selected_plus_maybe_useful_doc_ids,
        "candidate20_doc_ids": candidate20_doc_ids,
        "candidate20_useful_doc_ids": candidate20_useful_doc_ids,
        "maybe_recovered_doc_ids": maybe_recovered_doc_ids,
        "selected_but_unused_doc_ids": selected_but_unused_doc_ids,
        "selected_not_helpful_doc_ids": selected_not_helpful_doc_ids,
        "missed_useful_doc_ids": missed_useful_doc_ids,
        "retrieval_selected_doc_ids": sorted(retrieval_selected),
        "retrieval_useful_selected_doc_ids": retrieval_selected_useful_doc_ids,
        "retrieval_selected_but_unused_doc_ids": retrieval_selected_but_unused_doc_ids,
        "retrieval_selected_not_helpful_doc_ids": retrieval_selected_not_helpful_doc_ids,
        "mandatory_contract_doc_ids": sorted(mandatory_selected),
        "mandatory_contract_but_unused_doc_ids": mandatory_selected_but_unused_doc_ids,
        "safety_guardrail_doc_ids": sorted(safety_selected),
        "safety_guardrail_but_unused_doc_ids": safety_selected_but_unused_doc_ids,
        "core_doc_ids": sorted(core_selected),
        "core_selected_but_unused_doc_ids": core_selected_but_unused_doc_ids,
    }


def _catalog_created_at_by_doc_id(repo_wiki_dir: Path) -> dict[str, datetime | None]:
    catalog = build_repo_catalog(repo_wiki_dir)
    result: dict[str, datetime | None] = {}
    for entry in catalog.get("documents", []):
        if not isinstance(entry, dict):
            continue
        doc_id = entry.get("doc_id")
        if not isinstance(doc_id, str) or not doc_id:
            continue
        result[doc_id] = _parse_timestamp(entry.get("created_at"))
    return result


def _selected_catalog_timing(
    *,
    selected_doc_ids: list[str],
    trace_routed_at: datetime | None,
    catalog_created_at_by_doc_id: dict[str, datetime | None],
    route_catalog_cutoff: dict[str, Any],
    mode: str,
) -> dict[str, Any]:
    future_doc_ids: list[str] = []
    unknown_doc_ids: list[str] = []
    for doc_id in sorted(set(selected_doc_ids)):
        created_at = catalog_created_at_by_doc_id.get(doc_id)
        if created_at is None:
            unknown_doc_ids.append(doc_id)
            continue
        if trace_routed_at is not None and created_at > trace_routed_at:
            future_doc_ids.append(doc_id)
    return {
        "mode": mode,
        "cutoff_at": trace_routed_at.isoformat() if trace_routed_at is not None else None,
        "filtered_future_doc_count": int(route_catalog_cutoff.get("filtered_future_doc_count") or 0),
        "filtered_future_doc_ids": _string_list(route_catalog_cutoff.get("filtered_future_doc_ids")),
        "unknown_created_at_doc_count": int(
            route_catalog_cutoff.get("unknown_created_at_doc_count") or 0
        ),
        "selected_future_doc_count": len(future_doc_ids),
        "selected_future_doc_ids": future_doc_ids,
        "selected_unknown_created_at_doc_count": len(unknown_doc_ids),
        "selected_unknown_created_at_doc_ids": unknown_doc_ids,
    }


def _summarize_metric_dicts(metrics_list: list[dict[str, Any]], *, trace_count: int) -> dict[str, Any]:
    selected = 0
    useful_selected = 0
    noisy = 0
    selected_plus_maybe = 0
    selected_plus_maybe_useful = 0
    maybe_load = 0
    maybe_load_useful = 0
    maybe_recovered_docs = 0
    candidate20 = 0
    candidate20_useful = 0
    candidate20_useful_total = 0
    retrieval_selected = 0
    retrieval_useful_selected = 0
    retrieval_noisy = 0
    selected_but_unused = 0
    selected_not_helpful = 0
    retrieval_selected_but_unused = 0
    retrieval_selected_not_helpful = 0
    mandatory_contract = 0
    mandatory_contract_but_unused = 0
    safety_guardrail = 0
    safety_guardrail_but_unused = 0
    background_reference = 0
    core = 0
    core_selected_but_unused = 0
    missed = 0
    useful = 0
    traces_with_useful = 0
    failed_selected = 0
    failed_selected_plus_maybe = 0
    candidate20_evaluable = 0
    failed_candidate20 = 0
    maybe_recovery_opportunities = 0
    maybe_recovered_traces = 0
    packet_word_total = 0
    packet_word_traces = 0
    reason_type_counts: Counter[str] = Counter()
    for metrics in metrics_list:
        selected += int(metrics.get("selected_doc_count") or 0)
        useful_selected += int(metrics.get("selected_useful_doc_count") or 0)
        noisy += int(metrics.get("noisy_selected_doc_count") or 0)
        selected_plus_maybe += int(metrics.get("selected_plus_maybe_doc_count") or 0)
        selected_plus_maybe_useful += int(
            metrics.get("selected_plus_maybe_useful_doc_count") or 0
        )
        maybe_load += int(metrics.get("maybe_load_doc_count") or 0)
        maybe_load_useful += int(metrics.get("maybe_load_useful_doc_count") or 0)
        maybe_recovered_docs += int(metrics.get("maybe_recovered_doc_count") or 0)
        candidate20_count = metrics.get("candidate20_doc_count")
        if isinstance(candidate20_count, int):
            candidate20 += candidate20_count
        candidate20_useful_count = metrics.get("candidate20_useful_doc_count")
        if isinstance(candidate20_useful_count, int):
            candidate20_useful += candidate20_useful_count
        retrieval_selected += int(metrics.get("retrieval_selected_doc_count") or 0)
        retrieval_useful_selected += int(
            metrics.get("retrieval_selected_useful_doc_count") or 0
        )
        retrieval_noisy += (
            int(metrics.get("retrieval_selected_doc_count") or 0)
            - int(metrics.get("retrieval_selected_useful_doc_count") or 0)
        )
        selected_but_unused += int(metrics.get("selected_but_unused_doc_count") or 0)
        selected_not_helpful += int(metrics.get("selected_not_helpful_doc_count") or 0)
        retrieval_selected_but_unused += int(
            metrics.get("retrieval_selected_but_unused_doc_count") or 0
        )
        retrieval_selected_not_helpful += int(
            metrics.get("retrieval_selected_not_helpful_doc_count") or 0
        )
        mandatory_contract += int(metrics.get("mandatory_contract_doc_count") or 0)
        mandatory_contract_but_unused += int(
            metrics.get("mandatory_contract_but_unused_doc_count") or 0
        )
        safety_guardrail += int(metrics.get("safety_guardrail_doc_count") or 0)
        safety_guardrail_but_unused += int(
            metrics.get("safety_guardrail_but_unused_doc_count") or 0
        )
        background_reference += int(metrics.get("background_reference_doc_count") or 0)
        core += int(metrics.get("core_doc_count") or 0)
        core_selected_but_unused += int(
            metrics.get("core_selected_but_unused_doc_count") or 0
        )
        missed += int(metrics.get("missed_useful_doc_count") or 0)
        useful_count = int(metrics.get("useful_doc_count") or 0)
        useful += useful_count
        if useful_count:
            traces_with_useful += 1
            if metrics.get("failed_route_at_selected") is True:
                failed_selected += 1
                maybe_recovery_opportunities += 1
            if metrics.get("failed_route_at_selected_plus_maybe") is True:
                failed_selected_plus_maybe += 1
            if metrics.get("candidate20_available") is True:
                candidate20_evaluable += 1
                candidate20_useful_total += useful_count
                if metrics.get("failed_route_at_candidate20") is True:
                    failed_candidate20 += 1
        if metrics.get("maybe_recovered") is True:
            maybe_recovered_traces += 1
        packet_words = metrics.get("packet_word_count")
        if isinstance(packet_words, int):
            packet_word_total += packet_words
            packet_word_traces += 1
        counts = metrics.get("selection_reason_type_counts")
        if isinstance(counts, dict):
            for reason_type, count in counts.items():
                if isinstance(reason_type, str):
                    reason_type_counts[reason_type] += int(count or 0)
    return {
        "trace_count": trace_count,
        "selected_doc_count": selected,
        "useful_doc_count": useful,
        "selected_useful_doc_count": useful_selected,
        "selected_but_unused_doc_count": selected_but_unused,
        "selected_not_helpful_doc_count": selected_not_helpful,
        "missed_useful_doc_count": missed,
        "route_precision": useful_selected / selected if selected else None,
        "route_noise_rate": noisy / selected if selected else None,
        "useful_coverage_at_selected": useful_selected / useful if useful else None,
        "maybe_load_doc_count": maybe_load,
        "maybe_load_useful_doc_count": maybe_load_useful,
        "selected_plus_maybe_doc_count": selected_plus_maybe,
        "selected_plus_maybe_useful_doc_count": selected_plus_maybe_useful,
        "useful_coverage_at_selected_plus_maybe": (
            selected_plus_maybe_useful / useful if useful else None
        ),
        "candidate20_evaluable_trace_count": candidate20_evaluable,
        "candidate20_doc_count": candidate20,
        "candidate20_useful_doc_count": candidate20_useful,
        "useful_coverage_at_candidate20": (
            candidate20_useful / candidate20_useful_total
            if candidate20_useful_total
            else None
        ),
        "traces_with_useful_doc_count": traces_with_useful,
        "failed_route_at_selected_count": failed_selected,
        "failed_route_at_selected_rate": (
            failed_selected / traces_with_useful if traces_with_useful else None
        ),
        "failed_route_at_selected_plus_maybe_count": failed_selected_plus_maybe,
        "failed_route_at_selected_plus_maybe_rate": (
            failed_selected_plus_maybe / traces_with_useful if traces_with_useful else None
        ),
        "failed_route_at_candidate20_count": failed_candidate20,
        "failed_route_at_candidate20_rate": (
            failed_candidate20 / candidate20_evaluable if candidate20_evaluable else None
        ),
        "maybe_recovered_doc_count": maybe_recovered_docs,
        "maybe_recovery_opportunity_count": maybe_recovery_opportunities,
        "maybe_recovered_trace_count": maybe_recovered_traces,
        "maybe_recovery_rate": (
            maybe_recovered_traces / maybe_recovery_opportunities
            if maybe_recovery_opportunities
            else None
        ),
        "avg_packet_words": (
            packet_word_total / packet_word_traces if packet_word_traces else None
        ),
        "packet_word_trace_count": packet_word_traces,
        "avg_selected_docs": selected / trace_count if trace_count else None,
        "avg_maybe_load_docs": maybe_load / trace_count if trace_count else None,
        "avg_selected_plus_maybe_docs": (
            selected_plus_maybe / trace_count if trace_count else None
        ),
        "avg_candidate20_docs": (
            candidate20 / candidate20_evaluable if candidate20_evaluable else None
        ),
        "retrieval_selected_doc_count": retrieval_selected,
        "retrieval_selected_useful_doc_count": retrieval_useful_selected,
        "retrieval_selected_but_unused_doc_count": retrieval_selected_but_unused,
        "retrieval_selected_not_helpful_doc_count": retrieval_selected_not_helpful,
        "retrieval_precision": (
            retrieval_useful_selected / retrieval_selected
            if retrieval_selected
            else None
        ),
        "retrieval_noise_rate": (
            retrieval_noisy / retrieval_selected if retrieval_selected else None
        ),
        "mandatory_contract_doc_count": mandatory_contract,
        "mandatory_contract_but_unused_doc_count": mandatory_contract_but_unused,
        "safety_guardrail_doc_count": safety_guardrail,
        "safety_guardrail_but_unused_doc_count": safety_guardrail_but_unused,
        "background_reference_doc_count": background_reference,
        "core_doc_count": core,
        "core_selected_but_unused_doc_count": core_selected_but_unused,
        "selection_reason_type_counts": dict(sorted(reason_type_counts.items())),
    }


def _summarize_replay_metrics(items: list[dict[str, Any]], *, key: str) -> dict[str, Any]:
    metric_dicts = [item[key] for item in items if isinstance(item.get(key), dict)]
    return _summarize_metric_dicts(metric_dicts, trace_count=len(items))


def _summarize_replay_catalog_timing(items: list[dict[str, Any]]) -> dict[str, Any]:
    filtered_future = 0
    selected_future = 0
    selected_unknown = 0
    unknown_created_at = 0
    for item in items:
        replay = item.get("replay")
        if not isinstance(replay, dict):
            continue
        timing = replay.get("catalog_cutoff")
        if not isinstance(timing, dict):
            continue
        filtered_future += int(timing.get("filtered_future_doc_count") or 0)
        selected_future += int(timing.get("selected_future_doc_count") or 0)
        selected_unknown += int(timing.get("selected_unknown_created_at_doc_count") or 0)
        unknown_created_at = max(unknown_created_at, int(timing.get("unknown_created_at_doc_count") or 0))
    return {
        "filtered_future_doc_count": filtered_future,
        "selected_future_doc_count": selected_future,
        "selected_unknown_created_at_doc_count": selected_unknown,
        "unknown_created_at_doc_count": unknown_created_at,
    }


def _summarize_replay_item_regressions(items: list[dict[str, Any]]) -> dict[str, Any]:
    precision_regressions = 0
    precision_improvements = 0
    precision_ties = 0
    precision_uncomputed = 0
    noise_regressions = 0
    noise_improvements = 0
    noise_ties = 0
    noise_uncomputed = 0
    for item in items:
        comparison = item.get("comparison")
        if not isinstance(comparison, dict):
            continue
        precision_delta = comparison.get("route_precision_delta")
        if isinstance(precision_delta, int | float) and not isinstance(precision_delta, bool):
            if precision_delta < 0:
                precision_regressions += 1
            elif precision_delta > 0:
                precision_improvements += 1
            else:
                precision_ties += 1
        else:
            precision_uncomputed += 1
        noise_delta = comparison.get("route_noise_delta")
        if isinstance(noise_delta, int | float) and not isinstance(noise_delta, bool):
            if noise_delta > 0:
                noise_regressions += 1
            elif noise_delta < 0:
                noise_improvements += 1
            else:
                noise_ties += 1
        else:
            noise_uncomputed += 1
    return {
        "compared_item_count": len(items),
        "precision_regression_count": precision_regressions,
        "precision_improvement_count": precision_improvements,
        "precision_tie_count": precision_ties,
        "precision_uncomputed_count": precision_uncomputed,
        "noise_regression_count": noise_regressions,
        "noise_improvement_count": noise_improvements,
        "noise_tie_count": noise_ties,
        "noise_uncomputed_count": noise_uncomputed,
    }


def _eval_doc_slots(doc_slots: Any) -> list[str]:
    if not isinstance(doc_slots, list):
        return []
    return [slot for slot in doc_slots if isinstance(slot, str) and slot in EVAL_STAGE_SLOT_IDS]


def _doc_stage_for_task(doc_slots: Any, *, compatible_slots: set[str]) -> str:
    eval_slots = _eval_doc_slots(doc_slots)
    if not eval_slots:
        return "none"
    for slot in eval_slots:
        if slot in compatible_slots:
            return slot
    return eval_slots[0]


def _summarize_eval_stage_confusion(items: list[dict[str, Any]], *, key: str) -> dict[str, Any]:
    matrix: Counter[tuple[str, str]] = Counter()
    off_diagonal: Counter[tuple[str, str]] = Counter()
    compatible_count = 0
    incompatible_count = 0
    stage_active_count = 0
    selected_eval_doc_count = 0
    useful_compatible_count = 0
    useful_incompatible_count = 0
    for item in items:
        metrics = item.get(key)
        if not isinstance(metrics, dict):
            continue
        eval_stage = metrics.get("eval_stage")
        if not isinstance(eval_stage, dict) or not eval_stage.get("active"):
            task_stage = "none"
            compatible_slots: set[str] = set()
        else:
            stage_active_count += 1
            task_stage = str(eval_stage.get("primary") or "unknown")
            compatible_slots = {
                slot
                for slot in eval_stage.get("compatible_doc_slots", [])
                if isinstance(slot, str)
            }
        selected_doc_ids = _string_list(metrics.get("selected_doc_ids"))
        useful_doc_ids = set(_string_list(metrics.get("useful_selected_doc_ids")))
        doc_slots_by_id = metrics.get("doc_slots")
        if not isinstance(doc_slots_by_id, dict):
            doc_slots_by_id = {}
        for doc_id in selected_doc_ids:
            eval_doc_slots = _eval_doc_slots(doc_slots_by_id.get(doc_id))
            doc_stage = _doc_stage_for_task(
                doc_slots_by_id.get(doc_id),
                compatible_slots=compatible_slots,
            )
            matrix[(task_stage, doc_stage)] += 1
            if task_stage == "none" or doc_stage == "none":
                continue
            selected_eval_doc_count += 1
            if set(eval_doc_slots) & compatible_slots:
                compatible_count += 1
                if doc_id in useful_doc_ids:
                    useful_compatible_count += 1
            else:
                incompatible_count += 1
                off_diagonal[(task_stage, doc_stage)] += 1
                if doc_id in useful_doc_ids:
                    useful_incompatible_count += 1

    return {
        "stage_active_trace_count": stage_active_count,
        "selected_eval_doc_count": selected_eval_doc_count,
        "compatible_eval_doc_count": compatible_count,
        "incompatible_eval_doc_count": incompatible_count,
        "useful_compatible_eval_doc_count": useful_compatible_count,
        "useful_incompatible_eval_doc_count": useful_incompatible_count,
        "compatibility_rate": (
            compatible_count / selected_eval_doc_count if selected_eval_doc_count else None
        ),
        "matrix": [
            {
                "task_stage": task_stage,
                "doc_stage": doc_stage,
                "selected_doc_count": count,
            }
            for (task_stage, doc_stage), count in sorted(
                matrix.items(),
                key=lambda item: (-item[1], item[0][0], item[0][1]),
            )
        ],
        "top_off_diagonal": [
            {
                "task_stage": task_stage,
                "doc_stage": doc_stage,
                "selected_doc_count": count,
            }
            for (task_stage, doc_stage), count in sorted(
                off_diagonal.items(),
                key=lambda item: (-item[1], item[0][0], item[0][1]),
            )[:10]
        ],
    }


def _codex_session_id_from_rollout_path(path: Path) -> str | None:
    match = _SESSION_ID_RE.search(path.name)
    return match.group(1) if match else None


def _load_codex_thread_metadata(state_db: Path | None) -> tuple[dict[str, dict[str, Any]], str]:
    if state_db is None:
        return {}, "not_configured"
    selected_db = state_db.expanduser()
    if not selected_db.exists():
        return {}, "missing"
    requested_columns = [
        "id",
        "rollout_path",
        "cwd",
        "title",
        "source",
        "model",
        "git_branch",
        "git_sha",
        "created_at",
        "updated_at",
    ]
    try:
        with sqlite3.connect(selected_db) as connection:
            columns = {
                row[1]
                for row in connection.execute("pragma table_info(threads)").fetchall()
                if len(row) > 1
            }
            selected_columns = [column for column in requested_columns if column in columns]
            if "id" not in selected_columns:
                return {}, "missing_id_column"
            rows = connection.execute(
                f"select {', '.join(selected_columns)} from threads"
            ).fetchall()
    except sqlite3.Error:
        return {}, "sqlite_error"

    metadata: dict[str, dict[str, Any]] = {}
    for row in rows:
        item = dict(zip(selected_columns, row, strict=True))
        title = item.get("title")
        if isinstance(title, str):
            normalized_title = re.sub(r"\s+", " ", title).strip()
            item["title"] = (
                normalized_title
                if len(normalized_title) <= 240
                else normalized_title[:237].rstrip() + "..."
            )
        session_id = item.get("id")
        if isinstance(session_id, str) and session_id:
            metadata[session_id] = item
    return metadata, "loaded"


def _parse_route_command_options(command: str) -> dict[str, Any] | None:
    try:
        tokens = shlex.split(command)
    except ValueError:
        return None

    route_tokens: list[str] | None = None
    for index, token in enumerate(tokens[:-1]):
        if Path(token).name == "aiwiki-toolkit" and tokens[index + 1] == "route":
            route_tokens = tokens[index + 2 :]
            break
    if route_tokens is None:
        return None

    trimmed: list[str] = []
    for token in route_tokens:
        if token in _COMMAND_SEPARATORS:
            break
        trimmed.append(token)

    def option_value(name: str) -> str | None:
        prefix = f"{name}="
        for option_index, option in enumerate(trimmed):
            if option == name and option_index + 1 < len(trimmed):
                return trimmed[option_index + 1]
            if option.startswith(prefix):
                return option[len(prefix) :]
        return None

    changed_paths: list[str] = []
    for option_index, option in enumerate(trimmed):
        if option == "--changed-path" and option_index + 1 < len(trimmed):
            changed_paths.append(trimmed[option_index + 1])
        elif option.startswith("--changed-path="):
            changed_paths.append(option.split("=", 1)[1])

    return {
        "task": option_value("--task"),
        "task_file": option_value("--task-file"),
        "task_id": option_value("--task-id"),
        "changed_paths": [path for path in changed_paths if path],
    }


def _read_task_file_from_command(task_file: str, workdir: str | None) -> str | None:
    task_path = Path(task_file).expanduser()
    if not task_path.is_absolute() and workdir:
        task_path = Path(workdir).expanduser() / task_path
    if not task_path.exists() or not task_path.is_file():
        return None
    try:
        return task_path.read_text(encoding="utf-8")
    except OSError:
        return None


def _extract_route_command_candidate(
    *,
    record: dict[str, Any],
    rollout_path: Path,
    thread_metadata: dict[str, dict[str, Any]],
) -> dict[str, Any] | None:
    payload = record.get("payload")
    if not isinstance(payload, dict):
        return None
    if payload.get("type") != "function_call" or payload.get("name") != "exec_command":
        return None
    raw_arguments = payload.get("arguments")
    if isinstance(raw_arguments, str):
        try:
            arguments = json.loads(raw_arguments)
        except json.JSONDecodeError:
            return None
    elif isinstance(raw_arguments, dict):
        arguments = raw_arguments
    else:
        return None
    command = arguments.get("cmd")
    if not isinstance(command, str) or "aiwiki-toolkit" not in command or " route" not in command:
        return None
    options = _parse_route_command_options(command)
    if options is None:
        return None
    workdir = arguments.get("workdir") if isinstance(arguments.get("workdir"), str) else None
    task = options.get("task")
    task_source = "task"
    if not isinstance(task, str) or not task.strip():
        task_file = options.get("task_file")
        if isinstance(task_file, str) and task_file:
            task = _read_task_file_from_command(task_file, workdir)
            task_source = "task_file" if task else "task_file_unreadable"
    if not isinstance(task, str) or not task.strip():
        return None

    explicit_task_id = options.get("task_id") if isinstance(options.get("task_id"), str) else ""
    task_id = explicit_task_id.strip() if explicit_task_id.strip() else _route_task_id_from_task(task)
    session_id = _codex_session_id_from_rollout_path(rollout_path)
    metadata = thread_metadata.get(session_id or "", {})
    return {
        "task": task.strip(),
        "task_id": task_id,
        "explicit_task_id": explicit_task_id.strip() or None,
        "task_source": task_source,
        "timestamp": record.get("timestamp"),
        "session_id": session_id,
        "rollout_path": str(rollout_path),
        "workdir": workdir,
        "command": command,
        "changed_paths": options.get("changed_paths") if isinstance(options.get("changed_paths"), list) else [],
        "thread": metadata,
    }


def _load_codex_route_command_candidates(
    *,
    sessions_root: Path | None,
    state_db: Path | None,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    selected_sessions_root = (
        sessions_root.expanduser() if sessions_root is not None else Path.home() / ".codex" / "sessions"
    )
    thread_metadata, thread_metadata_status = _load_codex_thread_metadata(state_db)
    scan: dict[str, Any] = {
        "sessions_root": str(selected_sessions_root),
        "state_db": str(state_db.expanduser()) if state_db is not None else None,
        "thread_metadata_status": thread_metadata_status,
        "session_file_count": 0,
        "candidate_count": 0,
        "skipped_json_lines": 0,
    }
    if not selected_sessions_root.exists():
        scan["sessions_status"] = "missing"
        return [], scan

    candidates: list[dict[str, Any]] = []
    for rollout_path in sorted(selected_sessions_root.rglob("rollout-*.jsonl")):
        scan["session_file_count"] += 1
        try:
            lines = rollout_path.read_text(encoding="utf-8").splitlines()
        except OSError:
            continue
        for line in lines:
            if not line.strip():
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                scan["skipped_json_lines"] += 1
                continue
            if not isinstance(record, dict):
                continue
            candidate = _extract_route_command_candidate(
                record=record,
                rollout_path=rollout_path,
                thread_metadata=thread_metadata,
            )
            if candidate is not None:
                candidates.append(candidate)
    scan["sessions_status"] = "loaded"
    scan["candidate_count"] = len(candidates)
    return candidates, scan


def _timestamp_delta_seconds(left: Any, right: Any) -> int | None:
    parsed_left = _parse_timestamp(left)
    parsed_right = _parse_timestamp(right)
    if parsed_left is None or parsed_right is None:
        return None
    return abs(int((parsed_left - parsed_right).total_seconds()))


def _match_route_replay_prompt(
    trace: dict[str, Any],
    candidates_by_task: dict[str, list[dict[str, Any]]],
) -> dict[str, Any]:
    trace_task = trace.get("task")
    if isinstance(trace_task, str) and trace_task.strip():
        return {
            "status": "recovered",
            "confidence": "trace_task",
            "task": trace_task.strip(),
            "task_source": "route_trace",
            "source_session_id": trace.get("source_session_id"),
            "source_rollout_path": trace.get("source_rollout_path"),
            "time_delta_seconds": None,
            "command": None,
            "changed_paths": [],
        }

    task_id = trace.get("task_id")
    if not isinstance(task_id, str) or not task_id:
        return {"status": "unmatched", "reason": "trace_missing_task_id"}

    candidates = candidates_by_task.get(task_id, [])
    if not candidates:
        return {"status": "unmatched", "reason": "no_route_command_with_matching_task_id"}

    source_session_id = trace.get("source_session_id")
    if isinstance(source_session_id, str) and source_session_id:
        session_candidates = [
            candidate for candidate in candidates if candidate.get("session_id") == source_session_id
        ]
        if session_candidates:
            candidates = session_candidates

    source_rollout_path = trace.get("source_rollout_path")
    if isinstance(source_rollout_path, str) and source_rollout_path:
        rollout_candidates = [
            candidate
            for candidate in candidates
            if candidate.get("rollout_path") == source_rollout_path
        ]
        if rollout_candidates:
            candidates = rollout_candidates

    ranked = sorted(
        candidates,
        key=lambda candidate: (
            _timestamp_delta_seconds(trace.get("routed_at"), candidate.get("timestamp")) is None,
            _timestamp_delta_seconds(trace.get("routed_at"), candidate.get("timestamp")) or 10**12,
            str(candidate.get("rollout_path") or ""),
        ),
    )
    selected = ranked[0]
    delta = _timestamp_delta_seconds(trace.get("routed_at"), selected.get("timestamp"))
    if source_session_id and selected.get("session_id") == source_session_id:
        confidence = "exact_session"
    elif isinstance(delta, int) and delta <= 300:
        confidence = "high"
    elif isinstance(delta, int) and delta <= 3600:
        confidence = "medium"
    else:
        confidence = "low"
    return {
        "status": "recovered",
        "confidence": confidence,
        "task": selected.get("task"),
        "task_source": selected.get("task_source"),
        "source_session_id": selected.get("session_id"),
        "source_rollout_path": selected.get("rollout_path"),
        "source_thread_cwd": selected.get("thread", {}).get("cwd")
        if isinstance(selected.get("thread"), dict)
        else None,
        "source_thread_title": selected.get("thread", {}).get("title")
        if isinstance(selected.get("thread"), dict)
        else None,
        "route_command_timestamp": selected.get("timestamp"),
        "time_delta_seconds": delta,
        "command": selected.get("command"),
        "changed_paths": selected.get("changed_paths", []),
        "candidate_count_for_task_id": len(candidates),
    }


def _route_replay_item(
    *,
    trace: dict[str, Any],
    task_events: list[dict[str, Any]],
    match: dict[str, Any],
    repo_root: Path,
    catalog_created_at_by_doc_id: dict[str, datetime | None],
    catalog_cutoff: str,
    max_docs: int,
    rerank_top: int,
    budget_words: int,
    selector_mode: str = "intent_bucket_selector",
    stage_compatible_doc_slots: bool = False,
    eval_stage_scoring_mode: str = "off",
    disable_route_quality_history: bool = False,
) -> dict[str, Any]:
    trace_selection_reason_types = (
        trace.get("selection_reason_types")
        if isinstance(trace.get("selection_reason_types"), dict)
        else trace.get("route_selection_reason_types")
        if isinstance(trace.get("route_selection_reason_types"), dict)
        else None
    )
    trace_candidate_doc_ids = (
        _string_list(trace.get("candidate_doc_ids"))
        if isinstance(trace.get("candidate_doc_ids"), list)
        else None
    )
    baseline_metrics = _selection_metrics(
        _string_list(trace.get("selected_doc_ids")),
        task_events,
        selection_reason_types=trace_selection_reason_types,
        maybe_doc_ids=_string_list(trace.get("maybe_load_doc_ids")),
        candidate_doc_ids=trace_candidate_doc_ids,
        packet_words=_int_or_none(trace.get("packet_words")),
    )
    item: dict[str, Any] = {
        "trace_id": trace.get("trace_id"),
        "task_id": trace.get("task_id"),
        "task_type": trace.get("task_type"),
        "routed_at": trace.get("routed_at"),
        "prompt_recovery": match,
        "baseline": baseline_metrics,
        "replay": None,
        "comparison": {},
    }
    if match.get("status") != "recovered" or not isinstance(match.get("task"), str):
        return item

    trace_routed_at = _parse_timestamp(trace.get("routed_at"))
    replay_catalog_cutoff = trace_routed_at if catalog_cutoff == "trace-routed-at" else None
    result = generate_route_packet(
        task=str(match["task"]),
        task_id=str(trace.get("task_id") or ""),
        changed_paths=_string_list(match.get("changed_paths")),
        budget_words=budget_words,
        max_docs=max_docs,
        rerank_top=rerank_top,
        selector_mode=selector_mode,
        stage_compatible_doc_slots=stage_compatible_doc_slots,
        eval_stage_scoring_mode=eval_stage_scoring_mode,
        disable_route_quality_history=disable_route_quality_history,
        start=repo_root,
        catalog_cutoff=replay_catalog_cutoff,
    )
    selected_doc_ids = _selected_doc_ids_from_packet(result.packet)
    maybe_doc_ids = _string_list(
        [
            item.get("doc_id")
            for item in result.packet.get("maybe_load", [])
            if isinstance(item, dict)
        ]
    )
    routing_strategy = (
        result.packet.get("routing_strategy")
        if isinstance(result.packet.get("routing_strategy"), dict)
        else {}
    )
    candidate_doc_ids = (
        _string_list(routing_strategy.get("candidate_doc_ids"))
        if isinstance(routing_strategy.get("candidate_doc_ids"), list)
        else None
    )
    replay_selection_reason_types = _packet_doc_field(
        result.packet,
        "selection_reason_type",
        selected_doc_ids=selected_doc_ids,
    )
    rendered_packet = render_route_packet_text(result.packet)
    packet_words = len(re.findall(r"\S+", rendered_packet))
    replay_metrics = _selection_metrics(
        selected_doc_ids,
        task_events,
        selection_reason_types=replay_selection_reason_types,
        maybe_doc_ids=maybe_doc_ids,
        candidate_doc_ids=candidate_doc_ids,
        packet_words=packet_words,
    )
    route = result.packet.get("route", {}) if isinstance(result.packet.get("route"), dict) else {}
    route_catalog_cutoff = (
        route.get("catalog_cutoff") if isinstance(route.get("catalog_cutoff"), dict) else {}
    )
    item["replay"] = {
        **replay_metrics,
        "task": match["task"],
        "task_id": result.packet.get("task_id"),
        "task_type": route.get("task_type"),
        "domain_tags": _string_list(route.get("domain_tags")),
        "guardrail_tags": _string_list(route.get("guardrail_tags")),
        "language_signals": route.get("language_signals")
        if isinstance(route.get("language_signals"), dict)
        else {},
        "intent_signals": route.get("intent_signals")
        if isinstance(route.get("intent_signals"), dict)
        else {},
        "mentioned_labels": route.get("mentioned_labels")
        if isinstance(route.get("mentioned_labels"), dict)
        else {},
        "task_type_arbitration": route.get("task_type_arbitration")
        if isinstance(route.get("task_type_arbitration"), dict)
        else {},
        "route_mode": route.get("mode") if isinstance(route.get("mode"), dict) else {},
        "route_self_audit": route.get("route_self_audit")
        if isinstance(route.get("route_self_audit"), dict)
        else {},
        "workflow_contract": route.get("workflow_contract")
        if isinstance(route.get("workflow_contract"), dict)
        else None,
        "eval_stage": route.get("eval_stage")
        if isinstance(route.get("eval_stage"), dict)
        else {},
        "intent_buckets": route.get("intent_buckets")
        if isinstance(route.get("intent_buckets"), list)
        else [],
        "phase_plan": result.packet.get("phase_plan")
        if isinstance(result.packet.get("phase_plan"), dict)
        else {},
        "changed_path_signal_source": route.get("changed_path_signal_source"),
        "changed_path_signal_used": route.get("changed_path_signal_used"),
        "route_quality_adjustments": _packet_doc_field(
            result.packet,
            "route_quality_adjustment",
            selected_doc_ids=selected_doc_ids,
        ),
        "route_quality_signals": _packet_doc_field(
            result.packet,
            "route_quality_signal",
            selected_doc_ids=selected_doc_ids,
        ),
        "multi_signal_adjustments": _packet_doc_field(
            result.packet,
            "multi_signal_adjustment",
            selected_doc_ids=selected_doc_ids,
        ),
        "multi_signals": _packet_doc_field(
            result.packet,
            "multi_signal",
            selected_doc_ids=selected_doc_ids,
        ),
        "applies_when_adjustments": _packet_doc_field(
            result.packet,
            "applies_when_adjustment",
            selected_doc_ids=selected_doc_ids,
        ),
        "applies_when_signals": _packet_doc_field(
            result.packet,
            "applies_when_signal",
            selected_doc_ids=selected_doc_ids,
        ),
        "eval_stage_adjustments": _packet_doc_field(
            result.packet,
            "eval_stage_adjustment",
            selected_doc_ids=selected_doc_ids,
        ),
        "eval_stage_signals": _packet_doc_field(
            result.packet,
            "eval_stage_signal",
            selected_doc_ids=selected_doc_ids,
        ),
        "doc_slots": _packet_doc_field(
            result.packet,
            "doc_slots",
            selected_doc_ids=selected_doc_ids,
        ),
        "selection_reason_types": replay_selection_reason_types,
        "reranker": result.packet.get("routing_strategy", {}).get("reranker")
        if isinstance(result.packet.get("routing_strategy"), dict)
        else None,
        "selector": result.packet.get("routing_strategy", {}).get("selector")
        if isinstance(result.packet.get("routing_strategy"), dict)
        else None,
        "catalog_cutoff": _selected_catalog_timing(
            selected_doc_ids=selected_doc_ids,
            trace_routed_at=trace_routed_at,
            catalog_created_at_by_doc_id=catalog_created_at_by_doc_id,
            route_catalog_cutoff=route_catalog_cutoff,
            mode=catalog_cutoff,
        ),
        "packet_words": packet_words,
    }
    baseline_precision = baseline_metrics.get("route_precision")
    replay_precision = replay_metrics.get("route_precision")
    baseline_noise = baseline_metrics.get("route_noise_rate")
    replay_noise = replay_metrics.get("route_noise_rate")
    item["comparison"] = {
        "route_precision_delta": (
            replay_precision - baseline_precision
            if isinstance(replay_precision, float) and isinstance(baseline_precision, float)
            else None
        ),
        "route_noise_delta": (
            replay_noise - baseline_noise
            if isinstance(replay_noise, float) and isinstance(baseline_noise, float)
            else None
        ),
        "selected_doc_count_delta": int(replay_metrics.get("selected_doc_count") or 0)
        - int(baseline_metrics.get("selected_doc_count") or 0),
    }
    return item


def generate_route_replay_report(
    *,
    repo_root: Path | None = None,
    repo_wiki_dir: Path | None = None,
    handle: str | None = None,
    before: str | None = None,
    catalog_cutoff: str = "current",
    target_evaluable_traces: int = 57,
    codex_sessions_root: Path | None = None,
    codex_state_db: Path | None = None,
    max_docs: int = 6,
    rerank_top: int = DEFAULT_ROUTE_RERANK_TOP,
    budget_words: int = DEFAULT_ROUTE_SAFETY_CAP_WORDS,
    selector_mode: str = "intent_bucket_selector",
    stage_compatible_doc_slots: bool = False,
    eval_stage_scoring_mode: str = "off",
    disable_route_quality_history: bool = False,
    max_items: int = DEFAULT_DIAGNOSTICS_MAX_ITEMS,
) -> dict[str, Any]:
    """Replay historical route prompts through the current router."""

    paths = build_paths(repo_root)
    selected_repo_root = paths.repo_root
    selected_repo_wiki_dir = _repo_wiki_dir(selected_repo_root, repo_wiki_dir)
    selected_handle = handle or resolve_user_handle(selected_repo_root)
    cutoff = _parse_timestamp(before) if before else None
    if before and cutoff is None:
        raise ValueError("Invalid --before value. Use an ISO timestamp.")
    normalized_catalog_cutoff = catalog_cutoff.strip().lower()
    if normalized_catalog_cutoff not in ROUTE_REPLAY_CATALOG_CUTOFF_MODES:
        raise ValueError("Invalid --catalog-cutoff. Expected one of: current, trace-routed-at.")

    traces, events, skipped_lines = _load_route_cohort_inputs(
        selected_repo_wiki_dir,
        handle=selected_handle,
    )
    grouped_events = _events_by_task(events)
    evaluable_traces = [
        trace
        for trace in sorted(traces, key=_route_trace_sort_key)
        if isinstance(trace.get("task_id"), str)
        and grouped_events.get(trace.get("task_id"))
        and (
            cutoff is None
            or (
                (parsed := _parse_timestamp(trace.get("routed_at"))) is not None
                and parsed < cutoff
            )
        )
    ]
    if target_evaluable_traces > 0 and len(evaluable_traces) > target_evaluable_traces:
        evaluable_traces = evaluable_traces[-target_evaluable_traces:]

    selected_state_db = codex_state_db if codex_state_db is not None else Path.home() / ".codex" / "state_5.sqlite"
    candidates, scan = _load_codex_route_command_candidates(
        sessions_root=codex_sessions_root,
        state_db=selected_state_db,
    )
    candidates_by_task: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for candidate in candidates:
        task_id = candidate.get("task_id")
        if isinstance(task_id, str) and task_id:
            candidates_by_task[task_id].append(candidate)
    catalog_created_at_by_doc_id = _catalog_created_at_by_doc_id(selected_repo_wiki_dir)

    items: list[dict[str, Any]] = []
    unmatched: list[dict[str, Any]] = []
    for trace in evaluable_traces:
        match = _match_route_replay_prompt(trace, candidates_by_task)
        if match.get("status") != "recovered":
            unmatched.append(
                {
                    "trace_id": trace.get("trace_id"),
                    "task_id": trace.get("task_id"),
                    "routed_at": trace.get("routed_at"),
                    "reason": match.get("reason"),
                }
            )
            continue
        item = _route_replay_item(
            trace=trace,
            task_events=grouped_events.get(trace.get("task_id"), []),
            match=match,
            repo_root=selected_repo_root,
            catalog_created_at_by_doc_id=catalog_created_at_by_doc_id,
            catalog_cutoff=normalized_catalog_cutoff,
            max_docs=max_docs,
            rerank_top=rerank_top,
            budget_words=budget_words,
            selector_mode=selector_mode,
            stage_compatible_doc_slots=stage_compatible_doc_slots,
            eval_stage_scoring_mode=eval_stage_scoring_mode,
            disable_route_quality_history=disable_route_quality_history,
        )
        items.append(item)

    replayed_items = [item for item in items if isinstance(item.get("replay"), dict)]
    baseline_summary = _summarize_replay_metrics(replayed_items, key="baseline")
    replay_summary = _summarize_replay_metrics(replayed_items, key="replay")
    catalog_timing_summary = _summarize_replay_catalog_timing(replayed_items)
    item_regression_summary = _summarize_replay_item_regressions(replayed_items)
    eval_stage_confusion = _summarize_eval_stage_confusion(replayed_items, key="replay")
    baseline_precision = baseline_summary.get("route_precision")
    replay_precision = replay_summary.get("route_precision")
    baseline_noise = baseline_summary.get("route_noise_rate")
    replay_noise = replay_summary.get("route_noise_rate")
    confidence_counts = Counter(
        str(item.get("prompt_recovery", {}).get("confidence") or "unknown") for item in items
    )
    payload: dict[str, Any] = {
        "schema_version": ROUTE_REPLAY_REPORT_SCHEMA_VERSION,
        "generated_at": _now_iso(),
        "repo_root": str(selected_repo_root),
        "repo_wiki_dir": str(selected_repo_wiki_dir),
        "filters": {
            "handle": selected_handle,
            "before": before,
            "catalog_cutoff": normalized_catalog_cutoff,
            "target_evaluable_traces": target_evaluable_traces,
            "max_docs": max_docs,
            "rerank_top": rerank_top,
            "budget_words": budget_words,
            "selector_mode": selector_mode,
            "stage_compatible_doc_slots": stage_compatible_doc_slots,
            "eval_stage_scoring_mode": eval_stage_scoring_mode,
            "disable_route_quality_history": disable_route_quality_history,
            "max_items": max_items,
        },
        "replay_policy": {
            "router": "current working tree route scorer",
            "task_text_source": "route trace task text when present, otherwise local Codex session command recovery",
            "changed_path_policy": (
                "Use only explicit --changed-path values recovered from the original route command; "
                "do not replay old implicit git-status changed_paths from route traces."
            ),
            "catalog_cutoff_policy": (
                "Use the current catalog for projection."
                if normalized_catalog_cutoff == "current"
                else "Filter known future docs using each trace routed_at timestamp; retain docs without created_at and report them separately."
            ),
            "causal_claim": "retrospective projection, not a post-change production cohort",
        },
        "prompt_recovery": {
            "target_trace_count": len(evaluable_traces),
            "recovered_trace_count": len(items),
            "replayed_trace_count": len(replayed_items),
            "unmatched_trace_count": len(unmatched),
            "confidence_counts": dict(sorted(confidence_counts.items())),
            "scan": scan,
            "unmatched": unmatched[:max_items],
        },
        "baseline": {
            "summary": baseline_summary,
        },
        "replay": {
            "summary": replay_summary,
        },
        "catalog_timing": catalog_timing_summary,
        "item_regression_summary": item_regression_summary,
        "eval_stage_confusion": eval_stage_confusion,
        "comparison": {
            "route_precision_delta": (
                replay_precision - baseline_precision
                if isinstance(replay_precision, float) and isinstance(baseline_precision, float)
                else None
            ),
            "route_noise_delta": (
                replay_noise - baseline_noise
                if isinstance(replay_noise, float) and isinstance(baseline_noise, float)
                else None
            ),
        },
        "items": items[:max_items],
        "skipped_lines": skipped_lines,
        "warnings": [
            "Historical replay is approximate when prompt recovery confidence is not exact_session or trace_task.",
            "Use the route-noise cohort report for forward-looking post-change production evidence.",
        ],
    }
    return payload


def _route_ablation_options(variant: str, *, rerank_top: int) -> dict[str, Any]:
    if variant == "current":
        return {
            "selector_mode": "intent_bucket_selector",
            "stage_compatible_doc_slots": False,
            "eval_stage_scoring_mode": "off",
            "disable_route_quality_history": False,
            "rerank_top": rerank_top,
            "description": "Current working-tree router.",
        }
    if variant == "eval_stage_shadow":
        return {
            "selector_mode": "intent_bucket_selector",
            "stage_compatible_doc_slots": False,
            "eval_stage_scoring_mode": "off",
            "disable_route_quality_history": False,
            "rerank_top": rerank_top,
            "description": "Current router with eval_stage diagnostics observed but not enforced.",
        }
    if variant == "eval_stage_soft_scoring":
        return {
            "selector_mode": "intent_bucket_selector",
            "stage_compatible_doc_slots": False,
            "eval_stage_scoring_mode": "soft",
            "disable_route_quality_history": False,
            "rerank_top": rerank_top,
            "description": "Use eval_stage as soft scoring, tie-breaker, and maybe-load boundary.",
        }
    if variant == "stage_compatible_doc_slots":
        return {
            "selector_mode": "intent_bucket_selector",
            "stage_compatible_doc_slots": True,
            "eval_stage_scoring_mode": "off",
            "disable_route_quality_history": False,
            "rerank_top": rerank_top,
            "description": "Require selected eval docs to match the task eval_stage compatible slots.",
        }
    if variant == "no_eval_bucket_selector":
        return {
            "selector_mode": "flat_top_k",
            "stage_compatible_doc_slots": False,
            "eval_stage_scoring_mode": "off",
            "disable_route_quality_history": False,
            "rerank_top": rerank_top,
            "description": "Disable intent bucket coverage and select flat top-k scored docs.",
        }
    if variant == "no_reranker":
        return {
            "selector_mode": "intent_bucket_selector",
            "stage_compatible_doc_slots": False,
            "eval_stage_scoring_mode": "off",
            "disable_route_quality_history": False,
            "rerank_top": 0,
            "description": "Disable deterministic index-card reranker.",
        }
    if variant == "no_route_quality_history":
        return {
            "selector_mode": "intent_bucket_selector",
            "stage_compatible_doc_slots": False,
            "eval_stage_scoring_mode": "off",
            "disable_route_quality_history": True,
            "rerank_top": rerank_top,
            "description": "Disable route-quality history bonuses and penalties.",
        }
    raise ValueError(f"Unknown route ablation variant: {variant}")


def _replay_summary_for_ablation(report: dict[str, Any]) -> dict[str, Any]:
    replay = report.get("replay", {}).get("summary", {})
    baseline = report.get("baseline", {}).get("summary", {})
    comparison = report.get("comparison", {})
    regressions = report.get("item_regression_summary", {})
    confusion = report.get("eval_stage_confusion", {})
    recovery = report.get("prompt_recovery", {})
    return {
        "replayed_trace_count": recovery.get("replayed_trace_count"),
        "route_precision": replay.get("route_precision"),
        "route_noise_rate": replay.get("route_noise_rate"),
        "retrieval_precision": replay.get("retrieval_precision"),
        "failed_route_at_selected_rate": replay.get("failed_route_at_selected_rate"),
        "failed_route_at_selected_plus_maybe_rate": replay.get(
            "failed_route_at_selected_plus_maybe_rate"
        ),
        "failed_route_at_candidate20_rate": replay.get("failed_route_at_candidate20_rate"),
        "maybe_recovery_rate": replay.get("maybe_recovery_rate"),
        "useful_coverage_at_selected": replay.get("useful_coverage_at_selected"),
        "useful_coverage_at_selected_plus_maybe": replay.get(
            "useful_coverage_at_selected_plus_maybe"
        ),
        "useful_coverage_at_candidate20": replay.get("useful_coverage_at_candidate20"),
        "avg_packet_words": replay.get("avg_packet_words"),
        "avg_selected_plus_maybe_docs": replay.get("avg_selected_plus_maybe_docs"),
        "avg_candidate20_docs": replay.get("avg_candidate20_docs"),
        "selected_doc_count": replay.get("selected_doc_count"),
        "selected_plus_maybe_doc_count": replay.get("selected_plus_maybe_doc_count"),
        "selected_useful_doc_count": replay.get("selected_useful_doc_count"),
        "selected_plus_maybe_useful_doc_count": replay.get(
            "selected_plus_maybe_useful_doc_count"
        ),
        "missed_useful_doc_count": replay.get("missed_useful_doc_count"),
        "retrieval_selected_doc_count": replay.get("retrieval_selected_doc_count"),
        "retrieval_selected_useful_doc_count": replay.get("retrieval_selected_useful_doc_count"),
        "core_doc_count": replay.get("core_doc_count"),
        "core_selected_but_unused_doc_count": replay.get("core_selected_but_unused_doc_count"),
        "baseline_route_precision": baseline.get("route_precision"),
        "baseline_retrieval_precision": baseline.get("retrieval_precision"),
        "baseline_failed_route_at_selected_plus_maybe_rate": baseline.get(
            "failed_route_at_selected_plus_maybe_rate"
        ),
        "route_precision_delta_vs_baseline": comparison.get("route_precision_delta"),
        "route_noise_delta_vs_baseline": comparison.get("route_noise_delta"),
        "selected_useful_delta_vs_baseline": (
            int(replay.get("selected_useful_doc_count") or 0)
            - int(baseline.get("selected_useful_doc_count") or 0)
        ),
        "missed_useful_delta_vs_baseline": (
            int(replay.get("missed_useful_doc_count") or 0)
            - int(baseline.get("missed_useful_doc_count") or 0)
        ),
        "precision_regression_count": regressions.get("precision_regression_count"),
        "noise_regression_count": regressions.get("noise_regression_count"),
        "eval_stage_compatibility_rate": confusion.get("compatibility_rate"),
        "eval_stage_incompatible_doc_count": confusion.get("incompatible_eval_doc_count"),
        "eval_stage_top_off_diagonal": confusion.get("top_off_diagonal", [])[:5]
        if isinstance(confusion.get("top_off_diagonal"), list)
        else [],
    }


def _metric_delta(value: Any, baseline: Any) -> float | int | None:
    if isinstance(value, bool) or isinstance(baseline, bool):
        return None
    if isinstance(value, int | float) and isinstance(baseline, int | float):
        return value - baseline
    return None


def generate_route_ablation_report(
    *,
    repo_root: Path | None = None,
    repo_wiki_dir: Path | None = None,
    handle: str | None = None,
    before: str | None = None,
    catalog_cutoff: str = "trace-routed-at",
    target_evaluable_traces: int = 57,
    codex_sessions_root: Path | None = None,
    codex_state_db: Path | None = None,
    max_docs: int = 6,
    rerank_top: int = DEFAULT_ROUTE_RERANK_TOP,
    budget_words: int = DEFAULT_ROUTE_SAFETY_CAP_WORDS,
    variants: tuple[str, ...] = ROUTE_ABLATION_VARIANTS,
    max_items: int = DEFAULT_DIAGNOSTICS_MAX_ITEMS,
) -> dict[str, Any]:
    """Run route ablation variants over the same replay cohort."""

    selected_variants = tuple(variants) if variants else ROUTE_ABLATION_VARIANTS
    reports: dict[str, dict[str, Any]] = {}
    variant_rows: list[dict[str, Any]] = []
    for variant in selected_variants:
        options = _route_ablation_options(variant, rerank_top=rerank_top)
        report = generate_route_replay_report(
            repo_root=repo_root,
            repo_wiki_dir=repo_wiki_dir,
            handle=handle,
            before=before,
            catalog_cutoff=catalog_cutoff,
            target_evaluable_traces=target_evaluable_traces,
            codex_sessions_root=codex_sessions_root,
            codex_state_db=codex_state_db,
            max_docs=max_docs,
            rerank_top=int(options["rerank_top"]),
            budget_words=budget_words,
            selector_mode=str(options["selector_mode"]),
            stage_compatible_doc_slots=bool(options["stage_compatible_doc_slots"]),
            eval_stage_scoring_mode=str(options["eval_stage_scoring_mode"]),
            disable_route_quality_history=bool(options["disable_route_quality_history"]),
            max_items=max_items,
        )
        reports[variant] = report
        summary = _replay_summary_for_ablation(report)
        variant_rows.append(
            {
                "variant": variant,
                "description": options["description"],
                "options": {
                    key: value
                    for key, value in options.items()
                    if key != "description"
                },
                **summary,
            }
        )

    current = next((row for row in variant_rows if row["variant"] == "current"), None)
    if current:
        for row in variant_rows:
            row["retrieval_precision_delta_vs_current"] = _metric_delta(
                row.get("retrieval_precision"),
                current.get("retrieval_precision"),
            )
            row["failed_route_at_selected_plus_maybe_delta_vs_current"] = _metric_delta(
                row.get("failed_route_at_selected_plus_maybe_rate"),
                current.get("failed_route_at_selected_plus_maybe_rate"),
            )
            row["maybe_recovery_rate_delta_vs_current"] = _metric_delta(
                row.get("maybe_recovery_rate"),
                current.get("maybe_recovery_rate"),
            )
            row["useful_coverage_at_selected_plus_maybe_delta_vs_current"] = _metric_delta(
                row.get("useful_coverage_at_selected_plus_maybe"),
                current.get("useful_coverage_at_selected_plus_maybe"),
            )
            row["selected_useful_delta_vs_current"] = _metric_delta(
                row.get("selected_useful_doc_count"),
                current.get("selected_useful_doc_count"),
            )
            row["missed_useful_delta_vs_current"] = _metric_delta(
                row.get("missed_useful_doc_count"),
                current.get("missed_useful_doc_count"),
            )
            row["eval_stage_incompatible_delta_vs_current"] = _metric_delta(
                row.get("eval_stage_incompatible_doc_count"),
                current.get("eval_stage_incompatible_doc_count"),
            )

    best_retrieval = sorted(
        variant_rows,
        key=lambda row: (
            float(row.get("failed_route_at_selected_plus_maybe_rate"))
            if isinstance(row.get("failed_route_at_selected_plus_maybe_rate"), int | float)
            and not isinstance(row.get("failed_route_at_selected_plus_maybe_rate"), bool)
            else 1.0,
            -float(row.get("retrieval_precision") or -1),
            -int(row.get("selected_useful_doc_count") or 0),
            int(row.get("missed_useful_doc_count") or 0),
            str(row.get("variant")),
        ),
    )[0] if variant_rows else None
    activation = {
        "status": "blocked",
        "reason": "Ablation is diagnostic only; activation requires non-regressing replay plus behavior tests.",
        "recommended_next_step": (
            "Prioritize eval-stage selector if it improves retrieval precision without losing useful docs; "
            "otherwise inspect the largest off-diagonal stage pairs."
        ),
        "best_retrieval_variant": best_retrieval.get("variant") if best_retrieval else None,
    }
    if current and best_retrieval and best_retrieval.get("variant") != "current":
        activation["candidate_signal"] = {
            "variant": best_retrieval.get("variant"),
            "retrieval_precision_delta_vs_current": best_retrieval.get(
                "retrieval_precision_delta_vs_current"
            ),
            "failed_route_at_selected_plus_maybe_delta_vs_current": best_retrieval.get(
                "failed_route_at_selected_plus_maybe_delta_vs_current"
            ),
            "maybe_recovery_rate_delta_vs_current": best_retrieval.get(
                "maybe_recovery_rate_delta_vs_current"
            ),
            "selected_useful_delta_vs_current": best_retrieval.get(
                "selected_useful_delta_vs_current"
            ),
            "missed_useful_delta_vs_current": best_retrieval.get(
                "missed_useful_delta_vs_current"
            ),
        }

    first_report = reports.get(selected_variants[0], {}) if selected_variants else {}
    return {
        "schema_version": ROUTE_ABLATION_REPORT_SCHEMA_VERSION,
        "generated_at": _now_iso(),
        "repo_root": first_report.get("repo_root"),
        "repo_wiki_dir": first_report.get("repo_wiki_dir"),
        "filters": {
            "handle": handle,
            "before": before,
            "catalog_cutoff": catalog_cutoff,
            "target_evaluable_traces": target_evaluable_traces,
            "max_docs": max_docs,
            "rerank_top": rerank_top,
            "budget_words": budget_words,
            "variants": list(selected_variants),
            "max_items": max_items,
        },
        "variant_summaries": variant_rows,
        "reports": reports,
        "activation": activation,
        "warnings": [
            "Ablation variants are retrospective projections over recovered route prompts.",
            "Do not activate a selector change from ablation alone; combine with behavior tests.",
        ],
    }


def generate_route_noise_report(
    *,
    repo_root: Path | None = None,
    repo_wiki_dir: Path | None = None,
    handle: str | None = None,
    since: str | None = DEFAULT_REPO_EVALUATION_SINCE,
    max_items: int = DEFAULT_DIAGNOSTICS_MAX_ITEMS,
) -> dict[str, Any]:
    """Generate a focused route precision/noise report from route traces."""

    paths = build_paths(repo_root)
    selected_repo_root = paths.repo_root
    selected_repo_wiki_dir = _repo_wiki_dir(selected_repo_root, repo_wiki_dir)
    selected_handle = handle or resolve_user_handle(selected_repo_root)
    scan_max_items = max(max_items, 500)
    diagnostics = build_memory_diagnostics_report(
        selected_repo_wiki_dir,
        handle=selected_handle,
        since=since,
        focus="route",
        max_items=scan_max_items,
    )
    route = diagnostics.get("route_diagnostics", {})
    items = route.get("items") if isinstance(route, dict) else []
    if not isinstance(items, list):
        items = []
    noisy_docs, missed_docs = _route_doc_hotspots(items)
    top_noisy_traces = sorted(
        items,
        key=lambda item: (
            -(item.get("route_noise_rate") or 0),
            -int(item.get("selected_but_unused_doc_count") or 0),
            str(item.get("task_id") or ""),
        ),
    )[:max_items]
    payload: dict[str, Any] = {
        "schema_version": ROUTE_NOISE_REPORT_SCHEMA_VERSION,
        "generated_at": _now_iso(),
        "repo_root": str(selected_repo_root),
        "repo_wiki_dir": str(selected_repo_wiki_dir),
        "filters": {
            "handle": selected_handle,
            "since": since,
            "max_items": max_items,
            "scan_max_items": scan_max_items,
        },
        "summary": route.get("summary", {}) if isinstance(route, dict) else {},
        "task_type_summary": _aggregate_route_task_types(items)[:max_items],
        "top_noisy_traces": top_noisy_traces,
        "noisy_doc_hotspots": noisy_docs[:max_items],
        "missed_doc_hotspots": missed_docs[:max_items],
        "recommendations": [
            "Review task types with high selected-but-unused counts before adding more memory.",
            "Add or refine route hints for repeated missed useful docs.",
            "Demote or narrow docs repeatedly selected without downstream reuse.",
            "Treat recall as a proxy; useful docs that were never looked up remain unknown.",
        ],
    }
    return payload


def _parse_datetime(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None


def _duration_seconds(started_at: Any, finished_at: Any) -> int | None:
    started = _parse_datetime(started_at)
    finished = _parse_datetime(finished_at)
    if started is None or finished is None:
        return None
    return max(0, int((finished - started).total_seconds()))


def _load_slot_command_results(run_dir: Path) -> dict[tuple[str, str], dict[str, Any]]:
    path = run_dir / "slot_command_results.json"
    payload = _read_json_or_empty(path)
    rows = payload.get("results")
    if not isinstance(rows, list):
        return {}
    result: dict[tuple[str, str], dict[str, Any]] = {}
    for row in rows:
        if not isinstance(row, dict):
            continue
        slot = row.get("slot")
        prompt_level = row.get("prompt_level")
        if not isinstance(slot, str) or not isinstance(prompt_level, str):
            continue
        enriched = dict(row)
        enriched["duration_seconds"] = _duration_seconds(
            row.get("started_at"),
            row.get("finished_at"),
        )
        enriched["heartbeat_present"] = any(
            key in row for key in ("heartbeat", "heartbeats", "last_heartbeat_at")
        )
        result[(slot, prompt_level)] = enriched
    return result


def _load_rubric_judgment_summary(run_dir: Path, *, slot: str, prompt_level: str) -> dict[str, Any] | None:
    path = run_dir / slot / prompt_level / "rubric_judgment.json"
    if not path.exists():
        return None
    payload = _read_json(path)
    criteria = payload.get("criteria")
    if not isinstance(criteria, dict):
        criteria = {}
    groups: dict[str, dict[str, int]] = {}
    for label, rows in criteria.items():
        if not isinstance(rows, list):
            continue
        matched = sum(1 for row in rows if isinstance(row, dict) and row.get("matched") is True)
        groups[str(label)] = {"matched": matched, "total": len(rows)}
    return {
        "path": str(path),
        "label": payload.get("label"),
        "criteria": groups,
    }


def _score_rank(label: Any) -> int | None:
    if label == "success":
        return 2
    if label == "partial":
        return 1
    if label == "fail":
        return 0
    return None


def _neutral_reason(primary_rows: list[dict[str, Any]]) -> str:
    labels = [row.get("score_label") for row in primary_rows if row.get("score_label")]
    if len(labels) < 2:
        return "primary_scores_missing"
    if all(label == "success" for label in labels):
        return "baseline_also_success"
    if len(set(labels)) == 1:
        return f"same_primary_score_{labels[0]}"
    ranks = [_score_rank(label) for label in labels]
    if all(rank is not None for rank in ranks) and len(set(ranks)) == 1:
        return "same_primary_score"
    return "neutral_by_aggregate_metrics"


def _primary_variant_names(report_dict: dict[str, Any]) -> set[str]:
    primary = report_dict.get("primary_comparison")
    if not isinstance(primary, dict):
        return set()
    return {
        value
        for value in (
            primary.get("no_aiwiki_variant"),
            primary.get("aiwiki_variant"),
        )
        if isinstance(value, str) and value
    }


def _family_neutral_item(run_index_item: dict[str, Any]) -> dict[str, Any]:
    run_dir_value = run_index_item.get("run_dir")
    family = str(run_index_item.get("family") or "unknown")
    run_dir = Path(run_dir_value).resolve() if isinstance(run_dir_value, str) else None
    base: dict[str, Any] = {
        "family": family,
        "period_id": run_index_item.get("period_id"),
        "run_dir": str(run_dir) if run_dir is not None else None,
        "score_policy": run_index_item.get("score_policy"),
        "runner_success": run_index_item.get("runner_success"),
        "artifact_status": "ok",
        "primary_comparison": {
            "outcome": run_index_item.get("primary_outcome"),
            "first_attempt_success_delta": run_index_item.get("first_attempt_success_delta"),
            "avg_score_delta": run_index_item.get("avg_score_delta"),
        },
        "neutral_reason": "not_analyzed",
        "primary_slot_records": [],
        "slot_records": [],
        "observability": {},
        "warnings": [],
    }
    if run_dir is None or not run_dir.exists():
        base["artifact_status"] = "run_dir_missing"
        base["warnings"].append("Run directory is missing; slot-level neutral analysis is unavailable.")
        return base

    report = generate_impact_eval_report(run_dir)
    report_dict = impact_eval_report_to_dict(report)
    base["primary_comparison"] = report_dict["primary_comparison"]
    slot_results = _load_slot_command_results(run_dir)
    primary_variants = _primary_variant_names(report_dict)
    rows: list[dict[str, Any]] = []
    for record in report.records:
        slot_result = slot_results.get((record.slot, record.prompt_level), {})
        row = {
            "slot": record.slot,
            "variant": record.variant,
            "prompt_level": record.prompt_level,
            "phase": record.phase,
            "is_primary_variant": record.variant in primary_variants,
            "score_label": record.score_label,
            "first_attempt_success": record.first_attempt_success,
            "attempt": record.attempt,
            "human_nudges": record.human_nudges,
            "changed_file_count": len(record.changed_files),
            "untracked_file_count": len(record.untracked_files),
            "project_changed_file_count": len(record.project_changed_files),
            "managed_wiki_changed_file_count": len(record.managed_wiki_changed_files),
            "user_wiki_changed_file_count": len(record.user_wiki_changed_files),
            "user_wiki_untracked_file_count": len(record.user_wiki_untracked_files),
            "duration_seconds": slot_result.get("duration_seconds"),
            "started_at": slot_result.get("started_at"),
            "finished_at": slot_result.get("finished_at"),
            "codex_returncode": slot_result.get("codex_returncode"),
            "save_result_returncode": slot_result.get("save_result_returncode"),
            "heartbeat_present": bool(slot_result.get("heartbeat_present")),
            "rubric_judgment": _load_rubric_judgment_summary(
                run_dir,
                slot=record.slot,
                prompt_level=record.prompt_level,
            ),
            "result_path": str(record.result_path),
        }
        rows.append(row)
    primary_rows = [row for row in rows if row["is_primary_variant"] and row["phase"] in {"first_pass", "legacy"}]
    durations = [row["duration_seconds"] for row in rows if isinstance(row.get("duration_seconds"), int)]
    base["slot_records"] = rows
    base["primary_slot_records"] = primary_rows
    base["neutral_reason"] = _neutral_reason(primary_rows)
    base["observability"] = {
        "slot_command_results_present": bool(slot_results),
        "duration_seconds_present": bool(durations),
        "heartbeat_present": any(row["heartbeat_present"] for row in rows),
        "max_duration_seconds": max(durations) if durations else None,
        "total_duration_seconds": sum(durations) if durations else None,
    }
    if not slot_results:
        base["warnings"].append("slot_command_results.json is missing or empty.")
    if not base["observability"]["heartbeat_present"]:
        base["warnings"].append("No heartbeat fields were found in slot command results.")
    return base


def generate_neutral_impact_eval_report(
    *,
    period_id: str,
    repo_root: Path | None = None,
    repo_wiki_dir: Path | None = None,
    families: tuple[str, ...] = (),
    neutral_only: bool = True,
) -> dict[str, Any]:
    """Generate a neutral-family report for one scheduled impact-eval period."""

    paths = build_paths(repo_root)
    selected_repo_root = paths.repo_root
    selected_repo_wiki_dir = _repo_wiki_dir(selected_repo_root, repo_wiki_dir)
    run_index = _load_run_index(selected_repo_root, selected_repo_wiki_dir)
    selected_families = {family for family in families if family}
    runs = [
        item
        for item in run_index.get("runs", [])
        if isinstance(item, dict)
        and item.get("period_id") == period_id
        and (not selected_families or item.get("family") in selected_families)
    ]
    family_items: list[dict[str, Any]] = []
    skipped: list[dict[str, Any]] = []
    for item in runs:
        analyzed = _family_neutral_item(item)
        outcome = analyzed.get("primary_comparison", {}).get("outcome")
        if neutral_only and outcome != "neutral_signal":
            skipped.append(
                {
                    "family": analyzed.get("family"),
                    "reason": f"primary outcome is {outcome or 'unknown'}",
                }
            )
            continue
        family_items.append(analyzed)

    reason_counts = Counter(str(item.get("neutral_reason") or "unknown") for item in family_items)
    payload: dict[str, Any] = {
        "schema_version": NEUTRAL_REPORT_SCHEMA_VERSION,
        "generated_at": _now_iso(),
        "repo_root": str(selected_repo_root),
        "repo_wiki_dir": str(selected_repo_wiki_dir),
        "filters": {
            "period_id": period_id,
            "families": sorted(selected_families),
            "neutral_only": neutral_only,
        },
        "run_index_path": run_index.get("path"),
        "summary": {
            "indexed_runs_for_period": len(runs),
            "reported_family_count": len(family_items),
            "skipped_family_count": len(skipped),
            "neutral_reason_counts": dict(sorted(reason_counts.items())),
            "families_missing_run_dir": sum(
                1 for item in family_items if item.get("artifact_status") == "run_dir_missing"
            ),
            "families_without_heartbeat": sum(
                1
                for item in family_items
                if not item.get("observability", {}).get("heartbeat_present")
            ),
        },
        "families": family_items,
        "skipped": skipped,
        "recommendations": [
            "If primary slots are both success, make the task harder or tighten the rubric before adding memory.",
            "If both primary slots fail or partial, inspect prompt ambiguity and expected-behavior coverage.",
            "Use duration and heartbeat gaps to prioritize runner observability hardening.",
        ],
    }
    return payload


def render_route_noise_report_json(payload: dict[str, Any]) -> str:
    return json.dumps(payload, indent=2, sort_keys=True) + "\n"


def render_route_cohort_report_json(payload: dict[str, Any]) -> str:
    return json.dumps(payload, indent=2, sort_keys=True) + "\n"


def render_route_replay_report_json(payload: dict[str, Any]) -> str:
    return json.dumps(payload, indent=2, sort_keys=True) + "\n"


def render_route_ablation_report_json(payload: dict[str, Any]) -> str:
    return json.dumps(payload, indent=2, sort_keys=True) + "\n"


def render_neutral_impact_eval_report_json(payload: dict[str, Any]) -> str:
    return json.dumps(payload, indent=2, sort_keys=True) + "\n"


def render_route_noise_report(payload: dict[str, Any]) -> str:
    summary = payload.get("summary", {})
    task_rows = [
        [
            str(item.get("task_type")),
            str(item.get("trace_count")),
            _format_metric(item.get("route_precision")),
            _format_metric(item.get("route_noise_rate")),
            str(item.get("selected_but_unused_doc_count")),
            str(item.get("missed_useful_doc_count")),
        ]
        for item in payload.get("task_type_summary", [])
        if isinstance(item, dict)
    ]
    trace_rows = [
        [
            str(item.get("task_id")),
            str(item.get("task_type")),
            _format_metric(item.get("route_precision")),
            _format_metric(item.get("route_noise_rate")),
            str(item.get("selected_but_unused_doc_count")),
            str(len(item.get("missed_useful_doc_ids", []))),
        ]
        for item in payload.get("top_noisy_traces", [])
        if isinstance(item, dict)
    ]
    noisy_doc_rows = [
        [
            str(item.get("doc_id")),
            str(item.get("selected_but_unused_count")),
            str(item.get("selected_not_helpful_count")),
        ]
        for item in payload.get("noisy_doc_hotspots", [])
        if isinstance(item, dict)
    ]
    missed_doc_rows = [
        [str(item.get("doc_id")), str(item.get("missed_useful_count"))]
        for item in payload.get("missed_doc_hotspots", [])
        if isinstance(item, dict)
    ]
    lines = [
        "# Impact Eval Route Noise Report",
        "",
        f"- Generated at: `{payload.get('generated_at')}`",
        f"- Since: `{payload.get('filters', {}).get('since')}`",
        f"- Handle: `{payload.get('filters', {}).get('handle')}`",
        "",
        "## Summary",
        "",
        f"- Route traces: `{summary.get('route_trace_count')}`",
        f"- Selected docs: `{summary.get('selected_doc_count')}`",
        f"- Selected-but-unused docs: `{summary.get('selected_but_unused_doc_count')}`",
        f"- Missed useful docs: `{summary.get('missed_useful_doc_count')}`",
        f"- Route precision: `{_format_metric(summary.get('route_precision'))}`",
        f"- Route recall proxy: `{_format_metric(summary.get('route_recall_proxy'))}`",
        f"- Route noise rate: `{_format_metric(summary.get('route_noise_rate'))}`",
        "",
        "## Task Types",
        "",
        _markdown_table(
            ["task_type", "traces", "precision", "noise", "unused", "missed"],
            task_rows,
        ),
        "",
        "## Top Noisy Traces",
        "",
        _markdown_table(
            ["task", "task_type", "precision", "noise", "unused", "missed"],
            trace_rows,
        ),
        "",
        "## Noisy Doc Hotspots",
        "",
        _markdown_table(["doc", "selected_unused", "selected_not_helpful"], noisy_doc_rows),
        "",
        "## Missed Doc Hotspots",
        "",
        _markdown_table(["doc", "missed_useful"], missed_doc_rows),
        "",
        "## Recommendations",
        "",
    ]
    lines.extend(f"- {item}" for item in payload.get("recommendations", []))
    lines.append("")
    return "\n".join(lines)


def render_route_cohort_report(payload: dict[str, Any]) -> str:
    baseline = payload.get("baseline", {}).get("summary", {})
    post_change = payload.get("post_change", {}).get("summary", {})
    progress = payload.get("progress", {})
    comparison = payload.get("comparison", {})
    baseline_rows = [
        [
            "baseline",
            str(baseline.get("trace_count")),
            _format_metric(baseline.get("route_precision")),
            _format_metric(baseline.get("route_noise_rate")),
            _format_metric(baseline.get("failed_route_at_selected_plus_maybe_rate")),
            str(baseline.get("selected_doc_count")),
            str(baseline.get("selected_plus_maybe_doc_count")),
            str(baseline.get("selected_useful_doc_count")),
        ],
        [
            "post_change",
            str(post_change.get("trace_count")),
            _format_metric(post_change.get("route_precision")),
            _format_metric(post_change.get("route_noise_rate")),
            _format_metric(post_change.get("failed_route_at_selected_plus_maybe_rate")),
            str(post_change.get("selected_doc_count")),
            str(post_change.get("selected_plus_maybe_doc_count")),
            str(post_change.get("selected_useful_doc_count")),
        ],
    ]
    warnings = payload.get("warnings", [])
    lines = [
        "# Route Precision Cohort Report",
        "",
        f"- Generated at: `{payload.get('generated_at')}`",
        f"- Post-change since: `{payload.get('filters', {}).get('post_change_since')}`",
        f"- Handle: `{payload.get('filters', {}).get('handle')}`",
        f"- Only evaluable: `{payload.get('filters', {}).get('only_evaluable')}`",
        "",
        "## Progress",
        "",
        f"- Target evaluable traces: `{progress.get('target_evaluable_traces')}`",
        f"- Current evaluable traces: `{progress.get('current_evaluable_traces')}`",
        f"- Remaining evaluable traces: `{progress.get('remaining_evaluable_traces')}`",
        f"- Complete: `{progress.get('complete')}`",
        "",
        "## Comparison",
        "",
        _markdown_table(
            [
                "cohort",
                "traces",
                "precision",
                "noise",
                "failed@selected+maybe",
                "selected",
                "selected+maybe",
                "selected_useful",
            ],
            baseline_rows,
        ),
        "",
        f"- Precision delta: `{_format_metric(comparison.get('route_precision_delta'))}`",
        f"- Noise delta: `{_format_metric(comparison.get('route_noise_delta'))}`",
    ]
    if warnings:
        lines.extend(["", "## Warnings", ""])
        lines.extend(f"- {warning}" for warning in warnings)
    lines.append("")
    return "\n".join(lines)


def _prompt_preview(value: Any, *, limit: int = 90) -> str:
    if not isinstance(value, str):
        return ""
    normalized = re.sub(r"\s+", " ", value).strip()
    if len(normalized) <= limit:
        return normalized
    return normalized[: limit - 3].rstrip() + "..."


def render_route_replay_report(payload: dict[str, Any]) -> str:
    recovery = payload.get("prompt_recovery", {})
    baseline = payload.get("baseline", {}).get("summary", {})
    replay = payload.get("replay", {}).get("summary", {})
    comparison = payload.get("comparison", {})
    catalog_timing = payload.get("catalog_timing", {})
    regression_summary = payload.get("item_regression_summary", {})
    eval_stage_confusion = payload.get("eval_stage_confusion", {})
    rows = [
        [
            str(item.get("task_id")),
            str(item.get("prompt_recovery", {}).get("confidence")),
            _format_metric(item.get("baseline", {}).get("route_precision")),
            _format_metric(item.get("replay", {}).get("route_precision") if isinstance(item.get("replay"), dict) else None),
            _format_metric(item.get("comparison", {}).get("route_precision_delta")),
            _prompt_preview(item.get("replay", {}).get("task") if isinstance(item.get("replay"), dict) else None),
        ]
        for item in payload.get("items", [])
        if isinstance(item, dict)
    ]
    summary_rows = [
        [
            "baseline",
            str(baseline.get("trace_count")),
            _format_metric(baseline.get("route_precision")),
            _format_metric(baseline.get("route_noise_rate")),
            _format_metric(baseline.get("retrieval_precision")),
            str(baseline.get("selected_doc_count")),
            str(baseline.get("selected_useful_doc_count")),
            str(baseline.get("retrieval_selected_doc_count")),
            str(baseline.get("retrieval_selected_useful_doc_count")),
            str(baseline.get("core_doc_count")),
        ],
        [
            "replay",
            str(replay.get("trace_count")),
            _format_metric(replay.get("route_precision")),
            _format_metric(replay.get("route_noise_rate")),
            _format_metric(replay.get("retrieval_precision")),
            str(replay.get("selected_doc_count")),
            str(replay.get("selected_useful_doc_count")),
            str(replay.get("retrieval_selected_doc_count")),
            str(replay.get("retrieval_selected_useful_doc_count")),
            str(replay.get("core_doc_count")),
        ],
    ]
    lines = [
        "# Historical Route Replay Report",
        "",
        f"- Generated at: `{payload.get('generated_at')}`",
        f"- Before: `{payload.get('filters', {}).get('before')}`",
        f"- Catalog cutoff: `{payload.get('filters', {}).get('catalog_cutoff')}`",
        f"- Handle: `{payload.get('filters', {}).get('handle')}`",
        "",
        "## Prompt Recovery",
        "",
        f"- Target traces: `{recovery.get('target_trace_count')}`",
        f"- Recovered traces: `{recovery.get('recovered_trace_count')}`",
        f"- Replayed traces: `{recovery.get('replayed_trace_count')}`",
        f"- Unmatched traces: `{recovery.get('unmatched_trace_count')}`",
        f"- Confidence counts: `{recovery.get('confidence_counts')}`",
        f"- Route command candidates scanned: `{recovery.get('scan', {}).get('candidate_count')}`",
        "",
        "## Comparison",
        "",
        _markdown_table(
            [
                "cohort",
                "traces",
                "precision",
                "noise",
                "retrieval_precision",
                "selected",
                "selected_useful",
                "retrieval_selected",
                "retrieval_useful",
                "core_docs",
            ],
            summary_rows,
        ),
        "",
        f"- Precision delta: `{_format_metric(comparison.get('route_precision_delta'))}`",
        f"- Noise delta: `{_format_metric(comparison.get('route_noise_delta'))}`",
        "",
        "## Layered Metrics",
        "",
        f"- Baseline reason types: `{baseline.get('selection_reason_type_counts')}`",
        f"- Replay reason types: `{replay.get('selection_reason_type_counts')}`",
        f"- Replay mandatory contract docs: `{replay.get('mandatory_contract_doc_count')}`",
        f"- Replay safety guardrail docs: `{replay.get('safety_guardrail_doc_count')}`",
        f"- Replay core docs selected-but-unused: `{replay.get('core_selected_but_unused_doc_count')}`",
        f"- Replay retrieval selected-but-unused: `{replay.get('retrieval_selected_but_unused_doc_count')}`",
        "",
        "## RAG-Style Retrieval Metrics",
        "",
        _markdown_table(
            [
                "cohort",
                "failed@selected",
                "failed@selected+maybe",
                "failed@candidate20",
                "coverage@selected",
                "coverage@selected+maybe",
                "coverage@candidate20",
                "maybe_recovery",
                "avg_words",
                "avg_docs",
            ],
            [
                [
                    "baseline",
                    _format_metric(baseline.get("failed_route_at_selected_rate")),
                    _format_metric(baseline.get("failed_route_at_selected_plus_maybe_rate")),
                    _format_metric(baseline.get("failed_route_at_candidate20_rate")),
                    _format_metric(baseline.get("useful_coverage_at_selected")),
                    _format_metric(baseline.get("useful_coverage_at_selected_plus_maybe")),
                    _format_metric(baseline.get("useful_coverage_at_candidate20")),
                    _format_metric(baseline.get("maybe_recovery_rate")),
                    _format_metric(baseline.get("avg_packet_words")),
                    _format_metric(baseline.get("avg_selected_plus_maybe_docs")),
                ],
                [
                    "replay",
                    _format_metric(replay.get("failed_route_at_selected_rate")),
                    _format_metric(replay.get("failed_route_at_selected_plus_maybe_rate")),
                    _format_metric(replay.get("failed_route_at_candidate20_rate")),
                    _format_metric(replay.get("useful_coverage_at_selected")),
                    _format_metric(replay.get("useful_coverage_at_selected_plus_maybe")),
                    _format_metric(replay.get("useful_coverage_at_candidate20")),
                    _format_metric(replay.get("maybe_recovery_rate")),
                    _format_metric(replay.get("avg_packet_words")),
                    _format_metric(replay.get("avg_selected_plus_maybe_docs")),
                ],
            ],
        ),
        "",
        "## Per-Trace Regression Summary",
        "",
        f"- Compared items: `{regression_summary.get('compared_item_count')}`",
        f"- Precision regressions: `{regression_summary.get('precision_regression_count')}`",
        f"- Precision improvements: `{regression_summary.get('precision_improvement_count')}`",
        f"- Precision ties: `{regression_summary.get('precision_tie_count')}`",
        f"- Precision uncomputed: `{regression_summary.get('precision_uncomputed_count')}`",
        f"- Noise regressions: `{regression_summary.get('noise_regression_count')}`",
        f"- Noise improvements: `{regression_summary.get('noise_improvement_count')}`",
        f"- Noise ties: `{regression_summary.get('noise_tie_count')}`",
        f"- Noise uncomputed: `{regression_summary.get('noise_uncomputed_count')}`",
        "",
        "## Temporal Catalog",
        "",
        f"- Filtered future docs: `{catalog_timing.get('filtered_future_doc_count')}`",
        f"- Selected future docs: `{catalog_timing.get('selected_future_doc_count')}`",
        f"- Selected unknown-created-at docs: `{catalog_timing.get('selected_unknown_created_at_doc_count')}`",
        f"- Catalog docs without created_at: `{catalog_timing.get('unknown_created_at_doc_count')}`",
        "",
        "## Eval Stage Confusion",
        "",
        f"- Stage-active traces: `{eval_stage_confusion.get('stage_active_trace_count')}`",
        f"- Selected eval docs: `{eval_stage_confusion.get('selected_eval_doc_count')}`",
        f"- Compatible eval docs: `{eval_stage_confusion.get('compatible_eval_doc_count')}`",
        f"- Incompatible eval docs: `{eval_stage_confusion.get('incompatible_eval_doc_count')}`",
        f"- Compatibility rate: `{_format_metric(eval_stage_confusion.get('compatibility_rate'))}`",
        "",
        _markdown_table(
            ["task_stage", "doc_stage", "selected_docs"],
            [
                [
                    str(item.get("task_stage")),
                    str(item.get("doc_stage")),
                    str(item.get("selected_doc_count")),
                ]
                for item in eval_stage_confusion.get("top_off_diagonal", [])
                if isinstance(item, dict)
            ],
        ),
        "",
        "## Replay Rows",
        "",
        _markdown_table(
            ["task_id", "confidence", "old_precision", "replay_precision", "delta", "prompt"],
            rows,
        ),
    ]
    warnings = payload.get("warnings", [])
    if warnings:
        lines.extend(["", "## Warnings", ""])
        lines.extend(f"- {warning}" for warning in warnings)
    lines.append("")
    return "\n".join(lines)


def render_route_ablation_report(payload: dict[str, Any]) -> str:
    rows = [
        [
            str(item.get("variant")),
            _format_metric(item.get("retrieval_precision")),
            _format_metric(item.get("retrieval_precision_delta_vs_current")),
            _format_metric(item.get("failed_route_at_selected_plus_maybe_rate")),
            _format_metric(item.get("failed_route_at_selected_plus_maybe_delta_vs_current")),
            _format_metric(item.get("maybe_recovery_rate")),
            _format_metric(item.get("useful_coverage_at_selected_plus_maybe")),
            str(item.get("selected_useful_doc_count")),
            str(item.get("selected_useful_delta_vs_current")),
            str(item.get("missed_useful_doc_count")),
            str(item.get("missed_useful_delta_vs_current")),
            str(item.get("eval_stage_incompatible_doc_count")),
            str(item.get("precision_regression_count")),
        ]
        for item in payload.get("variant_summaries", [])
        if isinstance(item, dict)
    ]
    off_diagonal_rows: list[list[str]] = []
    for item in payload.get("variant_summaries", []):
        if not isinstance(item, dict):
            continue
        variant = str(item.get("variant"))
        top_pairs = item.get("eval_stage_top_off_diagonal")
        if not isinstance(top_pairs, list):
            continue
        for pair in top_pairs[:5]:
            if not isinstance(pair, dict):
                continue
            off_diagonal_rows.append(
                [
                    variant,
                    str(pair.get("task_stage")),
                    str(pair.get("doc_stage")),
                    str(pair.get("selected_doc_count")),
                ]
            )
    activation = payload.get("activation") if isinstance(payload.get("activation"), dict) else {}
    lines = [
        "# Route Eval-Stage Ablation Report",
        "",
        f"- Generated at: `{payload.get('generated_at')}`",
        f"- Before: `{payload.get('filters', {}).get('before')}`",
        f"- Catalog cutoff: `{payload.get('filters', {}).get('catalog_cutoff')}`",
        f"- Target evaluable traces: `{payload.get('filters', {}).get('target_evaluable_traces')}`",
        "",
        "## Variant Summary",
        "",
        _markdown_table(
            [
                "variant",
                "retrieval_precision",
                "retrieval_delta",
                "failed@selected+maybe",
                "failed_delta",
                "maybe_recovery",
                "coverage@selected+maybe",
                "selected_useful",
                "useful_delta",
                "missed_useful",
                "missed_delta",
                "stage_incompatible",
                "precision_regressions",
            ],
            rows,
        ),
        "",
        "## Top Eval-Stage Off-Diagonal Pairs",
        "",
        _markdown_table(
            ["variant", "task_stage", "doc_stage", "selected_docs"],
            off_diagonal_rows,
        ),
        "",
        "## Activation",
        "",
        f"- Status: `{activation.get('status')}`",
        f"- Reason: {activation.get('reason')}",
        f"- Best retrieval variant: `{activation.get('best_retrieval_variant')}`",
        f"- Recommended next step: {activation.get('recommended_next_step')}",
    ]
    candidate = activation.get("candidate_signal")
    if isinstance(candidate, dict):
        lines.extend(
            [
                "",
                "## Candidate Signal",
                "",
                f"- Variant: `{candidate.get('variant')}`",
                f"- Retrieval precision delta vs current: `{_format_metric(candidate.get('retrieval_precision_delta_vs_current'))}`",
                f"- Failed route@selected+maybe delta vs current: `{_format_metric(candidate.get('failed_route_at_selected_plus_maybe_delta_vs_current'))}`",
                f"- Maybe recovery rate delta vs current: `{_format_metric(candidate.get('maybe_recovery_rate_delta_vs_current'))}`",
                f"- Selected useful delta vs current: `{candidate.get('selected_useful_delta_vs_current')}`",
                f"- Missed useful delta vs current: `{candidate.get('missed_useful_delta_vs_current')}`",
            ]
        )
    warnings = payload.get("warnings", [])
    if warnings:
        lines.extend(["", "## Warnings", ""])
        lines.extend(f"- {warning}" for warning in warnings)
    lines.append("")
    return "\n".join(lines)


def render_neutral_impact_eval_report(payload: dict[str, Any]) -> str:
    summary = payload.get("summary", {})
    family_rows = [
        [
            str(item.get("family")),
            str(item.get("primary_comparison", {}).get("outcome")),
            str(item.get("neutral_reason")),
            str(item.get("observability", {}).get("max_duration_seconds")),
            "yes" if item.get("observability", {}).get("heartbeat_present") else "no",
        ]
        for item in payload.get("families", [])
        if isinstance(item, dict)
    ]
    primary_rows: list[list[str]] = []
    for item in payload.get("families", []):
        if not isinstance(item, dict):
            continue
        for row in item.get("primary_slot_records", []):
            if not isinstance(row, dict):
                continue
            primary_rows.append(
                [
                    str(item.get("family")),
                    str(row.get("slot")),
                    str(row.get("variant")),
                    str(row.get("score_label")),
                    str(row.get("duration_seconds")),
                    str(row.get("changed_file_count")),
                    str(row.get("untracked_file_count")),
                ]
            )
    lines = [
        "# Impact Eval Neutral Family Report",
        "",
        f"- Generated at: `{payload.get('generated_at')}`",
        f"- Period: `{payload.get('filters', {}).get('period_id')}`",
        f"- Neutral only: `{payload.get('filters', {}).get('neutral_only')}`",
        "",
        "## Summary",
        "",
        f"- Indexed runs for period: `{summary.get('indexed_runs_for_period')}`",
        f"- Reported families: `{summary.get('reported_family_count')}`",
        f"- Skipped families: `{summary.get('skipped_family_count')}`",
        f"- Neutral reasons: `{summary.get('neutral_reason_counts')}`",
        f"- Families without heartbeat: `{summary.get('families_without_heartbeat')}`",
        "",
        "## Families",
        "",
        _markdown_table(["family", "outcome", "reason", "max_duration_seconds", "heartbeat"], family_rows),
        "",
        "## Primary Slots",
        "",
        _markdown_table(
            ["family", "slot", "variant", "score", "duration_seconds", "changed", "untracked"],
            primary_rows,
        ),
        "",
        "## Recommendations",
        "",
    ]
    lines.extend(f"- {item}" for item in payload.get("recommendations", []))
    lines.append("")
    return "\n".join(lines)
