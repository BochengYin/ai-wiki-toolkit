"""Helpers for recording route packet selection traces."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import sqlite3
from typing import Any
from uuid import uuid4

from ai_wiki_toolkit.paths import build_paths, resolve_user_handle
from ai_wiki_toolkit.reuse_events import RepoWikiNotInitializedError

ROUTE_TRACE_SCHEMA_VERSION = "route-trace-v1"


@dataclass(frozen=True)
class RecordRouteTraceResult:
    trace_id: str
    routed_at: str
    author_handle: str
    trace_log_path: Path


def _timestamp(explicit_routed_at: str | None = None) -> str:
    if explicit_routed_at:
        return explicit_routed_at
    return datetime.now().astimezone().isoformat(timespec="seconds")


def _append_jsonl(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, sort_keys=True) + "\n")


def _packet_words(rendered_packet: str) -> int:
    return len(re.findall(r"\S+", rendered_packet))


def _doc_ids(items: object) -> list[str]:
    if not isinstance(items, list):
        return []
    doc_ids: list[str] = []
    for item in items:
        if isinstance(item, dict) and isinstance(item.get("doc_id"), str):
            doc_ids.append(item["doc_id"])
    return doc_ids


def _route_scores(packet: dict[str, Any]) -> dict[str, int]:
    scores: dict[str, int] = {}
    for section in ("index_cards", "must_load", "maybe_load"):
        items = packet.get(section)
        if not isinstance(items, list):
            continue
        for item in items:
            if not isinstance(item, dict):
                continue
            doc_id = item.get("doc_id")
            score = item.get("score")
            if isinstance(doc_id, str) and isinstance(score, int):
                scores[doc_id] = score
    return scores


def _route_numeric_field(packet: dict[str, Any], field: str) -> dict[str, int]:
    values: dict[str, int] = {}
    for section in ("index_cards", "must_load", "maybe_load"):
        items = packet.get(section)
        if not isinstance(items, list):
            continue
        for item in items:
            if not isinstance(item, dict):
                continue
            doc_id = item.get("doc_id")
            value = item.get(field)
            if isinstance(doc_id, str) and isinstance(value, int):
                values[doc_id] = value
    return values


def _route_quality_adjustments(packet: dict[str, Any]) -> dict[str, int]:
    return _route_numeric_field(packet, "route_quality_adjustment")


def _route_object_field(packet: dict[str, Any], field: str) -> dict[str, object]:
    values: dict[str, object] = {}
    for section in ("index_cards", "must_load", "maybe_load"):
        items = packet.get(section)
        if not isinstance(items, list):
            continue
        for item in items:
            if not isinstance(item, dict):
                continue
            doc_id = item.get("doc_id")
            value = item.get(field)
            if isinstance(doc_id, str) and isinstance(value, dict):
                values[doc_id] = value
    return values


def _route_list_field(packet: dict[str, Any], field: str) -> dict[str, object]:
    values: dict[str, object] = {}
    for section in ("index_cards", "must_load", "maybe_load"):
        items = packet.get(section)
        if not isinstance(items, list):
            continue
        for item in items:
            if not isinstance(item, dict):
                continue
            doc_id = item.get("doc_id")
            value = item.get(field)
            if isinstance(doc_id, str) and isinstance(value, list):
                values[doc_id] = value
    return values


def _route_string_field(packet: dict[str, Any], field: str) -> dict[str, str]:
    values: dict[str, str] = {}
    for section in ("index_cards", "must_load", "maybe_load"):
        items = packet.get(section)
        if not isinstance(items, list):
            continue
        for item in items:
            if not isinstance(item, dict):
                continue
            doc_id = item.get("doc_id")
            value = item.get(field)
            if isinstance(doc_id, str) and isinstance(value, str):
                values[doc_id] = value
    return values


def _current_source_session_metadata() -> dict[str, object]:
    """Best-effort local Codex session provenance for later route replay."""

    env_names = ("CODEX_THREAD_ID", "CODEX_SESSION_ID", "CODEX_CONVERSATION_ID")
    session_id = ""
    env_name = ""
    for candidate in env_names:
        value = os.environ.get(candidate, "").strip()
        if value:
            session_id = value
            env_name = candidate
            break

    metadata: dict[str, object] = {
        "source_session_id": session_id or None,
        "source_session_env": env_name or None,
        "source_session_lookup": "not_available" if not session_id else "env_only",
    }
    if not session_id:
        return metadata

    db_path = Path(os.environ.get("CODEX_STATE_DB", "~/.codex/state_5.sqlite")).expanduser()
    if not db_path.exists():
        return metadata

    try:
        with sqlite3.connect(db_path) as connection:
            connection.row_factory = sqlite3.Row
            row = connection.execute(
                """
                select
                    rollout_path,
                    cwd,
                    title,
                    source,
                    model,
                    git_branch,
                    git_sha,
                    created_at,
                    updated_at
                from threads
                where id = ?
                limit 1
                """,
                (session_id,),
            ).fetchone()
    except sqlite3.Error:
        metadata["source_session_lookup"] = "sqlite_error"
        return metadata

    if row is None:
        metadata["source_session_lookup"] = "not_found"
        return metadata

    def timestamp(value: object) -> str | None:
        if not isinstance(value, int):
            return None
        return datetime.fromtimestamp(value, tz=timezone.utc).isoformat()

    def preview(value: object, *, limit: int = 240) -> str | None:
        if not isinstance(value, str) or not value:
            return None
        normalized = re.sub(r"\s+", " ", value).strip()
        if len(normalized) <= limit:
            return normalized
        return normalized[: limit - 3].rstrip() + "..."

    metadata.update(
        {
            "source_session_lookup": "state_5.sqlite",
            "source_rollout_path": row["rollout_path"],
            "source_thread_cwd": row["cwd"],
            "source_thread_title": preview(row["title"]),
            "source_thread_source": row["source"],
            "source_thread_model": row["model"],
            "source_thread_git_branch": row["git_branch"],
            "source_thread_git_sha": row["git_sha"],
            "source_thread_created_at": timestamp(row["created_at"]),
            "source_thread_updated_at": timestamp(row["updated_at"]),
        }
    )
    return metadata


def build_route_trace_payload(
    *,
    packet: dict[str, Any],
    rendered_packet: str,
    author_handle: str,
    routed_at: str,
    trace_id: str,
) -> dict[str, object]:
    maybe_doc_ids = _doc_ids(packet.get("maybe_load"))
    maybe_set = set(maybe_doc_ids)
    index_card_doc_ids = _doc_ids(packet.get("index_cards"))
    selected_doc_ids = [doc_id for doc_id in index_card_doc_ids if doc_id not in maybe_set]
    must_load_doc_ids = _doc_ids(packet.get("must_load"))
    skipped_doc_ids = _doc_ids(packet.get("skip"))
    route = packet.get("route") if isinstance(packet.get("route"), dict) else {}
    context_budget = (
        packet.get("context_budget") if isinstance(packet.get("context_budget"), dict) else {}
    )
    routing_strategy = (
        packet.get("routing_strategy") if isinstance(packet.get("routing_strategy"), dict) else {}
    )

    payload = {
        "schema_version": ROUTE_TRACE_SCHEMA_VERSION,
        "trace_id": trace_id,
        "routed_at": routed_at,
        "author_handle": author_handle,
        "task_id": str(packet.get("task_id", "")),
        "task": str(packet.get("task", "")),
        "task_type": str(route.get("task_type", "")),
        "effort": str(route.get("effort", "")),
        "domain_tags": [
            tag for tag in route.get("domain_tags", []) if isinstance(tag, str) and tag
        ],
        "guardrail_tags": [
            tag for tag in route.get("guardrail_tags", []) if isinstance(tag, str) and tag
        ],
        "changed_paths": [
            path for path in route.get("changed_paths", []) if isinstance(path, str) and path
        ],
        "selected_doc_ids": selected_doc_ids,
        "must_load_doc_ids": must_load_doc_ids,
        "index_card_doc_ids": index_card_doc_ids,
        "maybe_load_doc_ids": maybe_doc_ids,
        "skipped_doc_ids": skipped_doc_ids,
        "packet_words": _packet_words(rendered_packet),
        "selected_doc_count": len(selected_doc_ids),
        "index_card_count": len(index_card_doc_ids),
        "maybe_load_count": len(maybe_doc_ids),
        "must_load_count": len(must_load_doc_ids),
        "route_scores": _route_scores(packet),
        "base_route_scores": _route_numeric_field(packet, "base_score"),
        "route_rerank_adjustments": _route_numeric_field(packet, "rerank_adjustment"),
        "route_multi_signal_adjustments": _route_numeric_field(
            packet,
            "multi_signal_adjustment",
        ),
        "context_budget": {
            "safety_cap_words": context_budget.get("safety_cap_words"),
            "effective_max_docs": context_budget.get("effective_max_docs"),
            "max_docs": context_budget.get("max_docs"),
        },
        "changed_path_signal_source": route.get("changed_path_signal_source"),
        "changed_path_signal_used": route.get("changed_path_signal_used"),
        "language_signals": route.get("language_signals")
        if isinstance(route.get("language_signals"), dict)
        else {},
        "intent_signals": route.get("intent_signals")
        if isinstance(route.get("intent_signals"), dict)
        else {},
        "route_mode": route.get("mode") if isinstance(route.get("mode"), dict) else {},
        "workflow_contract": route.get("workflow_contract")
        if isinstance(route.get("workflow_contract"), dict)
        else None,
        "intent_buckets": [
            bucket for bucket in route.get("intent_buckets", []) if isinstance(bucket, dict)
        ],
        "behavior_contract": packet.get("behavior_contract")
        if isinstance(packet.get("behavior_contract"), dict)
        else {},
        "reranker": routing_strategy.get("reranker") if isinstance(routing_strategy, dict) else None,
        "selector": routing_strategy.get("selector") if isinstance(routing_strategy, dict) else None,
        "route_quality_adjustments": _route_quality_adjustments(packet),
        "route_quality_signals": _route_object_field(packet, "route_quality_signal"),
        "route_multi_signals": _route_object_field(packet, "multi_signal"),
        "route_applies_when_adjustments": _route_numeric_field(
            packet,
            "applies_when_adjustment",
        ),
        "route_applies_when_signals": _route_object_field(packet, "applies_when_signal"),
        "route_doc_slots": _route_list_field(packet, "doc_slots"),
        "route_selection_reason_types": _route_string_field(packet, "selection_reason_type"),
    }
    payload.update(_current_source_session_metadata())
    return payload


def record_route_trace(
    *,
    packet: dict[str, Any],
    rendered_packet: str,
    handle: str | None = None,
    routed_at: str | None = None,
    start: Path | None = None,
) -> RecordRouteTraceResult:
    paths = build_paths(start)
    if not paths.repo_wiki_dir.exists():
        raise RepoWikiNotInitializedError(
            "Repo AI wiki is not initialized. Run `aiwiki-toolkit install` first."
        )

    resolved_handle = resolve_user_handle(paths.repo_root, explicit_handle=handle)
    resolved_routed_at = _timestamp(routed_at)
    trace_id = f"rt_{uuid4().hex[:12]}"
    payload = build_route_trace_payload(
        packet=packet,
        rendered_packet=rendered_packet,
        author_handle=resolved_handle,
        routed_at=resolved_routed_at,
        trace_id=trace_id,
    )

    trace_log_path = paths.repo_wiki_dir / "metrics" / "route-traces" / f"{resolved_handle}.jsonl"
    _append_jsonl(trace_log_path, payload)
    return RecordRouteTraceResult(
        trace_id=trace_id,
        routed_at=resolved_routed_at,
        author_handle=resolved_handle,
        trace_log_path=trace_log_path,
    )


def load_route_traces(trace_log_path: Path) -> tuple[list[dict[str, Any]], int]:
    paths: list[Path] = []
    if trace_log_path.is_dir():
        paths.extend(sorted(trace_log_path.glob("*.jsonl")))
    elif trace_log_path.exists():
        paths.append(trace_log_path)
    else:
        return [], 0

    traces: list[dict[str, Any]] = []
    skipped_lines = 0
    for path in paths:
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
                traces.append(payload)
            else:
                skipped_lines += 1
    return traces, skipped_lines
