"""Helpers for recording route packet selection traces."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import json
from pathlib import Path
import re
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

    return {
        "schema_version": ROUTE_TRACE_SCHEMA_VERSION,
        "trace_id": trace_id,
        "routed_at": routed_at,
        "author_handle": author_handle,
        "task_id": str(packet.get("task_id", "")),
        "task_type": str(route.get("task_type", "")),
        "effort": str(route.get("effort", "")),
        "risk_tags": [
            tag for tag in route.get("risk_tags", []) if isinstance(tag, str) and tag
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
        "context_budget": {
            "safety_cap_words": context_budget.get("safety_cap_words"),
            "effective_max_docs": context_budget.get("effective_max_docs"),
            "max_docs": context_budget.get("max_docs"),
        },
    }


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
