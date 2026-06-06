"""Task-aware AI wiki context routing."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import subprocess
from typing import Any, Iterable

from ai_wiki_toolkit.diagnostics import build_memory_diagnostics_report
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
DEFAULT_ROUTE_RERANK_TOP = 20
ROUTE_QUALITY_LOOKBACK = "30d"
ROUTE_QUALITY_SCAN_MAX_ITEMS = 500

_TOKEN_RE = re.compile(r"[a-z0-9][a-z0-9_-]{1,}", re.IGNORECASE)
_CJK_RE = re.compile(r"[\u3400-\u9fff]")
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
    "as",
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
    "not",
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
        "baseline",
        "benchmark",
        "eval",
        "evaluate",
        "evaluation",
        "experiment",
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
        "noise",
        "packet",
        "precision",
        "promote",
        "promotion",
        "recall",
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

_EVAL_WORKFLOW_STRONG_KEYWORDS = {
    "benchmark",
    "eval",
    "evaluation",
    "families",
    "family",
    "impact",
    "project-a",
    "rubric",
    "rubrics",
    "score",
    "scoring",
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

_DOMAIN_TAG_KEYWORDS: dict[str, set[str]] = {
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
        "evaluate",
        "evaluation",
        "replay",
        "rubric",
        "score",
    },
}

_GUARDRAIL_TAG_KEYWORDS: dict[str, set[str]] = {
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
}

_ROUTE_CONCERN_TAG_KEYWORDS: dict[str, set[str]] = {
    **_DOMAIN_TAG_KEYWORDS,
    **_GUARDRAIL_TAG_KEYWORDS,
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

_WEAK_ROUTE_MATCH_TERMS = {
    "analysis",
    "code",
    "current",
    "first",
    "local",
    "project",
    "report",
    "tool",
    "tools",
    "workflow",
}

_GENERIC_TASK_SIGNAL_TERMS = {
    "change",
    "changes",
    "check",
    "continue",
    "do",
    "fix",
    "look",
    "next",
    "review",
    "run",
    "see",
    "status",
    "test",
    "tests",
    "thing",
    "things",
    "update",
    "work",
}

_NEGATIVE_APPLIES_WHEN_RE = re.compile(
    r"\b(?:not\s+for|not\s+when|excluding|except\s+for|except)\b",
    re.IGNORECASE,
)

_ROUTE_INTENT_CATEGORIES: dict[str, set[str]] = {
    "implementation": {
        "add",
        "build",
        "change",
        "code",
        "fix",
        "implement",
        "implementation",
        "patch",
        "refactor",
        "update",
        "wire",
    },
    "execution": {
        "benchmark",
        "execute",
        "replay",
        "rerun",
        "run",
        "smoke",
        "test",
    },
    "design": {
        "assess",
        "compare",
        "decide",
        "design",
        "discuss",
        "evaluate",
        "plan",
        "planning",
        "proposal",
        "propose",
        "research",
        "scope",
    },
    "capture": {
        "artifact",
        "artifacts",
        "capture",
        "diff",
        "result",
        "results",
        "save",
        "untracked",
    },
    "reporting": {
        "dashboard",
        "metric",
        "metrics",
        "public",
        "publish",
        "report",
        "summary",
    },
    "metadata": {
        "applies",
        "applies_when",
        "hint",
        "label",
        "metadata",
        "routing_hint",
        "tag",
    },
    "provenance": {
        "codex",
        "provenance",
        "recover",
        "rollout",
        "session",
        "source",
        "timing",
        "transcript",
    },
    "runner": {
        "auto-runner",
        "execution",
        "manifest",
        "orchestrator",
        "runner",
        "workspace",
        "workspaces",
    },
    "prompting": {
        "family",
        "families",
        "prompt",
        "prompts",
        "rubric",
        "rubrics",
        "task-family",
    },
}

_ROUTE_INTENT_ALIGNMENT_TERMS = set().union(*_ROUTE_INTENT_CATEGORIES.values())

_ROUTE_MODE_PLAN_PHRASES = (
    "think hard",
    "plan first",
    "先计划",
    "先要计划",
    "先不要代码",
    "不要代码",
    "不要直接实现",
    "先不要写代码",
    "只计划",
)

_ROUTE_MODE_QUESTION_PHRASES = (
    "what is",
    "what are",
    "why does",
    "why is",
    "how does",
    "how should",
    "是否",
    "是什么",
    "为什么",
    "怎么理解",
)

_WORKFLOW_SUPPORT_REQUEST_PHRASES = (
    "add ",
    "change ",
    "debug ",
    "fix ",
    "implement ",
    "refactor ",
    "update ",
    "修改",
    "改成",
    "加入",
    "加上",
    "实现",
    "提出",
    "修复",
)

_ROUTE_WORKFLOW_CONTRACTS: tuple[dict[str, Any], ...] = (
    {
        "id": "weekly-report-diagnostics",
        "name": "Weekly Report Diagnostics",
        "trigger_phrases": ("weekly report", "weekly html report", "weekly-report"),
        "trigger_tokens": {"weekly", "report", "diagnosis", "diagnostic", "coverage", "promotion"},
        "required_steps": [
            "load local metrics",
            "compute coverage, promotion, noisy, and not_helpful signals",
            "render the weekly report artifact",
            "record the task-level reuse check",
        ],
        "supporting_docs_allowed_when": ["workflow_change", "bug_fix", "exception_case"],
        "bucket_id": "workflow_contract",
    },
    {
        "id": "memory-promotion",
        "name": "Memory Promotion",
        "trigger_phrases": ("promote draft", "promotion candidate", "draft reuse"),
        "trigger_tokens": {"promote", "promotion", "candidate", "draft", "reuse"},
        "required_steps": [
            "load promotion thresholds",
            "inspect reuse evidence for the candidate memory",
            "preserve user-owned shared docs unless promotion is explicitly confirmed",
            "record the reuse/write-back outcome",
        ],
        "supporting_docs_allowed_when": ["workflow_change", "bug_fix", "exception_case"],
        "bucket_id": "memory_metrics",
    },
    {
        "id": "reuse-metrics",
        "name": "Reuse Metrics",
        "trigger_phrases": ("reuse metrics", "reuse events", "task checks", "record-reuse"),
        "trigger_tokens": {"reuse", "metrics", "task-check", "task-checks", "telemetry"},
        "required_steps": [
            "read per-handle reuse events and task checks",
            "exclude managed _toolkit docs from user-owned reuse metrics",
            "aggregate by task and document",
            "record the task-level reuse check",
        ],
        "supporting_docs_allowed_when": ["workflow_change", "bug_fix", "exception_case"],
        "bucket_id": "memory_metrics",
    },
    {
        "id": "diagnostics-provenance",
        "name": "Diagnostics Provenance",
        "trigger_phrases": ("diagnostics provenance", "telemetry provenance", "source incident"),
        "trigger_tokens": {"diagnosis", "diagnostic", "provenance", "source", "incident", "timing"},
        "required_steps": [
            "identify the source incident or diagnostic event",
            "preserve provenance fields and timing source",
            "separate generated diagnostics from source Markdown",
            "record whether the diagnostic evidence changed the task outcome",
        ],
        "supporting_docs_allowed_when": ["workflow_change", "bug_fix", "exception_case"],
        "bucket_id": "source_incident_timing",
    },
    {
        "id": "release-flow",
        "name": "Release Flow",
        "trigger_phrases": ("release to npm", "release ai-wiki-toolkit", "push current changes"),
        "trigger_tokens": {"release", "publish", "npm", "version", "merge", "push"},
        "required_steps": [
            "verify the worktree and target branch",
            "run the focused release or smoke checks",
            "publish through the configured distribution path",
            "verify the installed package or release artifact",
        ],
        "supporting_docs_allowed_when": ["workflow_change", "bug_fix", "exception_case"],
        "bucket_id": "release_distribution",
    },
)

_ROUTE_BUCKET_DEFINITIONS: tuple[dict[str, Any], ...] = (
    {
        "id": "release_distribution",
        "keywords": {"asset", "binary", "distribution", "npm", "package", "publish", "release", "version"},
    },
    {
        "id": "prompt_design",
        "keywords": {"design", "families", "family", "prompt", "prompts", "task-family"},
    },
    {
        "id": "manifest_or_runner",
        "keywords": {"execution", "manifest", "orchestrator", "run", "runner", "workspace", "workspaces"},
    },
    {
        "id": "artifact_capture",
        "keywords": {"artifact", "artifacts", "capture", "diff", "result", "results", "save", "untracked"},
    },
    {
        "id": "rubric_scoring",
        "keywords": {"rubric", "rubrics", "score", "scoring"},
    },
    {
        "id": "report_quality",
        "keywords": {"change", "churn", "metrics", "neutral", "profile", "quality", "report"},
    },
    {
        "id": "route_usefulness",
        "keywords": {"misses", "noise", "noisy", "precision", "recall", "route", "routing", "selected", "usefulness"},
    },
    {
        "id": "source_incident_timing",
        "keywords": {"incident", "provenance", "session", "source", "timing", "transcript"},
    },
    {
        "id": "public_metrics",
        "keywords": {"dashboard", "metric", "metrics", "proof", "public", "report"},
    },
    {
        "id": "memory_consolidation",
        "keywords": {"consolidate", "consolidation", "draft", "memory", "promote", "promotion"},
    },
)

_ROUTE_BUCKET_ALIASES: dict[str, set[str]] = {
    "release_distribution": {"release_distribution"},
    "prompt_design": {"prompt_design"},
    "manifest_or_runner": {"manifest_or_runner"},
    "artifact_capture": {"artifact_capture"},
    "rubric_scoring": {"rubric_scoring"},
    "report_quality": {"report_quality", "public_metrics"},
    "route_usefulness": {"route_usefulness"},
    "source_incident_timing": {"source_incident_timing"},
    "public_metrics": {"public_metrics", "report_quality"},
    "memory_consolidation": {"memory_consolidation", "memory_metrics"},
    "memory_metrics": {"memory_metrics", "public_metrics", "route_usefulness"},
    "workflow_contract": {"workflow_contract"},
}

_CHINESE_INTENT_SYNONYMS: tuple[tuple[tuple[str, ...], set[str]], ...] = (
    (("实现", "改", "修改", "补", "加", "修", "修复", "写进", "接进"), {"implement", "update", "fix"}),
    (("跑", "重跑", "执行", "测试", "验证"), {"run", "rerun", "test"}),
    (("设计", "计划", "方案", "判断", "分析", "评估", "讨论", "说说", "觉得"), {"design", "evaluate", "discuss"}),
    (("报告", "发布", "公开", "dashboard", "仪表盘", "指标"), {"report", "publish", "metric"}),
    (("标签", "元数据", "applies_when", "routing_hint"), {"label", "metadata", "applies_when", "routing_hint"}),
    (("session", "会话", "回放", "来源", "溯源", "时间"), {"session", "replay", "source", "provenance", "timing"}),
)

_CHINESE_TASK_SYNONYMS: tuple[tuple[tuple[str, ...], set[str]], ...] = (
    (
        ("自评估", "评测", "评分", "基准", "回放", "复盘", "跑分", "打分", "任务集", "对照实验", "基线"),
        {"eval", "evaluation", "score", "scoring", "benchmark", "replay", "baseline", "experiment"},
    ),
    (
        ("发布", "发版", "版本", "打包", "分发", "安装包", "发布包", "产物", "二进制"),
        {"release", "version", "package", "publish", "distribution", "asset", "binary"},
    ),
    (("失败", "报错", "错误", "修复", "回归", "坏了"), {"bug", "error", "fail", "fix", "regression"}),
    (
        ("测试", "验证", "检查", "诊断", "烟测"),
        {"test", "tests", "verify", "diagnosis", "diagnostic", "smoke"},
    ),
    (
        ("记忆", "路由", "复用", "写回", "上下文", "召回", "命中", "漏选", "误选", "噪音", "准确率", "精度"),
        {"memory", "route", "routing", "reuse", "write-back", "context", "recall", "precision", "noise"},
    ),
    (
        ("权限", "边界", "用户文档", "用户自己的", "公司代码", "隐私", "不能覆盖"),
        {"constraints", "user-owned", "ownership", "boundary"},
    ),
    (("工作流", "流水线", "持续集成"), {"workflow", "workflows", "ci", "actions"}),
)

_ENGLISH_TASK_SYNONYMS: dict[str, set[str]] = {
    "evaluate": {"eval", "evaluation"},
    "evaluating": {"eval", "evaluation"},
    "scoring": {"score"},
    "benchmarking": {"benchmark"},
    "diagnostics": {"diagnosis", "diagnostic"},
    "routing": {"route"},
    "precision": {"route"},
    "noise": {"route"},
    "recall": {"route"},
}

_ROUTE_CONCERN_SIGNAL_KEYWORDS: dict[str, set[str]] = {
    "release_distribution": {
        "asset",
        "binary",
        "brew",
        "distribution",
        "glibc",
        "homebrew",
        "musl",
        "npm",
        "package",
        "publish",
        "release",
        "version",
    },
    "ci_workflow": {
        "actions",
        "ci",
        "github",
        "smoke",
        "workflow",
        "workflows",
    },
    "task_evaluation": {
        "benchmark",
        "eval",
        "evaluate",
        "evaluation",
        "impact",
        "metric",
        "replay",
        "rubric",
        "score",
        "scoring",
    },
    "memory_governance": {
        "context",
        "draft",
        "memory",
        "noise",
        "packet",
        "precision",
        "recall",
        "reuse",
        "route",
        "routing",
        "write-back",
    },
    "user_owned_docs": {
        "ownership",
        "user-owned",
        "user",
        "managed",
        "scaffold",
        "toolkit",
    },
    "managed_prompt_block": {
        "agent",
        "agents",
        "claude",
        "codex",
        "managed",
        "prompt",
    },
    "workflow_state": {
        "active",
        "blocked",
        "done",
        "epic",
        "ledger",
        "status",
        "todo",
        "work",
    },
}

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


def _task_synonym_tokens(value: str, *, filter_stopwords: bool = True) -> set[str]:
    tokens: set[str] = set()
    lexical_tokens = _tokenize(value, filter_stopwords=False)
    for token in lexical_tokens:
        tokens.update(_ENGLISH_TASK_SYNONYMS.get(token, set()))
    for needles, expansions in _CHINESE_TASK_SYNONYMS:
        if any(needle in value for needle in needles):
            tokens.update(expansions)
    if filter_stopwords:
        return {token for token in tokens if token not in _STOPWORDS}
    return tokens


def _task_language_signals(value: str) -> dict[str, Any]:
    """Return explainable mixed-language routing expansions for diagnostics."""

    lexical_tokens = _tokenize(value, filter_stopwords=False)
    english_synonyms: list[dict[str, Any]] = []
    expanded_tokens: set[str] = set()
    for token in sorted(lexical_tokens):
        expansions = sorted(_ENGLISH_TASK_SYNONYMS.get(token, set()) - _STOPWORDS)
        if not expansions:
            continue
        english_synonyms.append(
            {
                "source_token": token,
                "expanded_tokens": expansions,
            }
        )
        expanded_tokens.update(expansions)

    chinese_synonyms: list[dict[str, Any]] = []
    for needles, expansions in _CHINESE_TASK_SYNONYMS:
        matched_terms = [needle for needle in needles if needle in value]
        if not matched_terms:
            continue
        filtered_expansions = sorted(expansions - _STOPWORDS)
        chinese_synonyms.append(
            {
                "matched_terms": matched_terms,
                "expanded_tokens": filtered_expansions,
            }
        )
        expanded_tokens.update(filtered_expansions)

    return {
        "contains_cjk": bool(_CJK_RE.search(value)),
        "english_synonyms": english_synonyms,
        "chinese_synonyms": chinese_synonyms,
        "expanded_tokens": sorted(expanded_tokens - _STOPWORDS),
    }


def _task_tokens(value: str, *, filter_stopwords: bool = True) -> set[str]:
    return _tokenize(value, filter_stopwords=filter_stopwords) | _task_synonym_tokens(
        value,
        filter_stopwords=filter_stopwords,
    )


def _route_intent_signals(
    value: str,
    *,
    raw_task_tokens: set[str],
    task_tokens: set[str],
) -> dict[str, Any]:
    """Return action/stage signals used to avoid broad topic-only routing."""

    lexical_tokens = raw_task_tokens | task_tokens
    chinese_expansions: set[str] = set()
    chinese_matches: list[dict[str, Any]] = []
    for needles, expansions in _CHINESE_INTENT_SYNONYMS:
        matched_terms = [needle for needle in needles if needle in value]
        if not matched_terms:
            continue
        chinese_expansions.update(expansions)
        chinese_matches.append(
            {
                "matched_terms": matched_terms,
                "expanded_tokens": sorted(expansions),
            }
        )

    alignment_tokens = (lexical_tokens | chinese_expansions) & _ROUTE_INTENT_ALIGNMENT_TERMS
    categories: list[dict[str, Any]] = []
    for category, keywords in _ROUTE_INTENT_CATEGORIES.items():
        matches = sorted(alignment_tokens & keywords)
        if matches:
            categories.append({"name": category, "matches": matches})

    has_implementation_signal = bool(
        alignment_tokens & (_ROUTE_INTENT_CATEGORIES["implementation"] | _ROUTE_INTENT_CATEGORIES["execution"])
    )
    has_discussion_signal = bool(alignment_tokens & _ROUTE_INTENT_CATEGORIES["design"])
    if has_implementation_signal:
        mode = "action"
    elif has_discussion_signal:
        mode = "analysis"
    else:
        mode = "unspecified"

    return {
        "mode": mode,
        "alignment_tokens": sorted(alignment_tokens),
        "categories": categories,
        "chinese_intent_synonyms": chinese_matches,
    }


def _contains_phrase(value: str, phrases: Iterable[str]) -> list[str]:
    lowered = value.lower()
    return [phrase for phrase in phrases if phrase.lower() in lowered]


def _has_workflow_support_request(value: str, tokens: set[str]) -> bool:
    return bool(
        tokens
        & {
            "add",
            "build",
            "change",
            "debug",
            "design",
            "fix",
            "implement",
            "implementation",
            "refactor",
            "update",
        }
    ) or bool(_contains_phrase(value, _WORKFLOW_SUPPORT_REQUEST_PHRASES))


def _detect_workflow_contract(
    *,
    value: str,
    task_tokens: set[str],
) -> dict[str, Any] | None:
    candidates: list[tuple[int, dict[str, Any], list[str], list[str]]] = []
    for contract in _ROUTE_WORKFLOW_CONTRACTS:
        phrase_matches = _contains_phrase(value, contract.get("trigger_phrases", ()))
        token_matches = sorted(task_tokens & set(contract.get("trigger_tokens", set())))
        if not phrase_matches and len(token_matches) < 2:
            continue
        score = len(phrase_matches) * 4 + len(token_matches)
        candidates.append((score, contract, phrase_matches, token_matches))
    if not candidates:
        return None
    candidates.sort(key=lambda item: (-item[0], str(item[1]["id"])))
    score, contract, phrase_matches, token_matches = candidates[0]
    supporting_docs_allowed = _has_workflow_support_request(value, task_tokens)
    return {
        "id": contract["id"],
        "name": contract["name"],
        "confidence": "high" if phrase_matches or score >= 5 else "medium",
        "matched_phrases": phrase_matches,
        "matched_terms": token_matches[:8],
        "required_steps": list(contract["required_steps"]),
        "supporting_docs_allowed": supporting_docs_allowed,
        "supporting_docs_allowed_when": list(contract["supporting_docs_allowed_when"]),
        "bucket_id": contract.get("bucket_id", "workflow_contract"),
    }


def _classify_route_mode(
    *,
    value: str,
    raw_task_tokens: set[str],
    task_tokens: set[str],
    route_intent: dict[str, Any],
    workflow_contract: dict[str, Any] | None,
) -> dict[str, Any]:
    evidence: list[str] = []
    disallowed_actions: list[str] = []
    plan_phrases = _contains_phrase(value, _ROUTE_MODE_PLAN_PHRASES)
    question_phrases = _contains_phrase(value, _ROUTE_MODE_QUESTION_PHRASES)
    if plan_phrases:
        evidence.extend(plan_phrases[:4])
    alignment_tokens = set(route_intent.get("alignment_tokens") or [])
    implementation_terms = sorted(
        (raw_task_tokens | alignment_tokens) & _ROUTE_INTENT_CATEGORIES["implementation"]
    )
    execution_terms = sorted((raw_task_tokens | alignment_tokens) & _ROUTE_INTENT_CATEGORIES["execution"])
    design_terms = sorted((raw_task_tokens | alignment_tokens) & _ROUTE_INTENT_CATEGORIES["design"])
    review_terms = sorted(raw_task_tokens & {"review", "feedback", "comment", "pr", "ci"})
    report_terms = sorted(raw_task_tokens & _ROUTE_INTENT_CATEGORIES["reporting"])

    if plan_phrases:
        name = "plan"
        disallowed_actions.append("edit_files")
    elif workflow_contract and not _has_workflow_support_request(value, raw_task_tokens | alignment_tokens):
        name = "fixed_workflow"
        evidence.append(f"workflow:{workflow_contract['id']}")
    elif implementation_terms:
        name = "code"
        evidence.extend(implementation_terms[:4])
    elif review_terms:
        name = "review"
        evidence.extend(review_terms[:4])
    elif report_terms and not implementation_terms:
        name = "report"
        evidence.extend(report_terms[:4])
    elif question_phrases and not execution_terms:
        name = "question_only"
        evidence.extend(question_phrases[:4])
        disallowed_actions.append("edit_files")
    elif design_terms:
        name = "plan"
        evidence.extend(design_terms[:4])
    else:
        name = "question_only" if not raw_task_tokens else "plan"

    if name in {"plan", "question_only"} and "edit_files" not in disallowed_actions:
        disallowed_actions.append("edit_files")
    if name == "question_only":
        disallowed_actions.extend(action for action in ("run_commands",) if action not in disallowed_actions)

    eligible_doc_slots = {
        "code": [
            "artifact_capture",
            "manifest_or_runner",
            "release_distribution",
            "rubric_scoring",
            "workflow_contract",
        ],
        "fixed_workflow": ["workflow_contract"],
        "plan": [
            "memory_consolidation",
            "prompt_design",
            "public_metrics",
            "report_quality",
            "route_usefulness",
            "source_incident_timing",
            "workflow_contract",
        ],
        "question_only": ["public_metrics", "route_usefulness", "workflow_contract"],
        "review": ["release_distribution", "route_usefulness", "workflow_contract"],
        "report": ["public_metrics", "report_quality", "source_incident_timing", "workflow_contract"],
    }.get(name, [])

    return {
        "name": name,
        "confidence": "high" if evidence or plan_phrases or workflow_contract else "medium",
        "evidence": evidence[:8],
        "disallowed_actions": sorted(set(disallowed_actions)),
        "eligible_doc_slots": eligible_doc_slots,
    }


def _classify_intent_buckets(
    *,
    task_tokens: set[str],
    task_type: str,
    domain_tags: list[str],
    route_mode: dict[str, Any],
    workflow_contract: dict[str, Any] | None,
) -> list[dict[str, Any]]:
    buckets: list[dict[str, Any]] = []
    if workflow_contract:
        buckets.append(
            {
                "id": str(workflow_contract.get("bucket_id") or "workflow_contract"),
                "role": "workflow_contract",
                "quota": 1,
                "matched_terms": workflow_contract.get("matched_terms", []),
                "matched_phrases": workflow_contract.get("matched_phrases", []),
            }
        )

    for definition in _ROUTE_BUCKET_DEFINITIONS:
        bucket_id = str(definition["id"])
        matched_terms = sorted(task_tokens & set(definition["keywords"]))
        if not matched_terms:
            continue
        if bucket_id == "release_distribution" and "release_distribution" not in domain_tags:
            continue
        if bucket_id in {"prompt_design", "manifest_or_runner", "artifact_capture", "rubric_scoring", "report_quality"}:
            if task_type != "eval_workflow" and "task_evaluation" not in domain_tags:
                continue
        buckets.append(
            {
                "id": bucket_id,
                "role": "primary" if not buckets else "secondary",
                "quota": 1,
                "matched_terms": matched_terms[:8],
                "matched_phrases": [],
            }
        )

    if route_mode.get("name") in {"plan", "question_only"} and not any(
        bucket["id"] == "public_metrics" for bucket in buckets
    ):
        buckets.append(
            {
                "id": "public_metrics",
                "role": "mode_default",
                "quota": 1,
                "matched_terms": [],
                "matched_phrases": [],
            }
        )

    deduped: list[dict[str, Any]] = []
    seen: set[str] = set()
    for bucket in buckets:
        bucket_id = str(bucket["id"])
        if bucket_id in seen:
            continue
        seen.add(bucket_id)
        deduped.append(bucket)
        if len(deduped) >= 4:
            break
    return deduped


def _classify_doc_slots(*, text: str, kind: str, doc_id: str) -> list[str]:
    tokens = _tokenize(text)
    slots: list[str] = []
    for definition in _ROUTE_BUCKET_DEFINITIONS:
        if tokens & set(definition["keywords"]):
            slots.append(str(definition["id"]))
    if kind == "workflows" or doc_id == "workflows":
        slots.append("workflow_contract")
    if "reuse" in tokens and "metrics" in tokens:
        slots.append("memory_metrics")
    if "route" in tokens and {"precision", "noise", "recall", "usefulness"} & tokens:
        slots.append("route_usefulness")
    return sorted(set(slots))


def _bucket_matches_candidate(bucket_id: str, candidate: dict[str, Any]) -> bool:
    candidate_slots = set(candidate.get("doc_slots") or [])
    aliases = _ROUTE_BUCKET_ALIASES.get(bucket_id, {bucket_id})
    return bool(candidate_slots & aliases)


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


def _parse_catalog_timestamp(value: object) -> datetime | None:
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        parsed = datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _filter_catalog_for_cutoff(
    documents: list[dict[str, Any]],
    *,
    catalog_cutoff: datetime | None,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    stats: dict[str, Any] = {
        "cutoff_at": catalog_cutoff.astimezone(timezone.utc).isoformat()
        if catalog_cutoff is not None
        else None,
        "input_doc_count": len(documents),
        "filtered_future_doc_count": 0,
        "unknown_created_at_doc_count": sum(
            1 for entry in documents if _parse_catalog_timestamp(entry.get("created_at")) is None
        ),
    }
    if catalog_cutoff is None:
        stats["output_doc_count"] = len(documents)
        return documents, stats

    cutoff = catalog_cutoff.astimezone(timezone.utc)
    filtered: list[dict[str, Any]] = []
    future_doc_ids: list[str] = []
    unknown_doc_ids: list[str] = []
    for entry in documents:
        created_at = _parse_catalog_timestamp(entry.get("created_at"))
        if created_at is None:
            unknown_doc_ids.append(str(entry.get("doc_id") or ""))
            filtered.append(entry)
            continue
        if created_at <= cutoff:
            filtered.append(entry)
            continue
        doc_id = entry.get("doc_id")
        if isinstance(doc_id, str) and doc_id:
            future_doc_ids.append(doc_id)

    stats.update(
        {
            "output_doc_count": len(filtered),
            "filtered_future_doc_count": len(future_doc_ids),
            "unknown_created_at_doc_count": len([doc_id for doc_id in unknown_doc_ids if doc_id]),
            "filtered_future_doc_ids": future_doc_ids[:20],
        }
    )
    return filtered, stats


def _should_use_changed_path_signals(
    *,
    explicit_changed_paths: bool,
    task_tokens: set[str],
    raw_task_tokens: set[str],
) -> bool:
    if explicit_changed_paths:
        return True
    if not raw_task_tokens:
        return True
    specific_tokens = task_tokens - _GENERIC_TASK_SIGNAL_TERMS
    return not specific_tokens


def _classify_task_type(tokens: set[str]) -> str:
    eval_matches = tokens & _EVAL_WORKFLOW_STRONG_KEYWORDS
    if len(eval_matches) >= 2 and {"benchmark", "eval", "evaluation", "impact", "rubric", "rubrics"} & eval_matches:
        return "eval_workflow"
    scored: list[tuple[int, str]] = []
    for task_type, keywords in _TASK_TYPE_KEYWORDS.items():
        scored.append((len(tokens & keywords), task_type))
    scored.sort(key=lambda item: (-item[0], item[1]))
    if not scored or scored[0][0] == 0:
        return "general"
    return scored[0][1]


def _classify_domain_tags(tokens: set[str]) -> list[str]:
    tags = [
        tag
        for tag, keywords in _DOMAIN_TAG_KEYWORDS.items()
        if tokens & keywords
    ]
    return sorted(tags)


def _classify_guardrail_tags(tokens: set[str]) -> list[str]:
    tags = [
        tag
        for tag, keywords in _GUARDRAIL_TAG_KEYWORDS.items()
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


def _build_route_quality_doc_stats(
    repo_wiki_dir: Path,
    *,
    handle: str,
) -> dict[str, dict[str, int]]:
    try:
        report = build_memory_diagnostics_report(
            repo_wiki_dir,
            handle=handle,
            since=ROUTE_QUALITY_LOOKBACK,
            focus="route",
            max_items=ROUTE_QUALITY_SCAN_MAX_ITEMS,
        )
    except (OSError, ValueError, json.JSONDecodeError):
        return {}
    route = report.get("route_diagnostics")
    if not isinstance(route, dict):
        return {}
    items = route.get("items")
    if not isinstance(items, list):
        return {}

    stats: dict[str, dict[str, int]] = {}

    def add(doc_id: object, key: str) -> None:
        if not isinstance(doc_id, str) or not doc_id:
            return
        bucket = stats.setdefault(
            doc_id,
            {
                "missed_useful_count": 0,
                "selected_count": 0,
                "selected_useful_count": 0,
                "selected_but_unused_count": 0,
                "selected_not_helpful_count": 0,
            },
        )
        bucket[key] += 1

    for item in items:
        if not isinstance(item, dict):
            continue
        selected_doc_ids = {
            doc_id for doc_id in item.get("selected_doc_ids", []) if isinstance(doc_id, str) and doc_id
        }
        if not selected_doc_ids:
            selected_doc_ids = {
                doc_id
                for key in (
                    "useful_selected_doc_ids",
                    "selected_but_unused_doc_ids",
                    "selected_not_helpful_doc_ids",
                )
                for doc_id in item.get(key, [])
                if isinstance(doc_id, str) and doc_id
            }
        for doc_id in selected_doc_ids:
            add(doc_id, "selected_count")
        for doc_id in item.get("useful_selected_doc_ids", []):
            add(doc_id, "selected_useful_count")
        for doc_id in item.get("missed_useful_doc_ids", []):
            add(doc_id, "missed_useful_count")
        for doc_id in item.get("selected_but_unused_doc_ids", []):
            add(doc_id, "selected_but_unused_count")
        for doc_id in item.get("selected_not_helpful_doc_ids", []):
            add(doc_id, "selected_not_helpful_count")
    return stats


def _strong_path_signal(path_title_matches: list[str]) -> bool:
    strong_matches = [
        term for term in path_title_matches if term not in _WEAK_ROUTE_MATCH_TERMS
    ]
    return len(strong_matches) >= 2


def _route_quality_adjustment(
    *,
    doc_id: str,
    core_doc: bool,
    path_title_matches: list[str],
    body_matches: list[str],
    route_quality_doc_stats: dict[str, dict[str, int]],
) -> tuple[int, list[str], dict[str, Any]]:
    stats = route_quality_doc_stats.get(doc_id, {})
    selected_count = int(stats.get("selected_count", 0) or 0)
    selected_useful = int(stats.get("selected_useful_count", 0) or 0)
    selected_but_unused = int(stats.get("selected_but_unused_count", 0) or 0)
    selected_not_helpful = int(stats.get("selected_not_helpful_count", 0) or 0)
    missed_useful = int(stats.get("missed_useful_count", 0) or 0)
    adjustment = 0
    missed_useful_bonus = 0
    not_helpful_penalty = 0
    unused_penalty = 0
    unused_penalty_capped_by_support = False
    reasons: list[str] = []

    has_strong_path_signal = _strong_path_signal(path_title_matches)
    if missed_useful and (path_title_matches or len(body_matches) >= 2):
        bonus = min(missed_useful, 4)
        missed_useful_bonus = bonus
        adjustment += missed_useful_bonus
        reasons.append(f"route missed-useful bonus: +{bonus} from {missed_useful}")

    selected_precision = selected_useful / selected_count if selected_count else None
    if selected_not_helpful:
        penalty = min(selected_not_helpful * 2, 6)
        not_helpful_penalty = penalty
        adjustment -= not_helpful_penalty
        support_note = (
            f", support {selected_useful}/{selected_count} useful selections"
            if selected_count
            else ""
        )
        reasons.append(
            f"route not-helpful penalty: -{penalty} from {selected_not_helpful}{support_note}"
        )

    if selected_but_unused >= 2 and not core_doc:
        penalty = 0
        legacy_penalty = (
            min(selected_but_unused // 10, 3)
            if has_strong_path_signal
            else min(2 + selected_but_unused // 5, 7)
        )
        if selected_count >= 5 and selected_precision is not None:
            if selected_precision >= 0.5:
                penalty = min(legacy_penalty, 1 if has_strong_path_signal else 2)
                if penalty < legacy_penalty:
                    unused_penalty_capped_by_support = True
                    reasons.append(
                        "route unused-selection penalty capped by support: "
                        f"{selected_useful}/{selected_count} useful selections"
                    )
            elif selected_precision < 0.25:
                penalty = min(legacy_penalty, 2 + selected_but_unused // 5)
            elif selected_precision < 0.4 and selected_count >= 10:
                penalty = min(legacy_penalty, 1 + selected_but_unused // 8)
            else:
                penalty = legacy_penalty
        elif selected_useful == 0 and selected_but_unused >= 3:
            penalty = 2
        if has_strong_path_signal and penalty > 1 and selected_precision is not None and selected_precision >= 0.25:
            penalty -= 1
        if penalty:
            unused_penalty = penalty
            adjustment -= unused_penalty
            reasons.append(
                "route unused-selection penalty: "
                f"-{penalty} from {selected_but_unused} unused, "
                f"support {selected_useful}/{selected_count} useful selections"
            )

    signal = {
        "selected_count": selected_count,
        "selected_useful_count": selected_useful,
        "selected_but_unused_count": selected_but_unused,
        "selected_not_helpful_count": selected_not_helpful,
        "missed_useful_count": missed_useful,
        "selected_precision": round(selected_precision, 3)
        if selected_precision is not None
        else None,
        "missed_useful_bonus": missed_useful_bonus,
        "not_helpful_penalty": not_helpful_penalty,
        "unused_penalty": unused_penalty,
        "unused_penalty_capped_by_support": unused_penalty_capped_by_support,
        "has_strong_path_signal": has_strong_path_signal,
    }
    return adjustment, reasons, signal


def _route_concern_signal_adjustment(
    *,
    kind: str,
    route_tags: list[str],
    path_title_tokens: set[str],
    body_tokens: set[str],
) -> tuple[int, list[str], dict[str, Any]]:
    total = 0
    reasons: list[str] = []
    items: list[dict[str, Any]] = []
    for route_tag in route_tags:
        keywords = _ROUTE_CONCERN_SIGNAL_KEYWORDS.get(route_tag)
        if not keywords:
            continue
        path_matches = sorted(path_title_tokens & keywords)
        body_matches = sorted(body_tokens & keywords)
        if not path_matches and not body_matches:
            continue
        boost = 1
        if kind in _AUTHORITATIVE_KINDS:
            boost += 2
        elif kind in {"draft", "work"}:
            boost += 1
        if path_matches:
            boost += 1
        boost = min(boost, 4)
        total += boost
        matched = path_matches or body_matches
        items.append(
            {
                "route_tag": route_tag,
                "adjustment": boost,
                "path_matches": path_matches[:8],
                "body_matches": body_matches[:8],
                "protected_kind": kind in _AUTHORITATIVE_KINDS or kind in {"draft", "work"},
            }
        )
        reasons.append(
            f"route tag signal {route_tag} protected doc: +{boost} via {', '.join(matched[:4])}"
        )
    raw_total = total
    if total > 6:
        reasons.append(f"route tag signal boost capped at +6 from +{total}")
        total = 6
    return total, reasons, {
        "adjustment": total,
        "raw_adjustment": raw_total,
        "capped": raw_total > total,
        "items": items,
    }


def _split_applies_when(value: object) -> dict[str, Any]:
    if not isinstance(value, str) or not value.strip():
        return {
            "raw": None,
            "positive_text": "",
            "negative_text": "",
            "positive_tokens": set(),
            "negative_tokens": set(),
        }
    normalized = re.sub(r"\s+", " ", value).strip()
    match = _NEGATIVE_APPLIES_WHEN_RE.search(normalized)
    if match is None:
        positive_text = normalized
        negative_text = ""
    else:
        positive_text = normalized[: match.start()].strip(" ;,.")
        negative_text = normalized[match.end() :].strip(" ;,.")
    return {
        "raw": normalized,
        "positive_text": positive_text,
        "negative_text": negative_text,
        "positive_tokens": _tokenize(positive_text),
        "negative_tokens": _tokenize(negative_text),
    }


def _strong_route_terms(matches: set[str]) -> list[str]:
    weak_terms = _WEAK_ROUTE_MATCH_TERMS | _GENERIC_TASK_SIGNAL_TERMS
    return sorted(term for term in matches if term not in weak_terms)


def _applies_when_adjustment(
    *,
    applies_when: dict[str, Any],
    task_tokens: set[str],
    route_intent: dict[str, Any] | None = None,
) -> tuple[int, list[str], dict[str, Any]]:
    positive_tokens = applies_when.get("positive_tokens")
    negative_tokens = applies_when.get("negative_tokens")
    positive_matches = (
        set(task_tokens) & positive_tokens if isinstance(positive_tokens, set) else set()
    )
    negative_matches = (
        set(task_tokens) & negative_tokens if isinstance(negative_tokens, set) else set()
    )
    strong_positive = _strong_route_terms(positive_matches)
    strong_negative = _strong_route_terms(negative_matches)
    route_intent = route_intent if isinstance(route_intent, dict) else {}
    task_alignment_tokens = set(route_intent.get("alignment_tokens") or [])
    positive_alignment_tokens = (
        set(positive_tokens) & _ROUTE_INTENT_ALIGNMENT_TERMS
        if isinstance(positive_tokens, set)
        else set()
    )
    positive_alignment_matches = sorted(task_alignment_tokens & positive_alignment_tokens)
    adjustment = 0
    reasons: list[str] = []
    if strong_negative:
        penalty = min(len(strong_negative) * 3, 6)
        if strong_positive:
            penalty = max(2, penalty - 1)
        adjustment -= penalty
        reasons.append(
            f"applies_when negative boundary penalty: -{penalty} via {', '.join(strong_negative[:4])}"
        )
    if (
        applies_when.get("raw")
        and task_alignment_tokens
        and positive_alignment_tokens
        and not positive_alignment_matches
    ):
        penalty = 2
        adjustment -= penalty
        reasons.append(
            "applies_when action/stage mismatch penalty: "
            f"-{penalty}; task has {', '.join(sorted(task_alignment_tokens)[:4])}"
        )
    signal = {
        "positive_text": applies_when.get("positive_text") or "",
        "negative_text": applies_when.get("negative_text") or "",
        "positive_matches": sorted(positive_matches)[:8],
        "negative_matches": sorted(negative_matches)[:8],
        "strong_positive_matches": strong_positive[:8],
        "strong_negative_matches": strong_negative[:8],
        "task_alignment_tokens": sorted(task_alignment_tokens)[:12],
        "positive_alignment_tokens": sorted(positive_alignment_tokens)[:12],
        "positive_alignment_matches": positive_alignment_matches[:8],
        "adjustment": adjustment,
    }
    return adjustment, reasons, signal


def _score_document(
    *,
    entry: dict[str, str],
    repo_root: Path,
    task_type: str,
    task_tokens: set[str],
    route_intent: dict[str, Any],
    route_tags: list[str],
    document_stats: dict[str, Any],
    route_quality_doc_stats: dict[str, dict[str, int]],
) -> dict[str, Any]:
    text = _load_document_text(repo_root, entry)
    body = _strip_frontmatter(text)
    applies_when = _split_applies_when(entry.get("applies_when"))
    routing_hint_for_scoring = (
        str(applies_when["positive_text"])
        if applies_when.get("raw")
        else entry.get("routing_hint", "")
    )
    path_title_text = " ".join(
        [
            entry.get("doc_id", ""),
            entry.get("kind", ""),
            entry.get("path", ""),
            entry.get("title", ""),
            entry.get("short_description", ""),
            routing_hint_for_scoring,
        ]
    )
    slot_text = " ".join(
        [
            path_title_text,
            str(entry.get("applies_when") or ""),
            str(entry.get("routing_hint") or ""),
        ]
    )
    path_title_tokens = _tokenize(path_title_text)
    body_tokens = _tokenize(body[:5000])
    path_title_matches = sorted(task_tokens & path_title_tokens)
    strong_path_title_matches = [
        term for term in path_title_matches if term not in _WEAK_ROUTE_MATCH_TERMS
    ]
    weak_path_title_matches = [
        term for term in path_title_matches if term in _WEAK_ROUTE_MATCH_TERMS
    ]
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
    applied_kind_priority = (
        kind_priority if (strong_path_title_matches or body_matches or core_doc) else kind_priority // 2
    )
    path_title_score = min(len(strong_path_title_matches) * 4 + len(weak_path_title_matches), 16)
    score = (
        path_title_score
        + min(len(body_matches), 6)
        + applied_kind_priority
        + min(effective_reuse_count * 2, 4)
    )
    route_tag_signal_adjustment, route_tag_signal_reasons, route_tag_signal = (
        _route_concern_signal_adjustment(
            kind=kind,
            route_tags=route_tags,
            path_title_tokens=path_title_tokens,
            body_tokens=body_tokens,
        )
    )
    score += route_tag_signal_adjustment

    if entry["doc_id"] == "constraints" and route_tags:
        score += 4
    if entry["doc_id"] == "decisions" and {"user_owned_docs", "memory_governance"} & set(route_tags):
        score += 3
    if kind == "draft" and "memory_governance" in route_tags:
        score += 2

    route_quality_adjustment, route_quality_reasons, route_quality_signal = _route_quality_adjustment(
        doc_id=entry["doc_id"],
        core_doc=core_doc,
        path_title_matches=path_title_matches,
        body_matches=body_matches,
        route_quality_doc_stats=route_quality_doc_stats,
    )
    applies_when_adjustment, applies_when_reasons, applies_when_signal = _applies_when_adjustment(
        applies_when=applies_when,
        task_tokens=task_tokens,
        route_intent=route_intent,
    )
    score = max(0, score + route_quality_adjustment + applies_when_adjustment)

    reasons: list[str] = []
    if path_title_matches:
        reasons.append(f"matched path/title terms: {', '.join(path_title_matches[:6])}")
    if body_matches:
        reasons.append(f"matched body terms: {', '.join(body_matches[:6])}")
    if applied_kind_priority:
        reasons.append(f"{kind} docs are prioritized for {task_type} tasks")
    if effective_reuse_count:
        reasons.append(f"prior resolved reuse count: {effective_reuse_count}")
    reasons.extend(route_tag_signal_reasons)
    if entry["doc_id"] == "constraints" and route_tags:
        reasons.append("active route tags require checking hard constraints")
    if entry["doc_id"] == "decisions" and {"user_owned_docs", "memory_governance"} & set(route_tags):
        reasons.append("ownership or memory-governance work may depend on durable decisions")
    reasons.extend(route_quality_reasons)
    reasons.extend(applies_when_reasons)
    if not reasons:
        reasons.append("no strong task-specific signal")

    return {
        "doc_id": entry["doc_id"],
        "path": entry["path"],
        "title": entry["title"],
        "short_description": entry.get("short_description", entry["title"]),
        "reference_path": entry.get("reference_path", entry["path"]),
        "routing_hint": entry.get("routing_hint"),
        "applies_when": entry.get("applies_when"),
        "routing_hint_positive_text": routing_hint_for_scoring,
        "kind": kind,
        "score": score,
        "confidence": _confidence(score),
        "trust_level": _trust_level(kind),
        "reason": "; ".join(reasons),
        "matched_terms": matched_terms[:10],
        "prior_effective_reuse_count": effective_reuse_count,
        "prior_total_reuse_events": total_events,
        "route_quality_adjustment": route_quality_adjustment,
        "route_quality_signal": route_quality_signal,
        "multi_signal_adjustment": route_tag_signal_adjustment,
        "multi_signal": route_tag_signal,
        "applies_when_adjustment": applies_when_adjustment,
        "applies_when_signal": applies_when_signal,
        "doc_slots": _classify_doc_slots(
            text=slot_text,
            kind=kind,
            doc_id=entry["doc_id"],
        ),
    }


def _task_id_from_task(task: str | None) -> str:
    if not task or not task.strip():
        return "current-task"
    return slugify(task)[:80].strip("-") or "current-task"


def _candidate_card_tokens(candidate: dict[str, Any]) -> dict[str, set[str]]:
    title_text = " ".join(
        str(candidate.get(key) or "")
        for key in ("doc_id", "kind", "title")
    )
    description_text = str(candidate.get("short_description") or "")
    hint_text = str(candidate.get("routing_hint_positive_text") or candidate.get("routing_hint") or "")
    return {
        "title": _tokenize(title_text),
        "description": _tokenize(description_text),
        "hint": _tokenize(hint_text),
    }


def _strong_card_matches(matches: set[str]) -> list[str]:
    return _strong_route_terms(matches)


def _index_card_rerank_adjustment(
    *,
    candidate: dict[str, Any],
    task_tokens: set[str],
) -> tuple[int, list[str]]:
    card_tokens = _candidate_card_tokens(candidate)
    title_matches = task_tokens & card_tokens["title"]
    description_matches = task_tokens & card_tokens["description"]
    hint_matches = task_tokens & card_tokens["hint"]
    all_card_matches = title_matches | description_matches | hint_matches
    strong_title = _strong_card_matches(title_matches)
    strong_description = _strong_card_matches(description_matches)
    strong_hint = _strong_card_matches(hint_matches)
    strong_matches = _strong_card_matches(all_card_matches)
    applies_signal = candidate.get("applies_when_signal")
    strong_negative = (
        applies_signal.get("strong_negative_matches", [])
        if isinstance(applies_signal, dict)
        else []
    )
    adjustment = 0
    reasons: list[str] = []

    if strong_hint:
        boost = min(len(strong_hint) * 4, 8)
        adjustment += boost
        reasons.append(f"card reranker hint match: +{boost} via {', '.join(strong_hint[:4])}")
    if strong_title:
        boost = min(len(strong_title) * 3, 9)
        adjustment += boost
        reasons.append(f"card reranker title match: +{boost} via {', '.join(strong_title[:4])}")
    description_only = [term for term in strong_description if term not in set(strong_title) | set(strong_hint)]
    if description_only:
        boost = min(len(description_only) * 2, 6)
        adjustment += boost
        reasons.append(
            f"card reranker description match: +{boost} via {', '.join(description_only[:4])}"
        )

    if not strong_matches:
        penalty = 1 if candidate.get("trust_level") == "authoritative" else 4
        adjustment -= penalty
        reasons.append(f"card reranker weak card signal penalty: -{penalty}")
    elif all_card_matches and not (strong_title or strong_hint):
        adjustment -= 1
        reasons.append("card reranker only description/body-derived card signal: -1")

    if str(candidate.get("kind") or "").endswith("_index") and len(strong_matches) < 2:
        adjustment -= 2
        reasons.append("card reranker index-doc specificity penalty: -2")

    if strong_negative:
        penalty = min(len(strong_negative) * 4, 8)
        adjustment -= penalty
        reasons.append(
            f"card reranker applies_when negative boundary penalty: -{penalty} via {', '.join(strong_negative[:4])}"
        )

    if adjustment > 10:
        reasons.append(f"card reranker adjustment capped at +10 from +{adjustment}")
        adjustment = 10
    elif adjustment < -6:
        reasons.append(f"card reranker adjustment capped at -6 from {adjustment}")
        adjustment = -6

    return adjustment, reasons


def _rerank_index_card_candidates(
    candidates: list[dict[str, Any]],
    *,
    task_tokens: set[str],
    rerank_top: int,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    if rerank_top <= 0 or not candidates:
        untouched: list[dict[str, Any]] = []
        for candidate in candidates:
            base_score = int(candidate.get("score") or 0)
            updated = dict(candidate)
            updated["base_score"] = base_score
            updated["rerank_score"] = base_score
            updated["rerank_adjustment"] = 0
            updated["rerank_reason"] = "index-card reranker disabled"
            untouched.append(updated)
        return untouched, {
            "enabled": False,
            "mode": "disabled",
            "candidate_count": 0,
            "rerank_top": rerank_top,
        }

    candidate_count = min(len(candidates), rerank_top)
    reranked: list[dict[str, Any]] = []
    for candidate in candidates[:candidate_count]:
        base_score = int(candidate.get("score") or 0)
        adjustment, reasons = _index_card_rerank_adjustment(
            candidate=candidate,
            task_tokens=task_tokens,
        )
        final_score = max(0, base_score + adjustment)
        updated = dict(candidate)
        updated["base_score"] = base_score
        updated["rerank_score"] = final_score
        updated["rerank_adjustment"] = adjustment
        updated["rerank_reason"] = "; ".join(reasons) if reasons else "card reranker kept base score"
        updated["score"] = final_score
        updated["confidence"] = _confidence(final_score)
        if reasons:
            updated["reason"] = f"{updated['reason']}; {updated['rerank_reason']}"
        reranked.append(updated)

    tail: list[dict[str, Any]] = []
    for candidate in candidates[candidate_count:]:
        base_score = int(candidate.get("score") or 0)
        updated = dict(candidate)
        updated["base_score"] = base_score
        updated["rerank_score"] = base_score
        updated["rerank_adjustment"] = 0
        updated["rerank_reason"] = "outside rerank window"
        tail.append(updated)

    reranked.sort(key=lambda item: (-item["score"], -item["base_score"], item["doc_id"]))
    return reranked + tail, {
        "enabled": True,
        "mode": "deterministic_index_card",
        "candidate_count": candidate_count,
        "rerank_top": rerank_top,
    }


def _selection_reason_type(
    candidate: dict[str, Any],
    *,
    route_mode: dict[str, Any],
    workflow_contract: dict[str, Any] | None,
    bucket_id: str | None = None,
) -> str:
    doc_id = str(candidate.get("doc_id") or "")
    kind = str(candidate.get("kind") or "")
    if workflow_contract and (doc_id == "workflows" or bucket_id == "workflow_contract"):
        return "mandatory_contract"
    if kind in {"constraints", "decisions", "workflows", "convention"}:
        if route_mode.get("name") in {"code", "review", "fixed_workflow"}:
            return "safety_guardrail"
        return "background_reference"
    if bucket_id:
        return "bucket_primary"
    return "topical_memory"


def _mark_selected_candidate(
    candidate: dict[str, Any],
    *,
    route_mode: dict[str, Any],
    workflow_contract: dict[str, Any] | None,
    bucket_id: str | None = None,
    note: str | None = None,
) -> dict[str, Any]:
    updated = dict(candidate)
    reason_type = _selection_reason_type(
        candidate,
        route_mode=route_mode,
        workflow_contract=workflow_contract,
        bucket_id=bucket_id,
    )
    updated["selection_reason_type"] = reason_type
    updated["selected_bucket_id"] = bucket_id
    if note:
        updated["reason"] = f"{updated['reason']}; {note}"
    elif bucket_id:
        updated["reason"] = f"{updated['reason']}; selected to cover intent bucket `{bucket_id}`"
    return updated


def _select_route_candidates(
    scored: list[dict[str, Any]],
    *,
    effective_max_docs: int,
    route_mode: dict[str, Any],
    workflow_contract: dict[str, Any] | None,
    intent_buckets: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    selected: list[dict[str, Any]] = []
    selected_ids: set[str] = set()
    selected_bucket_ids: list[str] = []

    fixed_workflow_without_support = (
        route_mode.get("name") == "fixed_workflow"
        and workflow_contract
        and not workflow_contract.get("supporting_docs_allowed")
    )
    eligible = [candidate for candidate in scored if int(candidate.get("score") or 0) >= 7]
    if fixed_workflow_without_support:
        return [], {
            "mode": "intent_bucket_selector",
            "fixed_workflow_without_support": True,
            "bucket_count": len(intent_buckets),
            "selected_bucket_ids": [],
            "selected_doc_count": 0,
            "abstained_reason": "workflow contract selected without supporting docs",
        }

    for bucket in intent_buckets:
        if len(selected) >= effective_max_docs:
            break
        bucket_id = str(bucket.get("id") or "")
        quota = int(bucket.get("quota") or 1)
        if quota <= 0:
            continue
        matches = [
            candidate
            for candidate in eligible
            if candidate["doc_id"] not in selected_ids
            and _bucket_matches_candidate(bucket_id, candidate)
        ]
        for candidate in matches[:quota]:
            selected.append(
                _mark_selected_candidate(
                    candidate,
                    route_mode=route_mode,
                    workflow_contract=workflow_contract,
                    bucket_id=bucket_id,
                )
            )
            selected_ids.add(candidate["doc_id"])
            selected_bucket_ids.append(bucket_id)
            if len(selected) >= effective_max_docs:
                break

    for candidate in eligible:
        if len(selected) >= effective_max_docs:
            break
        if candidate["doc_id"] in selected_ids:
            continue
        selected.append(
            _mark_selected_candidate(
                candidate,
                route_mode=route_mode,
                workflow_contract=workflow_contract,
            )
        )
        selected_ids.add(candidate["doc_id"])

    if not selected and scored and not fixed_workflow_without_support:
        for candidate in scored[: min(3, effective_max_docs)]:
            selected.append(
                _mark_selected_candidate(
                    candidate,
                    route_mode=route_mode,
                    workflow_contract=workflow_contract,
                    note="fallback selected because no scored docs cleared threshold",
                )
            )
            selected_ids.add(candidate["doc_id"])

    return selected, {
        "mode": "intent_bucket_selector",
        "fixed_workflow_without_support": bool(fixed_workflow_without_support),
        "bucket_count": len(intent_buckets),
        "selected_bucket_ids": selected_bucket_ids,
        "selected_doc_count": len(selected),
    }


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
                "applies_when": candidate.get("applies_when"),
                "reason": candidate["reason"],
                "confidence": candidate["confidence"],
                "trust_level": candidate["trust_level"],
                "score": candidate["score"],
                "base_score": candidate.get("base_score", candidate["score"]),
                "rerank_score": candidate.get("rerank_score", candidate["score"]),
                "rerank_adjustment": candidate.get("rerank_adjustment", 0),
                "rerank_reason": candidate.get("rerank_reason"),
                "route_quality_adjustment": candidate.get("route_quality_adjustment", 0),
                "route_quality_signal": candidate.get("route_quality_signal", {}),
                "multi_signal_adjustment": candidate.get("multi_signal_adjustment", 0),
                "multi_signal": candidate.get("multi_signal", {}),
                "applies_when_adjustment": candidate.get("applies_when_adjustment", 0),
                "applies_when_signal": candidate.get("applies_when_signal", {}),
                "doc_slots": candidate.get("doc_slots", []),
                "selection_reason_type": candidate.get("selection_reason_type"),
                "selected_bucket_id": candidate.get("selected_bucket_id"),
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
                "applies_when": candidate.get("applies_when"),
                "load_mode": _reference_mode(candidate, selected_ids),
                "reason": candidate["reason"],
                "score": candidate["score"],
                "base_score": candidate.get("base_score", candidate["score"]),
                "rerank_score": candidate.get("rerank_score", candidate["score"]),
                "rerank_adjustment": candidate.get("rerank_adjustment", 0),
                "rerank_reason": candidate.get("rerank_reason"),
                "route_quality_adjustment": candidate.get("route_quality_adjustment", 0),
                "route_quality_signal": candidate.get("route_quality_signal", {}),
                "multi_signal_adjustment": candidate.get("multi_signal_adjustment", 0),
                "multi_signal": candidate.get("multi_signal", {}),
                "applies_when_adjustment": candidate.get("applies_when_adjustment", 0),
                "applies_when_signal": candidate.get("applies_when_signal", {}),
                "doc_slots": candidate.get("doc_slots", []),
                "selection_reason_type": candidate.get("selection_reason_type"),
                "selected_bucket_id": candidate.get("selected_bucket_id"),
            }
        )
    return cards


def _success_criterion_key(item: dict[str, str]) -> tuple[str, str]:
    return (item["criterion"], item["verification"])


def _build_success_criteria(
    *,
    task_type: str,
    effort: str,
    domain_tags: list[str],
    guardrail_tags: list[str],
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

    if "memory_governance" in domain_tags and task_type != "memory_governance":
        items.append(
            {
                "criterion": "Memory-related changes remain governed and auditable.",
                "verification": "Confirm generated memory artifacts are cited, disposable, and do not replace source Markdown.",
                "reason": "memory_governance domain tag",
            }
        )

    if "user_owned_docs" in guardrail_tags:
        items.append(
            {
                "criterion": "User-owned AI wiki content is not rewritten as a package side effect.",
                "verification": "Inspect the diff for `ai-wiki/**` changes outside managed `_toolkit/**` or explicitly requested draft paths.",
                "reason": "user_owned_docs guardrail tag",
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
    rerank_top: int = DEFAULT_ROUTE_RERANK_TOP,
    start: Path | None = None,
    catalog_cutoff: datetime | None = None,
) -> RouteResult:
    """Generate a conservative task-aware context packet."""

    paths = build_paths(start)
    if not paths.repo_wiki_dir.exists():
        raise RepoWikiNotInitializedError(
            "Repo AI wiki is not initialized. Run `aiwiki-toolkit install` first."
        )

    explicit_changed_path_list = [path for path in changed_paths if path.strip()]
    changed_path_list = list(explicit_changed_path_list)
    changed_path_signal_source = "explicit" if explicit_changed_path_list else "git_status"
    if not changed_path_list:
        changed_path_list = _read_git_changed_paths(paths.repo_root)
        if not changed_path_list:
            changed_path_signal_source = "none"

    task_text = task.strip() if task else ""
    raw_request_tokens = _task_tokens(task_text, filter_stopwords=False)
    request_tokens = _task_tokens(task_text)
    use_changed_path_signals = _should_use_changed_path_signals(
        explicit_changed_paths=bool(explicit_changed_path_list),
        task_tokens=request_tokens,
        raw_task_tokens=raw_request_tokens,
    )
    changed_path_signal_list = changed_path_list if use_changed_path_signals else []
    signal_text = " ".join([task_text, *changed_path_signal_list])
    raw_task_tokens = _task_tokens(signal_text, filter_stopwords=False)
    task_tokens = _task_tokens(signal_text)
    language_signals = _task_language_signals(signal_text)
    intent_signals = _route_intent_signals(
        signal_text,
        raw_task_tokens=raw_task_tokens,
        task_tokens=task_tokens,
    )
    task_type = _classify_task_type(raw_task_tokens)
    domain_tags = _classify_domain_tags(raw_task_tokens)
    guardrail_tags = _classify_guardrail_tags(raw_task_tokens)
    route_tags = sorted({*domain_tags, *guardrail_tags})
    workflow_contract = _detect_workflow_contract(
        value=signal_text,
        task_tokens=raw_task_tokens | task_tokens,
    )
    route_mode = _classify_route_mode(
        value=task_text,
        raw_task_tokens=raw_request_tokens or raw_task_tokens,
        task_tokens=request_tokens or task_tokens,
        route_intent=intent_signals,
        workflow_contract=workflow_contract,
    )
    intent_buckets = _classify_intent_buckets(
        task_tokens=raw_task_tokens | task_tokens,
        task_type=task_type,
        domain_tags=domain_tags,
        route_mode=route_mode,
        workflow_contract=workflow_contract,
    )
    effort = _classify_effort(raw_request_tokens or raw_task_tokens, task_type)
    actor_handle = resolve_user_handle(paths.repo_root)

    catalog = build_repo_catalog(paths.repo_wiki_dir)
    catalog_documents = [
        entry for entry in catalog.get("documents", []) if isinstance(entry, dict)
    ]
    catalog_documents, catalog_cutoff_stats = _filter_catalog_for_cutoff(
        catalog_documents,
        catalog_cutoff=catalog_cutoff,
    )
    document_stats = build_document_stats(paths.repo_wiki_dir).get("documents", {})
    if not isinstance(document_stats, dict):
        document_stats = {}
    route_quality_doc_stats = _build_route_quality_doc_stats(
        paths.repo_wiki_dir,
        handle=actor_handle,
    )
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
            route_intent=intent_signals,
            route_tags=route_tags,
            document_stats=document_stats,
            route_quality_doc_stats=route_quality_doc_stats,
        )
        for entry in catalog_documents
    ]
    scored.sort(key=lambda item: (-item["score"], item["doc_id"]))
    scored, reranker_stats = _rerank_index_card_candidates(
        scored,
        task_tokens=task_tokens,
        rerank_top=rerank_top,
    )

    effective_max_docs = min(max_docs, 3) if effort == "low" else max_docs
    selected, selector_stats = _select_route_candidates(
        scored,
        effective_max_docs=effective_max_docs,
        route_mode=route_mode,
        workflow_contract=workflow_contract,
        intent_buckets=intent_buckets,
    )

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
        domain_tags=domain_tags,
        guardrail_tags=guardrail_tags,
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
            "domain_tags": domain_tags,
            "guardrail_tags": guardrail_tags,
            "changed_paths": changed_path_list,
            "changed_path_signal_source": changed_path_signal_source,
            "changed_path_signal_used": use_changed_path_signals,
            "language_signals": language_signals,
            "intent_signals": intent_signals,
            "mode": route_mode,
            "workflow_contract": workflow_contract,
            "intent_buckets": intent_buckets,
            "catalog_cutoff": catalog_cutoff_stats,
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
            "reranker": reranker_stats,
            "selector": selector_stats,
            "reference_policy": (
                "Include mandatory workflow or constraint material directly; provide "
                "short index cards and reference paths for other memory so the acting "
                "agent can open full documents at runtime when needed."
            ),
        },
        "behavior_contract": {
            "recognized_mode": route_mode["name"],
            "workflow_contract_id": workflow_contract.get("id") if workflow_contract else None,
            "workflow_steps_to_follow": workflow_contract.get("required_steps", [])
            if workflow_contract
            else [],
            "disallowed_actions": route_mode.get("disallowed_actions", []),
            "supporting_docs_policy": (
                "open supporting docs only for workflow changes, bug fixes, or exception cases"
                if workflow_contract
                else "open selected docs according to route mode and task scope"
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
    domain_tags = packet["route"].get("domain_tags") or []
    if domain_tags:
        lines.append(f"Domain Tags: {', '.join(f'`{tag}`' for tag in domain_tags)}")
    guardrail_tags = packet["route"].get("guardrail_tags") or []
    if guardrail_tags:
        lines.append(f"Guardrail Tags: {', '.join(f'`{tag}`' for tag in guardrail_tags)}")
    route_mode = packet["route"].get("mode")
    if isinstance(route_mode, dict) and route_mode.get("name"):
        lines.append(f"Route Mode: `{route_mode['name']}`")
        disallowed = route_mode.get("disallowed_actions")
        if isinstance(disallowed, list) and disallowed:
            lines.append(f"Disallowed Actions: {', '.join(f'`{item}`' for item in disallowed)}")
    workflow_contract = packet["route"].get("workflow_contract")
    if isinstance(workflow_contract, dict) and workflow_contract.get("id"):
        lines.append(f"Workflow Contract: `{workflow_contract['id']}`")
    intent_buckets = packet["route"].get("intent_buckets")
    if isinstance(intent_buckets, list) and intent_buckets:
        bucket_ids = [
            bucket.get("id")
            for bucket in intent_buckets
            if isinstance(bucket, dict) and isinstance(bucket.get("id"), str)
        ]
        if bucket_ids:
            lines.append(f"Intent Buckets: {', '.join(f'`{bucket_id}`' for bucket_id in bucket_ids)}")
    language_signals = packet["route"].get("language_signals")
    if isinstance(language_signals, dict) and language_signals.get("contains_cjk"):
        expanded = language_signals.get("expanded_tokens")
        expanded_text = ""
        if isinstance(expanded, list) and expanded:
            expanded_text = f" Expanded: {', '.join(f'`{token}`' for token in expanded[:8])}"
        lines.append(f"Language Signals: CJK/mixed-language task detected.{expanded_text}")
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
        reranker = strategy.get("reranker") if isinstance(strategy.get("reranker"), dict) else {}
        selector = strategy.get("selector") if isinstance(strategy.get("selector"), dict) else {}
        reranker_text = ""
        if reranker:
            reranker_text = (
                f"- Reranker: `{reranker.get('mode', 'unknown')}`, "
                f"{reranker.get('candidate_count', 0)} candidate cards\n"
            )
        selector_text = ""
        if selector:
            selector_text = (
                f"- Selector: `{selector.get('mode', 'unknown')}`, "
                f"{selector.get('bucket_count', 0)} buckets\n"
            )
        lines.extend(
            [
                "",
                "## Routing Strategy",
                f"- Mode: `{strategy.get('mode', 'unknown')}`",
                f"- Budget: `{strategy.get('budget_policy', 'unknown')}`",
                *(reranker_text.rstrip().splitlines() if reranker_text else []),
                *(selector_text.rstrip().splitlines() if selector_text else []),
                f"- References: {strategy.get('reference_policy', 'Open relevant references at runtime.')}",
            ]
        )
    behavior_contract = (
        packet.get("behavior_contract")
        if isinstance(packet.get("behavior_contract"), dict)
        else {}
    )
    if behavior_contract:
        lines.extend(["", "## Behavior Contract"])
        lines.append(f"- Mode: `{behavior_contract.get('recognized_mode', 'unknown')}`")
        workflow_id = behavior_contract.get("workflow_contract_id")
        if workflow_id:
            lines.append(f"- Workflow: `{workflow_id}`")
        disallowed = behavior_contract.get("disallowed_actions")
        if isinstance(disallowed, list) and disallowed:
            lines.append(f"- Disallowed: {', '.join(f'`{item}`' for item in disallowed)}")
        steps = behavior_contract.get("workflow_steps_to_follow")
        if isinstance(steps, list) and steps:
            lines.append("- Steps: " + "; ".join(str(step) for step in steps[:6]))
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
                f"Reason Type: `{card.get('selection_reason_type') or 'reference'}` "
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
