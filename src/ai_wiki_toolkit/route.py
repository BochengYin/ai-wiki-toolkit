"""Task-aware AI wiki context routing."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import re
import subprocess
from typing import Any, Iterable

from ai_wiki_toolkit.frontmatter import parse_frontmatter
from ai_wiki_toolkit.paths import build_paths, resolve_user_handle, slugify
from ai_wiki_toolkit.reuse_events import RepoWikiNotInitializedError
from ai_wiki_toolkit.wiki_schema import (
    build_document_stats,
    build_repo_catalog,
)
from ai_wiki_toolkit.work_ledger import OPEN_WORK_STATUSES, build_work_state

ROUTE_SCHEMA_VERSION = "route-v1"
DEFAULT_ROUTE_SAFETY_CAP_WORDS = 3000

_TOKEN_RE = re.compile(r"[a-z0-9][a-z0-9_-]{1,}", re.IGNORECASE)
_MARKDOWN_LINK_RE = re.compile(r"\[([^\]]+)\]\([^)]+\)")
_RULE_PREFIX_RE = re.compile(r"^(?:[-*]\s+|\d+[.)]\s+|>\s*)+")
_STOPWORDS = {
    "about",
    "add",
    "after",
    "again",
    "agent",
    "ai",
    "ai-wiki",
    "aiwiki",
    "all",
    "also",
    "and",
    "are",
    "because",
    "before",
    "bochengyin",
    "but",
    "can",
    "codex",
    "current",
    "does",
    "for",
    "from",
    "have",
    "how",
    "in",
    "into",
    "is",
    "it",
    "its",
    "md",
    "need",
    "now",
    "our",
    "should",
    "support",
    "task",
    "test",
    "that",
    "the",
    "their",
    "this",
    "toolkit",
    "to",
    "use",
    "user",
    "users",
    "what",
    "when",
    "where",
    "whether",
    "wiki",
    "with",
    "you",
    "drafts",
    "people",
    "py",
    "src",
}

_TASK_TYPE_KEYWORDS: dict[str, set[str]] = {
    "release_distribution": {
        "asset",
        "binary",
        "brew",
        "ci",
        "distribution",
        "glibc",
        "homebrew",
        "musl",
        "npm",
        "package",
        "publish",
        "release",
        "smoke",
        "version",
        "workflow",
    },
    "scaffold_prompt_workflow": {
        "agent",
        "agents",
        "ai-wiki",
        "aiwiki",
        "claude",
        "codex",
        "install",
        "managed",
        "prompt",
        "route",
        "scaffold",
        "skill",
        "toolkit",
        "_toolkit",
    },
    "eval_workflow": {
        "benchmark",
        "eval",
        "evaluation",
        "impact",
        "metric",
        "replay",
        "rubric",
        "score",
        "task-family",
    },
    "memory_governance": {
        "conflict",
        "consolidate",
        "consolidation",
        "context",
        "draft",
        "memory",
        "packet",
        "promote",
        "promotion",
        "reuse",
        "route",
        "stale",
        "write-back",
    },
    "workflow_state": {
        "active",
        "archive",
        "archived",
        "blocked",
        "done",
        "epic",
        "ledger",
        "planned",
        "processing",
        "status",
        "todo",
        "todos",
        "work",
        "work-ledger",
    },
    "review_feedback": {
        "comment",
        "feedback",
        "pr",
        "review",
        "reviewer",
    },
    "docs_positioning": {
        "copy",
        "docs",
        "documentation",
        "positioning",
        "readme",
        "website",
    },
    "bug_fix": {
        "bug",
        "error",
        "fail",
        "failing",
        "fix",
        "regression",
        "test",
    },
}

_KIND_PRIORITIES_BY_TASK_TYPE: dict[str, dict[str, int]] = {
    "release_distribution": {
        "constraints": 6,
        "convention": 7,
        "decisions": 5,
        "problem": 7,
        "review_pattern": 4,
        "workflows": 6,
    },
    "scaffold_prompt_workflow": {
        "constraints": 8,
        "convention": 7,
        "convention_index": 3,
        "decisions": 6,
        "feature": 3,
        "problem": 4,
        "review_pattern": 5,
        "workflows": 5,
    },
    "eval_workflow": {
        "convention": 4,
        "decisions": 4,
        "draft": 4,
        "feature": 5,
        "problem": 5,
        "trail": 4,
        "workflows": 4,
    },
    "memory_governance": {
        "constraints": 7,
        "convention": 7,
        "decisions": 5,
        "draft": 5,
        "feature": 4,
        "problem": 5,
        "review_pattern": 5,
        "workflows": 5,
    },
    "workflow_state": {
        "constraints": 4,
        "decisions": 4,
        "feature": 5,
        "problem": 4,
        "trail": 4,
        "workflows": 5,
    },
    "review_feedback": {
        "convention": 4,
        "draft": 4,
        "review_pattern": 8,
        "review_pattern_index": 3,
    },
    "docs_positioning": {
        "constraints": 3,
        "decisions": 4,
        "feature": 4,
        "workflows": 3,
    },
    "bug_fix": {
        "constraints": 3,
        "convention": 4,
        "problem": 8,
        "review_pattern": 5,
        "workflows": 4,
    },
    "general": {
        "constraints": 2,
        "decisions": 2,
        "workflows": 2,
    },
}

_RISK_TAG_KEYWORDS: dict[str, set[str]] = {
    "user_owned_docs": {
        "ai-wiki",
        "aiwiki",
        "install",
        "managed",
        "scaffold",
        "starter",
        "toolkit",
        "user-owned",
        "_toolkit",
    },
    "managed_prompt_block": {
        "agent",
        "agents",
        "claude",
        "codex",
        "managed",
        "prompt",
    },
    "release_distribution": {
        "binary",
        "brew",
        "homebrew",
        "npm",
        "package",
        "publish",
        "release",
        "version",
    },
    "ci_workflow": {
        "actions",
        "ci",
        "smoke",
        "workflow",
    },
    "memory_governance": {
        "consolidate",
        "context",
        "draft",
        "memory",
        "packet",
        "promotion",
        "reuse",
        "route",
        "write-back",
    },
    "workflow_state": {
        "active",
        "blocked",
        "done",
        "epic",
        "ledger",
        "processing",
        "status",
        "todo",
        "work",
    },
    "task_evaluation": {
        "benchmark",
        "eval",
        "replay",
        "rubric",
        "score",
    },
}

_LOW_EFFORT_OPERATIONAL_KEYWORDS = {
    "branch",
    "finish",
    "merge",
    "open",
    "pr",
    "pull-request",
    "push",
    "status",
    "sync",
}

_NON_LOW_EFFORT_KEYWORDS = {
    "add",
    "build",
    "change",
    "code",
    "debug",
    "design",
    "fix",
    "implement",
    "refactor",
    "release",
    "test",
    "update",
}

_DEEP_EFFORT_KEYWORDS = {
    "architecture",
    "budget",
    "compile",
    "consolidation",
    "context",
    "design",
    "diagnosis",
    "framework",
    "index",
    "memory",
    "roadmap",
    "route",
    "routing",
    "v2",
}

_ACTION_MARKERS = (
    "avoid ",
    "do not ",
    "don't ",
    "keep ",
    "must ",
    "never ",
    "only ",
    "prefer ",
    "preserve ",
    "put ",
    "record ",
    "require ",
    "should ",
    "treat ",
    "use ",
)

_AUTHORITATIVE_KINDS = {
    "constraints",
    "convention",
    "decisions",
    "feature",
    "problem",
    "review_pattern",
    "workflows",
}

_SUCCESS_CRITERIA_BY_TASK_TYPE: dict[str, list[dict[str, str]]] = {
    "release_distribution": [
        {
            "criterion": "Release and distribution behavior stays aligned across published targets.",
            "verification": "Run the targeted release, distribution, or smoke tests that cover the changed target matrix.",
            "reason": "release_distribution task",
        },
    ],
    "scaffold_prompt_workflow": [
        {
            "criterion": "Managed prompt, scaffold, or toolkit changes stay inside package-owned surfaces.",
            "verification": "Review the diff for user-owned AI wiki docs and run targeted scaffold, prompt, or doctor tests.",
            "reason": "scaffold_prompt_workflow task",
        },
    ],
    "eval_workflow": [
        {
            "criterion": "Eval output is reproducible and exposes the primary product signal.",
            "verification": "Run the targeted eval/report command and confirm baseline, treatment, score, and first-pass fields are present.",
            "reason": "eval_workflow task",
        },
    ],
    "memory_governance": [
        {
            "criterion": "Stable Markdown remains the source of truth for memory behavior.",
            "verification": "Confirm generated packets or assets cite source paths and no shared user-owned docs were rewritten automatically.",
            "reason": "memory_governance task",
        },
    ],
    "workflow_state": [
        {
            "criterion": "Work state transitions are captured in the append-only ledger.",
            "verification": "Run or inspect the work report/state refresh and confirm the item status, assignee, and source are correct.",
            "reason": "workflow_state task",
        },
    ],
    "review_feedback": [
        {
            "criterion": "Actionable review feedback is addressed with a clear comment-to-diff trace.",
            "verification": "Check each changed line against the review request and run targeted tests for behavior changes.",
            "reason": "review_feedback task",
        },
    ],
    "docs_positioning": [
        {
            "criterion": "Documentation claims match the implemented product surface.",
            "verification": "Review changed docs for unsupported promises and run any docs or README-related smoke checks.",
            "reason": "docs_positioning task",
        },
    ],
    "bug_fix": [
        {
            "criterion": "The reported bug is reproduced or its failure mode is explicitly identified.",
            "verification": "Add or run a focused regression test that fails before the fix or documents the existing failing path, then confirm it passes.",
            "reason": "bug_fix task",
        },
    ],
    "general": [
        {
            "criterion": "The requested outcome is complete without widening scope.",
            "verification": "Review the final diff or command result against the user request and note any deliberate omissions.",
            "reason": "general task",
        },
    ],
}


@dataclass(frozen=True)
class RouteResult:
    """Generated route packet and resolved paths."""

    packet: dict[str, Any]
    repo_root: Path
    repo_wiki_dir: Path


def _tokenize(value: str, *, filter_stopwords: bool = True) -> set[str]:
    tokens = {match.group(0).lower() for match in _TOKEN_RE.finditer(value)}
    expanded: set[str] = set()
    for token in tokens:
        expanded.add(token)
        expanded.update(part for part in re.split(r"[-_]+", token) if len(part) > 1)
    if not filter_stopwords:
        return expanded
    return {token for token in expanded if token not in _STOPWORDS}


def _read_git_changed_paths(repo_root: Path) -> list[str]:
    try:
        result = subprocess.run(
            ["git", "status", "--short"],
            cwd=repo_root,
            capture_output=True,
            check=False,
            text=True,
        )
    except OSError:
        return []
    if result.returncode != 0:
        return []

    changed_paths: list[str] = []
    for line in result.stdout.splitlines():
        if len(line) < 4:
            continue
        path = line[3:].strip()
        if " -> " in path:
            path = path.rsplit(" -> ", maxsplit=1)[-1].strip()
        if path:
            changed_paths.append(path)
    return changed_paths


def _classify_task_type(tokens: set[str]) -> str:
    scored: list[tuple[int, str]] = []
    for task_type, keywords in _TASK_TYPE_KEYWORDS.items():
        scored.append((len(tokens & keywords), task_type))
    scored.sort(key=lambda item: (-item[0], item[1]))
    if not scored or scored[0][0] == 0:
        return "general"
    return scored[0][1]


def _classify_risk_tags(tokens: set[str]) -> list[str]:
    tags = [
        tag
        for tag, keywords in _RISK_TAG_KEYWORDS.items()
        if tokens & keywords
    ]
    return sorted(tags)


def _classify_effort(tokens: set[str], task_type: str) -> str:
    if tokens & _LOW_EFFORT_OPERATIONAL_KEYWORDS and not tokens & _NON_LOW_EFFORT_KEYWORDS:
        return "low"
    if task_type in {"memory_governance", "eval_workflow"} or tokens & _DEEP_EFFORT_KEYWORDS:
        return "deep"
    return "normal"


def _confidence(score: int) -> str:
    if score >= 14:
        return "high"
    if score >= 7:
        return "medium"
    return "low"


def _trust_level(kind: str) -> str:
    if kind in _AUTHORITATIVE_KINDS:
        return "authoritative"
    if kind.endswith("_index"):
        return "index"
    return "exploratory"


def _load_document_text(repo_root: Path, catalog_entry: dict[str, str]) -> str:
    path = repo_root / catalog_entry["path"]
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return ""


def _strip_frontmatter(text: str) -> str:
    _metadata, body = parse_frontmatter(text)
    return body


def _normalise_rule_line(line: str) -> str:
    stripped = _RULE_PREFIX_RE.sub("", line.strip())
    stripped = _MARKDOWN_LINK_RE.sub(r"\1", stripped)
    return re.sub(r"\s+", " ", stripped).strip()


def _extract_actionable_rules(
    *,
    repo_root: Path,
    candidate: dict[str, Any],
    max_rules: int,
) -> list[dict[str, str]]:
    if candidate["trust_level"] != "authoritative":
        return []

    body = _strip_frontmatter(_load_document_text(repo_root, candidate))
    rules: list[dict[str, str]] = []
    for line in body.splitlines():
        normalised = _normalise_rule_line(line)
        if not normalised or normalised.startswith("#"):
            continue
        lowered = normalised.lower()
        if not any(marker in f" {lowered}" for marker in _ACTION_MARKERS):
            continue
        if len(normalised) < 12:
            continue
        if len(normalised) > 240:
            normalised = normalised[:237].rstrip() + "..."
        rules.append(
            {
                "rule": normalised,
                "source": candidate["path"],
            }
        )
        if len(rules) >= max_rules:
            break
    return rules


def _extract_context_note(repo_root: Path, candidate: dict[str, Any]) -> dict[str, str] | None:
    if candidate["trust_level"] == "authoritative":
        return None
    body = _strip_frontmatter(_load_document_text(repo_root, candidate))
    for line in body.splitlines():
        normalised = _normalise_rule_line(line)
        if not normalised or normalised.startswith("#"):
            continue
        if len(normalised) < 20:
            continue
        if len(normalised) > 240:
            normalised = normalised[:237].rstrip() + "..."
        return {"note": normalised, "source": candidate["path"]}
    return None


def _score_document(
    *,
    entry: dict[str, str],
    repo_root: Path,
    task_type: str,
    task_tokens: set[str],
    risk_tags: list[str],
    document_stats: dict[str, Any],
) -> dict[str, Any]:
    text = _load_document_text(repo_root, entry)
    body = _strip_frontmatter(text)
    path_title_text = " ".join(
        [
            entry.get("doc_id", ""),
            entry.get("kind", ""),
            entry.get("path", ""),
            entry.get("title", ""),
            entry.get("short_description", ""),
            entry.get("routing_hint", ""),
        ]
    )
    path_title_tokens = _tokenize(path_title_text)
    body_tokens = _tokenize(body[:5000])
    path_title_matches = sorted(task_tokens & path_title_tokens)
    body_matches = sorted((task_tokens & body_tokens) - set(path_title_matches))
    matched_terms = path_title_matches + body_matches
    kind = entry["kind"]
    kind_priority = _KIND_PRIORITIES_BY_TASK_TYPE.get(task_type, {}).get(kind, 0)
    stat = document_stats.get(entry["doc_id"], {})
    effective_reuse_count = stat.get("effective_reuse_count", 0)
    total_events = stat.get("total_events", 0)
    if not isinstance(effective_reuse_count, int):
        effective_reuse_count = 0
    if not isinstance(total_events, int):
        total_events = 0

    core_doc = entry["doc_id"] in {"constraints", "decisions", "workflows"}
    applied_kind_priority = kind_priority if (path_title_matches or core_doc) else kind_priority // 2
    score = (
        min(len(path_title_matches) * 4, 16)
        + min(len(body_matches), 6)
        + applied_kind_priority
        + min(effective_reuse_count * 2, 4)
    )

    if entry["doc_id"] == "constraints" and risk_tags:
        score += 4
    if entry["doc_id"] == "decisions" and {"user_owned_docs", "memory_governance"} & set(risk_tags):
        score += 3
    if kind == "draft" and "memory_governance" in risk_tags:
        score += 2

    reasons: list[str] = []
    if path_title_matches:
        reasons.append(f"matched path/title terms: {', '.join(path_title_matches[:6])}")
    if body_matches:
        reasons.append(f"matched body terms: {', '.join(body_matches[:6])}")
    if applied_kind_priority:
        reasons.append(f"{kind} docs are prioritized for {task_type} tasks")
    if effective_reuse_count:
        reasons.append(f"prior resolved reuse count: {effective_reuse_count}")
    if entry["doc_id"] == "constraints" and risk_tags:
        reasons.append("active risk tags require checking hard constraints")
    if entry["doc_id"] == "decisions" and {"user_owned_docs", "memory_governance"} & set(risk_tags):
        reasons.append("ownership or memory-governance work may depend on durable decisions")
    if not reasons:
        reasons.append("no strong task-specific signal")

    return {
        "doc_id": entry["doc_id"],
        "path": entry["path"],
        "title": entry["title"],
        "short_description": entry.get("short_description", entry["title"]),
        "reference_path": entry.get("reference_path", entry["path"]),
        "routing_hint": entry.get("routing_hint"),
        "kind": kind,
        "score": score,
        "confidence": _confidence(score),
        "trust_level": _trust_level(kind),
        "reason": "; ".join(reasons),
        "matched_terms": matched_terms[:10],
        "prior_effective_reuse_count": effective_reuse_count,
        "prior_total_reuse_events": total_events,
    }


def _task_id_from_task(task: str | None) -> str:
    if not task or not task.strip():
        return "current-task"
    return slugify(task)[:80].strip("-") or "current-task"


def _packet_docs(candidates: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    rendered: list[dict[str, Any]] = []
    for candidate in candidates:
        rendered.append(
            {
                "doc_id": candidate["doc_id"],
                "path": candidate["path"],
                "kind": candidate["kind"],
                "title": candidate["title"],
                "short_description": candidate["short_description"],
                "reference_path": candidate["reference_path"],
                "routing_hint": candidate.get("routing_hint"),
                "reason": candidate["reason"],
                "confidence": candidate["confidence"],
                "trust_level": candidate["trust_level"],
                "score": candidate["score"],
            }
        )
    return rendered


def _reference_mode(candidate: dict[str, Any], selected_ids: set[str]) -> str:
    if candidate["doc_id"] not in selected_ids:
        return "runtime_reference"
    if candidate["trust_level"] == "authoritative":
        return "required_context"
    return "runtime_reference"


def _packet_index_cards(
    candidates: Iterable[dict[str, Any]],
    *,
    selected_ids: set[str],
) -> list[dict[str, Any]]:
    cards: list[dict[str, Any]] = []
    for candidate in candidates:
        cards.append(
            {
                "doc_id": candidate["doc_id"],
                "name": candidate["title"],
                "short_description": candidate["short_description"],
                "doc_kind": candidate["kind"],
                "trust_level": candidate["trust_level"],
                "confidence": candidate["confidence"],
                "reference_path": candidate["reference_path"],
                "routing_hint": candidate.get("routing_hint"),
                "load_mode": _reference_mode(candidate, selected_ids),
                "reason": candidate["reason"],
            }
        )
    return cards


def _success_criterion_key(item: dict[str, str]) -> tuple[str, str]:
    return (item["criterion"], item["verification"])


def _build_success_criteria(
    *,
    task_type: str,
    effort: str,
    risk_tags: list[str],
    required_docs: list[dict[str, Any]],
    work_context_items: list[dict[str, Any]],
) -> dict[str, Any]:
    items: list[dict[str, str]] = []

    if effort == "low":
        items.append(
            {
                "criterion": "The requested operation completes without pulling in unrelated work.",
                "verification": "Run the intended command or check, then inspect the resulting repo state if files or branches changed.",
                "reason": "low-effort operational task",
            }
        )
    else:
        items.append(
            {
                "criterion": "The requested outcome is complete without widening scope.",
                "verification": "Review the final diff or command result against the user request and note any deliberate omissions.",
                "reason": "baseline scope control",
            }
        )

    items.extend(
        _SUCCESS_CRITERIA_BY_TASK_TYPE.get(
            task_type,
            _SUCCESS_CRITERIA_BY_TASK_TYPE["general"],
        )
    )

    if required_docs:
        doc_ids = ", ".join(f"`{doc['doc_id']}`" for doc in required_docs[:3])
        items.append(
            {
                "criterion": "Required AI wiki context is either consulted or explicitly found not applicable.",
                "verification": f"Read or intentionally skip {doc_ids}; record reuse only for user-owned docs actually consulted or materially used.",
                "reason": "route selected must_load docs",
            }
        )

    if work_context_items:
        work_ids = ", ".join(f"`{item['work_id']}`" for item in work_context_items[:3])
        items.append(
            {
                "criterion": "Relevant work-ledger context is reflected in the implementation plan.",
                "verification": f"Check {work_ids} before acting, especially any item assigned to the current actor.",
                "reason": "route matched work_context",
            }
        )

    if "memory_governance" in risk_tags and task_type != "memory_governance":
        items.append(
            {
                "criterion": "Memory-related changes remain governed and auditable.",
                "verification": "Confirm generated memory artifacts are cited, disposable, and do not replace source Markdown.",
                "reason": "memory_governance risk tag",
            }
        )

    if "user_owned_docs" in risk_tags:
        items.append(
            {
                "criterion": "User-owned AI wiki content is not rewritten as a package side effect.",
                "verification": "Inspect the diff for `ai-wiki/**` changes outside managed `_toolkit/**` or explicitly requested draft paths.",
                "reason": "user_owned_docs risk tag",
            }
        )

    items.append(
        {
            "criterion": "Verification evidence is available before the task is closed.",
            "verification": "Run the most focused relevant tests or commands, or state why they could not be run.",
            "reason": "end-of-task verification",
        }
    )

    deduped: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for item in items:
        key = _success_criterion_key(item)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(item)
        if len(deduped) >= 5:
            break

    return {
        "source": "generated_from_task_signals",
        "trust_level": "generated_guidance",
        "items": deduped,
    }


def _select_work_context(
    *,
    work_state: dict[str, Any],
    task_tokens: set[str],
    actor_handle: str | None,
    max_items: int = 5,
) -> list[dict[str, Any]]:
    status_weights = {
        "blocked": 8,
        "active": 7,
        "processing": 7,
        "review": 6,
        "planned": 4,
        "todo": 3,
        "inbox": 3,
        "proposed": 2,
        "done": -2,
        "archived": -4,
        "dropped": -4,
    }
    candidates: list[dict[str, Any]] = []
    for item_type, collection_name in (("task", "tasks"), ("epic", "epics")):
        collection = work_state.get(collection_name)
        if not isinstance(collection, dict):
            continue
        for item in collection.values():
            if not isinstance(item, dict):
                continue
            work_id = item.get("work_id")
            title = item.get("title")
            status = item.get("status")
            if not isinstance(work_id, str) or not isinstance(title, str) or not isinstance(status, str):
                continue
            reporter_handle = (
                item.get("reporter_handle")
                if isinstance(item.get("reporter_handle"), str)
                else None
            )
            assignee_handles = (
                item.get("assignee_handles", [])
                if isinstance(item.get("assignee_handles"), list)
                else []
            )
            assignee_handles = [
                handle for handle in assignee_handles if isinstance(handle, str) and handle
            ]
            normalized_actor = actor_handle if actor_handle else None
            actor_relation = "none"
            if normalized_actor and normalized_actor in assignee_handles:
                actor_relation = "assignee"
            elif normalized_actor and reporter_handle == normalized_actor:
                actor_relation = "reporter"
            elif not assignee_handles:
                actor_relation = "unassigned"
            match_text_parts = [
                work_id,
                title,
                item.get("epic_id") if isinstance(item.get("epic_id"), str) else "",
                " ".join(link for link in item.get("links", []) if isinstance(link, str)),
            ]
            work_tokens = _tokenize(" ".join(match_text_parts))
            matches = sorted(task_tokens & work_tokens)
            directly_requested = bool(matches)
            assigned_to_actor = actor_relation == "assignee"
            unassigned_open_epic = (
                actor_relation == "unassigned"
                and item_type == "epic"
                and status in OPEN_WORK_STATUSES
            )
            if not directly_requested and status not in OPEN_WORK_STATUSES:
                continue
            if not directly_requested and not assigned_to_actor and not unassigned_open_epic:
                continue
            score = min(len(matches) * 4, 16) + status_weights.get(status, 0)
            if assigned_to_actor:
                score += 8
            elif actor_relation == "reporter" and directly_requested:
                score += 2
            elif actor_relation == "unassigned":
                score += 1
            elif directly_requested and assignee_handles:
                score -= 2
            if item_type == "epic" and status in OPEN_WORK_STATUSES:
                score += 1
            if score < 5:
                continue
            reasons: list[str] = []
            if actor_relation == "assignee":
                reasons.append("assigned to current actor")
            elif actor_relation == "reporter":
                reasons.append("reported by current actor")
            elif actor_relation == "unassigned":
                reasons.append("unassigned shared work")
            elif assignee_handles:
                reasons.append("matched requested work but is assigned to another handle")
            if matches:
                reasons.append(f"matched work terms: {', '.join(matches[:6])}")
            if status in {"active", "processing", "blocked", "review"}:
                reasons.append(f"{status} work should be visible before acting")
            elif status in {"todo", "planned", "inbox", "proposed"}:
                reasons.append(f"{status} work may define next steps")
            if not reasons:
                reasons.append("open work item")
            candidates.append(
                {
                    "work_id": work_id,
                    "item_type": item_type,
                    "title": title,
                    "status": status,
                    "epic_id": item.get("epic_id") if isinstance(item.get("epic_id"), str) else None,
                    "reporter_handle": reporter_handle,
                    "assignee_handles": assignee_handles,
                    "actor_relation": actor_relation,
                    "links": item.get("links", []) if isinstance(item.get("links"), list) else [],
                    "source_paths": item.get("source_paths", [])
                    if isinstance(item.get("source_paths"), list)
                    else [],
                    "reason": "; ".join(reasons),
                    "score": score,
                }
            )
    candidates.sort(key=lambda item: (-item["score"], item["item_type"], item["work_id"]))
    return candidates[:max_items]


def generate_route_packet(
    *,
    task: str | None = None,
    task_id: str | None = None,
    changed_paths: Iterable[str] = (),
    budget_words: int = DEFAULT_ROUTE_SAFETY_CAP_WORDS,
    max_docs: int = 6,
    start: Path | None = None,
) -> RouteResult:
    """Generate a conservative task-aware context packet."""

    paths = build_paths(start)
    if not paths.repo_wiki_dir.exists():
        raise RepoWikiNotInitializedError(
            "Repo AI wiki is not initialized. Run `aiwiki-toolkit install` first."
        )

    changed_path_list = [path for path in changed_paths if path.strip()]
    if not changed_path_list:
        changed_path_list = _read_git_changed_paths(paths.repo_root)

    task_text = task.strip() if task else ""
    signal_text = " ".join([task_text, *changed_path_list])
    raw_task_tokens = _tokenize(signal_text, filter_stopwords=False)
    raw_request_tokens = _tokenize(task_text, filter_stopwords=False)
    task_tokens = _tokenize(signal_text)
    task_type = _classify_task_type(raw_task_tokens)
    risk_tags = _classify_risk_tags(raw_task_tokens)
    effort = _classify_effort(raw_request_tokens or raw_task_tokens, task_type)
    actor_handle = resolve_user_handle(paths.repo_root)

    catalog = build_repo_catalog(paths.repo_wiki_dir)
    document_stats = build_document_stats(paths.repo_wiki_dir).get("documents", {})
    if not isinstance(document_stats, dict):
        document_stats = {}
    work_state = build_work_state(paths.repo_wiki_dir)
    work_context_items = _select_work_context(
        work_state=work_state,
        task_tokens=task_tokens,
        actor_handle=actor_handle,
    )

    scored = [
        _score_document(
            entry=entry,
            repo_root=paths.repo_root,
            task_type=task_type,
            task_tokens=task_tokens,
            risk_tags=risk_tags,
            document_stats=document_stats,
        )
        for entry in catalog.get("documents", [])
        if isinstance(entry, dict)
    ]
    scored.sort(key=lambda item: (-item["score"], item["doc_id"]))

    effective_max_docs = min(max_docs, 3) if effort == "low" else max_docs
    selected = [candidate for candidate in scored if candidate["score"] >= 7][:effective_max_docs]
    if not selected and scored:
        selected = scored[: min(3, effective_max_docs)]

    maybe = [
        candidate
        for candidate in scored
        if 3 <= candidate["score"] < 7 and candidate["doc_id"] not in {doc["doc_id"] for doc in selected}
    ][:3]
    skipped = [
        {
            "doc_id": candidate["doc_id"],
            "path": candidate["path"],
            "reason": "no strong task, path, kind, or reuse signal for this route",
        }
        for candidate in scored
        if candidate["score"] <= 2
    ][:5]

    must_follow: list[dict[str, str]] = []
    context_notes: list[dict[str, str]] = []
    for candidate in selected:
        remaining_rule_slots = max(0, 8 - len(must_follow))
        if remaining_rule_slots:
            must_follow.extend(
                _extract_actionable_rules(
                    repo_root=paths.repo_root,
                    candidate=candidate,
                    max_rules=min(3, remaining_rule_slots),
                )
            )
        note = _extract_context_note(paths.repo_root, candidate)
        if note:
            context_notes.append(note)

    selected_ids = {candidate["doc_id"] for candidate in selected}
    index_card_candidates = selected + maybe
    required_docs = [
        candidate
        for candidate in selected
        if _reference_mode(candidate, selected_ids) == "required_context"
    ]
    success_criteria = _build_success_criteria(
        task_type=task_type,
        effort=effort,
        risk_tags=risk_tags,
        required_docs=required_docs,
        work_context_items=work_context_items,
    )
    packet: dict[str, Any] = {
        "schema_version": ROUTE_SCHEMA_VERSION,
        "task_id": task_id.strip() if task_id and task_id.strip() else _task_id_from_task(task_text),
        "task": task_text,
        "route": {
            "task_type": task_type,
            "effort": effort,
            "risk_tags": risk_tags,
            "changed_paths": changed_path_list,
        },
        "actor": {
            "handle": actor_handle,
            "source": ".env.aiwiki, environment, git config, or fallback",
        },
        "context_budget": {
            "target_words": budget_words,
            "safety_cap_words": budget_words,
            "policy": "safety_cap_not_fill_target",
            "max_docs": max_docs,
            "effective_max_docs": effective_max_docs,
        },
        "routing_strategy": {
            "mode": "index_cards_with_runtime_references",
            "budget_policy": "safety_cap_not_fill_target",
            "reference_policy": (
                "Include mandatory workflow or constraint material directly; provide "
                "short index cards and reference paths for other memory so the acting "
                "agent can open full documents at runtime when needed."
            ),
        },
        "work_context": {
            "source": "ai-wiki/_toolkit/work/state.json",
            "actor_handle": actor_handle,
            "items": work_context_items,
        },
        "success_criteria": success_criteria,
        "index_cards": _packet_index_cards(index_card_candidates, selected_ids=selected_ids),
        "must_load": _packet_docs(required_docs),
        "maybe_load": _packet_docs(maybe),
        "must_follow": must_follow,
        "context_notes": context_notes[:5],
        "skip": skipped,
        "packet_status": "generated_from_sources",
        "trust_model": [
            "Markdown files under ai-wiki/ remain the source of truth.",
            "Every must_follow rule is copied or compressed from a cited user-owned source path.",
            "Exploratory drafts can appear as context_notes, not uncited rules.",
            "Success criteria are generated task guidance, not canonical memory.",
            "Regenerate packets instead of editing them as canonical memory.",
        ],
    }
    return RouteResult(packet=packet, repo_root=paths.repo_root, repo_wiki_dir=paths.repo_wiki_dir)


def render_route_packet_text(packet: dict[str, Any]) -> str:
    """Render a route packet as concise Markdown for agent consumption."""

    lines: list[str] = [
        "# AI Wiki Context Packet",
        "",
        f"Schema: `{packet['schema_version']}`",
        f"Task ID: `{packet['task_id']}`",
        f"Task Type: `{packet['route']['task_type']}`",
    ]
    effort = packet["route"].get("effort")
    if effort:
        lines.append(f"Effort: `{effort}`")
    actor = packet.get("actor") if isinstance(packet.get("actor"), dict) else {}
    if actor.get("handle"):
        lines.append(f"Actor: `{actor['handle']}`")
    risk_tags = packet["route"].get("risk_tags") or []
    if risk_tags:
        lines.append(f"Risk Tags: {', '.join(f'`{tag}`' for tag in risk_tags)}")
    changed_paths = packet["route"].get("changed_paths") or []
    if changed_paths:
        lines.append(f"Changed Paths: {', '.join(f'`{path}`' for path in changed_paths[:8])}")
    lines.extend(
        [
            f"Context Safety Cap: up to {packet['context_budget']['safety_cap_words']} words, "
            f"{packet['context_budget']['effective_max_docs']} selected docs "
            f"({packet['context_budget']['max_docs']} max); route may use less",
        ]
    )
    strategy = packet.get("routing_strategy") if isinstance(packet.get("routing_strategy"), dict) else {}
    if strategy:
        lines.extend(
            [
                "",
                "## Routing Strategy",
                f"- Mode: `{strategy.get('mode', 'unknown')}`",
                f"- Budget: `{strategy.get('budget_policy', 'unknown')}`",
                f"- References: {strategy.get('reference_policy', 'Open relevant references at runtime.')}",
            ]
        )
    work_context = packet.get("work_context") or {}
    work_items = work_context.get("items") if isinstance(work_context, dict) else []
    if work_items:
        lines.extend(["", "## Work Context"])
        for item in work_items:
            epic = f", epic `{item['epic_id']}`" if item.get("epic_id") else ""
            assignees = item.get("assignee_handles") or []
            assignee_text = (
                f", assignees {', '.join(f'`{handle}`' for handle in assignees[:3])}"
                if assignees
                else ""
            )
            actor_relation = item.get("actor_relation")
            relation_text = f", relation `{actor_relation}`" if actor_relation else ""
            sources = item.get("source_paths") or [work_context.get("source", "ai-wiki/_toolkit/work/state.json")]
            source_text = ", ".join(f"`{source}`" for source in sources[:2])
            lines.append(
                f"- `{item['work_id']}` ({item['item_type']}, {item['status']}{epic}{assignee_text}{relation_text}): "
                f"{item['title']} - {item['reason']} Source: {source_text}"
            )
    success_criteria = packet.get("success_criteria") or {}
    success_items = (
        success_criteria.get("items")
        if isinstance(success_criteria, dict)
        else []
    )
    if success_items:
        lines.extend(["", "## Success Criteria"])
        for item in success_items:
            lines.append(
                f"- {item['criterion']} Verify: {item['verification']}"
            )
    index_cards = packet.get("index_cards") or []
    if index_cards:
        lines.extend(["", "## Index Cards"])
        for card in index_cards:
            routing_hint = f" Hint: {card['routing_hint']}" if card.get("routing_hint") else ""
            lines.append(
                f"- `{card['doc_id']}` ({card['confidence']}, {card['load_mode']}): "
                f"{card['name']} - {card['short_description']}{routing_hint} "
                f"Reference: `{card['reference_path']}`"
            )
    lines.extend(["", "## Must Load"])
    must_load = packet.get("must_load") or []
    if must_load:
        for doc in must_load:
            lines.append(
                f"- `{doc['doc_id']}` ({doc['confidence']}, {doc['trust_level']}): "
                f"{doc['reason']} Source: `{doc['path']}`"
            )
    else:
        lines.append("- None selected.")

    lines.extend(["", "## Must Follow"])
    must_follow = packet.get("must_follow") or []
    if must_follow:
        for item in must_follow:
            lines.append(f"- {item['rule']} Source: `{item['source']}`")
    else:
        lines.append("- No authoritative rules extracted. Read the selected sources before acting.")

    context_notes = packet.get("context_notes") or []
    if context_notes:
        lines.extend(["", "## Context Notes"])
        for item in context_notes:
            lines.append(f"- {item['note']} Source: `{item['source']}`")

    maybe_load = packet.get("maybe_load") or []
    if maybe_load:
        lines.extend(["", "## Maybe Load"])
        for doc in maybe_load:
            lines.append(
                f"- `{doc['doc_id']}` ({doc['confidence']}): {doc['reason']} Source: `{doc['path']}`"
            )

    skipped = packet.get("skip") or []
    if skipped:
        lines.extend(["", "## Skip For This Route"])
        for item in skipped:
            lines.append(f"- `{item['doc_id']}`: {item['reason']}")

    lines.extend(
        [
            "",
            "## Trust Model",
            "- Markdown files under `ai-wiki/` remain the source of truth.",
            "- Treat uncited claims as non-authoritative.",
            "- Treat success criteria as generated task guidance, not canonical memory.",
            "- Record reuse only for user-owned docs you actually consult or materially use.",
        ]
    )
    return "\n".join(lines) + "\n"


def render_route_packet_json(packet: dict[str, Any]) -> str:
    """Render a route packet as stable JSON."""

    return json.dumps(packet, indent=2, sort_keys=True) + "\n"
