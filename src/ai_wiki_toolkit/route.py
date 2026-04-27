"""Task-aware AI wiki context routing."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import re
import subprocess
from typing import Any, Iterable

from ai_wiki_toolkit.frontmatter import parse_frontmatter
from ai_wiki_toolkit.paths import build_paths, slugify
from ai_wiki_toolkit.reuse_events import RepoWikiNotInitializedError
from ai_wiki_toolkit.wiki_schema import (
    build_document_stats,
    build_repo_catalog,
)

ROUTE_SCHEMA_VERSION = "route-v1"

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
    "task_evaluation": {
        "benchmark",
        "eval",
        "replay",
        "rubric",
        "score",
    },
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
                "reason": candidate["reason"],
                "confidence": candidate["confidence"],
                "trust_level": candidate["trust_level"],
                "score": candidate["score"],
            }
        )
    return rendered


def generate_route_packet(
    *,
    task: str | None = None,
    task_id: str | None = None,
    changed_paths: Iterable[str] = (),
    budget_words: int = 900,
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
    task_tokens = _tokenize(signal_text)
    task_type = _classify_task_type(raw_task_tokens)
    risk_tags = _classify_risk_tags(raw_task_tokens)

    catalog = build_repo_catalog(paths.repo_wiki_dir)
    document_stats = build_document_stats(paths.repo_wiki_dir).get("documents", {})
    if not isinstance(document_stats, dict):
        document_stats = {}

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

    selected = [candidate for candidate in scored if candidate["score"] >= 7][:max_docs]
    if not selected and scored:
        selected = scored[: min(3, max_docs)]

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

    packet: dict[str, Any] = {
        "schema_version": ROUTE_SCHEMA_VERSION,
        "task_id": task_id.strip() if task_id and task_id.strip() else _task_id_from_task(task_text),
        "task": task_text,
        "route": {
            "task_type": task_type,
            "risk_tags": risk_tags,
            "changed_paths": changed_path_list,
        },
        "context_budget": {
            "target_words": budget_words,
            "max_docs": max_docs,
        },
        "must_load": _packet_docs(selected),
        "maybe_load": _packet_docs(maybe),
        "must_follow": must_follow,
        "context_notes": context_notes[:5],
        "skip": skipped,
        "packet_status": "generated_from_sources",
        "trust_model": [
            "Markdown files under ai-wiki/ remain the source of truth.",
            "Every must_follow rule is copied or compressed from a cited user-owned source path.",
            "Exploratory drafts can appear as context_notes, not uncited rules.",
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
    risk_tags = packet["route"].get("risk_tags") or []
    if risk_tags:
        lines.append(f"Risk Tags: {', '.join(f'`{tag}`' for tag in risk_tags)}")
    changed_paths = packet["route"].get("changed_paths") or []
    if changed_paths:
        lines.append(f"Changed Paths: {', '.join(f'`{path}`' for path in changed_paths[:8])}")
    lines.extend(
        [
            f"Context Budget: {packet['context_budget']['target_words']} words, "
            f"{packet['context_budget']['max_docs']} docs max",
            "",
            "## Must Load",
        ]
    )
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
            "- Record reuse only for user-owned docs you actually consult or materially use.",
        ]
    )
    return "\n".join(lines) + "\n"


def render_route_packet_json(packet: dict[str, Any]) -> str:
    """Render a route packet as stable JSON."""

    return json.dumps(packet, indent=2, sort_keys=True) + "\n"
