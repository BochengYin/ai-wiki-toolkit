"""AI wiki usefulness report helpers."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
from typing import Any

from ai_wiki_toolkit.frontmatter import parse_frontmatter
from ai_wiki_toolkit.wiki_schema import infer_doc_kind, load_reuse_events, load_task_checks

USEFULNESS_REPORT_SCHEMA_VERSION = "usefulness-report-v1"


@dataclass(frozen=True)
class UsefulnessReportResult:
    """Rendered usefulness report and optional generated output paths."""

    report: dict[str, Any]
    markdown: str
    json_text: str
    markdown_path: Path | None = None
    json_path: Path | None = None


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
        return (now or datetime.now(timezone.utc)).astimezone(timezone.utc) - timedelta(
            days=int(normalized[:-1])
        )
    parsed = _parse_timestamp(normalized)
    if parsed is None:
        raise ValueError("Invalid --since value. Use an ISO timestamp or a duration like 14d.")
    return parsed


def _timestamp_matches(
    payload: dict[str, Any],
    key: str,
    since: datetime | None,
    until: datetime | None,
) -> bool:
    parsed = _parse_timestamp(payload.get(key))
    if parsed is None:
        return since is None and until is None
    if since is not None and parsed < since:
        return False
    if until is not None and parsed >= until:
        return False
    return True


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


def _load_repo_reuse_events(repo_wiki_dir: Path) -> tuple[list[dict[str, Any]], int]:
    legacy_events, legacy_skipped = load_reuse_events(repo_wiki_dir / "metrics" / "reuse-events.jsonl")
    sharded_events, sharded_skipped = load_reuse_events(repo_wiki_dir / "metrics" / "reuse-events")
    return legacy_events + sharded_events, legacy_skipped + sharded_skipped


def _load_repo_task_checks(repo_wiki_dir: Path) -> tuple[list[dict[str, Any]], int]:
    legacy_checks, legacy_skipped = load_task_checks(repo_wiki_dir / "metrics" / "task-checks.jsonl")
    sharded_checks, sharded_skipped = load_task_checks(repo_wiki_dir / "metrics" / "task-checks")
    return legacy_checks + sharded_checks, legacy_skipped + sharded_skipped


def _normalize_handle(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = value.strip()
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
    parts = normalized.split("/")
    if normalized.startswith("/") or any(part in {"", ".", ".."} for part in parts):
        return None
    return normalized


def _filter_events(
    events: list[dict[str, Any]],
    *,
    handle: str | None,
    since: datetime | None,
    until: datetime | None,
) -> list[dict[str, Any]]:
    normalized_handle = _normalize_handle(handle)
    filtered: list[dict[str, Any]] = []
    for event in events:
        if normalized_handle and event.get("author_handle") != normalized_handle:
            continue
        if not _timestamp_matches(event, "observed_at", since, until):
            continue
        doc_id = _normalize_doc_id(event.get("doc_id"))
        if doc_id is None:
            continue
        filtered.append(event | {"doc_id": doc_id})
    return filtered


def _filter_checks(
    checks: list[dict[str, Any]],
    *,
    handle: str | None,
    since: datetime | None,
    until: datetime | None,
) -> list[dict[str, Any]]:
    normalized_handle = _normalize_handle(handle)
    filtered: list[dict[str, Any]] = []
    for check in checks:
        if normalized_handle and check.get("author_handle") != normalized_handle:
            continue
        if not _timestamp_matches(check, "checked_at", since, until):
            continue
        task_id = check.get("task_id")
        if isinstance(task_id, str) and task_id:
            filtered.append(check)
    return filtered


def _estimated_savings(event: dict[str, Any]) -> tuple[int, int]:
    estimates = event.get("estimated_savings")
    if not isinstance(estimates, dict):
        return 0, 0
    seconds = estimates.get("saved_seconds")
    tokens = estimates.get("saved_tokens")
    return (
        seconds if isinstance(seconds, int) else 0,
        tokens if isinstance(tokens, int) else 0,
    )


def _optional_string(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    normalized = value.strip()
    return normalized or None


def _timing_value(payload: dict[str, Any], keys: tuple[str, ...]) -> int | None:
    sources: list[Any] = [payload]
    timing = payload.get("timing")
    if isinstance(timing, dict):
        sources.append(timing)
    time_evidence = payload.get("time_evidence")
    if isinstance(time_evidence, dict):
        sources.append(time_evidence)
    for source in sources:
        if not isinstance(source, dict):
            continue
        for key in keys:
            value = source.get(key)
            if isinstance(value, int) and value >= 0:
                return value
    return None


def _document_title(repo_wiki_dir: Path, doc_id: str) -> tuple[str, str, bool]:
    path = repo_wiki_dir / f"{doc_id}.md"
    if not path.exists() or not path.is_file():
        return doc_id.rsplit("/", maxsplit=1)[-1].replace("-", " "), f"ai-wiki/{doc_id}.md", False
    text = path.read_text(encoding="utf-8")
    metadata, body = parse_frontmatter(text)
    title = metadata.get("title")
    if isinstance(title, str) and title.strip():
        return title.strip(), f"ai-wiki/{doc_id}.md", True
    for line in body.splitlines():
        if line.startswith("# "):
            return line[2:].strip(), f"ai-wiki/{doc_id}.md", True
    return path.stem.replace("-", " ").replace("_", " "), f"ai-wiki/{doc_id}.md", True


def _format_seconds(value: int | None) -> str:
    if value is None:
        return "unknown"
    if value <= 0:
        return "0s"
    minutes, seconds = divmod(value, 60)
    if minutes == 0:
        return f"{value}s"
    hours, minutes = divmod(minutes, 60)
    if hours == 0:
        return f"{value}s ({minutes}m {seconds}s)"
    return f"{value}s ({hours}h {minutes}m {seconds}s)"


def _aggregate_documents(repo_wiki_dir: Path, events: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    documents: dict[str, dict[str, Any]] = {}
    for event in events:
        doc_id = event["doc_id"]
        title, path, source_exists = _document_title(repo_wiki_dir, doc_id)
        stats = documents.setdefault(
            doc_id,
            {
                "doc_id": doc_id,
                "doc_kind": event.get("doc_kind") or infer_doc_kind(f"{doc_id}.md"),
                "candidate_not_helpful_events": 0,
                "confirmed_not_helpful_events": 0,
                "estimated_seconds_saved": 0,
                "estimated_token_savings": 0,
                "last_observed_at": None,
                "lookup_reuse_count": 0,
                "not_helpful_reasons": Counter(),
                "not_helpful_events": 0,
                "partial_events": 0,
                "path": path,
                "preloaded_reuse_count": 0,
                "resolved_by_doc_ids": set(),
                "resolved_events": 0,
                "reuse_effects": Counter(),
                "session_ids": set(),
                "source_exists": source_exists,
                "source_session_ids": set(),
                "source_task_ids": set(),
                "superseded_by_doc_ids": set(),
                "tasks": set(),
                "title": title,
                "total_events": 0,
            },
        )
        stats["total_events"] += 1
        outcome = event.get("reuse_outcome")
        if outcome == "resolved":
            stats["resolved_events"] += 1
            saved_seconds, saved_tokens = _estimated_savings(event)
            stats["estimated_seconds_saved"] += saved_seconds
            stats["estimated_token_savings"] += saved_tokens
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
        task_id = event.get("task_id")
        if isinstance(task_id, str) and task_id:
            stats["tasks"].add(task_id)
        retrieval_mode = event.get("retrieval_mode")
        if retrieval_mode == "lookup":
            stats["lookup_reuse_count"] += 1
        elif retrieval_mode == "preloaded":
            stats["preloaded_reuse_count"] += 1
        effects = event.get("reuse_effects")
        if isinstance(effects, list):
            for effect in effects:
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
        stats["last_observed_at"] = _last_timestamp(stats["last_observed_at"], event.get("observed_at"))
    return documents


def _document_item(stats: dict[str, Any]) -> dict[str, Any]:
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
        "resolved_events": stats["resolved_events"],
        "reuse_effects": dict(sorted(stats["reuse_effects"].items())),
        "session_ids": sorted(stats["session_ids"]),
        "source_exists": stats["source_exists"],
        "source_session_ids": sorted(stats["source_session_ids"]),
        "source_task_ids": sorted(stats["source_task_ids"]),
        "superseded_by_doc_ids": sorted(stats["superseded_by_doc_ids"]),
        "tasks": sorted(stats["tasks"]),
        "title": stats["title"],
        "total_events": stats["total_events"],
    }


def _timing_summary(events: list[dict[str, Any]]) -> dict[str, Any]:
    first_values: list[int] = []
    current_values: list[int] = []
    remaining_values: list[int] = []
    estimated_seconds_saved = 0
    estimated_token_savings = 0
    for event in events:
        if event.get("reuse_outcome") == "resolved":
            saved_seconds, saved_tokens = _estimated_savings(event)
            estimated_seconds_saved += saved_seconds
            estimated_token_savings += saved_tokens
        first = _timing_value(
            event,
            ("first_trial_error_seconds", "baseline_seconds", "first_attempt_seconds"),
        )
        current = _timing_value(event, ("current_elapsed_seconds", "current_seconds", "after_seconds"))
        remaining = _timing_value(event, ("remaining_seconds", "unresolved_seconds"))
        if first is not None:
            first_values.append(first)
        if current is not None:
            current_values.append(current)
        if remaining is not None:
            remaining_values.append(remaining)
    first_total = sum(first_values) if first_values else None
    current_total = sum(current_values) if current_values else None
    remaining_total = sum(remaining_values) if remaining_values else None
    measured_saved = (
        max(first_total - current_total, 0)
        if first_total is not None and current_total is not None
        else None
    )
    return {
        "current_elapsed_seconds": current_total,
        "estimated_seconds_saved_from_resolved_reuse": estimated_seconds_saved,
        "estimated_token_savings_from_resolved_reuse": estimated_token_savings,
        "first_trial_error_seconds": first_total,
        "measurement_note": (
            "baseline/current/remaining durations are unknown unless reuse events include timing evidence"
        ),
        "measured_seconds_saved": measured_saved,
        "remaining_seconds": remaining_total,
    }


def build_usefulness_report(
    repo_wiki_dir: Path,
    *,
    handle: str | None = None,
    since: str | None = None,
    until: str | None = None,
    generated_at: str | None = None,
) -> dict[str, Any]:
    """Build a usefulness report from local reuse evidence."""
    generated_at = generated_at or datetime.now().astimezone().isoformat(timespec="seconds")
    since_dt = _parse_since(since)
    until_dt = _parse_since(until)
    events, skipped_event_lines = _load_repo_reuse_events(repo_wiki_dir)
    checks, skipped_check_lines = _load_repo_task_checks(repo_wiki_dir)
    filtered_events = _filter_events(events, handle=handle, since=since_dt, until=until_dt)
    filtered_checks = _filter_checks(checks, handle=handle, since=since_dt, until=until_dt)
    document_stats = _aggregate_documents(repo_wiki_dir, filtered_events)
    documents = sorted(
        [_document_item(stats) for stats in document_stats.values()],
        key=lambda item: (-item["resolved_events"], item["doc_id"]),
    )
    referenced_tasks = {
        task_id
        for event in filtered_events
        for task_id in [event.get("task_id")]
        if isinstance(task_id, str) and task_id
    }
    timing = _timing_summary(filtered_events)
    return {
        "schema_version": USEFULNESS_REPORT_SCHEMA_VERSION,
        "generated_at": generated_at,
        "filters": {
            "handle": _normalize_handle(handle) or "all",
            "since": since,
            "until": until,
        },
        "summary": {
            "documents_referenced": len(documents),
            "reuse_events": len(filtered_events),
            "skipped_check_lines": skipped_check_lines,
            "skipped_event_lines": skipped_event_lines,
            "task_checks": len(filtered_checks),
            "tasks_with_references": len(referenced_tasks),
            "total_estimated_seconds_saved": timing[
                "estimated_seconds_saved_from_resolved_reuse"
            ],
            "total_estimated_token_savings": timing[
                "estimated_token_savings_from_resolved_reuse"
            ],
        },
        "timing": timing,
        "referenced_documents": documents,
        "notes": [
            "This report is generated from local evidence logs and should not be treated as canonical guidance.",
            "Estimated savings are counted only from resolved reuse events.",
            "Baseline/current/remaining durations require explicit timing evidence in future task logs.",
        ],
    }


def render_usefulness_report_json(report: dict[str, Any]) -> str:
    """Render usefulness report as stable JSON."""
    return json.dumps(report, indent=2, sort_keys=True) + "\n"


def render_usefulness_report_markdown(
    report: dict[str, Any],
    *,
    markdown_path: Path | None = None,
    json_path: Path | None = None,
) -> str:
    """Render usefulness report as Markdown."""
    filters = report["filters"]
    summary = report["summary"]
    timing = report["timing"]
    lines = [
        "# AI Wiki Usefulness Report",
        "",
        f"Generated at: `{report['generated_at']}`",
        "",
        "## Filters",
        "",
        f"- Handle: `{filters['handle']}`",
        f"- Since: `{filters['since'] or 'all'}`",
        f"- Until: `{filters['until'] or 'all'}`",
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
            f"- Documents referenced: {summary['documents_referenced']}",
            f"- Tasks with references: {summary['tasks_with_references']}",
            f"- Estimated time saved from resolved reuse: {_format_seconds(summary['total_estimated_seconds_saved'])}",
            f"- Estimated token savings from resolved reuse: {summary['total_estimated_token_savings']}",
            "",
            "## Timing",
            "",
            f"- First trial/error time: {_format_seconds(timing['first_trial_error_seconds'])}",
            f"- Current observed time: {_format_seconds(timing['current_elapsed_seconds'])}",
            f"- Measured time saved: {_format_seconds(timing['measured_seconds_saved'])}",
            f"- Remaining time: {_format_seconds(timing['remaining_seconds'])}",
            f"- Estimated time saved from resolved reuse: {_format_seconds(timing['estimated_seconds_saved_from_resolved_reuse'])}",
            f"- Note: {timing['measurement_note']}",
            "",
            "## Referenced Files",
            "",
        ]
    )
    if not report["referenced_documents"]:
        lines.extend(["- None detected.", ""])
    else:
        for item in report["referenced_documents"]:
            lines.append(
                f"- `{item['path']}` - {item['title']} "
                f"({item['resolved_events']} resolved, {item['partial_events']} partial, "
                f"{item['not_helpful_events']} not_helpful)"
            )
        lines.append("")
    lines.extend(["## Notes", ""])
    for note in report["notes"]:
        lines.append(f"- {note}")
    lines.append("")
    return "\n".join(lines)


def generate_usefulness_report(
    repo_wiki_dir: Path,
    *,
    handle: str | None = None,
    since: str | None = None,
    until: str | None = None,
    write: bool = True,
) -> UsefulnessReportResult:
    """Generate and optionally write a local usefulness report."""
    report = build_usefulness_report(repo_wiki_dir, handle=handle, since=since, until=until)
    handle_scope = report["filters"]["handle"] or "all"
    report_dir = repo_wiki_dir / "_toolkit" / "reports" / "usefulness" / handle_scope
    markdown_path = report_dir / "latest.md" if write else None
    json_path = report_dir / "latest.json" if write else None
    display_markdown_path = (
        Path(f"ai-wiki/_toolkit/reports/usefulness/{handle_scope}/latest.md") if write else None
    )
    display_json_path = (
        Path(f"ai-wiki/_toolkit/reports/usefulness/{handle_scope}/latest.json") if write else None
    )
    markdown = render_usefulness_report_markdown(
        report,
        markdown_path=display_markdown_path,
        json_path=display_json_path,
    )
    json_text = render_usefulness_report_json(report)
    if write:
        report_dir.mkdir(parents=True, exist_ok=True)
        assert markdown_path is not None
        assert json_path is not None
        markdown_path.write_text(markdown, encoding="utf-8")
        json_path.write_text(json_text, encoding="utf-8")
    return UsefulnessReportResult(
        report=report,
        markdown=markdown,
        json_text=json_text,
        markdown_path=markdown_path,
        json_path=json_path,
    )
