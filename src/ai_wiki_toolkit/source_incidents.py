"""Source incident timing helpers."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import json
from pathlib import Path
import re
from typing import Any
from uuid import uuid4

SOURCE_INCIDENT_TIMING_LABEL = "source active-turn estimate"
SOURCE_INCIDENT_TIMING_SOURCES = ("manual", "codex_session", "external")
SOURCE_INCIDENT_SESSION_EVENT_TYPES = ("task_complete", "turn_aborted")
SOURCE_INCIDENT_SCHEMA_VERSION = "source-incident-v1"
SOURCE_INCIDENT_WRITEBACK_TIMING_SOURCE = "codex_writeback_footer"
SOURCE_INCIDENT_WRITEBACK_POLICY = "first_writeback_user_task_inclusive"
_WRITEBACK_PATH_RE = re.compile(r"AI Wiki Write-Back Path:\s*`?([^\s`]+)`?")


@dataclass(frozen=True)
class SourceIncidentBackfillResult:
    """Result for write-back provenance source incident backfill."""

    schema_version: str
    generated_at: str
    author_handle: str
    apply: bool
    policy: str
    event_log_path: Path
    candidate_count: int
    written_count: int
    skipped_existing_count: int
    candidates: list[dict[str, object]]
    written_events: list[dict[str, object]]
    skipped_existing: list[dict[str, object]]


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


def normalize_source_incident_doc_id(value: str) -> str:
    """Normalize an AI wiki path or doc id into the doc_id form."""

    normalized = value.strip().strip("`")
    if not normalized:
        raise ValueError("doc_id must not be empty.")
    if normalized.startswith("./"):
        normalized = normalized[2:]
    if normalized.startswith("ai-wiki/"):
        normalized = normalized[len("ai-wiki/") :]
    normalized = normalized.removesuffix(".md")
    if normalized.startswith("_toolkit/"):
        raise ValueError("Managed `_toolkit/**` docs cannot be source incident targets.")
    return normalized


def _normalize_writeback_path(value: str) -> str:
    normalized = value.strip().strip("`")
    if not normalized:
        raise ValueError("writeback_path must not be empty.")
    if normalized.startswith("./"):
        normalized = normalized[2:]
    if not normalized.startswith("ai-wiki/"):
        normalized = f"ai-wiki/{normalized}"
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


def _session_meta(rows: list[dict[str, Any]]) -> dict[str, Any]:
    for row in rows:
        if row.get("type") != "session_meta":
            continue
        payload = row.get("payload")
        if isinstance(payload, dict):
            return payload
    return {}


def _session_id_from_rows(path: Path, rows: list[dict[str, Any]]) -> str:
    meta = _session_meta(rows)
    for key in ("id", "session_id"):
        value = meta.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return path.stem


def _session_cwd(rows: list[dict[str, Any]]) -> str | None:
    cwd = _session_meta(rows).get("cwd")
    return cwd if isinstance(cwd, str) and cwd.strip() else None


def _repo_matches_session(rows: list[dict[str, Any]], repo_root: Path | None) -> bool:
    if repo_root is None:
        return True
    cwd = _session_cwd(rows)
    if cwd is None:
        return False
    try:
        return Path(cwd).resolve() == repo_root.resolve()
    except OSError:
        return False


def _assistant_writeback_text(row: dict[str, Any]) -> str | None:
    payload = row.get("payload")
    if not isinstance(payload, dict):
        return None
    if payload.get("type") == "task_complete":
        message = payload.get("last_agent_message")
        return message if isinstance(message, str) else None
    return None


def _extract_writeback_paths(text: str | None) -> list[str]:
    if not text:
        return []
    return [_normalize_writeback_path(match.group(1)) for match in _WRITEBACK_PATH_RE.finditer(text)]


def _session_relpath(path: Path, sessions_root: Path) -> str:
    try:
        return path.relative_to(sessions_root).as_posix()
    except ValueError:
        return path.name


def _event_duration_counts(
    rows: list[dict[str, Any]],
    *,
    start_index: int,
    cutoff_index: int,
    include_aborted: bool = True,
) -> tuple[int, dict[str, int], list[str]]:
    included_event_types = [SOURCE_INCIDENT_SESSION_EVENT_TYPES[0]]
    if include_aborted:
        included_event_types.append(SOURCE_INCIDENT_SESSION_EVENT_TYPES[1])
    event_counts = {event_type: 0 for event_type in included_event_types}
    duration_ms = 0

    for row in rows[start_index : cutoff_index + 1]:
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

    return duration_ms, event_counts, included_event_types


def _is_user_task_start(row: dict[str, Any]) -> bool:
    payload = row.get("payload")
    if not isinstance(payload, dict):
        return False
    if row.get("type") == "event_msg" and payload.get("type") == "user_message":
        return True
    return (
        row.get("type") == "response_item"
        and payload.get("type") == "message"
        and payload.get("role") == "user"
    )


def _source_task_start_index(rows: list[dict[str, Any]], cutoff_index: int) -> int:
    for index in range(cutoff_index, -1, -1):
        if _is_user_task_start(rows[index]):
            return index
    return 0


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


def load_source_incident_events(event_log_path: Path) -> tuple[list[dict[str, Any]], int]:
    """Load source incident evidence from a legacy file or per-handle shard directory."""

    paths: list[Path] = []
    if event_log_path.is_dir():
        paths.extend(sorted(event_log_path.glob("*.jsonl")))
    elif event_log_path.exists():
        paths.append(event_log_path)
    else:
        return [], 0

    events: list[dict[str, Any]] = []
    skipped_lines = 0
    for path in paths:
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except OSError:
            skipped_lines += 1
            continue
        for line in lines:
            candidate = line.strip()
            if not candidate:
                continue
            try:
                payload = json.loads(candidate)
            except json.JSONDecodeError:
                skipped_lines += 1
                continue
            if isinstance(payload, dict):
                events.append(payload)
            else:
                skipped_lines += 1
    return events, skipped_lines


def _existing_source_incident_keys(events: list[dict[str, Any]]) -> set[tuple[str, str, str]]:
    keys: set[tuple[str, str, str]] = set()
    for event in events:
        doc_id = event.get("doc_id")
        session_id = event.get("session_id")
        policy = event.get("policy")
        if isinstance(doc_id, str) and isinstance(session_id, str) and isinstance(policy, str):
            keys.add((doc_id, session_id, policy))
    return keys


def _append_jsonl(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, sort_keys=True) + "\n")


def _writeback_sort_key(candidate: dict[str, object]) -> tuple[str, str, int]:
    timestamp = candidate.get("cutoff_timestamp")
    session_relpath = candidate.get("session_relpath")
    cutoff_index = candidate.get("cutoff_index")
    return (
        timestamp if isinstance(timestamp, str) else "",
        session_relpath if isinstance(session_relpath, str) else "",
        cutoff_index if isinstance(cutoff_index, int) else 0,
    )


def _target_doc_id_set(
    doc_ids: list[str] | tuple[str, ...],
    writeback_paths: list[str] | tuple[str, ...],
) -> set[str]:
    target_doc_ids = {normalize_source_incident_doc_id(value) for value in doc_ids}
    for path in writeback_paths:
        target_doc_ids.add(normalize_source_incident_doc_id(path))
    return target_doc_ids


def _writeback_candidate_for_row(
    *,
    session_path: Path,
    sessions_root: Path,
    rows: list[dict[str, Any]],
    index: int,
    writeback_path: str,
    target_doc_ids: set[str],
    repo_wiki_dir: Path | None,
    include_aborted: bool,
) -> dict[str, object] | None:
    doc_id = normalize_source_incident_doc_id(writeback_path)
    if target_doc_ids and doc_id not in target_doc_ids:
        return None
    if repo_wiki_dir is not None and not (repo_wiki_dir / f"{doc_id}.md").exists():
        return None

    source_task_start_index = _source_task_start_index(rows, index)
    source_task_start_row = rows[source_task_start_index]
    duration_ms, event_counts, included_event_types = _event_duration_counts(
        rows,
        start_index=source_task_start_index,
        cutoff_index=index,
        include_aborted=include_aborted,
    )
    if duration_ms == 0:
        return None

    payload = rows[index].get("payload")
    task_payload = payload if isinstance(payload, dict) else {}
    return {
        "doc_id": doc_id,
        "writeback_path": writeback_path,
        "session_id": _session_id_from_rows(session_path, rows),
        "session_file": session_path.name,
        "session_relpath": _session_relpath(session_path, sessions_root),
        "source_task_start_index": source_task_start_index,
        "source_task_start_timestamp": source_task_start_row.get("timestamp")
        if isinstance(source_task_start_row.get("timestamp"), str)
        else None,
        "cutoff_index": index,
        "cutoff_timestamp": rows[index].get("timestamp")
        if isinstance(rows[index].get("timestamp"), str)
        else None,
        "cutoff_turn_id": task_payload.get("turn_id")
        if isinstance(task_payload.get("turn_id"), str)
        else None,
        "duration_ms": duration_ms,
        "active_seconds": round(duration_ms / 1000),
        "event_counts": event_counts,
        "included_events": included_event_types,
    }


def _candidate_evidence(
    *,
    candidate: dict[str, object],
    author_handle: str,
    generated_at: str,
    source_kind: str = "writeback_backfill",
    note: str | None = None,
) -> dict[str, object]:
    duration_ms = int(candidate["duration_ms"])
    event_counts = candidate["event_counts"]
    if not isinstance(event_counts, dict):
        event_counts = {}
    evidence: dict[str, object] = {
        "schema_version": SOURCE_INCIDENT_SCHEMA_VERSION,
        "evidence_id": f"srcinc_{uuid4().hex[:12]}",
        "recorded_at": generated_at,
        "author_handle": author_handle,
        "doc_id": str(candidate["doc_id"]),
        "writeback_path": str(candidate["writeback_path"]),
        "source_kind": source_kind,
        "timing_label": SOURCE_INCIDENT_TIMING_LABEL,
        "timing_source": SOURCE_INCIDENT_WRITEBACK_TIMING_SOURCE,
        "policy": SOURCE_INCIDENT_WRITEBACK_POLICY,
        "active_seconds": round(duration_ms / 1000),
        "duration_ms": duration_ms,
        "included_events": candidate["included_events"],
        "session_id": str(candidate["session_id"]),
        "session_file": str(candidate["session_file"]),
        "session_relpath": str(candidate["session_relpath"]),
        "note": note
        or (
            "Backfilled from the first AI Wiki Write-Back Path footer; counts active "
            "turns from the current user task start through the first write-back turn."
        ),
    }
    source_task_start_timestamp = candidate.get("source_task_start_timestamp")
    if isinstance(source_task_start_timestamp, str) and source_task_start_timestamp:
        evidence["source_task_start_timestamp"] = source_task_start_timestamp
    cutoff_timestamp = candidate.get("cutoff_timestamp")
    if isinstance(cutoff_timestamp, str) and cutoff_timestamp:
        evidence["cutoff_timestamp"] = cutoff_timestamp
    cutoff_turn_id = candidate.get("cutoff_turn_id")
    if isinstance(cutoff_turn_id, str) and cutoff_turn_id:
        evidence["cutoff_turn_id"] = cutoff_turn_id
    for event_type in SOURCE_INCIDENT_SESSION_EVENT_TYPES:
        count = event_counts.get(event_type)
        if isinstance(count, int):
            evidence[f"{event_type}_count"] = count
    return evidence


def discover_writeback_source_incident_candidates(
    *,
    sessions_root: Path,
    repo_root: Path | None = None,
    repo_wiki_dir: Path | None = None,
    doc_ids: list[str] | tuple[str, ...] = (),
    writeback_paths: list[str] | tuple[str, ...] = (),
    include_aborted: bool = True,
    max_items: int | None = None,
) -> list[dict[str, object]]:
    """Find the first write-back footer per memory and compute source active-turn timing."""

    if not sessions_root.exists():
        raise ValueError(f"Codex sessions root does not exist: {sessions_root}")

    target_doc_ids = _target_doc_id_set(doc_ids, writeback_paths)

    candidates: list[dict[str, object]] = []
    for session_path in sorted(sessions_root.rglob("*.jsonl")):
        rows = _iter_session_rows(session_path)
        if not rows:
            continue
        if not _repo_matches_session(rows, repo_root):
            continue
        for index, row in enumerate(rows):
            writeback_paths_for_row = _extract_writeback_paths(_assistant_writeback_text(row))
            if not writeback_paths_for_row:
                continue
            for writeback_path in writeback_paths_for_row:
                candidate = _writeback_candidate_for_row(
                    session_path=session_path,
                    sessions_root=sessions_root,
                    rows=rows,
                    index=index,
                    writeback_path=writeback_path,
                    target_doc_ids=target_doc_ids,
                    repo_wiki_dir=repo_wiki_dir,
                    include_aborted=include_aborted,
                )
                if candidate is not None:
                    candidates.append(candidate)

    candidates.sort(key=_writeback_sort_key)
    first_by_doc_id: dict[str, dict[str, object]] = {}
    for candidate in candidates:
        doc_id = str(candidate["doc_id"])
        first_by_doc_id.setdefault(doc_id, candidate)
        if max_items is not None and len(first_by_doc_id) >= max_items:
            break
    return list(first_by_doc_id.values())


def discover_latest_writeback_source_incident_candidates(
    *,
    sessions_root: Path,
    repo_root: Path | None = None,
    repo_wiki_dir: Path | None = None,
    session_id: str | None = None,
    doc_ids: list[str] | tuple[str, ...] = (),
    writeback_paths: list[str] | tuple[str, ...] = (),
    include_aborted: bool = True,
) -> list[dict[str, object]]:
    """Find the latest completed write-back turn for this repo and compute source timing."""

    if not sessions_root.exists():
        raise ValueError(f"Codex sessions root does not exist: {sessions_root}")

    target_doc_ids = _target_doc_id_set(doc_ids, writeback_paths)
    session_items: list[tuple[Path, list[dict[str, Any]]]] = []
    if session_id is not None and session_id.strip():
        match = _find_codex_session_file(_normalize_session_id(session_id), sessions_root)
        if match is None:
            raise ValueError(f"Could not find Codex session id {session_id!r} under {sessions_root}.")
        session_items.append(match)
    else:
        for session_path in sorted(sessions_root.rglob("*.jsonl")):
            rows = _iter_session_rows(session_path)
            if rows:
                session_items.append((session_path, rows))

    latest_key: tuple[str, str, int] | None = None
    latest_candidates: list[dict[str, object]] = []
    for session_path, rows in session_items:
        if not _repo_matches_session(rows, repo_root):
            continue
        for index, row in enumerate(rows):
            writeback_paths_for_row = _extract_writeback_paths(_assistant_writeback_text(row))
            if not writeback_paths_for_row:
                continue
            row_candidates: list[dict[str, object]] = []
            for writeback_path in writeback_paths_for_row:
                candidate = _writeback_candidate_for_row(
                    session_path=session_path,
                    sessions_root=sessions_root,
                    rows=rows,
                    index=index,
                    writeback_path=writeback_path,
                    target_doc_ids=target_doc_ids,
                    repo_wiki_dir=repo_wiki_dir,
                    include_aborted=include_aborted,
                )
                if candidate is not None:
                    row_candidates.append(candidate)
            if not row_candidates:
                continue
            row_key = _writeback_sort_key(row_candidates[0])
            if latest_key is None or row_key >= latest_key:
                latest_key = row_key
                latest_candidates = row_candidates

    latest_candidates.sort(key=lambda candidate: str(candidate["doc_id"]))
    return latest_candidates


def _source_incident_result_from_candidates(
    *,
    repo_wiki_dir: Path,
    author_handle: str,
    raw_candidates: list[dict[str, object]],
    apply: bool,
    generated_at: str | None,
    source_kind: str,
    note: str | None,
) -> SourceIncidentBackfillResult:
    if not repo_wiki_dir.exists():
        raise ValueError("Repo AI wiki is not initialized. Run `aiwiki-toolkit install` first.")
    normalized_handle = author_handle.strip()
    if not normalized_handle:
        raise ValueError("author_handle must not be empty.")

    resolved_generated_at = generated_at or datetime.now().astimezone().isoformat(timespec="seconds")
    event_log_path = repo_wiki_dir / "metrics" / "source-incidents" / f"{normalized_handle}.jsonl"
    existing_events, _ = load_source_incident_events(event_log_path)
    existing_keys = _existing_source_incident_keys(existing_events)

    candidates: list[dict[str, object]] = []
    written_events: list[dict[str, object]] = []
    skipped_existing: list[dict[str, object]] = []
    for raw_candidate in raw_candidates:
        evidence = _candidate_evidence(
            candidate=raw_candidate,
            author_handle=normalized_handle,
            generated_at=resolved_generated_at,
            source_kind=source_kind,
            note=note,
        )
        key = (
            str(evidence["doc_id"]),
            str(evidence["session_id"]),
            str(evidence["policy"]),
        )
        status = "dry_run"
        if key in existing_keys:
            status = "skipped_existing"
            skipped_existing.append(evidence)
        elif apply:
            _append_jsonl(event_log_path, evidence)
            existing_keys.add(key)
            status = "written"
            written_events.append(evidence)
        candidate = {
            key: value
            for key, value in evidence.items()
            if key not in {"schema_version", "recorded_at", "author_handle"}
        }
        candidate["status"] = status
        candidates.append(candidate)

    return SourceIncidentBackfillResult(
        schema_version=SOURCE_INCIDENT_SCHEMA_VERSION,
        generated_at=resolved_generated_at,
        author_handle=normalized_handle,
        apply=apply,
        policy=SOURCE_INCIDENT_WRITEBACK_POLICY,
        event_log_path=event_log_path,
        candidate_count=len(candidates),
        written_count=len(written_events),
        skipped_existing_count=len(skipped_existing),
        candidates=candidates,
        written_events=written_events,
        skipped_existing=skipped_existing,
    )


def backfill_writeback_source_incidents(
    *,
    repo_wiki_dir: Path,
    sessions_root: Path,
    author_handle: str,
    repo_root: Path | None = None,
    doc_ids: list[str] | tuple[str, ...] = (),
    writeback_paths: list[str] | tuple[str, ...] = (),
    apply: bool = False,
    include_aborted: bool = True,
    max_items: int | None = None,
    generated_at: str | None = None,
) -> SourceIncidentBackfillResult:
    """Backfill source incident evidence from first AI wiki write-back footers."""

    raw_candidates = discover_writeback_source_incident_candidates(
        sessions_root=sessions_root,
        repo_root=repo_root,
        repo_wiki_dir=repo_wiki_dir,
        doc_ids=doc_ids,
        writeback_paths=writeback_paths,
        include_aborted=include_aborted,
        max_items=max_items,
    )
    return _source_incident_result_from_candidates(
        repo_wiki_dir=repo_wiki_dir,
        author_handle=author_handle,
        raw_candidates=raw_candidates,
        apply=apply,
        generated_at=generated_at,
        source_kind="writeback_backfill",
        note=None,
    )


def capture_post_turn_source_incidents(
    *,
    repo_wiki_dir: Path,
    sessions_root: Path,
    author_handle: str,
    repo_root: Path | None = None,
    session_id: str | None = None,
    doc_ids: list[str] | tuple[str, ...] = (),
    writeback_paths: list[str] | tuple[str, ...] = (),
    apply: bool = False,
    include_aborted: bool = True,
    generated_at: str | None = None,
) -> SourceIncidentBackfillResult:
    """Capture source incident evidence for the latest completed write-back turn."""

    raw_candidates = discover_latest_writeback_source_incident_candidates(
        sessions_root=sessions_root,
        repo_root=repo_root,
        repo_wiki_dir=repo_wiki_dir,
        session_id=session_id,
        doc_ids=doc_ids,
        writeback_paths=writeback_paths,
        include_aborted=include_aborted,
    )
    return _source_incident_result_from_candidates(
        repo_wiki_dir=repo_wiki_dir,
        author_handle=author_handle,
        raw_candidates=raw_candidates,
        apply=apply,
        generated_at=generated_at,
        source_kind="writeback_post_turn_capture",
        note=(
            "Captured after a completed AI Wiki write-back turn; counts active turns from "
            "the current user task start through the first write-back turn."
        ),
    )


def render_source_incident_backfill_json(result: SourceIncidentBackfillResult) -> str:
    """Render source incident backfill result as JSON."""

    payload = {
        "schema_version": result.schema_version,
        "generated_at": result.generated_at,
        "author_handle": result.author_handle,
        "apply": result.apply,
        "policy": result.policy,
        "event_log_path": result.event_log_path.as_posix(),
        "candidate_count": result.candidate_count,
        "written_count": result.written_count,
        "skipped_existing_count": result.skipped_existing_count,
        "candidates": result.candidates,
        "written_events": result.written_events,
        "skipped_existing": result.skipped_existing,
    }
    return json.dumps(payload, indent=2, sort_keys=True) + "\n"


def render_source_incident_backfill_text(result: SourceIncidentBackfillResult) -> str:
    """Render source incident backfill result as Markdown-like text."""

    lines = [
        "# AI Wiki Source Incident Backfill",
        "",
        f"Generated at: `{result.generated_at}`",
        f"Author handle: `{result.author_handle}`",
        f"Mode: `{'apply' if result.apply else 'dry-run'}`",
        f"Policy: `{result.policy}`",
        f"Ledger: `{result.event_log_path.as_posix()}`",
        "",
        "## Summary",
        "",
        f"- Candidates: {result.candidate_count}",
        f"- Written: {result.written_count}",
        f"- Skipped existing: {result.skipped_existing_count}",
        "",
        "## Candidates",
        "",
    ]
    if not result.candidates:
        lines.extend(["- None detected.", ""])
        return "\n".join(lines)
    for candidate in result.candidates:
        active_seconds = candidate.get("active_seconds")
        active_minutes = (
            round(active_seconds / 60, 2) if isinstance(active_seconds, int) else "unknown"
        )
        lines.append(f"- `{candidate.get('doc_id')}`")
        lines.append(f"  - Status: `{candidate.get('status')}`")
        lines.append(f"  - Source active mins: `{active_minutes}`")
        lines.append(f"  - Session: `{candidate.get('session_id')}`")
        lines.append(f"  - Write-back: `{candidate.get('writeback_path')}`")
        cutoff = candidate.get("cutoff_timestamp")
        if isinstance(cutoff, str) and cutoff:
            lines.append(f"  - First write-back cutoff: `{cutoff}`")
    lines.append("")
    return "\n".join(lines)
