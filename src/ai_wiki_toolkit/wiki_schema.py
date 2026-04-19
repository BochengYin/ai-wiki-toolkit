"""Helpers for AI wiki catalog and reuse schema data."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .frontmatter import parse_frontmatter

REUSE_SCHEMA_VERSION = "reuse-v1"


def _relative_repo_wiki_path(path: Path, repo_wiki_dir: Path) -> str:
    return path.relative_to(repo_wiki_dir).as_posix()


def _extract_title(path: Path) -> str:
    text = path.read_text(encoding="utf-8")
    metadata, body = parse_frontmatter(text)
    title = metadata.get("title")
    if isinstance(title, str) and title.strip():
        return title.strip()

    for line in body.splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return path.stem.replace("-", " ").replace("_", " ").strip() or path.stem


def infer_doc_kind(relative_path: str) -> str:
    parts = relative_path.split("/")
    if relative_path == "index.md":
        return "repo_index"
    if relative_path == "constraints.md":
        return "constraints"
    if relative_path == "workflows.md":
        return "workflows"
    if relative_path == "decisions.md":
        return "decisions"
    if relative_path == "metrics/index.md":
        return "metrics_index"
    if parts[0] == "review-patterns":
        return "review_pattern_index" if relative_path.endswith("/index.md") else "review_pattern"
    if parts[0] == "trails":
        return "trail_index" if relative_path.endswith("/index.md") else "trail"
    if parts[0] == "people" and len(parts) >= 3:
        if len(parts) == 3 and parts[-1] == "index.md":
            return "person_index"
        if len(parts) >= 4 and parts[2] == "drafts":
            return "draft"
    return "document"


def doc_id_for_relative_path(relative_path: str) -> str:
    return relative_path.removesuffix(".md")


def build_repo_catalog(repo_wiki_dir: Path) -> dict[str, Any]:
    documents: list[dict[str, str]] = []
    for path in sorted(repo_wiki_dir.rglob("*.md")):
        if "_toolkit" in path.parts:
            continue
        relative_path = _relative_repo_wiki_path(path, repo_wiki_dir)
        documents.append(
            {
                "doc_id": doc_id_for_relative_path(relative_path),
                "kind": infer_doc_kind(relative_path),
                "path": f"ai-wiki/{relative_path}",
                "title": _extract_title(path),
                "source": "user_owned",
            }
        )
    return {
        "schema_version": REUSE_SCHEMA_VERSION,
        "documents": documents,
    }


def render_repo_catalog(repo_wiki_dir: Path) -> str:
    return json.dumps(build_repo_catalog(repo_wiki_dir), indent=2, sort_keys=True) + "\n"


def load_reuse_events(event_log_path: Path) -> tuple[list[dict[str, Any]], int]:
    if not event_log_path.exists():
        return [], 0

    events: list[dict[str, Any]] = []
    skipped_lines = 0
    for line in event_log_path.read_text(encoding="utf-8").splitlines():
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


def _numeric_estimate(payload: dict[str, Any], key: str) -> int:
    estimates = payload.get("estimated_savings")
    if not isinstance(estimates, dict):
        return 0
    value = estimates.get(key)
    return value if isinstance(value, int) else 0


def build_document_stats(repo_wiki_dir: Path) -> dict[str, Any]:
    events, skipped_lines = load_reuse_events(repo_wiki_dir / "metrics" / "reuse-events.jsonl")
    documents: dict[str, dict[str, Any]] = {}

    for event in events:
        doc_id = event.get("doc_id")
        if not isinstance(doc_id, str) or not doc_id:
            continue
        stats = documents.setdefault(
            doc_id,
            {
                "effective_reuse_count": 0,
                "last_effective_at": None,
                "last_observed_at": None,
                "lookup_reuse_count": 0,
                "preloaded_reuse_count": 0,
                "total_events": 0,
            },
        )
        stats["total_events"] += 1
        observed_at = event.get("observed_at")
        if isinstance(observed_at, str):
            stats["last_observed_at"] = observed_at
        retrieval_mode = event.get("retrieval_mode")
        if retrieval_mode == "preloaded":
            stats["preloaded_reuse_count"] += 1
        elif retrieval_mode == "lookup":
            stats["lookup_reuse_count"] += 1
        if event.get("reuse_outcome") == "resolved":
            stats["effective_reuse_count"] += 1
            if isinstance(observed_at, str):
                stats["last_effective_at"] = observed_at

    return {
        "schema_version": REUSE_SCHEMA_VERSION,
        "skipped_event_lines": skipped_lines,
        "documents": documents,
    }


def render_document_stats(repo_wiki_dir: Path) -> str:
    return json.dumps(build_document_stats(repo_wiki_dir), indent=2, sort_keys=True) + "\n"


def build_task_stats(repo_wiki_dir: Path) -> dict[str, Any]:
    events, skipped_lines = load_reuse_events(repo_wiki_dir / "metrics" / "reuse-events.jsonl")
    tasks: dict[str, dict[str, Any]] = {}

    for event in events:
        task_id = event.get("task_id")
        if not isinstance(task_id, str) or not task_id:
            continue
        task_stats = tasks.setdefault(
            task_id,
            {
                "_doc_ids": set(),
                "effective_reuse_count": 0,
                "estimated_seconds_saved": 0,
                "estimated_token_savings": 0,
                "lookup_reuse_count": 0,
                "preloaded_reuse_count": 0,
                "total_events": 0,
            },
        )
        task_stats["total_events"] += 1
        doc_id = event.get("doc_id")
        if isinstance(doc_id, str) and doc_id:
            task_stats["_doc_ids"].add(doc_id)
        retrieval_mode = event.get("retrieval_mode")
        if retrieval_mode == "preloaded":
            task_stats["preloaded_reuse_count"] += 1
        elif retrieval_mode == "lookup":
            task_stats["lookup_reuse_count"] += 1
        if event.get("reuse_outcome") == "resolved":
            task_stats["effective_reuse_count"] += 1
        task_stats["estimated_token_savings"] += _numeric_estimate(event, "saved_tokens")
        task_stats["estimated_seconds_saved"] += _numeric_estimate(event, "saved_seconds")

    rendered_tasks: dict[str, dict[str, Any]] = {}
    for task_id, payload in tasks.items():
        doc_ids = payload.pop("_doc_ids")
        payload["reused_docs"] = len(doc_ids)
        rendered_tasks[task_id] = payload

    return {
        "schema_version": REUSE_SCHEMA_VERSION,
        "skipped_event_lines": skipped_lines,
        "tasks": rendered_tasks,
    }


def render_task_stats(repo_wiki_dir: Path) -> str:
    return json.dumps(build_task_stats(repo_wiki_dir), indent=2, sort_keys=True) + "\n"
