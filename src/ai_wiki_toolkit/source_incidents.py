"""Source incident timing helpers."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

SOURCE_INCIDENT_TIMING_LABEL = "source active-turn estimate"
SOURCE_INCIDENT_TIMING_SOURCES = ("manual", "codex_session", "external")
SOURCE_INCIDENT_SESSION_EVENT_TYPES = ("task_complete", "turn_aborted")


def _duration_ms(value: object) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value if value >= 0 else None
    if isinstance(value, float):
        return int(value) if value >= 0 else None
    return None


def _normalize_session_id(value: str) -> str:
    normalized = value.strip()
    if not normalized:
        raise ValueError("source_session_id must not be empty.")
    return normalized


def _session_id_matches(path: Path, row: dict[str, Any], session_id: str) -> bool:
    payload = row.get("payload")
    if not isinstance(payload, dict):
        return False
    if payload.get("id") == session_id:
        return True
    if payload.get("session_id") == session_id:
        return True
    return session_id in path.name


def _iter_session_rows(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return rows
    for line in lines:
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(row, dict):
            rows.append(row)
    return rows


def _find_codex_session_file(
    session_id: str, sessions_root: Path
) -> tuple[Path, list[dict[str, Any]]] | None:
    for path in sorted(sessions_root.rglob("*.jsonl")):
        rows = _iter_session_rows(path)
        if not rows:
            continue
        if any(_session_id_matches(path, row, session_id) for row in rows):
            return path, rows
    return None


def source_incident_from_seconds(
    *,
    active_seconds: int,
    timing_source: str,
    note: str | None = None,
) -> dict[str, object]:
    """Build a source incident timing payload from an explicit duration."""

    if active_seconds < 0:
        raise ValueError("source incident seconds must be 0 or greater.")
    normalized_source = timing_source.strip().lower()
    if normalized_source not in SOURCE_INCIDENT_TIMING_SOURCES:
        choices = ", ".join(SOURCE_INCIDENT_TIMING_SOURCES)
        raise ValueError(
            f"Invalid source incident timing source: {timing_source!r}. Expected one of: {choices}."
        )

    payload: dict[str, object] = {
        "active_seconds": active_seconds,
        "duration_ms": active_seconds * 1000,
        "timing_label": SOURCE_INCIDENT_TIMING_LABEL,
        "timing_source": normalized_source,
    }
    if note and note.strip():
        payload["note"] = note.strip()
    return payload


def source_incident_from_codex_session(
    *,
    session_id: str,
    sessions_root: Path | None = None,
    include_aborted: bool = True,
    note: str | None = None,
) -> dict[str, object]:
    """Derive active-turn source incident timing from a local Codex session JSONL file."""

    normalized_session_id = _normalize_session_id(session_id)
    root = sessions_root or Path.home() / ".codex" / "sessions"
    if not root.exists():
        raise ValueError(f"Codex sessions root does not exist: {root}")

    match = _find_codex_session_file(normalized_session_id, root)
    if match is None:
        raise ValueError(f"Could not find Codex session id {normalized_session_id!r} under {root}.")

    session_path, rows = match
    included_event_types = [SOURCE_INCIDENT_SESSION_EVENT_TYPES[0]]
    if include_aborted:
        included_event_types.append(SOURCE_INCIDENT_SESSION_EVENT_TYPES[1])

    duration_ms = 0
    event_counts = {event_type: 0 for event_type in included_event_types}
    for row in rows:
        payload = row.get("payload")
        if not isinstance(payload, dict):
            continue
        event_type = payload.get("type")
        if event_type not in included_event_types:
            continue
        event_duration_ms = _duration_ms(payload.get("duration_ms"))
        if event_duration_ms is None:
            continue
        duration_ms += event_duration_ms
        event_counts[str(event_type)] += 1

    if duration_ms == 0:
        raise ValueError(
            f"Codex session id {normalized_session_id!r} did not contain task timing durations."
        )

    payload: dict[str, object] = {
        "active_seconds": round(duration_ms / 1000),
        "duration_ms": duration_ms,
        "included_events": included_event_types,
        "session_file": session_path.name,
        "session_id": normalized_session_id,
        "timing_label": SOURCE_INCIDENT_TIMING_LABEL,
        "timing_source": "codex_session",
    }
    for event_type, count in event_counts.items():
        payload[f"{event_type}_count"] = count
    if note and note.strip():
        payload["note"] = note.strip()
    return payload
