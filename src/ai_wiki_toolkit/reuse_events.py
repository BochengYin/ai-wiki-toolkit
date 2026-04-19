"""Helpers for recording AI wiki reuse events."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import json
from pathlib import Path
from typing import Sequence
from uuid import uuid4

from ai_wiki_toolkit.paths import (
    RepoRootNotFoundError,
    build_paths,
    resolve_model_name,
    resolve_user_handle,
)
from ai_wiki_toolkit.wiki_schema import (
    REUSE_SCHEMA_VERSION,
    infer_doc_kind,
    render_document_stats,
    render_task_stats,
)

RETRIEVAL_MODES = ("preloaded", "lookup")
EVIDENCE_MODES = ("explicit", "inferred")
REUSE_OUTCOMES = ("resolved", "partial", "not_helpful")
REUSE_CHECK_OUTCOMES = ("wiki_used", "no_wiki_use")


class RepoWikiNotInitializedError(RuntimeError):
    """Raised when reuse logging is attempted before the repo wiki exists."""


@dataclass(frozen=True)
class RecordReuseResult:
    event_id: str
    observed_at: str
    author_handle: str
    event_log_path: Path
    document_stats_path: Path
    task_stats_path: Path


@dataclass(frozen=True)
class RecordReuseCheckResult:
    check_id: str
    checked_at: str
    author_handle: str
    check_log_path: Path
    document_stats_path: Path
    task_stats_path: Path


def _normalize_choice(value: str, allowed: Sequence[str], label: str) -> str:
    normalized = value.strip().lower()
    if normalized not in allowed:
        choices = ", ".join(allowed)
        raise ValueError(f"Invalid {label}: {value!r}. Expected one of: {choices}.")
    return normalized


def _infer_doc_kind(doc_id: str) -> str:
    return infer_doc_kind(f"{doc_id}.md")


def _event_timestamp(explicit_observed_at: str | None = None) -> str:
    if explicit_observed_at:
        return explicit_observed_at
    return datetime.now().astimezone().isoformat(timespec="seconds")


def _append_jsonl(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, sort_keys=True) + "\n")


def _validate_reuse_doc_id(normalized_doc_id: str) -> None:
    if normalized_doc_id.startswith("_toolkit/"):
        raise ValueError(
            "Managed `_toolkit/**` docs are control-plane instructions and must not be recorded "
            "with `record-reuse`. Cite the path in your user-facing note instead."
        )


def _refresh_metrics(repo_wiki_dir: Path) -> tuple[Path, Path]:
    toolkit_metrics_dir = repo_wiki_dir / "_toolkit" / "metrics"
    toolkit_metrics_dir.mkdir(parents=True, exist_ok=True)

    document_stats_path = toolkit_metrics_dir / "document-stats.json"
    document_stats_path.write_text(render_document_stats(repo_wiki_dir), encoding="utf-8")

    task_stats_path = toolkit_metrics_dir / "task-stats.json"
    task_stats_path.write_text(render_task_stats(repo_wiki_dir), encoding="utf-8")

    return document_stats_path, task_stats_path


def record_reuse_event(
    *,
    doc_id: str,
    task_id: str,
    retrieval_mode: str,
    evidence_mode: str,
    reuse_outcome: str,
    doc_kind: str | None = None,
    reuse_effects: Sequence[str] = (),
    agent_name: str | None = None,
    model: str | None = None,
    notes: str | None = None,
    saved_tokens: int | None = None,
    saved_seconds: int | None = None,
    observed_at: str | None = None,
    handle: str | None = None,
    start: Path | None = None,
) -> RecordReuseResult:
    paths = build_paths(start)
    if not paths.repo_wiki_dir.exists():
        raise RepoWikiNotInitializedError(
            "Repo AI wiki is not initialized. Run `aiwiki-toolkit install` first."
        )

    normalized_doc_id = doc_id.strip()
    normalized_task_id = task_id.strip()
    if not normalized_doc_id:
        raise ValueError("doc_id must not be empty.")
    if not normalized_task_id:
        raise ValueError("task_id must not be empty.")
    _validate_reuse_doc_id(normalized_doc_id)

    normalized_retrieval = _normalize_choice(retrieval_mode, RETRIEVAL_MODES, "retrieval mode")
    normalized_evidence = _normalize_choice(evidence_mode, EVIDENCE_MODES, "evidence mode")
    normalized_outcome = _normalize_choice(reuse_outcome, REUSE_OUTCOMES, "reuse outcome")

    resolved_doc_kind = (doc_kind or _infer_doc_kind(normalized_doc_id)).strip()
    resolved_handle = resolve_user_handle(paths.repo_root, explicit_handle=handle)
    resolved_model = resolve_model_name(explicit_model=model)
    resolved_observed_at = _event_timestamp(observed_at)
    event_id = f"evt_{uuid4().hex[:12]}"

    payload: dict[str, object] = {
        "schema_version": REUSE_SCHEMA_VERSION,
        "event_id": event_id,
        "observed_at": resolved_observed_at,
        "author_handle": resolved_handle,
        "task_id": normalized_task_id,
        "doc_id": normalized_doc_id,
        "doc_kind": resolved_doc_kind,
        "retrieval_mode": normalized_retrieval,
        "evidence_mode": normalized_evidence,
        "reuse_outcome": normalized_outcome,
    }

    normalized_effects = [effect.strip() for effect in reuse_effects if effect.strip()]
    if normalized_effects:
        payload["reuse_effects"] = normalized_effects
    if agent_name and agent_name.strip():
        payload["agent_name"] = agent_name.strip()
    if resolved_model:
        payload["model"] = resolved_model
    if notes and notes.strip():
        payload["notes"] = notes.strip()
    if saved_tokens is not None or saved_seconds is not None:
        estimated_savings: dict[str, int] = {}
        if saved_tokens is not None:
            estimated_savings["saved_tokens"] = saved_tokens
        if saved_seconds is not None:
            estimated_savings["saved_seconds"] = saved_seconds
        payload["estimated_savings"] = estimated_savings

    event_log_path = paths.repo_wiki_dir / "metrics" / "reuse-events" / f"{resolved_handle}.jsonl"
    _append_jsonl(event_log_path, payload)
    document_stats_path, task_stats_path = _refresh_metrics(paths.repo_wiki_dir)

    return RecordReuseResult(
        event_id=event_id,
        observed_at=resolved_observed_at,
        author_handle=resolved_handle,
        event_log_path=event_log_path,
        document_stats_path=document_stats_path,
        task_stats_path=task_stats_path,
    )


def record_reuse_check(
    *,
    task_id: str,
    check_outcome: str,
    agent_name: str | None = None,
    model: str | None = None,
    notes: str | None = None,
    checked_at: str | None = None,
    handle: str | None = None,
    start: Path | None = None,
) -> RecordReuseCheckResult:
    paths = build_paths(start)
    if not paths.repo_wiki_dir.exists():
        raise RepoWikiNotInitializedError(
            "Repo AI wiki is not initialized. Run `aiwiki-toolkit install` first."
        )

    normalized_task_id = task_id.strip()
    if not normalized_task_id:
        raise ValueError("task_id must not be empty.")

    normalized_check_outcome = _normalize_choice(
        check_outcome, REUSE_CHECK_OUTCOMES, "reuse check outcome"
    )
    resolved_handle = resolve_user_handle(paths.repo_root, explicit_handle=handle)
    resolved_model = resolve_model_name(explicit_model=model)
    resolved_checked_at = _event_timestamp(checked_at)
    check_id = f"chk_{uuid4().hex[:12]}"

    payload: dict[str, object] = {
        "schema_version": REUSE_SCHEMA_VERSION,
        "check_id": check_id,
        "checked_at": resolved_checked_at,
        "author_handle": resolved_handle,
        "task_id": normalized_task_id,
        "check_outcome": normalized_check_outcome,
    }

    if agent_name and agent_name.strip():
        payload["agent_name"] = agent_name.strip()
    if resolved_model:
        payload["model"] = resolved_model
    if notes and notes.strip():
        payload["notes"] = notes.strip()

    check_log_path = paths.repo_wiki_dir / "metrics" / "task-checks" / f"{resolved_handle}.jsonl"
    _append_jsonl(check_log_path, payload)
    document_stats_path, task_stats_path = _refresh_metrics(paths.repo_wiki_dir)

    return RecordReuseCheckResult(
        check_id=check_id,
        checked_at=resolved_checked_at,
        author_handle=resolved_handle,
        check_log_path=check_log_path,
        document_stats_path=document_stats_path,
        task_stats_path=task_stats_path,
    )
