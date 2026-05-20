"""AI wiki draft promotion candidate helpers."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
from typing import Any

from ai_wiki_toolkit.frontmatter import parse_frontmatter, replace_frontmatter
from ai_wiki_toolkit.wiki_schema import doc_id_for_relative_path, infer_doc_kind, load_reuse_events

PROMOTION_CANDIDATES_SCHEMA_VERSION = "promotion-candidates-v1"
DEFAULT_RESOLVED_TASK_THRESHOLD = 3
NON_AUTO_PROMOTE_STATUSES = {"archived", "dropped", "promoted", "superseded"}
AUTO_PROMOTION_BASIS = (
    "Auto-marked from useful resolved reuse threshold; exact evidence is generated under "
    "ai-wiki/_toolkit/reports/promotion-candidates/<handle>/latest.md."
)
AUTO_PROMOTION_REPORT_PATH = "ai-wiki/_toolkit/reports/promotion-candidates/<handle>/latest.md"


@dataclass(frozen=True)
class PromotionCandidatesResult:
    """Rendered promotion candidate report and optional generated output paths."""

    report: dict[str, Any]
    markdown: str
    json_text: str
    markdown_path: Path | None = None
    json_path: Path | None = None


def _repo_relative(path: Path, repo_wiki_dir: Path) -> str:
    return path.relative_to(repo_wiki_dir).as_posix()


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


def _timestamp_matches(payload: dict[str, Any], key: str, since: datetime | None) -> bool:
    if since is None:
        return True
    parsed = _parse_timestamp(payload.get(key))
    return parsed is not None and parsed >= since


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


def _load_repo_reuse_events(repo_wiki_dir: Path) -> tuple[list[dict[str, Any]], int]:
    legacy_events, legacy_skipped = load_reuse_events(repo_wiki_dir / "metrics" / "reuse-events.jsonl")
    sharded_events, sharded_skipped = load_reuse_events(repo_wiki_dir / "metrics" / "reuse-events")
    return legacy_events + sharded_events, legacy_skipped + sharded_skipped


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


def _normalize_string(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    normalized = value.strip()
    return normalized or None


def _normalize_status(value: object) -> str | None:
    normalized = _normalize_string(value)
    return normalized.lower() if normalized else None


def _normalize_bool(value: object) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"1", "candidate", "true", "yes"}
    return False


def _document_title(metadata: dict[str, object], body: str, path: Path) -> str:
    title = _normalize_string(metadata.get("title"))
    if title:
        return title
    for line in body.splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return path.stem.replace("-", " ").replace("_", " ").strip() or path.stem


def _source_path_for_doc_id(repo_wiki_dir: Path, doc_id: str) -> Path:
    return repo_wiki_dir / f"{doc_id}.md"


def _source_metadata(repo_wiki_dir: Path, doc_id: str) -> dict[str, Any] | None:
    path = _source_path_for_doc_id(repo_wiki_dir, doc_id)
    if not path.exists() or not path.is_file():
        return None
    text = path.read_text(encoding="utf-8")
    metadata, body = parse_frontmatter(text)
    relative = _repo_relative(path, repo_wiki_dir)
    status = _normalize_status(metadata.get("status"))
    return {
        "basis": _normalize_string(metadata.get("promotion_basis")),
        "doc_id": doc_id,
        "doc_kind": infer_doc_kind(relative),
        "path": f"ai-wiki/{relative}",
        "promotion_candidate": _normalize_bool(metadata.get("promotion_candidate")),
        "status": status,
        "title": _document_title(metadata, body, path),
    }


def _all_candidate_drafts(repo_wiki_dir: Path, handle: str) -> list[dict[str, Any]]:
    drafts_dir = repo_wiki_dir / "people" / handle / "drafts"
    if not drafts_dir.exists():
        return []
    candidates: list[dict[str, Any]] = []
    for path in sorted(drafts_dir.glob("*.md")):
        relative = _repo_relative(path, repo_wiki_dir)
        doc_id = doc_id_for_relative_path(relative)
        metadata = _source_metadata(repo_wiki_dir, doc_id)
        if metadata and metadata["promotion_candidate"] and metadata["status"] not in NON_AUTO_PROMOTE_STATUSES:
            candidates.append(metadata)
    return sorted(candidates, key=lambda item: (item["title"].lower(), item["doc_id"]))


def _aggregate_draft_reuse(
    events: list[dict[str, Any]], *, handle: str, since: datetime | None
) -> dict[str, dict[str, Any]]:
    draft_prefix = f"people/{handle}/drafts/"
    documents: dict[str, dict[str, Any]] = {}
    for event in events:
        if not _timestamp_matches(event, "observed_at", since):
            continue
        doc_id = _normalize_doc_id(event.get("doc_id"))
        if doc_id is None or not doc_id.startswith(draft_prefix):
            continue
        stats = documents.setdefault(
            doc_id,
            {
                "doc_id": doc_id,
                "total_events": 0,
                "resolved_events": 0,
                "partial_events": 0,
                "not_helpful_events": 0,
                "lookup_reuse_count": 0,
                "preloaded_reuse_count": 0,
                "estimated_seconds_saved": 0,
                "estimated_token_savings": 0,
                "resolved_task_ids": set(),
                "partial_task_ids": set(),
                "not_helpful_task_ids": set(),
                "event_author_handles": set(),
                "last_observed_at": None,
            },
        )
        stats["total_events"] += 1
        outcome = event.get("reuse_outcome")
        task_id = event.get("task_id")
        task_bucket = None
        if outcome == "resolved":
            stats["resolved_events"] += 1
            task_bucket = stats["resolved_task_ids"]
            saved_seconds, saved_tokens = _estimated_savings(event)
            stats["estimated_seconds_saved"] += saved_seconds
            stats["estimated_token_savings"] += saved_tokens
        elif outcome == "partial":
            stats["partial_events"] += 1
            task_bucket = stats["partial_task_ids"]
        elif outcome == "not_helpful":
            stats["not_helpful_events"] += 1
            task_bucket = stats["not_helpful_task_ids"]
        if isinstance(task_id, str) and task_id and task_bucket is not None:
            task_bucket.add(task_id)
        author = event.get("author_handle")
        if isinstance(author, str) and author:
            stats["event_author_handles"].add(author)
        retrieval_mode = event.get("retrieval_mode")
        if retrieval_mode == "lookup":
            stats["lookup_reuse_count"] += 1
        elif retrieval_mode == "preloaded":
            stats["preloaded_reuse_count"] += 1
        stats["last_observed_at"] = _last_timestamp(stats["last_observed_at"], event.get("observed_at"))
    return documents


def _render_stats_item(
    repo_wiki_dir: Path,
    stats: dict[str, Any],
    *,
    reason: str,
    state: str,
) -> dict[str, Any]:
    source = _source_metadata(repo_wiki_dir, stats["doc_id"])
    item = {
        "doc_id": stats["doc_id"],
        "estimated_seconds_saved": stats["estimated_seconds_saved"],
        "estimated_token_savings": stats["estimated_token_savings"],
        "event_author_handles": sorted(stats["event_author_handles"]),
        "last_observed_at": stats["last_observed_at"],
        "lookup_reuse_count": stats["lookup_reuse_count"],
        "not_helpful_events": stats["not_helpful_events"],
        "not_helpful_tasks": sorted(stats["not_helpful_task_ids"]),
        "partial_events": stats["partial_events"],
        "partial_tasks": sorted(stats["partial_task_ids"]),
        "preloaded_reuse_count": stats["preloaded_reuse_count"],
        "reason": reason,
        "resolved_events": stats["resolved_events"],
        "resolved_tasks": sorted(stats["resolved_task_ids"]),
        "resolved_task_count": len(stats["resolved_task_ids"]),
        "state": state,
        "total_events": stats["total_events"],
    }
    if source is None:
        item.update(
            {
                "doc_kind": "draft",
                "path": f"ai-wiki/{stats['doc_id']}.md",
                "promotion_candidate": False,
                "status": None,
                "title": stats["doc_id"].rsplit("/", maxsplit=1)[-1].replace("-", " "),
            }
        )
    else:
        item.update(source)
    return item


def _classify_items(
    repo_wiki_dir: Path,
    documents: dict[str, dict[str, Any]],
    *,
    resolved_task_threshold: int,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    new_candidates: list[dict[str, Any]] = []
    already_marked: list[dict[str, Any]] = []
    skipped: list[dict[str, Any]] = []
    for doc_id, stats in sorted(documents.items()):
        source = _source_metadata(repo_wiki_dir, doc_id)
        resolved_task_count = len(stats["resolved_task_ids"])
        if source is None:
            skipped.append(
                _render_stats_item(
                    repo_wiki_dir,
                    stats,
                    reason="source draft file is missing",
                    state="missing_source",
                )
            )
            continue
        if source["status"] in NON_AUTO_PROMOTE_STATUSES:
            skipped.append(
                _render_stats_item(
                    repo_wiki_dir,
                    stats,
                    reason=f"draft status is {source['status']}",
                    state="blocked_status",
                )
            )
            continue
        if stats["not_helpful_events"] > 0:
            skipped.append(
                _render_stats_item(
                    repo_wiki_dir,
                    stats,
                    reason="not_helpful reuse blocks automatic candidate marking",
                    state="blocked_not_helpful",
                )
            )
            continue
        if resolved_task_count <= resolved_task_threshold:
            skipped.append(
                _render_stats_item(
                    repo_wiki_dir,
                    stats,
                    reason=(
                        f"resolved distinct task count must be greater than {resolved_task_threshold}"
                    ),
                    state="below_threshold",
                )
            )
            continue
        if source["promotion_candidate"]:
            already_marked.append(
                _render_stats_item(
                    repo_wiki_dir,
                    stats,
                    reason="draft frontmatter already marks promotion_candidate=true",
                    state="already_marked",
                )
            )
            continue
        new_candidates.append(
            _render_stats_item(
                repo_wiki_dir,
                stats,
                reason="useful resolved reuse threshold met with no not_helpful evidence",
                state="new_candidate",
            )
        )
    return new_candidates, already_marked, skipped


def build_promotion_candidates_report(
    repo_wiki_dir: Path,
    *,
    handle: str,
    since: str | None = None,
    resolved_task_threshold: int = DEFAULT_RESOLVED_TASK_THRESHOLD,
    generated_at: str | None = None,
) -> dict[str, Any]:
    """Build a strict auto-candidate report from draft reuse evidence."""
    generated_at = generated_at or datetime.now().astimezone().isoformat(timespec="seconds")
    since_dt = _parse_since(since)
    events, skipped_lines = _load_repo_reuse_events(repo_wiki_dir)
    documents = _aggregate_draft_reuse(events, handle=handle, since=since_dt)
    new_candidates, already_marked, skipped = _classify_items(
        repo_wiki_dir,
        documents,
        resolved_task_threshold=resolved_task_threshold,
    )
    known_candidates = _all_candidate_drafts(repo_wiki_dir, handle)
    return {
        "schema_version": PROMOTION_CANDIDATES_SCHEMA_VERSION,
        "generated_at": generated_at,
        "filters": {
            "handle": handle,
            "since": since,
            "resolved_task_threshold": resolved_task_threshold,
            "candidate_gate": (
                f"resolved distinct task count > {resolved_task_threshold}; "
                "not_helpful events must be 0; source draft must exist and not be stale"
            ),
        },
        "summary": {
            "already_marked": len(already_marked),
            "candidate_drafts_in_index_scope": len(known_candidates),
            "drafts_with_reuse_evidence": len(documents),
            "new_candidates": len(new_candidates),
            "skipped": len(skipped),
            "skipped_event_lines": skipped_lines,
        },
        "new_candidates": new_candidates,
        "already_marked": already_marked,
        "skipped": skipped,
        "known_candidates": known_candidates,
        "apply": {
            "attempted": False,
            "drafts_marked": 0,
            "drafts_normalized": 0,
            "index_updated": False,
        },
        "notes": [
            "Automatic marking only creates handle-local promotion candidates.",
            "Shared conventions, review patterns, problems, features, or decisions still require human confirmation.",
            "Exact reuse counts live in this generated report, not in people/<handle>/index.md.",
        ],
    }


def render_promotion_candidates_json(report: dict[str, Any]) -> str:
    """Render promotion candidates report as stable JSON."""
    return json.dumps(report, indent=2, sort_keys=True) + "\n"


def _format_saved_time(seconds: int) -> str:
    if seconds <= 0:
        return "0s"
    minutes, remainder = divmod(seconds, 60)
    if minutes == 0:
        return f"{seconds}s"
    hours, minutes = divmod(minutes, 60)
    if hours == 0:
        return f"{seconds}s ({minutes}m {remainder}s)"
    return f"{seconds}s ({hours}h {minutes}m {remainder}s)"


def _candidate_line(item: dict[str, Any]) -> str:
    return (
        f"- `{item['path']}` - {item['title']} "
        f"({item['resolved_task_count']} resolved tasks, "
        f"{item['not_helpful_events']} not_helpful, "
        f"saved {_format_saved_time(item['estimated_seconds_saved'])})"
    )


def render_promotion_candidates_markdown(
    report: dict[str, Any],
    *,
    markdown_path: Path | None = None,
    json_path: Path | None = None,
) -> str:
    """Render promotion candidates report as Markdown."""
    filters = report["filters"]
    summary = report["summary"]
    lines = [
        "# AI Wiki Promotion Candidates",
        "",
        f"Generated at: `{report['generated_at']}`",
        "",
        "## Filters",
        "",
        f"- Handle: `{filters['handle']}`",
        f"- Since: `{filters['since'] or 'all'}`",
        f"- Candidate gate: {filters['candidate_gate']}",
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
            f"- Drafts with reuse evidence: {summary['drafts_with_reuse_evidence']}",
            f"- New candidates: {summary['new_candidates']}",
            f"- Already marked: {summary['already_marked']}",
            f"- Skipped: {summary['skipped']}",
            f"- Candidate drafts in index scope: {summary['candidate_drafts_in_index_scope']}",
            "",
            "## New Candidates",
            "",
        ]
    )
    if not report["new_candidates"]:
        lines.extend(["- None detected.", ""])
    else:
        for item in report["new_candidates"]:
            lines.append(_candidate_line(item))
        lines.append("")
    lines.extend(["## Already Marked", ""])
    if not report["already_marked"]:
        lines.extend(["- None detected.", ""])
    else:
        for item in report["already_marked"]:
            lines.append(_candidate_line(item))
        lines.append("")
    lines.extend(["## Skipped", ""])
    if not report["skipped"]:
        lines.extend(["- None detected.", ""])
    else:
        for item in report["skipped"]:
            lines.append(f"- `{item['path']}` - {item['title']}: {item['reason']}")
        lines.append("")
    lines.extend(["## Apply Result", ""])
    apply = report["apply"]
    lines.extend(
        [
            f"- Attempted: `{apply['attempted']}`",
            f"- Drafts marked: {apply['drafts_marked']}",
            f"- Drafts normalized: {apply['drafts_normalized']}",
            f"- Index updated: `{apply['index_updated']}`",
            "",
            "## Notes",
            "",
        ]
    )
    for note in report["notes"]:
        lines.append(f"- {note}")
    lines.append("")
    return "\n".join(lines)


def _needs_auto_basis_normalization(metadata: dict[str, object]) -> bool:
    basis = _normalize_string(metadata.get("promotion_basis"))
    if basis is None:
        return True
    lowered = basis.lower()
    if lowered in {"n/a", "none", "unknown"}:
        return True
    return (
        "auto-marked from reuse log" in lowered
        or "resolved useful reuses" in lowered
        or "distinct tasks" in lowered
    )


def _mark_or_normalize_draft(
    path: Path, *, mark_candidate: bool, promotion_report_path: str
) -> tuple[bool, bool]:
    text = path.read_text(encoding="utf-8")
    metadata, _ = parse_frontmatter(text)
    changed = False
    marked = False
    if mark_candidate and not _normalize_bool(metadata.get("promotion_candidate")):
        metadata["promotion_candidate"] = True
        changed = True
        marked = True
    if _normalize_bool(metadata.get("promotion_candidate")) and _needs_auto_basis_normalization(metadata):
        metadata["promotion_basis"] = AUTO_PROMOTION_BASIS
        changed = True
    if (
        _normalize_bool(metadata.get("promotion_candidate"))
        and metadata.get("promotion_report") != promotion_report_path
    ):
        metadata["promotion_report"] = promotion_report_path
        changed = True
    if changed:
        path.write_text(replace_frontmatter(text, metadata), encoding="utf-8")
    return marked, changed and not marked


def _promotion_index_section(candidates: list[dict[str, Any]]) -> str:
    lines = [
        "## Promotion Candidates",
        "",
        "These handle-local drafts have enough useful reuse evidence or reviewer judgment to deserve human review before shared promotion.",
        "",
        "Promotion evidence and changing counts live in `ai-wiki/_toolkit/reports/promotion-candidates/<handle>/latest.md`; this index only keeps stable draft links.",
        "",
    ]
    if not candidates:
        lines.extend(["- None currently marked.", ""])
        return "\n".join(lines)
    for item in candidates:
        relative = Path(item["path"].removeprefix("ai-wiki/")).relative_to(
            f"people/{item['path'].split('/')[2]}"
        )
        lines.append(f"- [{item['title']}]({relative.as_posix()})")
    lines.append("")
    return "\n".join(lines)


def _replace_or_append_index_section(text: str, section: str) -> str:
    heading = "## Promotion Candidates"
    lines = text.rstrip().splitlines()
    start = None
    for index, line in enumerate(lines):
        if line.strip() == heading:
            start = index
            break
    if start is None:
        return text.rstrip() + "\n\n" + section
    end = len(lines)
    for index in range(start + 1, len(lines)):
        if lines[index].startswith("## "):
            end = index
            break
    return "\n".join(lines[:start] + section.rstrip().splitlines() + lines[end:]).rstrip() + "\n"


def _update_person_index(repo_wiki_dir: Path, *, handle: str) -> bool:
    index_path = repo_wiki_dir / "people" / handle / "index.md"
    if not index_path.exists():
        return False
    candidates = _all_candidate_drafts(repo_wiki_dir, handle)
    section = _promotion_index_section(candidates)
    text = index_path.read_text(encoding="utf-8")
    updated = _replace_or_append_index_section(text, section)
    if updated == text:
        return False
    index_path.write_text(updated, encoding="utf-8")
    return True


def _apply_promotion_candidates(
    repo_wiki_dir: Path,
    report: dict[str, Any],
    *,
    handle: str,
    update_index: bool,
) -> dict[str, Any]:
    drafts_marked = 0
    drafts_normalized = 0
    promotion_report_path = f"ai-wiki/_toolkit/reports/promotion-candidates/{handle}/latest.md"
    for item in report["new_candidates"]:
        path = _source_path_for_doc_id(repo_wiki_dir, item["doc_id"])
        marked, normalized = _mark_or_normalize_draft(
            path,
            mark_candidate=True,
            promotion_report_path=promotion_report_path,
        )
        if marked:
            drafts_marked += 1
        if normalized:
            drafts_normalized += 1
    for item in report["already_marked"]:
        path = _source_path_for_doc_id(repo_wiki_dir, item["doc_id"])
        marked, normalized = _mark_or_normalize_draft(
            path,
            mark_candidate=False,
            promotion_report_path=promotion_report_path,
        )
        if marked:
            drafts_marked += 1
        if normalized:
            drafts_normalized += 1
    index_updated = _update_person_index(repo_wiki_dir, handle=handle) if update_index else False
    return {
        "attempted": True,
        "drafts_marked": drafts_marked,
        "drafts_normalized": drafts_normalized,
        "index_updated": index_updated,
    }


def generate_promotion_candidates(
    repo_wiki_dir: Path,
    *,
    handle: str,
    since: str | None = None,
    resolved_task_threshold: int = DEFAULT_RESOLVED_TASK_THRESHOLD,
    apply: bool = False,
    update_index: bool = True,
    write: bool = True,
) -> PromotionCandidatesResult:
    """Generate promotion candidates and optionally mark draft frontmatter/index links."""
    report = build_promotion_candidates_report(
        repo_wiki_dir,
        handle=handle,
        since=since,
        resolved_task_threshold=resolved_task_threshold,
    )
    if apply:
        report["apply"] = _apply_promotion_candidates(
            repo_wiki_dir,
            report,
            handle=handle,
            update_index=update_index,
        )
        report["known_candidates"] = _all_candidate_drafts(repo_wiki_dir, handle)
        report["summary"]["candidate_drafts_in_index_scope"] = len(report["known_candidates"])

    report_dir = repo_wiki_dir / "_toolkit" / "reports" / "promotion-candidates" / handle
    markdown_path = report_dir / "latest.md" if write else None
    json_path = report_dir / "latest.json" if write else None
    display_markdown_path = (
        Path(f"ai-wiki/_toolkit/reports/promotion-candidates/{handle}/latest.md") if write else None
    )
    display_json_path = (
        Path(f"ai-wiki/_toolkit/reports/promotion-candidates/{handle}/latest.json") if write else None
    )
    markdown = render_promotion_candidates_markdown(
        report,
        markdown_path=display_markdown_path,
        json_path=display_json_path,
    )
    json_text = render_promotion_candidates_json(report)
    if write:
        report_dir.mkdir(parents=True, exist_ok=True)
        assert markdown_path is not None
        assert json_path is not None
        markdown_path.write_text(markdown, encoding="utf-8")
        json_path.write_text(json_text, encoding="utf-8")
    return PromotionCandidatesResult(
        report=report,
        markdown=markdown,
        json_text=json_text,
        markdown_path=markdown_path,
        json_path=json_path,
    )
