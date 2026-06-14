"""Helpers for recording taxonomy post-hoc evidence."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import json
from pathlib import Path
from typing import Sequence
from uuid import uuid4

from ai_wiki_toolkit.paths import build_paths, resolve_model_name, resolve_user_handle
from ai_wiki_toolkit.reuse_events import RepoWikiNotInitializedError

TAXONOMY_EVIDENCE_SCHEMA_VERSION = "taxonomy-evidence-v1"
TAXONOMY_EVIDENCE_SIGNAL_TYPES = (
    "unknown_task_language",
    "false_positive",
    "missed_useful",
    "user_correction",
)
TAXONOMY_EVIDENCE_CONFIDENCES = ("low", "medium", "high")


@dataclass(frozen=True)
class RecordTaxonomyEvidenceResult:
    evidence_id: str
    recorded_at: str
    author_handle: str
    evidence_log_path: Path


def _normalize_choice(value: str, allowed: Sequence[str], label: str) -> str:
    normalized = value.strip().lower()
    if normalized not in allowed:
        choices = ", ".join(allowed)
        raise ValueError(f"Invalid {label}: {value!r}. Expected one of: {choices}.")
    return normalized


def _normalize_required_text(value: str, label: str) -> str:
    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{label} must not be empty.")
    return normalized


def _normalize_optional_text(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = value.strip()
    return normalized or None


def _normalize_text_list(values: Sequence[str]) -> list[str]:
    normalized: list[str] = []
    seen: set[str] = set()
    for value in values:
        item = value.strip()
        if not item or item in seen:
            continue
        normalized.append(item)
        seen.add(item)
    return normalized


def _timestamp(explicit_recorded_at: str | None = None) -> str:
    if explicit_recorded_at:
        return explicit_recorded_at
    return datetime.now().astimezone().isoformat(timespec="seconds")


def _append_jsonl(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, sort_keys=True) + "\n")


def record_taxonomy_evidence(
    *,
    task_id: str,
    task: str,
    signal_type: str,
    reason: str,
    confidence: str = "medium",
    selected_doc_ids: Sequence[str] = (),
    used_doc_ids: Sequence[str] = (),
    missed_doc_ids: Sequence[str] = (),
    candidate_category_hint: str | None = None,
    wrong_category: str | None = None,
    suggested_category_hint: str | None = None,
    route_trace_id: str | None = None,
    agent_name: str | None = None,
    model: str | None = None,
    notes: str | None = None,
    recorded_at: str | None = None,
    handle: str | None = None,
    start: Path | None = None,
) -> RecordTaxonomyEvidenceResult:
    paths = build_paths(start)
    if not paths.repo_wiki_dir.exists():
        raise RepoWikiNotInitializedError(
            "Repo AI wiki is not initialized. Run `aiwiki-toolkit install` first."
        )

    normalized_task_id = _normalize_required_text(task_id, "task_id")
    normalized_task = _normalize_required_text(task, "task")
    normalized_signal_type = _normalize_choice(
        signal_type, TAXONOMY_EVIDENCE_SIGNAL_TYPES, "taxonomy evidence signal type"
    )
    normalized_reason = _normalize_required_text(reason, "reason")
    normalized_confidence = _normalize_choice(
        confidence, TAXONOMY_EVIDENCE_CONFIDENCES, "taxonomy evidence confidence"
    )
    resolved_handle = resolve_user_handle(paths.repo_root, explicit_handle=handle)
    resolved_model = resolve_model_name(explicit_model=model)
    resolved_recorded_at = _timestamp(recorded_at)
    evidence_id = f"txe_{uuid4().hex[:12]}"

    payload: dict[str, object] = {
        "schema_version": TAXONOMY_EVIDENCE_SCHEMA_VERSION,
        "evidence_id": evidence_id,
        "recorded_at": resolved_recorded_at,
        "author_handle": resolved_handle,
        "task_id": normalized_task_id,
        "task": normalized_task,
        "signal_type": normalized_signal_type,
        "selected_doc_ids": _normalize_text_list(selected_doc_ids),
        "used_doc_ids": _normalize_text_list(used_doc_ids),
        "missed_doc_ids": _normalize_text_list(missed_doc_ids),
        "reason": normalized_reason,
        "confidence": normalized_confidence,
        "active_taxonomy_changed": False,
    }

    optional_fields = {
        "candidate_category_hint": candidate_category_hint,
        "wrong_category": wrong_category,
        "suggested_category_hint": suggested_category_hint,
        "route_trace_id": route_trace_id,
        "agent_name": agent_name,
        "model": resolved_model,
        "notes": notes,
    }
    for key, value in optional_fields.items():
        normalized = _normalize_optional_text(value)
        if normalized is not None:
            payload[key] = normalized

    evidence_log_path = (
        paths.repo_wiki_dir / "metrics" / "taxonomy-evidence" / f"{resolved_handle}.jsonl"
    )
    _append_jsonl(evidence_log_path, payload)

    return RecordTaxonomyEvidenceResult(
        evidence_id=evidence_id,
        recorded_at=resolved_recorded_at,
        author_handle=resolved_handle,
        evidence_log_path=evidence_log_path,
    )
