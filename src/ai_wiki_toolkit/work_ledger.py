"""Append-only work ledger helpers for AI wiki task state."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import json
from pathlib import Path
from typing import Any, Iterable, Sequence
from uuid import uuid4

from ai_wiki_toolkit.paths import (
    RepoRootNotFoundError,
    build_paths,
    resolve_model_name,
    resolve_user_handle,
    slugify,
)
from ai_wiki_toolkit.reuse_events import RepoWikiNotInitializedError

WORK_SCHEMA_VERSION = "work-v1"
WORK_ITEM_TYPES = ("task", "epic")
WORK_STATUSES = (
    "inbox",
    "proposed",
    "todo",
    "planned",
    "active",
    "processing",
    "blocked",
    "review",
    "done",
    "archived",
    "dropped",
)
WORK_EVENT_TYPES = ("captured", "status_changed")
OPEN_WORK_STATUSES = {
    "inbox",
    "proposed",
    "todo",
    "planned",
    "active",
    "processing",
    "blocked",
    "review",
}
DEFAULT_STATUS_BY_ITEM_TYPE = {
    "task": "todo",
    "epic": "proposed",
}
STATUS_REPORT_ORDER = (
    "blocked",
    "active",
    "processing",
    "review",
    "planned",
    "todo",
    "inbox",
    "proposed",
    "done",
    "archived",
    "dropped",
)


@dataclass(frozen=True)
class WorkEventResult:
    event_id: str
    occurred_at: str
    author_handle: str
    event_log_path: Path
    state_path: Path
    report_path: Path


@dataclass(frozen=True)
class WorkReportResult:
    state_path: Path
    report_path: Path


def _event_timestamp(explicit_occurred_at: str | None = None) -> str:
    if explicit_occurred_at:
        return explicit_occurred_at
    return datetime.now().astimezone().isoformat(timespec="seconds")


def _append_jsonl(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, sort_keys=True) + "\n")


def _normalize_choice(value: str, allowed: Sequence[str], label: str) -> str:
    normalized = value.strip().lower()
    if normalized not in allowed:
        choices = ", ".join(allowed)
        raise ValueError(f"Invalid {label}: {value!r}. Expected one of: {choices}.")
    return normalized


def _normalize_work_id(work_id: str) -> str:
    normalized = slugify(work_id)
    if not normalized or normalized == "unknown":
        raise ValueError("work_id must not be empty.")
    return normalized


def _normalize_links(links: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    normalized_links: list[str] = []
    for link in links:
        value = link.strip()
        if not value or value in seen:
            continue
        seen.add(value)
        normalized_links.append(value)
    return normalized_links


def _read_jsonl(path: Path) -> tuple[list[dict[str, Any]], int]:
    events: list[dict[str, Any]] = []
    skipped_lines = 0
    if not path.exists():
        return events, skipped_lines
    for line in path.read_text(encoding="utf-8").splitlines():
        candidate = line.strip()
        if not candidate:
            continue
        try:
            payload = json.loads(candidate)
        except json.JSONDecodeError:
            skipped_lines += 1
            continue
        if isinstance(payload, dict):
            payload["_event_log_path"] = path
            events.append(payload)
        else:
            skipped_lines += 1
    return events, skipped_lines


def load_work_events(events_path: Path) -> tuple[list[dict[str, Any]], int]:
    paths: list[Path] = []
    if events_path.is_dir():
        paths.extend(sorted(events_path.glob("*.jsonl")))
    elif events_path.exists():
        paths.append(events_path)
    else:
        return [], 0

    events: list[dict[str, Any]] = []
    skipped_lines = 0
    for path in paths:
        path_events, path_skipped = _read_jsonl(path)
        events.extend(path_events)
        skipped_lines += path_skipped
    return events, skipped_lines


def _source_path_for_event(repo_wiki_dir: Path, event: dict[str, Any]) -> str | None:
    path = event.get("_event_log_path")
    if not isinstance(path, Path):
        return None
    try:
        return f"ai-wiki/{path.relative_to(repo_wiki_dir).as_posix()}"
    except ValueError:
        return path.as_posix()


def _new_work_item(event: dict[str, Any], source_path: str | None) -> dict[str, Any]:
    occurred_at = event.get("occurred_at") if isinstance(event.get("occurred_at"), str) else None
    raw_status = event.get("status")
    status = raw_status.strip().lower() if isinstance(raw_status, str) else None
    return {
        "work_id": event["work_id"],
        "item_type": event["item_type"],
        "title": event.get("title") if isinstance(event.get("title"), str) else event["work_id"],
        "status": status if status in WORK_STATUSES else None,
        "epic_id": None,
        "source": None,
        "links": [],
        "created_at": occurred_at,
        "updated_at": occurred_at,
        "last_event_id": event.get("event_id"),
        "last_notes": None,
        "last_author_handle": event.get("author_handle"),
        "source_paths": [source_path] if source_path else [],
        "_event_count": 0,
        "_link_set": set(),
        "_source_path_set": {source_path} if source_path else set(),
    }


def _apply_event(repo_wiki_dir: Path, item: dict[str, Any], event: dict[str, Any]) -> None:
    item["_event_count"] += 1
    occurred_at = event.get("occurred_at")
    if isinstance(occurred_at, str):
        if item.get("created_at") is None:
            item["created_at"] = occurred_at
        item["updated_at"] = occurred_at
    for field in ("title", "epic_id", "source"):
        value = event.get(field)
        if isinstance(value, str) and value.strip():
            item[field] = value.strip()
    status = event.get("status")
    if isinstance(status, str) and status.strip().lower() in WORK_STATUSES:
        item["status"] = status.strip().lower()
    notes = event.get("notes")
    if isinstance(notes, str) and notes.strip():
        item["last_notes"] = notes.strip()
    author_handle = event.get("author_handle")
    if isinstance(author_handle, str) and author_handle:
        item["last_author_handle"] = author_handle
    event_id = event.get("event_id")
    if isinstance(event_id, str) and event_id:
        item["last_event_id"] = event_id

    link_set = item["_link_set"]
    if isinstance(link_set, set):
        for link in event.get("links", []):
            if isinstance(link, str) and link.strip() and link not in link_set:
                link_set.add(link)
                item["links"].append(link)

    source_path = _source_path_for_event(repo_wiki_dir, event)
    source_path_set = item["_source_path_set"]
    if source_path and isinstance(source_path_set, set) and source_path not in source_path_set:
        source_path_set.add(source_path)
        item["source_paths"].append(source_path)


def _clean_item(item: dict[str, Any]) -> dict[str, Any]:
    cleaned = dict(item)
    cleaned["event_count"] = cleaned.pop("_event_count")
    cleaned.pop("_link_set", None)
    cleaned.pop("_source_path_set", None)
    if cleaned.get("status") is None:
        cleaned["status"] = DEFAULT_STATUS_BY_ITEM_TYPE.get(cleaned["item_type"], "todo")
    return cleaned


def build_work_state(repo_wiki_dir: Path) -> dict[str, Any]:
    events, skipped_lines = load_work_events(repo_wiki_dir / "work" / "events")
    events.sort(
        key=lambda event: (
            event.get("occurred_at") if isinstance(event.get("occurred_at"), str) else "",
            event.get("event_id") if isinstance(event.get("event_id"), str) else "",
        )
    )

    tasks: dict[str, dict[str, Any]] = {}
    epics: dict[str, dict[str, Any]] = {}
    skipped_events = 0
    for event in events:
        item_type = event.get("item_type")
        work_id = event.get("work_id")
        if item_type not in WORK_ITEM_TYPES or not isinstance(work_id, str) or not work_id:
            skipped_events += 1
            continue
        target = tasks if item_type == "task" else epics
        source_path = _source_path_for_event(repo_wiki_dir, event)
        item = target.setdefault(work_id, _new_work_item(event, source_path))
        _apply_event(repo_wiki_dir, item, event)

    rendered_tasks = {work_id: _clean_item(item) for work_id, item in sorted(tasks.items())}
    rendered_epics = {work_id: _clean_item(item) for work_id, item in sorted(epics.items())}

    task_status_counts = {status: 0 for status in WORK_STATUSES}
    epic_status_counts = {status: 0 for status in WORK_STATUSES}
    for item in rendered_tasks.values():
        status = item["status"]
        task_status_counts[status] = task_status_counts.get(status, 0) + 1
    for item in rendered_epics.values():
        status = item["status"]
        epic_status_counts[status] = epic_status_counts.get(status, 0) + 1

    return {
        "schema_version": WORK_SCHEMA_VERSION,
        "skipped_event_lines": skipped_lines,
        "skipped_events": skipped_events,
        "summary": {
            "epic_count": len(rendered_epics),
            "open_epic_count": sum(
                1 for item in rendered_epics.values() if item["status"] in OPEN_WORK_STATUSES
            ),
            "open_task_count": sum(
                1 for item in rendered_tasks.values() if item["status"] in OPEN_WORK_STATUSES
            ),
            "task_count": len(rendered_tasks),
            "epics_by_status": {k: v for k, v in epic_status_counts.items() if v},
            "tasks_by_status": {k: v for k, v in task_status_counts.items() if v},
        },
        "epics": rendered_epics,
        "tasks": rendered_tasks,
    }


def render_work_state_json(repo_wiki_dir: Path) -> str:
    return json.dumps(build_work_state(repo_wiki_dir), indent=2, sort_keys=True) + "\n"


def _format_item_line(item: dict[str, Any]) -> str:
    parts = [
        f"`{item['work_id']}`",
        f"**{item['title']}**",
    ]
    if item.get("epic_id"):
        parts.append(f"epic: `{item['epic_id']}`")
    if item.get("links"):
        links = ", ".join(f"`{link}`" for link in item["links"][:3])
        parts.append(f"links: {links}")
    if item.get("last_notes"):
        parts.append(f"note: {item['last_notes']}")
    return "- " + " - ".join(parts)


def _render_group(title: str, items: list[dict[str, Any]]) -> list[str]:
    lines = [f"## {title}"]
    if not items:
        lines.append("- None.")
        return lines
    for item in items:
        lines.append(_format_item_line(item))
    return lines


def render_work_report(repo_wiki_dir: Path) -> str:
    state = build_work_state(repo_wiki_dir)
    tasks = list(state["tasks"].values())
    epics = list(state["epics"].values())

    def by_status(statuses: set[str], values: list[dict[str, Any]]) -> list[dict[str, Any]]:
        return sorted(
            [item for item in values if item["status"] in statuses],
            key=lambda item: (
                STATUS_REPORT_ORDER.index(item["status"])
                if item["status"] in STATUS_REPORT_ORDER
                else len(STATUS_REPORT_ORDER),
                item.get("updated_at") or "",
                item["work_id"],
            ),
        )

    summary = state["summary"]
    lines: list[str] = [
        "# AI Wiki Work Report",
        "",
        "This generated report is derived from `ai-wiki/work/events/*.jsonl`.",
        "Regenerate it with `aiwiki-toolkit work report`.",
        "",
        "## Summary",
        f"- Open epics: {summary['open_epic_count']} / {summary['epic_count']}",
        f"- Open tasks: {summary['open_task_count']} / {summary['task_count']}",
        "",
    ]
    lines.extend(_render_group("Open Epics", by_status(OPEN_WORK_STATUSES, epics)))
    lines.append("")
    lines.extend(
        _render_group(
            "Active Or Blocked Tasks",
            by_status({"active", "processing", "blocked", "review"}, tasks),
        )
    )
    lines.append("")
    lines.extend(_render_group("Planned Tasks", by_status({"inbox", "proposed", "todo", "planned"}, tasks)))
    lines.append("")
    lines.extend(_render_group("Done Or Archived Tasks", by_status({"done", "archived", "dropped"}, tasks)))
    return "\n".join(lines) + "\n"


def refresh_work_views(repo_wiki_dir: Path) -> tuple[Path, Path]:
    work_dir = repo_wiki_dir / "_toolkit" / "work"
    work_dir.mkdir(parents=True, exist_ok=True)
    state_path = work_dir / "state.json"
    report_path = work_dir / "report.md"
    state_path.write_text(render_work_state_json(repo_wiki_dir), encoding="utf-8")
    report_path.write_text(render_work_report(repo_wiki_dir), encoding="utf-8")
    return state_path, report_path


def record_work_event(
    *,
    event_type: str,
    item_type: str,
    work_id: str,
    status: str | None = None,
    title: str | None = None,
    epic_id: str | None = None,
    source: str | None = None,
    links: Sequence[str] = (),
    agent_name: str | None = None,
    model: str | None = None,
    notes: str | None = None,
    occurred_at: str | None = None,
    handle: str | None = None,
    start: Path | None = None,
) -> WorkEventResult:
    paths = build_paths(start)
    if not paths.repo_wiki_dir.exists():
        raise RepoWikiNotInitializedError(
            "Repo AI wiki is not initialized. Run `aiwiki-toolkit install` first."
        )

    normalized_event_type = _normalize_choice(event_type, WORK_EVENT_TYPES, "work event type")
    normalized_item_type = _normalize_choice(item_type, WORK_ITEM_TYPES, "work item type")
    normalized_work_id = _normalize_work_id(work_id)
    normalized_status = (
        _normalize_choice(status, WORK_STATUSES, "work status")
        if status
        else DEFAULT_STATUS_BY_ITEM_TYPE[normalized_item_type]
    )
    if normalized_event_type == "captured" and (not title or not title.strip()):
        raise ValueError("title is required when capturing a work item.")

    resolved_handle = resolve_user_handle(paths.repo_root, explicit_handle=handle)
    resolved_model = resolve_model_name(explicit_model=model)
    resolved_occurred_at = _event_timestamp(occurred_at)
    event_id = f"wrk_{uuid4().hex[:12]}"

    payload: dict[str, object] = {
        "schema_version": WORK_SCHEMA_VERSION,
        "event_id": event_id,
        "event_type": normalized_event_type,
        "occurred_at": resolved_occurred_at,
        "author_handle": resolved_handle,
        "item_type": normalized_item_type,
        "work_id": normalized_work_id,
        "status": normalized_status,
    }
    if title and title.strip():
        payload["title"] = title.strip()
    if epic_id and epic_id.strip():
        payload["epic_id"] = _normalize_work_id(epic_id)
    if source and source.strip():
        payload["source"] = source.strip()
    normalized_links = _normalize_links(links)
    if normalized_links:
        payload["links"] = normalized_links
    if agent_name and agent_name.strip():
        payload["agent_name"] = agent_name.strip()
    if resolved_model:
        payload["model"] = resolved_model
    if notes and notes.strip():
        payload["notes"] = notes.strip()

    event_log_path = paths.repo_wiki_dir / "work" / "events" / f"{resolved_handle}.jsonl"
    _append_jsonl(event_log_path, payload)
    state_path, report_path = refresh_work_views(paths.repo_wiki_dir)

    return WorkEventResult(
        event_id=event_id,
        occurred_at=resolved_occurred_at,
        author_handle=resolved_handle,
        event_log_path=event_log_path,
        state_path=state_path,
        report_path=report_path,
    )


def refresh_work_report(start: Path | None = None) -> WorkReportResult:
    paths = build_paths(start)
    if not paths.repo_wiki_dir.exists():
        raise RepoWikiNotInitializedError(
            "Repo AI wiki is not initialized. Run `aiwiki-toolkit install` first."
        )
    state_path, report_path = refresh_work_views(paths.repo_wiki_dir)
    return WorkReportResult(state_path=state_path, report_path=report_path)
