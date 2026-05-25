"""AI wiki diagnostic report helpers."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
from typing import Any

from ai_wiki_toolkit.frontmatter import parse_frontmatter
from ai_wiki_toolkit.route_traces import load_route_traces
from ai_wiki_toolkit.source_incidents import load_source_incident_events
from ai_wiki_toolkit.wiki_schema import (
    doc_id_for_relative_path,
    infer_doc_kind,
    load_reuse_events,
    load_task_checks,
)

DIAGNOSTICS_SCHEMA_VERSION = "diagnostics-v1"
DEFAULT_DIAGNOSTICS_MAX_ITEMS = 10
DEFAULT_HIGH_ROI_MIN_EVENTS = 2
DEFAULT_NOISY_MIN_EVENTS = 2
DIAGNOSTIC_FOCUSES = {"all", "route", "trial-error"}
HIGH_VALUE_REUSE_EFFECTS = {
    "avoided_retry",
    "avoided_search",
    "blocked_wrong_path",
    "faster_resolution",
    "release_safety",
    "verified_release_matrix",
}
TRIAL_ERROR_REUSE_EFFECTS = {
    "avoided_retry",
    "blocked_wrong_path",
    "changed_plan",
    "faster_resolution",
}
STALE_KEYWORDS = ("stale", "outdated", "obsolete", "superseded")
CONFLICT_KEYWORDS = ("conflict", "conflicting", "contradict", "inconsistent")
MISSED_MEMORY_KEYWORDS = (
    "missed memory",
    "missed relevant memory",
    "should have used",
    "should have read",
)
TRIAL_ERROR_NOTE_KEYWORDS = (
    "extra iteration",
    "failed attempt",
    "repeated error",
    "repeated mistake",
    "retry",
    "wrong path",
    "wrong plan",
)


@dataclass(frozen=True)
class MemoryDiagnosticsResult:
    """Rendered memory diagnostics and optional generated output paths."""

    report: dict[str, Any]
    markdown: str
    json_text: str
    markdown_path: Path | None = None
    json_path: Path | None = None


def _repo_relative(path: Path, repo_wiki_dir: Path) -> str:
    return path.relative_to(repo_wiki_dir).as_posix()


def _parse_timestamp(value: object) -> datetime | None:
    if not isinstance(value, str) or not value.strip():
        return None
    normalized = value.strip().replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _parse_since(value: str | None, *, now: datetime | None = None) -> datetime | None:
    if value is None or not value.strip():
        return None
    normalized = value.strip().lower()
    if normalized.endswith("d") and normalized[:-1].isdigit():
        days = int(normalized[:-1])
        current = now or datetime.now(timezone.utc)
        return current.astimezone(timezone.utc) - timedelta(days=days)
    parsed = _parse_timestamp(normalized)
    if parsed is None:
        raise ValueError("Invalid --since value. Use an ISO timestamp or a duration like 14d.")
    return parsed


def _timestamp_matches(payload: dict[str, Any], key: str, since: datetime | None) -> bool:
    if since is None:
        return True
    parsed = _parse_timestamp(payload.get(key))
    return parsed is not None and parsed >= since


def _load_repo_reuse_events(repo_wiki_dir: Path) -> tuple[list[dict[str, Any]], int]:
    legacy_events, legacy_skipped = load_reuse_events(repo_wiki_dir / "metrics" / "reuse-events.jsonl")
    sharded_events, sharded_skipped = load_reuse_events(repo_wiki_dir / "metrics" / "reuse-events")
    return legacy_events + sharded_events, legacy_skipped + sharded_skipped


def _load_repo_task_checks(repo_wiki_dir: Path) -> tuple[list[dict[str, Any]], int]:
    legacy_checks, legacy_skipped = load_task_checks(repo_wiki_dir / "metrics" / "task-checks.jsonl")
    sharded_checks, sharded_skipped = load_task_checks(repo_wiki_dir / "metrics" / "task-checks")
    return legacy_checks + sharded_checks, legacy_skipped + sharded_skipped


def _load_repo_route_traces(repo_wiki_dir: Path) -> tuple[list[dict[str, Any]], int]:
    legacy_traces, legacy_skipped = load_route_traces(repo_wiki_dir / "metrics" / "route-traces.jsonl")
    sharded_traces, sharded_skipped = load_route_traces(repo_wiki_dir / "metrics" / "route-traces")
    return legacy_traces + sharded_traces, legacy_skipped + sharded_skipped


def _load_repo_source_incidents(repo_wiki_dir: Path) -> tuple[list[dict[str, Any]], int]:
    legacy_events, legacy_skipped = load_source_incident_events(
        repo_wiki_dir / "metrics" / "source-incidents.jsonl"
    )
    sharded_events, sharded_skipped = load_source_incident_events(
        repo_wiki_dir / "metrics" / "source-incidents"
    )
    return legacy_events + sharded_events, legacy_skipped + sharded_skipped


def _document_title(metadata: dict[str, Any], body: str, path: Path) -> str:
    title = metadata.get("title")
    if isinstance(title, str) and title.strip():
        return title.strip()
    for line in body.splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return path.stem.replace("-", " ").replace("_", " ").strip() or path.stem


def _load_document_metadata(repo_wiki_dir: Path) -> dict[str, dict[str, Any]]:
    documents: dict[str, dict[str, Any]] = {}
    for path in sorted(repo_wiki_dir.rglob("*.md")):
        if "_toolkit" in path.parts:
            continue
        relative_path = _repo_relative(path, repo_wiki_dir)
        text = path.read_text(encoding="utf-8")
        metadata, body = parse_frontmatter(text)
        status = metadata.get("status")
        documents[doc_id_for_relative_path(relative_path)] = {
            "doc_kind": infer_doc_kind(relative_path),
            "path": f"ai-wiki/{relative_path}",
            "status": status.strip().lower() if isinstance(status, str) else None,
            "title": _document_title(metadata, body, path),
        }
    return documents


def _normalize_handle_filter(handle: str | None) -> str | None:
    if handle is None:
        return None
    normalized = handle.strip()
    return normalized or None


def _normalize_doc_id(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    normalized = value.strip()
    if not normalized:
        return None
    normalized = normalized.removeprefix("ai-wiki/").removesuffix(".md")
    if normalized.startswith("_toolkit/"):
        return None
    return normalized


def _filter_reuse_events(
    events: list[dict[str, Any]], *, handle: str | None, since: datetime | None
) -> list[dict[str, Any]]:
    normalized_handle = _normalize_handle_filter(handle)
    filtered: list[dict[str, Any]] = []
    for event in events:
        if normalized_handle and event.get("author_handle") != normalized_handle:
            continue
        if not _timestamp_matches(event, "observed_at", since):
            continue
        doc_id = _normalize_doc_id(event.get("doc_id"))
        if doc_id is None:
            continue
        filtered.append(event | {"doc_id": doc_id})
    return filtered


def _filter_task_checks(
    checks: list[dict[str, Any]], *, handle: str | None, since: datetime | None
) -> list[dict[str, Any]]:
    normalized_handle = _normalize_handle_filter(handle)
    filtered: list[dict[str, Any]] = []
    for check in checks:
        if normalized_handle and check.get("author_handle") != normalized_handle:
            continue
        if not _timestamp_matches(check, "checked_at", since):
            continue
        task_id = check.get("task_id")
        if isinstance(task_id, str) and task_id:
            filtered.append(check)
    return filtered


def _filter_route_traces(
    traces: list[dict[str, Any]], *, handle: str | None, since: datetime | None
) -> list[dict[str, Any]]:
    normalized_handle = _normalize_handle_filter(handle)
    filtered: list[dict[str, Any]] = []
    for trace in traces:
        if normalized_handle and trace.get("author_handle") != normalized_handle:
            continue
        if not _timestamp_matches(trace, "routed_at", since):
            continue
        task_id = trace.get("task_id")
        if isinstance(task_id, str) and task_id:
            filtered.append(trace)
    return filtered


def _filter_source_incidents(
    events: list[dict[str, Any]], *, handle: str | None
) -> list[dict[str, Any]]:
    normalized_handle = _normalize_handle_filter(handle)
    filtered: list[dict[str, Any]] = []
    for event in events:
        if normalized_handle and event.get("author_handle") != normalized_handle:
            continue
        doc_id = _normalize_doc_id(event.get("doc_id"))
        if doc_id is None:
            continue
        filtered.append(event | {"doc_id": doc_id})
    return filtered


def _estimated_savings(event: dict[str, Any]) -> tuple[int, int]:
    estimates = event.get("estimated_savings")
    if not isinstance(estimates, dict):
        return 0, 0
    tokens = estimates.get("saved_tokens")
    seconds = estimates.get("saved_seconds")
    return (
        tokens if isinstance(tokens, int) else 0,
        seconds if isinstance(seconds, int) else 0,
    )


def _optional_string(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    normalized = value.strip()
    return normalized or None


def _note_text(payload: dict[str, Any]) -> str:
    notes = payload.get("notes")
    return notes if isinstance(notes, str) else ""


def _non_negative_int(value: object) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int) and value >= 0:
        return value
    if isinstance(value, float) and value >= 0:
        return int(value)
    return None


def _source_incident_key(event: dict[str, Any], source_incident: dict[str, Any]) -> str:
    source_session_id = _optional_string(event.get("source_session_id")) or _optional_string(
        source_incident.get("session_id")
    )
    source_task_id = _optional_string(event.get("source_task_id"))
    if source_session_id or source_task_id:
        return f"{source_session_id or '-'}::{source_task_id or '-'}"
    event_id = _optional_string(event.get("event_id"))
    return f"event::{event_id or id(event)}"


def _source_incident_item(event: dict[str, Any]) -> tuple[str, dict[str, Any]] | None:
    source_incident = event.get("source_incident")
    if not isinstance(source_incident, dict):
        return None
    active_seconds = _non_negative_int(source_incident.get("active_seconds"))
    duration_ms = _non_negative_int(source_incident.get("duration_ms"))
    if active_seconds is None:
        if duration_ms is None:
            return None
        active_seconds = round(duration_ms / 1000)
    if duration_ms is None:
        duration_ms = active_seconds * 1000

    item: dict[str, Any] = {
        "active_seconds": active_seconds,
        "duration_ms": duration_ms,
        "event_ids": set(),
        "timing_label": _optional_string(source_incident.get("timing_label"))
        or "source active-turn estimate",
        "timing_source": _optional_string(source_incident.get("timing_source")) or "unknown",
    }
    event_id = _optional_string(event.get("event_id"))
    if event_id:
        item["event_ids"].add(event_id)
    for key in (
        "source_session_id",
        "source_task_id",
    ):
        value = _optional_string(event.get(key))
        if value:
            item[key] = value
    session_id = _optional_string(source_incident.get("session_id"))
    if session_id and "source_session_id" not in item:
        item["source_session_id"] = session_id
    for key in (
        "included_events",
        "note",
        "policy",
        "session_file",
        "session_relpath",
        "source_kind",
        "source_task_start_timestamp",
        "task_complete_count",
        "turn_aborted_count",
        "cutoff_timestamp",
        "cutoff_turn_id",
    ):
        value = source_incident.get(key)
        if value not in (None, "", []):
            item[key] = value
    return _source_incident_key(event, source_incident), item


def _merge_source_incident_timing(
    timings: dict[str, dict[str, Any]], event: dict[str, Any]
) -> None:
    keyed_item = _source_incident_item(event)
    if keyed_item is None:
        return
    key, item = keyed_item
    existing = timings.get(key)
    if existing is None:
        timings[key] = item
        return
    event_ids = existing.setdefault("event_ids", set())
    if isinstance(event_ids, set) and isinstance(item.get("event_ids"), set):
        event_ids.update(item["event_ids"])
    if item["active_seconds"] > existing.get("active_seconds", 0):
        preserved_event_ids = existing.get("event_ids", set())
        if isinstance(preserved_event_ids, set) and isinstance(item.get("event_ids"), set):
            preserved_event_ids.update(item["event_ids"])
        timings[key] = {**item, "event_ids": preserved_event_ids}


def _source_incident_timing_summary(stats: dict[str, Any]) -> dict[str, Any]:
    raw_sources = stats.get("source_incident_timings")
    if not isinstance(raw_sources, dict) or not raw_sources:
        return {
            "active_seconds": 0,
            "active_minutes": 0.0,
            "evidence_count": 0,
            "event_count": 0,
            "sources": [],
            "status": "not_recorded",
        }

    sources: list[dict[str, Any]] = []
    for key, source in sorted(raw_sources.items()):
        if not isinstance(source, dict):
            continue
        event_ids = source.get("event_ids")
        rendered = {
            name: value
            for name, value in source.items()
            if name != "event_ids" and value not in (None, "", [])
        }
        rendered["evidence_key"] = str(key)
        rendered["event_ids"] = sorted(event_ids) if isinstance(event_ids, set) else []
        sources.append(rendered)

    active_seconds = sum(
        source.get("active_seconds", 0)
        for source in sources
        if isinstance(source.get("active_seconds"), int)
    )
    event_ids = {
        event_id
        for source in sources
        for event_id in source.get("event_ids", [])
        if isinstance(event_id, str)
    }
    return {
        "active_seconds": active_seconds,
        "active_minutes": round(active_seconds / 60, 2),
        "evidence_count": len(sources),
        "event_count": len(event_ids),
        "sources": sources,
        "status": "measured" if active_seconds > 0 else "not_recorded",
    }


def _contains_any_keyword(text: str, keywords: tuple[str, ...]) -> bool:
    lowered = text.lower()
    return any(keyword in lowered for keyword in keywords)


def _last_timestamp(current: str | None, candidate: object) -> str | None:
    if not isinstance(candidate, str) or not candidate:
        return current
    if current is None:
        return candidate
    parsed_current = _parse_timestamp(current)
    parsed_candidate = _parse_timestamp(candidate)
    if parsed_current is None or parsed_candidate is None:
        return max(current, candidate)
    return candidate if parsed_candidate >= parsed_current else current


def _document_stats_template(
    doc_id: str, metadata: dict[str, Any], *, doc_kind: object = None
) -> dict[str, Any]:
    return {
        "doc_id": doc_id,
        "doc_kind": doc_kind or metadata.get("doc_kind") or infer_doc_kind(f"{doc_id}.md"),
        "candidate_not_helpful_events": 0,
        "confirmed_not_helpful_events": 0,
        "path": metadata.get("path"),
        "status": metadata.get("status"),
        "title": metadata.get("title") or doc_id,
        "total_events": 0,
        "resolved_events": 0,
        "partial_events": 0,
        "not_helpful_events": 0,
        "not_helpful_reasons": Counter(),
        "lookup_reuse_count": 0,
        "preloaded_reuse_count": 0,
        "estimated_token_savings": 0,
        "estimated_seconds_saved": 0,
        "reuse_effects": Counter(),
        "resolved_by_doc_ids": set(),
        "session_ids": set(),
        "source_session_ids": set(),
        "source_incident_timings": {},
        "source_task_ids": set(),
        "superseded_by_doc_ids": set(),
        "tasks": set(),
        "last_observed_at": None,
        "stale_note_count": 0,
        "conflict_note_count": 0,
        "missed_note_count": 0,
    }


def _aggregate_documents(
    events: list[dict[str, Any]], document_metadata: dict[str, dict[str, Any]]
) -> dict[str, dict[str, Any]]:
    documents: dict[str, dict[str, Any]] = {}
    for event in events:
        doc_id = event["doc_id"]
        metadata = document_metadata.get(doc_id, {})
        stats = documents.setdefault(
            doc_id,
            _document_stats_template(doc_id, metadata, doc_kind=event.get("doc_kind")),
        )
        stats["total_events"] += 1
        outcome = event.get("reuse_outcome")
        if outcome == "resolved":
            stats["resolved_events"] += 1
        elif outcome == "partial":
            stats["partial_events"] += 1
        elif outcome == "not_helpful":
            stats["not_helpful_events"] += 1
            if event.get("signal_status") == "candidate":
                stats["candidate_not_helpful_events"] += 1
            else:
                stats["confirmed_not_helpful_events"] += 1
            reason = _optional_string(event.get("not_helpful_reason"))
            if reason:
                stats["not_helpful_reasons"][reason] += 1
        retrieval_mode = event.get("retrieval_mode")
        if retrieval_mode == "lookup":
            stats["lookup_reuse_count"] += 1
        elif retrieval_mode == "preloaded":
            stats["preloaded_reuse_count"] += 1
        saved_tokens, saved_seconds = _estimated_savings(event)
        stats["estimated_token_savings"] += saved_tokens
        stats["estimated_seconds_saved"] += saved_seconds
        _merge_source_incident_timing(stats["source_incident_timings"], event)
        reuse_effects = event.get("reuse_effects")
        if isinstance(reuse_effects, list):
            for effect in reuse_effects:
                if isinstance(effect, str) and effect.strip():
                    stats["reuse_effects"][effect.strip()] += 1
        for source_key, stats_key in (
            ("session_id", "session_ids"),
            ("source_session_id", "source_session_ids"),
            ("source_task_id", "source_task_ids"),
            ("resolved_by_doc_id", "resolved_by_doc_ids"),
            ("superseded_by_doc_id", "superseded_by_doc_ids"),
        ):
            value = _optional_string(event.get(source_key))
            if value:
                stats[stats_key].add(value)
        task_id = event.get("task_id")
        if isinstance(task_id, str) and task_id:
            stats["tasks"].add(task_id)
        stats["last_observed_at"] = _last_timestamp(stats["last_observed_at"], event.get("observed_at"))
        notes = _note_text(event)
        if _contains_any_keyword(notes, STALE_KEYWORDS):
            stats["stale_note_count"] += 1
        if _contains_any_keyword(notes, CONFLICT_KEYWORDS):
            stats["conflict_note_count"] += 1
        if _contains_any_keyword(notes, MISSED_MEMORY_KEYWORDS):
            stats["missed_note_count"] += 1
    return documents


def _source_incident_reuse_event(event: dict[str, Any]) -> dict[str, Any] | None:
    active_seconds = _non_negative_int(event.get("active_seconds"))
    duration_ms = _non_negative_int(event.get("duration_ms"))
    if active_seconds is None:
        if duration_ms is None:
            return None
        active_seconds = round(duration_ms / 1000)
    if duration_ms is None:
        duration_ms = active_seconds * 1000

    source_incident: dict[str, Any] = {
        "active_seconds": active_seconds,
        "duration_ms": duration_ms,
        "timing_label": _optional_string(event.get("timing_label"))
        or "source active-turn estimate",
        "timing_source": _optional_string(event.get("timing_source")) or "unknown",
    }
    for key in (
        "included_events",
        "note",
        "policy",
        "session_file",
        "session_relpath",
        "source_kind",
        "source_task_start_timestamp",
        "task_complete_count",
        "turn_aborted_count",
        "cutoff_timestamp",
        "cutoff_turn_id",
    ):
        value = event.get(key)
        if value not in (None, "", []):
            source_incident[key] = value
    session_id = _optional_string(event.get("session_id"))
    if session_id:
        source_incident["session_id"] = session_id
    evidence_id = _optional_string(event.get("evidence_id"))
    return {
        "event_id": evidence_id,
        "doc_id": event["doc_id"],
        "source_session_id": session_id,
        "source_incident": source_incident,
    }


def _attach_source_incident_events(
    documents: dict[str, dict[str, Any]],
    source_incidents: list[dict[str, Any]],
    document_metadata: dict[str, dict[str, Any]],
) -> None:
    for event in source_incidents:
        doc_id = event["doc_id"]
        metadata = document_metadata.get(doc_id, {})
        stats = documents.setdefault(doc_id, _document_stats_template(doc_id, metadata))
        pseudo_event = _source_incident_reuse_event(event)
        if pseudo_event is None:
            continue
        _merge_source_incident_timing(stats["source_incident_timings"], pseudo_event)
        source_session_id = _optional_string(event.get("session_id"))
        if source_session_id:
            stats["source_session_ids"].add(source_session_id)


def _aggregate_tasks(
    events: list[dict[str, Any]], checks: list[dict[str, Any]]
) -> dict[str, dict[str, Any]]:
    tasks: dict[str, dict[str, Any]] = {}
    for check in checks:
        task_id = check.get("task_id")
        if not isinstance(task_id, str) or not task_id:
            continue
        stats = tasks.setdefault(
            task_id,
            {
                "task_id": task_id,
                "check_count": 0,
                "last_check_outcome": None,
                "last_checked_at": None,
                "total_events": 0,
                "resolved_events": 0,
                "doc_ids": set(),
                "reuse_effects": Counter(),
                "notes": [],
            },
        )
        stats["check_count"] += 1
        stats["last_checked_at"] = _last_timestamp(stats["last_checked_at"], check.get("checked_at"))
        outcome = check.get("check_outcome")
        if isinstance(outcome, str):
            stats["last_check_outcome"] = outcome
        notes = _note_text(check)
        if notes:
            stats["notes"].append(notes)
    for event in events:
        task_id = event.get("task_id")
        if not isinstance(task_id, str) or not task_id:
            continue
        stats = tasks.setdefault(
            task_id,
            {
                "task_id": task_id,
                "check_count": 0,
                "last_check_outcome": None,
                "last_checked_at": None,
                "total_events": 0,
                "resolved_events": 0,
                "doc_ids": set(),
                "reuse_effects": Counter(),
                "notes": [],
            },
        )
        stats["total_events"] += 1
        if event.get("reuse_outcome") == "resolved":
            stats["resolved_events"] += 1
        doc_id = event.get("doc_id")
        if isinstance(doc_id, str) and doc_id:
            stats["doc_ids"].add(doc_id)
        reuse_effects = event.get("reuse_effects")
        if isinstance(reuse_effects, list):
            for effect in reuse_effects:
                if isinstance(effect, str) and effect.strip():
                    stats["reuse_effects"][effect.strip()] += 1
        notes = _note_text(event)
        if notes:
            stats["notes"].append(notes)
    return tasks


def _doc_item(stats: dict[str, Any], reason: str) -> dict[str, Any]:
    effects: Counter[str] = stats["reuse_effects"]
    return {
        "doc_id": stats["doc_id"],
        "doc_kind": stats["doc_kind"],
        "candidate_not_helpful_events": stats["candidate_not_helpful_events"],
        "confirmed_not_helpful_events": stats["confirmed_not_helpful_events"],
        "estimated_seconds_saved": stats["estimated_seconds_saved"],
        "estimated_token_savings": stats["estimated_token_savings"],
        "last_observed_at": stats["last_observed_at"],
        "lookup_reuse_count": stats["lookup_reuse_count"],
        "not_helpful_reasons": dict(sorted(stats["not_helpful_reasons"].items())),
        "not_helpful_events": stats["not_helpful_events"],
        "partial_events": stats["partial_events"],
        "path": stats["path"],
        "preloaded_reuse_count": stats["preloaded_reuse_count"],
        "resolved_by_doc_ids": sorted(stats["resolved_by_doc_ids"]),
        "reason": reason,
        "resolved_events": stats["resolved_events"],
        "reuse_effects": dict(sorted(effects.items())),
        "session_ids": sorted(stats["session_ids"]),
        "status": stats["status"],
        "source_session_ids": sorted(stats["source_session_ids"]),
        "source_incident_timing": _source_incident_timing_summary(stats),
        "source_task_ids": sorted(stats["source_task_ids"]),
        "superseded_by_doc_ids": sorted(stats["superseded_by_doc_ids"]),
        "tasks": sorted(stats["tasks"]),
        "title": stats["title"],
        "total_events": stats["total_events"],
    }


def _coverage_gap_item(stats: dict[str, Any], reason: str) -> dict[str, Any]:
    return {
        "doc_ids": sorted(stats["doc_ids"]),
        "last_check_outcome": stats["last_check_outcome"],
        "last_checked_at": stats["last_checked_at"],
        "reason": reason,
        "resolved_events": stats["resolved_events"],
        "task_id": stats["task_id"],
        "total_events": stats["total_events"],
    }


def _trial_error_effects(effects: Counter[str] | dict[str, int]) -> dict[str, int]:
    return {
        effect: count
        for effect, count in sorted(effects.items())
        if effect in TRIAL_ERROR_REUSE_EFFECTS and count > 0
    }


def _trial_error_signal_count(effects: Counter[str] | dict[str, int]) -> int:
    return sum(_trial_error_effects(effects).values())


def _trial_error_doc_item(stats: dict[str, Any], reason: str) -> dict[str, Any]:
    item = _doc_item(stats, reason)
    item["trial_error_effects"] = _trial_error_effects(stats["reuse_effects"])
    item["trial_error_signal_count"] = _trial_error_signal_count(stats["reuse_effects"])
    return item


def _trial_error_task_item(stats: dict[str, Any], reason: str) -> dict[str, Any]:
    effects = _trial_error_effects(stats["reuse_effects"])
    return {
        "doc_ids": sorted(stats["doc_ids"]),
        "last_check_outcome": stats["last_check_outcome"],
        "last_checked_at": stats["last_checked_at"],
        "reason": reason,
        "resolved_events": stats["resolved_events"],
        "task_id": stats["task_id"],
        "total_events": stats["total_events"],
        "trial_error_effects": effects,
        "trial_error_signal_count": sum(effects.values()),
    }


def _build_high_roi_items(
    documents: dict[str, dict[str, Any]], *, min_events: int, max_items: int
) -> list[dict[str, Any]]:
    items: list[tuple[int, str, dict[str, Any]]] = []
    for doc_id, stats in documents.items():
        high_value_effect_count = sum(
            count for effect, count in stats["reuse_effects"].items() if effect in HIGH_VALUE_REUSE_EFFECTS
        )
        if stats["resolved_events"] < min_events and high_value_effect_count == 0:
            continue
        score = (
            stats["resolved_events"] * 4
            + high_value_effect_count * 3
            + min(stats["estimated_seconds_saved"] // 60, 5)
            + min(stats["estimated_token_savings"] // 1000, 5)
        )
        reason = (
            f"{stats['resolved_events']} resolved reuse events"
            if stats["resolved_events"] >= min_events
            else "high-value reuse effect recorded"
        )
        items.append((score, doc_id, _doc_item(stats, reason)))
    return [item for _, _, item in sorted(items, key=lambda row: (-row[0], row[1]))[:max_items]]


def _build_noisy_items(
    documents: dict[str, dict[str, Any]], *, min_events: int, max_items: int
) -> list[dict[str, Any]]:
    items: list[tuple[int, str, dict[str, Any]]] = []
    for doc_id, stats in documents.items():
        if stats["total_events"] < min_events:
            continue
        useful_events = stats["resolved_events"] + stats["partial_events"]
        if useful_events > 0 and stats["not_helpful_events"] < useful_events:
            continue
        if useful_events > 0 and stats["not_helpful_events"] < min_events:
            continue
        score = stats["not_helpful_events"] * 3 + stats["partial_events"] - stats["resolved_events"]
        reason = "reused without resolved outcomes"
        if stats["confirmed_not_helpful_events"]:
            reason = f"{stats['confirmed_not_helpful_events']} confirmed not_helpful reuse events"
        elif stats["candidate_not_helpful_events"]:
            reason = f"{stats['candidate_not_helpful_events']} candidate not_helpful reuse events"
        items.append((score, doc_id, _doc_item(stats, reason)))
    return [item for _, _, item in sorted(items, key=lambda row: (-row[0], row[1]))[:max_items]]


def _build_stale_items(documents: dict[str, dict[str, Any]], *, max_items: int) -> list[dict[str, Any]]:
    items: list[tuple[int, str, dict[str, Any]]] = []
    for doc_id, stats in documents.items():
        reasons: list[str] = []
        if stats["status"] in {"archived", "dropped", "superseded"}:
            reasons.append(f"document status is {stats['status']}")
        if stats["stale_note_count"]:
            reasons.append(f"{stats['stale_note_count']} reuse notes mention stale or superseded guidance")
        if not reasons:
            continue
        score = stats["total_events"] + stats["stale_note_count"] * 3
        items.append((score, doc_id, _doc_item(stats, "; ".join(reasons))))
    return [item for _, _, item in sorted(items, key=lambda row: (-row[0], row[1]))[:max_items]]


def _build_conflict_items(documents: dict[str, dict[str, Any]], *, max_items: int) -> list[dict[str, Any]]:
    items: list[tuple[int, str, dict[str, Any]]] = []
    for doc_id, stats in documents.items():
        if not stats["conflict_note_count"]:
            continue
        reason = f"{stats['conflict_note_count']} reuse notes mention conflicting or inconsistent guidance"
        score = stats["conflict_note_count"] * 3 + stats["total_events"]
        items.append((score, doc_id, _doc_item(stats, reason)))
    return [item for _, _, item in sorted(items, key=lambda row: (-row[0], row[1]))[:max_items]]


def _build_missed_memory_items(
    documents: dict[str, dict[str, Any]], tasks: dict[str, dict[str, Any]], *, max_items: int
) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for stats in tasks.values():
        if any(_contains_any_keyword(note, MISSED_MEMORY_KEYWORDS) for note in stats["notes"]):
            items.append(_coverage_gap_item(stats, "task notes mention missed memory"))
    for stats in documents.values():
        if stats["missed_note_count"]:
            item = _doc_item(
                stats,
                f"{stats['missed_note_count']} reuse notes mention missed memory or should-have-read signals",
            )
            item["task_id"] = None
            items.append(item)
    return sorted(items, key=lambda item: item.get("task_id") or item.get("doc_id") or "")[:max_items]


def _build_coverage_gap_items(
    tasks: dict[str, dict[str, Any]], *, max_items: int
) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for stats in tasks.values():
        if stats["total_events"] > 0 and stats["check_count"] == 0:
            items.append(_coverage_gap_item(stats, "document reuse events exist but no task-level reuse check was recorded"))
        elif stats["last_check_outcome"] == "no_wiki_use" and stats["total_events"] > 0:
            items.append(_coverage_gap_item(stats, "`no_wiki_use` check conflicts with recorded document reuse events"))
        elif stats["last_check_outcome"] == "wiki_used" and stats["total_events"] == 0:
            items.append(_coverage_gap_item(stats, "`wiki_used` check has no document-level reuse events"))
    return sorted(items, key=lambda item: item["task_id"])[:max_items]


def _build_trial_error_positive_items(
    documents: dict[str, dict[str, Any]], *, max_items: int
) -> list[dict[str, Any]]:
    items: list[tuple[int, str, dict[str, Any]]] = []
    for doc_id, stats in documents.items():
        signal_count = _trial_error_signal_count(stats["reuse_effects"])
        if signal_count == 0:
            continue
        score = signal_count * 4 + stats["resolved_events"] * 2 + stats["partial_events"]
        reason = "trial/error reduction effect recorded"
        items.append((score, doc_id, _trial_error_doc_item(stats, reason)))
    return [item for _, _, item in sorted(items, key=lambda row: (-row[0], row[1]))[:max_items]]


def _build_trial_error_missed_items(
    documents: dict[str, dict[str, Any]], tasks: dict[str, dict[str, Any]], *, max_items: int
) -> list[dict[str, Any]]:
    items: list[tuple[int, str, dict[str, Any]]] = []
    for task_id, stats in tasks.items():
        notes = " ".join(stats["notes"])
        has_missed_signal = _contains_any_keyword(notes, MISSED_MEMORY_KEYWORDS)
        has_unresolved_trial_error_signal = (
            _contains_any_keyword(notes, TRIAL_ERROR_NOTE_KEYWORDS)
            and _trial_error_signal_count(stats["reuse_effects"]) == 0
        )
        if not (has_missed_signal or has_unresolved_trial_error_signal):
            continue
        score = stats["resolved_events"] + stats["total_events"]
        reason = "task notes mention missed memory or trial/error failure signals"
        items.append((score, task_id, _trial_error_task_item(stats, reason)))
    for doc_id, stats in documents.items():
        notes_score = stats["missed_note_count"]
        if notes_score == 0:
            continue
        reason = "reuse notes mention missed memory or should-have-read signals"
        items.append((notes_score, doc_id, _trial_error_doc_item(stats, reason)))
    return [item for _, _, item in sorted(items, key=lambda row: (-row[0], row[1]))[:max_items]]


def _build_trial_error_unproven_items(
    tasks: dict[str, dict[str, Any]], *, max_items: int
) -> list[dict[str, Any]]:
    items: list[tuple[int, str, dict[str, Any]]] = []
    for task_id, stats in tasks.items():
        if stats["last_check_outcome"] != "wiki_used":
            continue
        if stats["total_events"] == 0:
            continue
        if _trial_error_signal_count(stats["reuse_effects"]) > 0:
            continue
        score = stats["total_events"] - stats["resolved_events"]
        reason = "AI wiki use recorded without a trial/error reduction effect"
        items.append((score, task_id, _trial_error_task_item(stats, reason)))
    return [item for _, _, item in sorted(items, key=lambda row: (-row[0], row[1]))[:max_items]]


def _build_trial_error_replay_candidates(
    documents: dict[str, dict[str, Any]], *, max_items: int
) -> list[dict[str, Any]]:
    items: list[tuple[int, str, dict[str, Any]]] = []
    for doc_id, stats in documents.items():
        effects = _trial_error_effects(stats["reuse_effects"])
        direct_retry_signals = effects.get("avoided_retry", 0) + effects.get(
            "blocked_wrong_path", 0
        )
        if direct_retry_signals == 0:
            continue
        score = direct_retry_signals * 5 + stats["resolved_events"]
        reason = (
            "direct retry or wrong-path avoidance signal; candidate for formal replay "
            "if a concrete source incident exists"
        )
        items.append((score, doc_id, _trial_error_doc_item(stats, reason)))
    return [item for _, _, item in sorted(items, key=lambda row: (-row[0], row[1]))[:max_items]]


def _build_trial_error_section(
    documents: dict[str, dict[str, Any]], tasks: dict[str, dict[str, Any]], *, max_items: int
) -> dict[str, Any]:
    positive = _build_trial_error_positive_items(documents, max_items=max_items)
    missed = _build_trial_error_missed_items(documents, tasks, max_items=max_items)
    unproven = _build_trial_error_unproven_items(tasks, max_items=max_items)
    replay_candidates = _build_trial_error_replay_candidates(documents, max_items=max_items)
    tasks_with_trial_error_effect = {
        stats["task_id"]
        for stats in tasks.values()
        if _trial_error_signal_count(stats["reuse_effects"]) > 0
    }
    return {
        "summary": {
            "missed_or_repeated_issue_count": len(missed),
            "positive_evidence_count": len(positive),
            "replay_candidate_count": len(replay_candidates),
            "replay_candidates_with_source_incident_timing": sum(
                1
                for item in replay_candidates
                if item.get("source_incident_timing", {}).get("status") == "measured"
            ),
            "tasks_with_trial_error_effect": len(tasks_with_trial_error_effect),
            "trial_error_signal_count": sum(
                item["trial_error_signal_count"] for item in positive
            ),
            "unproven_wiki_use_count": len(unproven),
        },
        "positive_evidence": positive,
        "missed_or_repeated_issue_signals": missed,
        "unproven_wiki_use": unproven,
        "replay_candidates": replay_candidates,
        "interpretation": [
            "Positive evidence means local telemetry recorded a material effect such as avoided_retry or blocked_wrong_path.",
            "Unproven wiki use means AI wiki was used but no trial/error reduction effect was recorded for that task.",
            "Replay candidates still need source incident artifacts before they become formal impact-eval families.",
        ],
    }


def _string_list(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, str) and item]


def _rate(numerator: int, denominator: int) -> float | None:
    if denominator == 0:
        return None
    return numerator / denominator


def _build_route_diagnostics_section(
    traces: list[dict[str, Any]],
    events: list[dict[str, Any]],
    *,
    max_items: int,
    skipped_trace_lines: int,
) -> dict[str, Any]:
    events_by_task: dict[str, list[dict[str, Any]]] = {}
    for event in events:
        task_id = event.get("task_id")
        if isinstance(task_id, str) and task_id:
            events_by_task.setdefault(task_id, []).append(event)

    items: list[dict[str, Any]] = []
    total_selected = 0
    total_useful = 0
    total_selected_useful = 0
    total_noisy_selected = 0
    total_missed = 0
    total_extra_lookups = 0
    total_packet_words = 0
    outcome_effects: Counter[str] = Counter()

    for trace in traces:
        task_id = str(trace.get("task_id", ""))
        selected = set(_string_list(trace.get("selected_doc_ids")))
        task_events = events_by_task.get(task_id, [])
        event_doc_ids = {
            doc_id
            for event in task_events
            if isinstance((doc_id := event.get("doc_id")), str) and doc_id
        }
        useful_events = [
            event
            for event in task_events
            if event.get("reuse_outcome") in {"resolved", "partial"}
            and isinstance(event.get("doc_id"), str)
        ]
        useful_doc_ids = {str(event["doc_id"]) for event in useful_events}
        selected_useful = selected & useful_doc_ids
        noisy_selected = selected - selected_useful
        missed_useful = sorted(
            {
                str(event["doc_id"])
                for event in useful_events
                if event.get("retrieval_mode") == "lookup" and str(event["doc_id"]) not in selected
            }
        )
        extra_lookup_count = len(missed_useful)
        effects = Counter()
        for event in useful_events:
            reuse_effects = event.get("reuse_effects")
            if isinstance(reuse_effects, list):
                effects.update(str(effect) for effect in reuse_effects if str(effect))

        selected_count = len(selected)
        useful_count = len(useful_doc_ids)
        selected_useful_count = len(selected_useful)
        noisy_selected_count = len(noisy_selected)
        packet_words = trace.get("packet_words")
        packet_words = packet_words if isinstance(packet_words, int) else 0

        total_selected += selected_count
        total_useful += useful_count
        total_selected_useful += selected_useful_count
        total_noisy_selected += noisy_selected_count
        total_missed += len(missed_useful)
        total_extra_lookups += extra_lookup_count
        total_packet_words += packet_words
        outcome_effects.update(effects)

        items.append(
            {
                "trace_id": trace.get("trace_id"),
                "task_id": task_id,
                "routed_at": trace.get("routed_at"),
                "task_type": trace.get("task_type"),
                "selected_doc_count": selected_count,
                "useful_doc_count": useful_count,
                "selected_useful_doc_count": selected_useful_count,
                "noisy_selected_doc_count": noisy_selected_count,
                "route_precision": _rate(selected_useful_count, selected_count),
                "route_recall_proxy": _rate(selected_useful_count, useful_count),
                "route_noise_rate": _rate(noisy_selected_count, selected_count),
                "missed_useful_doc_ids": missed_useful,
                "extra_lookup_count": extra_lookup_count,
                "packet_words": packet_words,
                "index_card_count": trace.get("index_card_count", 0),
                "maybe_load_count": trace.get("maybe_load_count", 0),
                "selected_doc_ids": sorted(selected),
                "useful_doc_ids": sorted(useful_doc_ids),
                "selected_without_reuse_doc_ids": sorted(selected - event_doc_ids),
                "outcome_effects": dict(sorted(effects.items())),
            }
        )

    items.sort(
        key=lambda item: (
            -len(item["missed_useful_doc_ids"]),
            -(item["route_noise_rate"] or 0),
            item["task_id"],
        )
    )
    return {
        "summary": {
            "route_trace_count": len(traces),
            "selected_doc_count": total_selected,
            "useful_doc_count": total_useful,
            "useful_selected_doc_count": total_selected_useful,
            "noisy_selected_doc_count": total_noisy_selected,
            "missed_useful_doc_count": total_missed,
            "extra_lookup_count": total_extra_lookups,
            "avg_packet_words": _rate(total_packet_words, len(traces)),
            "avg_selected_docs": _rate(total_selected, len(traces)),
            "route_precision": _rate(total_selected_useful, total_selected),
            "route_recall_proxy": _rate(total_selected_useful, total_useful),
            "route_noise_rate": _rate(total_noisy_selected, total_selected),
            "skipped_trace_lines": skipped_trace_lines,
            "traces_with_missed_useful_docs": sum(
                1 for item in items if item["missed_useful_doc_ids"]
            ),
        },
        "items": items[:max_items],
        "outcome_effects": dict(sorted(outcome_effects.items())),
        "interpretation": [
            "Route precision counts selected docs that later had resolved or partial reuse.",
            "Route recall proxy counts useful docs for the task that were selected by route; it is a proxy because useful-but-unlooked-up docs remain unknown.",
            "Route noise counts selected docs with no useful reuse evidence yet, including docs with no reuse event or only not_helpful outcomes.",
            "Missed useful docs are useful lookup docs that were not in the route-selected set.",
        ],
    }


def build_memory_diagnostics_report(
    repo_wiki_dir: Path,
    *,
    handle: str | None = None,
    since: str | None = None,
    focus: str = "all",
    max_items: int = DEFAULT_DIAGNOSTICS_MAX_ITEMS,
    high_roi_min_events: int = DEFAULT_HIGH_ROI_MIN_EVENTS,
    noisy_min_events: int = DEFAULT_NOISY_MIN_EVENTS,
    generated_at: str | None = None,
) -> dict[str, Any]:
    """Build a deterministic memory diagnostics report from local evidence logs."""
    normalized_focus = focus.strip().lower()
    if normalized_focus not in DIAGNOSTIC_FOCUSES:
        raise ValueError("Invalid --focus. Expected one of: all, route, trial-error.")
    since_cutoff = _parse_since(since)
    all_events, skipped_event_lines = _load_repo_reuse_events(repo_wiki_dir)
    all_checks, skipped_check_lines = _load_repo_task_checks(repo_wiki_dir)
    all_traces, skipped_trace_lines = _load_repo_route_traces(repo_wiki_dir)
    all_source_incidents, skipped_source_incident_lines = _load_repo_source_incidents(repo_wiki_dir)
    events = _filter_reuse_events(all_events, handle=handle, since=since_cutoff)
    checks = _filter_task_checks(all_checks, handle=handle, since=since_cutoff)
    traces = _filter_route_traces(all_traces, handle=handle, since=since_cutoff)
    source_incidents = _filter_source_incidents(all_source_incidents, handle=handle)
    document_metadata = _load_document_metadata(repo_wiki_dir)
    documents = _aggregate_documents(events, document_metadata)
    _attach_source_incident_events(documents, source_incidents, document_metadata)
    tasks = _aggregate_tasks(events, checks)

    checked_tasks = sum(1 for task in tasks.values() if task["check_count"] > 0)
    tasks_with_wiki_use = sum(
        1 for task in tasks.values() if task["last_check_outcome"] == "wiki_used"
    )
    tasks_without_wiki_use = sum(
        1 for task in tasks.values() if task["last_check_outcome"] == "no_wiki_use"
    )
    all_coverage_gaps = _build_coverage_gap_items(tasks, max_items=max(len(tasks), 1))

    report = {
        "schema_version": DIAGNOSTICS_SCHEMA_VERSION,
        "generated_at": generated_at or datetime.now().astimezone().isoformat(timespec="seconds"),
        "filters": {
            "focus": normalized_focus,
            "handle": _normalize_handle_filter(handle),
            "since": since,
            "since_cutoff": since_cutoff.isoformat() if since_cutoff else None,
        },
        "thresholds": {
            "high_roi_min_events": high_roi_min_events,
            "max_items": max_items,
            "noisy_min_events": noisy_min_events,
        },
        "summary": {
            "checked_tasks": checked_tasks,
            "coverage_gap_count": len(all_coverage_gaps),
            "documents_with_reuse": sum(1 for stats in documents.values() if stats["total_events"] > 0),
            "reuse_events": len(events),
            "skipped_check_lines": skipped_check_lines,
            "skipped_event_lines": skipped_event_lines,
            "skipped_source_incident_lines": skipped_source_incident_lines,
            "skipped_trace_lines": skipped_trace_lines,
            "source_incident_events": len(source_incidents),
            "task_checks": len(checks),
            "tasks_with_wiki_use": tasks_with_wiki_use,
            "tasks_without_wiki_use": tasks_without_wiki_use,
            "total_tasks_seen": len(tasks),
            "route_traces": len(traces),
        },
        "high_roi_memory": _build_high_roi_items(
            documents,
            min_events=high_roi_min_events,
            max_items=max_items,
        ),
        "noisy_memory": _build_noisy_items(
            documents,
            min_events=noisy_min_events,
            max_items=max_items,
        ),
        "stale_memory": _build_stale_items(documents, max_items=max_items),
        "conflicting_memory": _build_conflict_items(documents, max_items=max_items),
        "missed_memory": _build_missed_memory_items(documents, tasks, max_items=max_items),
        "coverage_gaps": _build_coverage_gap_items(tasks, max_items=max_items),
        "trial_error_reduction": _build_trial_error_section(
            documents,
            tasks,
            max_items=max_items,
        ),
        "route_diagnostics": _build_route_diagnostics_section(
            traces,
            events,
            max_items=max_items,
            skipped_trace_lines=skipped_trace_lines,
        ),
        "diagnostic_notes": [
            (
                "Route diagnostics join route traces with reuse events by task_id; route recall remains a proxy because useful-but-unlooked-up docs are unknown."
                if traces
                else "No route traces are recorded for this filter; route precision and recall proxy are unavailable."
            ),
            "This report is generated from local evidence logs and should be regenerated rather than edited as canonical memory.",
        ],
    }
    return report


def render_memory_diagnostics_json(report: dict[str, Any]) -> str:
    """Render memory diagnostics as stable JSON."""
    return json.dumps(report, indent=2, sort_keys=True) + "\n"


def _item_label(item: dict[str, Any]) -> str:
    identifier = item.get("doc_id") or item.get("task_id") or "unknown"
    title = item.get("title")
    if isinstance(title, str) and title and title != identifier:
        return f"`{identifier}` - {title}"
    return f"`{identifier}`"


def _format_active_seconds(seconds: object) -> str:
    if not isinstance(seconds, int):
        return "not recorded"
    minutes = seconds / 60
    if minutes >= 1:
        return f"{minutes:.1f} active mins"
    return f"{seconds} active seconds"


def _render_source_incident_timing(item: dict[str, Any]) -> str | None:
    timing = item.get("source_incident_timing")
    if not isinstance(timing, dict):
        return None
    if timing.get("status") != "measured":
        return "not recorded"
    evidence_count = timing.get("evidence_count", 0)
    return (
        f"{_format_active_seconds(timing.get('active_seconds'))} "
        f"({evidence_count} source evidence; source active-turn estimate)"
    )


def _render_doc_section(title: str, items: list[dict[str, Any]]) -> list[str]:
    lines = [f"## {title}", ""]
    if not items:
        lines.extend(["- None detected.", ""])
        return lines
    for item in items:
        lines.append(f"- {_item_label(item)}")
        lines.append(f"  - Reason: {item['reason']}")
        if "total_events" in item:
            lines.append(
                "  - Evidence: "
                f"{item.get('resolved_events', 0)} resolved / {item.get('total_events', 0)} total events; "
                f"{item.get('not_helpful_events', 0)} not_helpful."
            )
            if item.get("not_helpful_events", 0):
                lines.append(
                    "  - Not helpful split: "
                    f"{item.get('confirmed_not_helpful_events', 0)} confirmed / "
                    f"{item.get('candidate_not_helpful_events', 0)} candidate."
                )
        reasons = item.get("not_helpful_reasons")
        if isinstance(reasons, dict) and reasons:
            rendered_reasons = ", ".join(f"{reason}={count}" for reason, count in reasons.items())
            lines.append(f"  - Not helpful reasons: {rendered_reasons}")
        source_sessions = item.get("source_session_ids")
        sessions = item.get("session_ids")
        if isinstance(source_sessions, list) and source_sessions:
            lines.append(
                f"  - Source sessions: {', '.join(f'`{session}`' for session in source_sessions[:5])}"
            )
        if isinstance(sessions, list) and sessions:
            lines.append(
                f"  - Reuse sessions: {', '.join(f'`{session}`' for session in sessions[:5])}"
            )
        effects = item.get("reuse_effects")
        if isinstance(effects, dict) and effects:
            rendered_effects = ", ".join(f"{effect}={count}" for effect, count in effects.items())
            lines.append(f"  - Effects: {rendered_effects}")
        source_incident_timing = _render_source_incident_timing(item)
        if source_incident_timing:
            lines.append(f"  - Source incident timing: {source_incident_timing}")
        tasks = item.get("tasks")
        if isinstance(tasks, list) and tasks:
            lines.append(f"  - Tasks: {', '.join(f'`{task}`' for task in tasks[:5])}")
        path = item.get("path")
        if isinstance(path, str) and path:
            lines.append(f"  - Source: `{path}`")
    lines.append("")
    return lines


def _render_coverage_section(items: list[dict[str, Any]]) -> list[str]:
    lines = ["## Coverage Gaps", ""]
    if not items:
        lines.extend(["- None detected.", ""])
        return lines
    for item in items:
        lines.append(f"- `{item['task_id']}`")
        lines.append(f"  - Reason: {item['reason']}")
        lines.append(
            "  - Evidence: "
            f"{item['resolved_events']} resolved / {item['total_events']} total events; "
            f"last check outcome: `{item['last_check_outcome']}`."
        )
        doc_ids = item.get("doc_ids")
        if isinstance(doc_ids, list) and doc_ids:
            lines.append(f"  - Docs: {', '.join(f'`{doc_id}`' for doc_id in doc_ids[:5])}")
    lines.append("")
    return lines


def _render_trial_error_item(item: dict[str, Any]) -> list[str]:
    lines = [f"- {_item_label(item)}", f"  - Reason: {item['reason']}"]
    effects = item.get("trial_error_effects")
    if isinstance(effects, dict) and effects:
        rendered_effects = ", ".join(f"{effect}={count}" for effect, count in effects.items())
        lines.append(f"  - Trial/error effects: {rendered_effects}")
    if "total_events" in item:
        lines.append(
            "  - Evidence: "
            f"{item.get('resolved_events', 0)} resolved / {item.get('total_events', 0)} total events."
        )
    source_incident_timing = _render_source_incident_timing(item)
    if source_incident_timing:
        lines.append(f"  - Source incident timing: {source_incident_timing}")
    tasks = item.get("tasks")
    if isinstance(tasks, list) and tasks:
        lines.append(f"  - Tasks: {', '.join(f'`{task}`' for task in tasks[:5])}")
    doc_ids = item.get("doc_ids")
    if isinstance(doc_ids, list) and doc_ids:
        lines.append(f"  - Docs: {', '.join(f'`{doc_id}`' for doc_id in doc_ids[:5])}")
    path = item.get("path")
    if isinstance(path, str) and path:
        lines.append(f"  - Source: `{path}`")
    return lines


def _render_trial_error_subsection(title: str, items: list[dict[str, Any]]) -> list[str]:
    lines = [f"### {title}", ""]
    if not items:
        lines.extend(["- None detected.", ""])
        return lines
    for item in items:
        lines.extend(_render_trial_error_item(item))
    lines.append("")
    return lines


def _render_trial_error_section(section: dict[str, Any]) -> list[str]:
    summary = section["summary"]
    lines = [
        "## Trial/Error Reduction",
        "",
        f"- Positive evidence items: {summary['positive_evidence_count']}",
        f"- Tasks with trial/error effects: {summary['tasks_with_trial_error_effect']}",
        f"- Trial/error effect signals: {summary['trial_error_signal_count']}",
        f"- Missed or repeated issue signals: {summary['missed_or_repeated_issue_count']}",
        f"- Unproven wiki-use tasks: {summary['unproven_wiki_use_count']}",
        f"- Replay candidates: {summary['replay_candidate_count']}",
        (
            "- Replay candidates with source incident timing: "
            f"{summary.get('replay_candidates_with_source_incident_timing', 0)}"
        ),
        "",
    ]
    lines.extend(_render_trial_error_subsection("Positive Evidence", section["positive_evidence"]))
    lines.extend(
        _render_trial_error_subsection(
            "Missed Or Repeated Issue Signals",
            section["missed_or_repeated_issue_signals"],
        )
    )
    lines.extend(_render_trial_error_subsection("Unproven Wiki Use", section["unproven_wiki_use"]))
    lines.extend(_render_trial_error_subsection("Replay Candidates", section["replay_candidates"]))
    lines.extend(["### Interpretation", ""])
    for note in section["interpretation"]:
        lines.append(f"- {note}")
    lines.append("")
    return lines


def _format_metric(value: float | None) -> str:
    if value is None:
        return "-"
    return f"{value:.2f}"


def _render_route_diagnostics_section(section: dict[str, Any]) -> list[str]:
    summary = section["summary"]
    lines = [
        "## Route Diagnostics",
        "",
        f"- Route traces: {summary['route_trace_count']}",
        f"- Selected docs: {summary['selected_doc_count']}",
        f"- Useful selected docs: {summary['useful_selected_doc_count']}",
        f"- Missed useful docs: {summary['missed_useful_doc_count']}",
        f"- Extra lookup docs: {summary['extra_lookup_count']}",
        f"- Route precision: `{_format_metric(summary['route_precision'])}`",
        f"- Route recall proxy: `{_format_metric(summary['route_recall_proxy'])}`",
        f"- Route noise rate: `{_format_metric(summary['route_noise_rate'])}`",
        f"- Average packet words: `{_format_metric(summary['avg_packet_words'])}`",
        f"- Average selected docs: `{_format_metric(summary['avg_selected_docs'])}`",
        f"- Skipped trace lines: {summary['skipped_trace_lines']}",
        "",
    ]
    effects = section.get("outcome_effects")
    if isinstance(effects, dict) and effects:
        rendered_effects = ", ".join(f"{effect}={count}" for effect, count in effects.items())
        lines.extend(["### Outcome Effects", "", f"- {rendered_effects}", ""])

    items = section.get("items") if isinstance(section.get("items"), list) else []
    lines.extend(["### Route Trace Items", ""])
    if not items:
        lines.extend(["- None detected.", ""])
    else:
        for item in items:
            lines.append(f"- `{item['task_id']}`")
            lines.append(
                "  - Metrics: "
                f"precision={_format_metric(item['route_precision'])}, "
                f"recall_proxy={_format_metric(item['route_recall_proxy'])}, "
                f"noise={_format_metric(item['route_noise_rate'])}."
            )
            lines.append(
                "  - Context cost: "
                f"{item['packet_words']} packet words, "
                f"{item['selected_doc_count']} selected docs, "
                f"{item['extra_lookup_count']} extra lookup docs."
            )
            missed = item.get("missed_useful_doc_ids")
            if isinstance(missed, list) and missed:
                lines.append(f"  - Missed useful docs: {', '.join(f'`{doc_id}`' for doc_id in missed)}")
            selected_without_reuse = item.get("selected_without_reuse_doc_ids")
            if isinstance(selected_without_reuse, list) and selected_without_reuse:
                lines.append(
                    "  - Selected without reuse: "
                    f"{', '.join(f'`{doc_id}`' for doc_id in selected_without_reuse[:5])}"
                )
    lines.extend(["### Interpretation", ""])
    for note in section["interpretation"]:
        lines.append(f"- {note}")
    lines.append("")
    return lines


def render_memory_diagnostics_markdown(
    report: dict[str, Any],
    *,
    markdown_path: Path | None = None,
    json_path: Path | None = None,
) -> str:
    """Render memory diagnostics as Markdown."""
    summary = report["summary"]
    filters = report["filters"]
    focus = filters.get("focus") or "all"
    title = "AI Wiki Memory Diagnostics"
    if focus == "trial-error":
        title = "AI Wiki Trial/Error Reduction Diagnostics"
    elif focus == "route":
        title = "AI Wiki Route Diagnostics"
    lines = [
        f"# {title}",
        "",
        f"Generated at: `{report['generated_at']}`",
        "",
        "## Filters",
        "",
        f"- Focus: `{focus}`",
        f"- Handle: `{filters['handle'] or 'all'}`",
        f"- Since: `{filters['since'] or 'all'}`",
        "",
    ]
    if markdown_path or json_path:
        lines.extend(["## Generated Outputs", ""])
        if markdown_path:
            lines.append(f"- Markdown: `{markdown_path}`")
        if json_path:
            lines.append(f"- JSON: `{json_path}`")
        lines.append("")
    lines.extend(
        [
            "## Summary",
            "",
            f"- Reuse events: {summary['reuse_events']}",
            f"- Source incident events: {summary.get('source_incident_events', 0)}",
            f"- Task checks: {summary['task_checks']}",
            f"- Route traces: {summary['route_traces']}",
            f"- Checked tasks: {summary['checked_tasks']}",
            f"- Documents with reuse: {summary['documents_with_reuse']}",
            f"- Coverage gaps: {summary['coverage_gap_count']}",
            f"- Skipped event lines: {summary['skipped_event_lines']}",
            f"- Skipped source incident lines: {summary.get('skipped_source_incident_lines', 0)}",
            f"- Skipped check lines: {summary['skipped_check_lines']}",
            f"- Skipped trace lines: {summary['skipped_trace_lines']}",
            "",
        ]
    )
    if focus == "trial-error":
        lines.extend(_render_trial_error_section(report["trial_error_reduction"]))
    elif focus == "route":
        lines.extend(_render_route_diagnostics_section(report["route_diagnostics"]))
    else:
        lines.extend(_render_doc_section("High-ROI Memory", report["high_roi_memory"]))
        lines.extend(_render_doc_section("Noisy Memory", report["noisy_memory"]))
        lines.extend(_render_doc_section("Stale Memory", report["stale_memory"]))
        lines.extend(_render_doc_section("Conflicting Memory", report["conflicting_memory"]))
        lines.extend(_render_doc_section("Missed Memory Signals", report["missed_memory"]))
        lines.extend(_render_coverage_section(report["coverage_gaps"]))
        lines.extend(_render_route_diagnostics_section(report["route_diagnostics"]))
        lines.extend(_render_trial_error_section(report["trial_error_reduction"]))
    lines.extend(["## Diagnostic Notes", ""])
    for note in report["diagnostic_notes"]:
        lines.append(f"- {note}")
    lines.append("")
    return "\n".join(lines)


def generate_memory_diagnostics(
    repo_wiki_dir: Path,
    *,
    handle: str | None = None,
    since: str | None = None,
    focus: str = "all",
    max_items: int = DEFAULT_DIAGNOSTICS_MAX_ITEMS,
    high_roi_min_events: int = DEFAULT_HIGH_ROI_MIN_EVENTS,
    noisy_min_events: int = DEFAULT_NOISY_MIN_EVENTS,
    write: bool = True,
) -> MemoryDiagnosticsResult:
    """Generate and optionally write the AI wiki memory diagnostics report."""
    report = build_memory_diagnostics_report(
        repo_wiki_dir,
        handle=handle,
        since=since,
        focus=focus,
        max_items=max_items,
        high_roi_min_events=high_roi_min_events,
        noisy_min_events=noisy_min_events,
    )
    handle_scope = report["filters"]["handle"] or "all"
    diagnostics_dir = repo_wiki_dir / "_toolkit" / "diagnostics" / handle_scope
    report_stem = "memory-report"
    if report["filters"]["focus"] == "trial-error":
        report_stem = "trial-error-report"
    elif report["filters"]["focus"] == "route":
        report_stem = "route-report"
    markdown_path = diagnostics_dir / f"{report_stem}.md" if write else None
    json_path = diagnostics_dir / f"{report_stem}.json" if write else None
    display_markdown_path = (
        Path(f"ai-wiki/_toolkit/diagnostics/{handle_scope}/{report_stem}.md") if write else None
    )
    display_json_path = (
        Path(f"ai-wiki/_toolkit/diagnostics/{handle_scope}/{report_stem}.json") if write else None
    )
    markdown = render_memory_diagnostics_markdown(
        report,
        markdown_path=display_markdown_path,
        json_path=display_json_path,
    )
    json_text = render_memory_diagnostics_json(report)
    if write:
        diagnostics_dir.mkdir(parents=True, exist_ok=True)
        assert markdown_path is not None
        assert json_path is not None
        markdown_path.write_text(markdown, encoding="utf-8")
        json_path.write_text(json_text, encoding="utf-8")
    return MemoryDiagnosticsResult(
        report=report,
        markdown=markdown,
        json_text=json_text,
        markdown_path=markdown_path,
        json_path=json_path,
    )
