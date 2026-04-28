"""AI wiki diagnostic report helpers."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
from typing import Any

from ai_wiki_toolkit.frontmatter import parse_frontmatter
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
HIGH_VALUE_REUSE_EFFECTS = {
    "avoided_retry",
    "avoided_search",
    "blocked_wrong_path",
    "faster_resolution",
    "release_safety",
    "verified_release_matrix",
}
STALE_KEYWORDS = ("stale", "outdated", "obsolete", "superseded")
CONFLICT_KEYWORDS = ("conflict", "conflicting", "contradict", "inconsistent")
MISSED_MEMORY_KEYWORDS = (
    "missed memory",
    "missed relevant memory",
    "should have used",
    "should have read",
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


def _note_text(payload: dict[str, Any]) -> str:
    notes = payload.get("notes")
    return notes if isinstance(notes, str) else ""


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


def _aggregate_documents(
    events: list[dict[str, Any]], document_metadata: dict[str, dict[str, Any]]
) -> dict[str, dict[str, Any]]:
    documents: dict[str, dict[str, Any]] = {}
    for event in events:
        doc_id = event["doc_id"]
        metadata = document_metadata.get(doc_id, {})
        stats = documents.setdefault(
            doc_id,
            {
                "doc_id": doc_id,
                "doc_kind": event.get("doc_kind") or metadata.get("doc_kind") or infer_doc_kind(f"{doc_id}.md"),
                "path": metadata.get("path"),
                "status": metadata.get("status"),
                "title": metadata.get("title") or doc_id,
                "total_events": 0,
                "resolved_events": 0,
                "partial_events": 0,
                "not_helpful_events": 0,
                "lookup_reuse_count": 0,
                "preloaded_reuse_count": 0,
                "estimated_token_savings": 0,
                "estimated_seconds_saved": 0,
                "reuse_effects": Counter(),
                "tasks": set(),
                "last_observed_at": None,
                "stale_note_count": 0,
                "conflict_note_count": 0,
                "missed_note_count": 0,
            },
        )
        stats["total_events"] += 1
        outcome = event.get("reuse_outcome")
        if outcome == "resolved":
            stats["resolved_events"] += 1
        elif outcome == "partial":
            stats["partial_events"] += 1
        elif outcome == "not_helpful":
            stats["not_helpful_events"] += 1
        retrieval_mode = event.get("retrieval_mode")
        if retrieval_mode == "lookup":
            stats["lookup_reuse_count"] += 1
        elif retrieval_mode == "preloaded":
            stats["preloaded_reuse_count"] += 1
        saved_tokens, saved_seconds = _estimated_savings(event)
        stats["estimated_token_savings"] += saved_tokens
        stats["estimated_seconds_saved"] += saved_seconds
        reuse_effects = event.get("reuse_effects")
        if isinstance(reuse_effects, list):
            for effect in reuse_effects:
                if isinstance(effect, str) and effect.strip():
                    stats["reuse_effects"][effect.strip()] += 1
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
                "notes": [],
            },
        )
        stats["total_events"] += 1
        if event.get("reuse_outcome") == "resolved":
            stats["resolved_events"] += 1
        doc_id = event.get("doc_id")
        if isinstance(doc_id, str) and doc_id:
            stats["doc_ids"].add(doc_id)
        notes = _note_text(event)
        if notes:
            stats["notes"].append(notes)
    return tasks


def _doc_item(stats: dict[str, Any], reason: str) -> dict[str, Any]:
    effects: Counter[str] = stats["reuse_effects"]
    return {
        "doc_id": stats["doc_id"],
        "doc_kind": stats["doc_kind"],
        "estimated_seconds_saved": stats["estimated_seconds_saved"],
        "estimated_token_savings": stats["estimated_token_savings"],
        "last_observed_at": stats["last_observed_at"],
        "lookup_reuse_count": stats["lookup_reuse_count"],
        "not_helpful_events": stats["not_helpful_events"],
        "partial_events": stats["partial_events"],
        "path": stats["path"],
        "preloaded_reuse_count": stats["preloaded_reuse_count"],
        "reason": reason,
        "resolved_events": stats["resolved_events"],
        "reuse_effects": dict(sorted(effects.items())),
        "status": stats["status"],
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
        if stats["not_helpful_events"]:
            reason = f"{stats['not_helpful_events']} not_helpful reuse events"
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


def build_memory_diagnostics_report(
    repo_wiki_dir: Path,
    *,
    handle: str | None = None,
    since: str | None = None,
    max_items: int = DEFAULT_DIAGNOSTICS_MAX_ITEMS,
    high_roi_min_events: int = DEFAULT_HIGH_ROI_MIN_EVENTS,
    noisy_min_events: int = DEFAULT_NOISY_MIN_EVENTS,
    generated_at: str | None = None,
) -> dict[str, Any]:
    """Build a deterministic memory diagnostics report from local evidence logs."""
    since_cutoff = _parse_since(since)
    all_events, skipped_event_lines = _load_repo_reuse_events(repo_wiki_dir)
    all_checks, skipped_check_lines = _load_repo_task_checks(repo_wiki_dir)
    events = _filter_reuse_events(all_events, handle=handle, since=since_cutoff)
    checks = _filter_task_checks(all_checks, handle=handle, since=since_cutoff)
    document_metadata = _load_document_metadata(repo_wiki_dir)
    documents = _aggregate_documents(events, document_metadata)
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
            "documents_with_reuse": len(documents),
            "reuse_events": len(events),
            "skipped_check_lines": skipped_check_lines,
            "skipped_event_lines": skipped_event_lines,
            "task_checks": len(checks),
            "tasks_with_wiki_use": tasks_with_wiki_use,
            "tasks_without_wiki_use": tasks_without_wiki_use,
            "total_tasks_seen": len(tasks),
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
        "diagnostic_notes": [
            "Route selection traces are not recorded yet; missed and noisy route diagnosis is limited to reuse/check evidence and notes.",
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
        effects = item.get("reuse_effects")
        if isinstance(effects, dict) and effects:
            rendered_effects = ", ".join(f"{effect}={count}" for effect, count in effects.items())
            lines.append(f"  - Effects: {rendered_effects}")
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


def render_memory_diagnostics_markdown(
    report: dict[str, Any],
    *,
    markdown_path: Path | None = None,
    json_path: Path | None = None,
) -> str:
    """Render memory diagnostics as Markdown."""
    summary = report["summary"]
    filters = report["filters"]
    lines = [
        "# AI Wiki Memory Diagnostics",
        "",
        f"Generated at: `{report['generated_at']}`",
        "",
        "## Filters",
        "",
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
            f"- Task checks: {summary['task_checks']}",
            f"- Checked tasks: {summary['checked_tasks']}",
            f"- Documents with reuse: {summary['documents_with_reuse']}",
            f"- Coverage gaps: {summary['coverage_gap_count']}",
            f"- Skipped event lines: {summary['skipped_event_lines']}",
            f"- Skipped check lines: {summary['skipped_check_lines']}",
            "",
        ]
    )
    lines.extend(_render_doc_section("High-ROI Memory", report["high_roi_memory"]))
    lines.extend(_render_doc_section("Noisy Memory", report["noisy_memory"]))
    lines.extend(_render_doc_section("Stale Memory", report["stale_memory"]))
    lines.extend(_render_doc_section("Conflicting Memory", report["conflicting_memory"]))
    lines.extend(_render_doc_section("Missed Memory Signals", report["missed_memory"]))
    lines.extend(_render_coverage_section(report["coverage_gaps"]))
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
        max_items=max_items,
        high_roi_min_events=high_roi_min_events,
        noisy_min_events=noisy_min_events,
    )
    diagnostics_dir = repo_wiki_dir / "_toolkit" / "diagnostics"
    markdown_path = diagnostics_dir / "memory-report.md" if write else None
    json_path = diagnostics_dir / "memory-report.json" if write else None
    display_markdown_path = Path("ai-wiki/_toolkit/diagnostics/memory-report.md") if write else None
    display_json_path = Path("ai-wiki/_toolkit/diagnostics/memory-report.json") if write else None
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
