"""AI wiki draft consolidation queue helpers."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import hashlib
import json
from pathlib import Path
import re
from typing import Any

from ai_wiki_toolkit.diagnostics import (
    DEFAULT_DIAGNOSTICS_MAX_ITEMS,
    DEFAULT_HIGH_ROI_MIN_EVENTS,
    DEFAULT_NOISY_MIN_EVENTS,
    build_memory_diagnostics_report,
)
from ai_wiki_toolkit.frontmatter import parse_frontmatter
from ai_wiki_toolkit.paths import slugify
from ai_wiki_toolkit.wiki_schema import doc_id_for_relative_path

CONSOLIDATION_SCHEMA_VERSION = "consolidation-queue-v1"
DEFAULT_CONSOLIDATION_MAX_ITEMS = 10

ACTION_KEEP_DRAFT = "Keep draft"
ACTION_REFINE_DRAFT = "Refine draft"
ACTION_PROMOTION_CANDIDATE = "Promotion candidate"
ACTION_CONFLICT = "Conflict"
ACTION_SUPERSESSION = "Supersession"

CONFLICT_PATTERNS = (
    re.compile(r"\bconflicts?\s+with\b", re.IGNORECASE),
    re.compile(r"\bconflicting\s+guidance\b", re.IGNORECASE),
    re.compile(r"\bcontradicts?\b", re.IGNORECASE),
    re.compile(r"\bcontradictory\b", re.IGNORECASE),
    re.compile(r"\binconsistent\s+with\b", re.IGNORECASE),
)
STALE_STATUSES = {"archived", "dropped", "superseded"}
STOPWORDS = {
    "a",
    "ai",
    "and",
    "as",
    "be",
    "by",
    "can",
    "for",
    "from",
    "in",
    "is",
    "it",
    "memory",
    "needs",
    "of",
    "on",
    "or",
    "should",
    "that",
    "the",
    "to",
    "use",
    "when",
    "wiki",
    "with",
}
TARGET_INDEX_PATHS = {
    "ai-wiki/conventions/": "ai-wiki/conventions/index.md",
    "ai-wiki/review-patterns/": "ai-wiki/review-patterns/index.md",
    "ai-wiki/problems/": "ai-wiki/problems/index.md",
    "ai-wiki/features/": "ai-wiki/features/index.md",
    "ai-wiki/decisions.md": "ai-wiki/decisions.md",
}


@dataclass(frozen=True)
class DraftDocument:
    """Handle-local draft metadata used to build consolidation clusters."""

    doc_id: str
    path: Path
    display_path: str
    title: str
    source_kind: str | None
    status: str | None
    promotion_candidate: bool
    promotion_basis: str | None
    superseded_by: str | None
    body: str


@dataclass(frozen=True)
class DiagnosticSignal:
    """A diagnostics-derived weak signal for one draft."""

    kind: str
    reason: str
    priority: int


@dataclass(frozen=True)
class DraftConsolidationResult:
    """Rendered draft consolidation queue and optional generated output paths."""

    report: dict[str, Any]
    markdown: str
    json_text: str
    markdown_path: Path | None = None
    json_path: Path | None = None


def _repo_relative(path: Path, repo_wiki_dir: Path) -> str:
    return path.relative_to(repo_wiki_dir).as_posix()


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
        return value.strip().lower() in {"true", "yes", "1", "candidate"}
    return False


def _document_title(metadata: dict[str, Any], body: str, path: Path) -> str:
    title = _normalize_string(metadata.get("title"))
    if title:
        return title
    for line in body.splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return path.stem.replace("-", " ").replace("_", " ").strip() or path.stem


def _load_drafts(repo_wiki_dir: Path, handle: str) -> list[DraftDocument]:
    drafts_dir = repo_wiki_dir / "people" / handle / "drafts"
    if not drafts_dir.exists():
        return []

    drafts: list[DraftDocument] = []
    for path in sorted(drafts_dir.glob("*.md")):
        text = path.read_text(encoding="utf-8")
        metadata, body = parse_frontmatter(text)
        relative = _repo_relative(path, repo_wiki_dir)
        drafts.append(
            DraftDocument(
                doc_id=doc_id_for_relative_path(relative),
                path=path,
                display_path=f"ai-wiki/{relative}",
                title=_document_title(metadata, body, path),
                source_kind=_normalize_string(metadata.get("source_kind")),
                status=_normalize_status(metadata.get("status")),
                promotion_candidate=_normalize_bool(metadata.get("promotion_candidate")),
                promotion_basis=_normalize_string(metadata.get("promotion_basis")),
                superseded_by=(
                    _normalize_string(metadata.get("superseded_by"))
                    or _normalize_string(metadata.get("replaced_by"))
                    or _normalize_string(metadata.get("successor"))
                ),
                body=body,
            )
        )
    return drafts


def _normalize_doc_id(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    normalized = value.strip()
    if not normalized:
        return None
    normalized = normalized.removeprefix("ai-wiki/").removesuffix(".md")
    if normalized.startswith("_toolkit/"):
        return None
    return normalized


def _signal_reason(item: dict[str, Any]) -> str:
    reason = item.get("reason")
    return reason if isinstance(reason, str) and reason.strip() else "diagnostic signal"


def _collect_diagnostic_signals(report: dict[str, Any]) -> dict[str, list[DiagnosticSignal]]:
    signals: dict[str, list[DiagnosticSignal]] = {}

    def add(doc_id: object, signal: DiagnosticSignal) -> None:
        normalized_doc_id = _normalize_doc_id(doc_id)
        if normalized_doc_id:
            signals.setdefault(normalized_doc_id, []).append(signal)

    for item in report.get("high_roi_memory", []):
        if isinstance(item, dict):
            add(
                item.get("doc_id"),
                DiagnosticSignal("high_roi_memory", _signal_reason(item), 70),
            )
    for item in report.get("noisy_memory", []):
        if isinstance(item, dict):
            add(
                item.get("doc_id"),
                DiagnosticSignal("noisy_memory", _signal_reason(item), 50),
            )
    for item in report.get("stale_memory", []):
        if isinstance(item, dict):
            add(
                item.get("doc_id"),
                DiagnosticSignal("stale_memory", _signal_reason(item), 80),
            )
    for item in report.get("conflicting_memory", []):
        if isinstance(item, dict):
            add(
                item.get("doc_id"),
                DiagnosticSignal("conflicting_memory", _signal_reason(item), 90),
            )
    for item in report.get("missed_memory", []):
        if isinstance(item, dict):
            add(
                item.get("doc_id"),
                DiagnosticSignal("missed_memory", _signal_reason(item), 45),
            )
    for item in report.get("coverage_gaps", []):
        if not isinstance(item, dict):
            continue
        reason = _signal_reason(item)
        doc_ids = item.get("doc_ids")
        if isinstance(doc_ids, list):
            for doc_id in doc_ids:
                add(doc_id, DiagnosticSignal("coverage_gap", reason, 35))

    return signals


def _contains_conflict_signal(text: str) -> bool:
    return any(pattern.search(text) for pattern in CONFLICT_PATTERNS)


def _topic_key(draft: DraftDocument) -> str:
    words = [
        word
        for word in re.split(r"[^a-z0-9]+", draft.title.lower())
        if word and word not in STOPWORDS
    ]
    if not words:
        words = [
            word
            for word in re.split(r"[^a-z0-9]+", draft.path.stem.lower())
            if word and word not in STOPWORDS
        ]
    source_kind = draft.source_kind or "draft"
    return f"{source_kind}:{'-'.join(words[:4]) or draft.path.stem}"


def _target_slug(drafts: list[DraftDocument]) -> str:
    return slugify(drafts[0].title) if drafts else "draft"


def _target_for_promotion(drafts: list[DraftDocument], handle: str) -> str:
    draft = drafts[0]
    slug = _target_slug(drafts)
    source_kind = (draft.source_kind or "").lower()
    haystack = f"{draft.title} {draft.path.stem}".lower()
    if source_kind == "review":
        return f"ai-wiki/review-patterns/{slug}.md"
    if source_kind == "feature_clarification":
        return f"ai-wiki/features/{slug}.md"
    if source_kind == "decision":
        return "ai-wiki/decisions.md"
    if "convention" in haystack or "team rule" in haystack:
        return f"ai-wiki/conventions/{slug}.md"
    if any(word in haystack for word in ("problem", "failure", "fix", "bug", "debug")):
        return f"ai-wiki/problems/{slug}.md"
    return f"ai-wiki/people/{handle}/drafts/{slug}.md"


def _target_for_refinement(drafts: list[DraftDocument], handle: str) -> str:
    if len(drafts) == 1:
        return drafts[0].display_path
    return f"ai-wiki/people/{handle}/drafts/{_target_slug(drafts)}.md"


def _existing_memory_checked(repo_wiki_dir: Path, action: str, target: str) -> list[str]:
    candidates: list[str]
    if action == ACTION_CONFLICT:
        candidates = [
            "ai-wiki/conventions/index.md",
            "ai-wiki/decisions.md",
            "ai-wiki/review-patterns/index.md",
            "ai-wiki/problems/index.md",
            "ai-wiki/features/index.md",
        ]
    else:
        candidates = []
        for prefix, index_path in TARGET_INDEX_PATHS.items():
            if target == prefix or target.startswith(prefix):
                candidates.append(index_path)
                break
    existing = []
    for candidate in candidates:
        repo_relative = candidate.removeprefix("ai-wiki/")
        if (repo_wiki_dir / repo_relative).exists():
            existing.append(candidate)
    return existing or ["None"]


def _weak_signals(drafts: list[DraftDocument], signals: list[DiagnosticSignal]) -> list[str]:
    rendered = [f"{signal.kind}: {signal.reason}" for signal in signals]
    if len(drafts) > 1:
        rendered.append(f"{len(drafts)} related drafts share a topic key")
    if any(draft.promotion_candidate for draft in drafts):
        rendered.append("draft frontmatter marks promotion_candidate=true")
    if any(draft.status in STALE_STATUSES for draft in drafts):
        statuses = sorted({draft.status for draft in drafts if draft.status in STALE_STATUSES})
        rendered.append(f"draft status: {', '.join(statuses)}")
    return rendered or ["None"]


def _choose_cluster_action(
    drafts: list[DraftDocument],
    signals: list[DiagnosticSignal],
    *,
    handle: str,
) -> tuple[str, str, str, int]:
    signal_kinds = {signal.kind for signal in signals}
    has_conflict_text = any(_contains_conflict_signal(draft.body) for draft in drafts)
    has_stale_status = any(draft.status in STALE_STATUSES for draft in drafts)
    score = len(drafts) * 5 + sum(signal.priority for signal in signals)

    if "conflicting_memory" in signal_kinds or has_conflict_text:
        why = "Diagnostics or draft text suggest overlapping guidance may conflict and needs human review."
        return ACTION_CONFLICT, "n/a", why, score + 500

    if "stale_memory" in signal_kinds or has_stale_status:
        replacement = next((draft.superseded_by for draft in drafts if draft.superseded_by), None)
        target = replacement or "n/a"
        why = "The draft or its reuse evidence is marked stale, archived, dropped, or superseded."
        return ACTION_SUPERSESSION, target, why, score + 450

    if any(draft.promotion_candidate for draft in drafts) or "high_roi_memory" in signal_kinds:
        target = _target_for_promotion(drafts, handle)
        why = "The draft has promotion-candidate metadata or high-ROI reuse evidence."
        return ACTION_PROMOTION_CANDIDATE, target, why, score + 400

    if len(drafts) > 1 or signal_kinds & {"noisy_memory", "missed_memory", "coverage_gap"}:
        target = _target_for_refinement(drafts, handle)
        why = "The draft cluster has weak evidence that it should be cleaned up before any promotion decision."
        return ACTION_REFINE_DRAFT, target, why, score + 300

    return ACTION_KEEP_DRAFT, drafts[0].display_path, "No strong consolidation signal yet.", score + 100


def _cluster_queue_items(
    repo_wiki_dir: Path,
    *,
    handle: str,
    drafts: list[DraftDocument],
    diagnostics_report: dict[str, Any],
    max_items: int,
) -> list[dict[str, Any]]:
    signals_by_doc_id = _collect_diagnostic_signals(diagnostics_report)
    candidate_drafts = [
        draft
        for draft in drafts
        if draft.doc_id in signals_by_doc_id
        or draft.promotion_candidate
        or draft.status in STALE_STATUSES
        or _contains_conflict_signal(draft.body)
    ]
    grouped: dict[str, list[DraftDocument]] = {}
    for draft in candidate_drafts:
        grouped.setdefault(_topic_key(draft), []).append(draft)

    scored_items: list[tuple[int, str, dict[str, Any]]] = []
    for key, group in grouped.items():
        group = sorted(group, key=lambda draft: draft.display_path)
        group_signals: list[DiagnosticSignal] = []
        for draft in group:
            group_signals.extend(signals_by_doc_id.get(draft.doc_id, []))
        action, target, why, score = _choose_cluster_action(group, group_signals, handle=handle)
        if action == ACTION_KEEP_DRAFT:
            continue
        source_drafts = [draft.display_path for draft in group]
        title = group[0].title
        if len(group) > 1:
            title = f"{title} and related drafts"
        identity = "|".join([action, key, *source_drafts])
        item_id = f"cq_{hashlib.sha1(identity.encode('utf-8')).hexdigest()[:12]}"
        item = {
            "item_id": item_id,
            "cluster_title": title,
            "source_drafts": source_drafts,
            "existing_memory_checked": _existing_memory_checked(repo_wiki_dir, action, target),
            "suggested_action": action,
            "suggested_target": target,
            "why": why,
            "weak_signals": _weak_signals(group, group_signals),
            "human_confirmation": "Required",
        }
        scored_items.append((score, item_id, item))

    return [
        item
        for _, _, item in sorted(scored_items, key=lambda row: (-row[0], row[1]))[:max_items]
    ]


def build_consolidation_queue_report(
    repo_wiki_dir: Path,
    *,
    handle: str,
    since: str | None = None,
    max_items: int = DEFAULT_CONSOLIDATION_MAX_ITEMS,
    high_roi_min_events: int = DEFAULT_HIGH_ROI_MIN_EVENTS,
    noisy_min_events: int = DEFAULT_NOISY_MIN_EVENTS,
    generated_at: str | None = None,
) -> dict[str, Any]:
    """Build a diagnostics-driven draft consolidation queue."""
    generated_at = generated_at or datetime.now().astimezone().isoformat(timespec="seconds")
    diagnostics_report = build_memory_diagnostics_report(
        repo_wiki_dir,
        handle=handle,
        since=since,
        max_items=max(max_items, DEFAULT_DIAGNOSTICS_MAX_ITEMS),
        high_roi_min_events=high_roi_min_events,
        noisy_min_events=noisy_min_events,
        generated_at=generated_at,
    )
    drafts = _load_drafts(repo_wiki_dir, handle)
    queue_items = _cluster_queue_items(
        repo_wiki_dir,
        handle=handle,
        drafts=drafts,
        diagnostics_report=diagnostics_report,
        max_items=max_items,
    )
    return {
        "schema_version": CONSOLIDATION_SCHEMA_VERSION,
        "generated_at": generated_at,
        "filters": {
            "handle": handle,
            "since": since,
        },
        "summary": {
            "drafts_scanned": len(drafts),
            "queue_items": len(queue_items),
            "diagnostics_summary": diagnostics_report["summary"],
        },
        "queue_items": queue_items,
        "diagnostics_source": {
            "schema_version": diagnostics_report["schema_version"],
            "generated_at": diagnostics_report["generated_at"],
            "note": "Queue priorities are derived from the same local evidence model as `aiwiki-toolkit diagnose memory`.",
        },
        "consolidation_notes": [
            "This is a generated human-review queue, not canonical memory.",
            "Shared conventions, review patterns, problems, features, or decisions still require human confirmation before writing shared docs.",
            "Metrics and diagnostics are weak signals for prioritization, not proof that a draft should be promoted.",
        ],
    }


def render_consolidation_queue_json(report: dict[str, Any]) -> str:
    """Render the consolidation queue as stable JSON."""
    return json.dumps(report, indent=2, sort_keys=True) + "\n"


def _render_list(lines: list[str], values: list[str]) -> None:
    for value in values:
        lines.append(f"- {value}")


def render_consolidation_queue_markdown(
    report: dict[str, Any],
    *,
    markdown_path: Path | None = None,
    json_path: Path | None = None,
) -> str:
    """Render the consolidation queue as Markdown."""
    filters = report["filters"]
    summary = report["summary"]
    lines = [
        "# AI Wiki Draft Consolidation",
        "",
        f"Generated at: `{report['generated_at']}`",
        "",
        "## Filters",
        "",
        f"- Handle: `{filters['handle']}`",
        f"- Since: `{filters['since'] or 'all'}`",
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
            f"- Drafts scanned: {summary['drafts_scanned']}",
            f"- Queue items: {summary['queue_items']}",
            "",
            "## Draft Clusters",
            "",
        ]
    )
    queue_items = report["queue_items"]
    if not queue_items:
        lines.extend(["- None detected.", ""])
    for index, item in enumerate(queue_items, start=1):
        lines.extend([f"### Cluster {index}: {item['cluster_title']}", ""])
        lines.extend(["Source drafts:"])
        _render_list(lines, [f"`{path}`" for path in item["source_drafts"]])
        lines.extend(["", "Existing memory checked:"])
        _render_list(
            lines,
            [
                f"`{path}`" if path != "None" else "`None`"
                for path in item["existing_memory_checked"]
            ],
        )
        lines.extend(["", "Suggested action:"])
        lines.append(f"- {item['suggested_action']}")
        lines.extend(["", "Suggested target:"])
        target = item["suggested_target"]
        lines.append(f"- `{target}`" if target != "n/a" else "- n/a")
        lines.extend(["", "Why:"])
        lines.append(f"- {item['why']}")
        lines.extend(["", "Weak signals considered:"])
        _render_list(
            lines,
            [
                f"`{signal}`" if signal == "None" else signal
                for signal in item["weak_signals"]
            ],
        )
        lines.extend(["", "Human confirmation:"])
        lines.append(f"- {item['human_confirmation']}")
        lines.append("")
    lines.extend(["## Notes", ""])
    for note in report["consolidation_notes"]:
        lines.append(f"- {note}")
    lines.append("")
    return "\n".join(lines)


def generate_consolidation_queue(
    repo_wiki_dir: Path,
    *,
    handle: str,
    since: str | None = None,
    max_items: int = DEFAULT_CONSOLIDATION_MAX_ITEMS,
    high_roi_min_events: int = DEFAULT_HIGH_ROI_MIN_EVENTS,
    noisy_min_events: int = DEFAULT_NOISY_MIN_EVENTS,
    write: bool = True,
) -> DraftConsolidationResult:
    """Generate and optionally write the AI wiki draft consolidation queue."""
    report = build_consolidation_queue_report(
        repo_wiki_dir,
        handle=handle,
        since=since,
        max_items=max_items,
        high_roi_min_events=high_roi_min_events,
        noisy_min_events=noisy_min_events,
    )
    consolidation_dir = repo_wiki_dir / "_toolkit" / "consolidation"
    markdown_path = consolidation_dir / "queue.md" if write else None
    json_path = consolidation_dir / "queue.json" if write else None
    display_markdown_path = Path("ai-wiki/_toolkit/consolidation/queue.md") if write else None
    display_json_path = Path("ai-wiki/_toolkit/consolidation/queue.json") if write else None
    markdown = render_consolidation_queue_markdown(
        report,
        markdown_path=display_markdown_path,
        json_path=display_json_path,
    )
    json_text = render_consolidation_queue_json(report)
    if write:
        consolidation_dir.mkdir(parents=True, exist_ok=True)
        assert markdown_path is not None
        assert json_path is not None
        markdown_path.write_text(markdown, encoding="utf-8")
        json_path.write_text(json_text, encoding="utf-8")
    return DraftConsolidationResult(
        report=report,
        markdown=markdown,
        json_text=json_text,
        markdown_path=markdown_path,
        json_path=json_path,
    )
