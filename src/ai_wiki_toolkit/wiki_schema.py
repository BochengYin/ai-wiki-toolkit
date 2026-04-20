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
    if parts[0] == "conventions":
        return "convention_index" if relative_path.endswith("/index.md") else "convention"
    if parts[0] == "review-patterns":
        return "review_pattern_index" if relative_path.endswith("/index.md") else "review_pattern"
    if parts[0] == "problems":
        return "problem_index" if relative_path.endswith("/index.md") else "problem"
    if parts[0] == "features":
        return "feature_index" if relative_path.endswith("/index.md") else "feature"
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
                events.append(payload)
            else:
                skipped_lines += 1
    return events, skipped_lines


def load_task_checks(task_check_path: Path) -> tuple[list[dict[str, Any]], int]:
    paths: list[Path] = []
    if task_check_path.is_dir():
        paths.extend(sorted(task_check_path.glob("*.jsonl")))
    elif task_check_path.exists():
        paths.append(task_check_path)
    else:
        return [], 0

    checks: list[dict[str, Any]] = []
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
                checks.append(payload)
            else:
                skipped_lines += 1
    return checks, skipped_lines


def _load_repo_reuse_events(repo_wiki_dir: Path) -> tuple[list[dict[str, Any]], int]:
    legacy_events, legacy_skipped = load_reuse_events(repo_wiki_dir / "metrics" / "reuse-events.jsonl")
    sharded_events, sharded_skipped = load_reuse_events(repo_wiki_dir / "metrics" / "reuse-events")
    return legacy_events + sharded_events, legacy_skipped + sharded_skipped


def _load_repo_task_checks(repo_wiki_dir: Path) -> tuple[list[dict[str, Any]], int]:
    legacy_checks, legacy_skipped = load_task_checks(repo_wiki_dir / "metrics" / "task-checks.jsonl")
    sharded_checks, sharded_skipped = load_task_checks(repo_wiki_dir / "metrics" / "task-checks")
    return legacy_checks + sharded_checks, legacy_skipped + sharded_skipped


def _counts_toward_reuse_metrics(event: dict[str, Any]) -> bool:
    doc_id = event.get("doc_id")
    return isinstance(doc_id, str) and doc_id != "" and not doc_id.startswith("_toolkit/")


def _numeric_estimate(payload: dict[str, Any], key: str) -> int:
    estimates = payload.get("estimated_savings")
    if not isinstance(estimates, dict):
        return 0
    value = estimates.get(key)
    return value if isinstance(value, int) else 0


def build_document_stats(repo_wiki_dir: Path) -> dict[str, Any]:
    events, skipped_lines = _load_repo_reuse_events(repo_wiki_dir)
    documents: dict[str, dict[str, Any]] = {}

    for event in events:
        if not _counts_toward_reuse_metrics(event):
            continue
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
    events, skipped_lines = _load_repo_reuse_events(repo_wiki_dir)
    checks, skipped_check_lines = _load_repo_task_checks(repo_wiki_dir)
    tasks: dict[str, dict[str, Any]] = {}

    for check in checks:
        task_id = check.get("task_id")
        if not isinstance(task_id, str) or not task_id:
            continue
        task_stats = tasks.setdefault(
            task_id,
            {
                "check_count": 0,
                "effective_reuse_count": 0,
                "estimated_seconds_saved": 0,
                "estimated_token_savings": 0,
                "last_check_outcome": None,
                "last_checked_at": None,
                "lookup_reuse_count": 0,
                "preloaded_reuse_count": 0,
                "reuse_checked": False,
                "total_events": 0,
                "_doc_ids": set(),
            },
        )
        task_stats["check_count"] += 1
        task_stats["reuse_checked"] = True
        checked_at = check.get("checked_at")
        if isinstance(checked_at, str):
            task_stats["last_checked_at"] = checked_at
        check_outcome = check.get("check_outcome")
        if isinstance(check_outcome, str):
            task_stats["last_check_outcome"] = check_outcome

    for event in events:
        if not _counts_toward_reuse_metrics(event):
            continue
        task_id = event.get("task_id")
        if not isinstance(task_id, str) or not task_id:
            continue
        task_stats = tasks.setdefault(
            task_id,
            {
                "check_count": 0,
                "_doc_ids": set(),
                "effective_reuse_count": 0,
                "estimated_seconds_saved": 0,
                "estimated_token_savings": 0,
                "last_check_outcome": None,
                "last_checked_at": None,
                "lookup_reuse_count": 0,
                "preloaded_reuse_count": 0,
                "reuse_checked": False,
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
    checked_tasks = 0
    tasks_with_wiki_use = 0
    tasks_without_wiki_use = 0
    tasks_with_events_but_no_check = 0
    for task_id, payload in tasks.items():
        doc_ids = payload.pop("_doc_ids")
        payload["reused_docs"] = len(doc_ids)
        if payload["reuse_checked"]:
            checked_tasks += 1
            if payload["last_check_outcome"] == "wiki_used":
                tasks_with_wiki_use += 1
            elif payload["last_check_outcome"] == "no_wiki_use":
                tasks_without_wiki_use += 1
        elif payload["total_events"] > 0:
            tasks_with_events_but_no_check += 1
        rendered_tasks[task_id] = payload

    return {
        "schema_version": REUSE_SCHEMA_VERSION,
        "skipped_check_lines": skipped_check_lines,
        "skipped_event_lines": skipped_lines,
        "summary": {
            "checked_tasks": checked_tasks,
            "tasks_with_events_but_no_check": tasks_with_events_but_no_check,
            "tasks_with_wiki_use": tasks_with_wiki_use,
            "tasks_without_wiki_use": tasks_without_wiki_use,
        },
        "tasks": rendered_tasks,
    }


def render_task_stats(repo_wiki_dir: Path) -> str:
    return json.dumps(build_task_stats(repo_wiki_dir), indent=2, sort_keys=True) + "\n"
