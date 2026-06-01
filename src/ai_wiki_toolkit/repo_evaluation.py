"""Repo-level AI wiki evaluation and advisor reports."""

from __future__ import annotations

from collections import Counter
from dataclasses import asdict, dataclass
from datetime import datetime
import json
from pathlib import Path
from typing import Any

from ai_wiki_toolkit.consolidation import build_consolidation_queue_report
from ai_wiki_toolkit.diagnostics import (
    DEFAULT_DIAGNOSTICS_MAX_ITEMS,
    DEFAULT_HIGH_ROI_MIN_EVENTS,
    DEFAULT_NOISY_MIN_EVENTS,
    build_memory_diagnostics_report,
)
from ai_wiki_toolkit.impact_eval import (
    discover_impact_eval_families,
    discover_impact_eval_family_candidates,
)
from ai_wiki_toolkit.promotion import (
    DEFAULT_RESOLVED_TASK_THRESHOLD,
    build_promotion_candidates_report,
)
from ai_wiki_toolkit.usefulness import build_usefulness_report

REPO_EVALUATION_SCHEMA_VERSION = "repo-evaluation-v1"
DEFAULT_REPO_EVALUATION_SINCE = "30d"
DEFAULT_REPO_EVALUATION_MAX_ITEMS = DEFAULT_DIAGNOSTICS_MAX_ITEMS

HIGH_ROUTE_NOISE_RATE = 0.5
HIGH_ROUTE_RECALL_PROXY = 0.75
HIGH_AVERAGE_PACKET_WORDS = 1500
HIGH_AVERAGE_SELECTED_DOCS = 8

RECOMMENDED_FORMS = {
    "note",
    "workflow",
    "skill",
    "subagent",
    "automation",
    "extend_existing",
    "skip",
}


@dataclass(frozen=True)
class RepoEvaluationMetric:
    """One named metric in the repo evaluation report."""

    name: str
    value: int | float | str | None
    status: str
    note: str


@dataclass(frozen=True)
class RepoEvaluationRecommendation:
    """One human-reviewable repo evaluation recommendation."""

    title: str
    recommended_form: str
    confidence: str
    evidence: dict[str, Any]
    reason: str
    suggested_next_command: str | None = None
    suggested_human_action: str | None = None


@dataclass(frozen=True)
class RepoEvaluationSummary:
    """Top-level repo evaluation summary."""

    overall_status: str
    top_opportunities: list[str]
    do_not_change_yet: list[str]


@dataclass(frozen=True)
class RepoEvaluationReport:
    """Repo evaluation report payload."""

    schema_version: str
    generated_at: str
    filters: dict[str, Any]
    summary: RepoEvaluationSummary
    workflow_coverage: dict[str, Any]
    route_quality: dict[str, Any]
    memory_quality: dict[str, Any]
    draft_consolidation: dict[str, Any]
    impact_eval_readiness: dict[str, Any]
    asset_selection_opportunities: list[RepoEvaluationRecommendation]
    recommended_next_commands: list[str]
    caveats: list[str]


@dataclass(frozen=True)
class RepoEvaluationResult:
    """Rendered repo evaluation and optional output paths."""

    report: RepoEvaluationReport
    markdown: str
    json_text: str
    markdown_path: Path | None = None
    json_path: Path | None = None


def _now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def _metric(name: str, value: int | float | str | None, status: str, note: str) -> dict[str, Any]:
    return asdict(RepoEvaluationMetric(name=name, value=value, status=status, note=note))


def _recommendation(
    *,
    title: str,
    recommended_form: str,
    confidence: str,
    evidence: dict[str, Any],
    reason: str,
    suggested_next_command: str | None = None,
    suggested_human_action: str | None = None,
) -> RepoEvaluationRecommendation:
    if recommended_form not in RECOMMENDED_FORMS:
        raise ValueError(f"Invalid recommendation form: {recommended_form}")
    return RepoEvaluationRecommendation(
        title=title,
        recommended_form=recommended_form,
        confidence=confidence,
        evidence=evidence,
        reason=reason,
        suggested_next_command=suggested_next_command,
        suggested_human_action=suggested_human_action,
    )


def _fmt_metric(value: object) -> str:
    if value is None:
        return "-"
    if isinstance(value, float):
        return f"{value:.2f}"
    return str(value)


def _as_count(value: object) -> int:
    return value if isinstance(value, int) and not isinstance(value, bool) else 0


def _as_number(value: object) -> int | float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int | float):
        return value
    return None


def _is_high_context_cost(route_summary: dict[str, Any]) -> bool:
    avg_packet_words = _as_number(route_summary.get("avg_packet_words"))
    avg_selected_docs = _as_number(route_summary.get("avg_selected_docs"))
    return (
        avg_packet_words is not None
        and avg_packet_words >= HIGH_AVERAGE_PACKET_WORDS
    ) or (
        avg_selected_docs is not None
        and avg_selected_docs >= HIGH_AVERAGE_SELECTED_DOCS
    )


def _safe_title(item: dict[str, Any]) -> str:
    title = item.get("title")
    if isinstance(title, str) and title.strip():
        return title.strip()
    doc_id = item.get("doc_id")
    if isinstance(doc_id, str) and doc_id.strip():
        return doc_id.rsplit("/", maxsplit=1)[-1].replace("-", " ").strip()
    task_id = item.get("task_id")
    if isinstance(task_id, str) and task_id.strip():
        return task_id.strip()
    return "Untitled"


def _build_workflow_coverage(
    diagnostics_report: dict[str, Any],
    usefulness_report: dict[str, Any],
) -> dict[str, Any]:
    summary = diagnostics_report["summary"]
    usefulness_summary = usefulness_report["summary"]
    gaps = diagnostics_report["coverage_gaps"]
    missing_or_weak: list[str] = []
    recommendations: list[str] = []

    if summary["task_checks"] == 0 and summary["reuse_events"] == 0:
        missing_or_weak.append(
            "No task-level reuse checks or document reuse events were recorded for this filter."
        )
        recommendations.append(
            "Use the AI Wiki reuse and write-back footer for a few tasks before interpreting coverage."
        )
    if summary["coverage_gap_count"] > 0:
        missing_or_weak.append(
            "Some tasks have conflicting or incomplete task-check and document-level reuse evidence."
        )
        recommendations.append("Review task-end reuse/write-back compliance.")
    if summary["task_checks"] == 0 and summary["reuse_events"] > 0:
        missing_or_weak.append("Document reuse exists but task-level reuse checks are missing.")
        recommendations.append("Record one task-level reuse check at the end of each completed task.")
    if summary["reuse_events"] == 0 and summary["tasks_with_wiki_use"] > 0:
        missing_or_weak.append("Tasks claim wiki use but no document-level reuse events were recorded.")
        recommendations.append("Record document-level reuse events for user-owned docs that affect work.")
    if not recommendations:
        recommendations.append("Keep collecting per-task reuse and write-back evidence.")

    return {
        "checked_tasks": summary["checked_tasks"],
        "task_checks": summary["task_checks"],
        "reuse_events": summary["reuse_events"],
        "documents_with_reuse": summary["documents_with_reuse"],
        "tasks_with_references": usefulness_summary["tasks_with_references"],
        "coverage_gaps": summary["coverage_gap_count"],
        "source_incident_events": summary.get("source_incident_events", 0),
        "missing_or_weak_workflow_evidence": missing_or_weak,
        "coverage_gap_items": gaps,
        "metrics": [
            _metric(
                "checked_tasks",
                summary["checked_tasks"],
                "ok" if summary["checked_tasks"] > 0 else "insufficient_data",
                "Task-level reuse checks found in the selected window.",
            ),
            _metric(
                "coverage_gaps",
                summary["coverage_gap_count"],
                "review" if summary["coverage_gap_count"] > 0 else "ok",
                "Conflicts or gaps between task-level checks and document-level reuse events.",
            ),
        ],
        "recommendations": recommendations,
    }


def _build_route_recommendations(route_summary: dict[str, Any], since: str | None) -> list[str]:
    recommendations: list[str] = []
    route_traces = _as_count(route_summary.get("route_trace_count"))
    missed = _as_count(route_summary.get("missed_useful_doc_count"))
    selected_but_unused = _as_count(route_summary.get("selected_but_unused_doc_count"))
    selected_not_helpful = _as_count(route_summary.get("selected_not_helpful_doc_count"))
    route_recall = _as_number(route_summary.get("route_recall_proxy"))
    route_noise = _as_number(route_summary.get("route_noise_rate"))

    if route_traces == 0:
        return [
            "No route traces were recorded. Use the workflow for a while before judging route quality."
        ]
    if (
        route_recall is not None
        and route_noise is not None
        and route_recall >= HIGH_ROUTE_RECALL_PROXY
        and route_noise >= HIGH_ROUTE_NOISE_RATE
    ):
        recommendations.append(
            "High recall with high noise: review sparse/index-card-first routing; do not auto-change route policy."
        )
    if missed > 0:
        recommendations.append(
            "Missed useful docs exist: improve route hints, index cards, or the relevant source docs after human review."
        )
    if _is_high_context_cost(route_summary):
        recommendations.append(
            "High context cost: review full-doc inclusion and prefer runtime references where possible."
        )
    if selected_but_unused > 0 or selected_not_helpful > 0:
        recommendations.append(
            "Selected-but-unused or not-helpful docs exist: review noisy memory candidates."
        )
    if not recommendations:
        recommendations.append("No route-quality recommendation triggered by the fixed heuristics.")
    if since:
        recommendations.append(
            f"Compare with `aiwiki-toolkit diagnose memory --focus route --since {since}` before changing route behavior."
        )
    return recommendations


def _build_route_quality(diagnostics_report: dict[str, Any], since: str | None) -> dict[str, Any]:
    route = diagnostics_report["route_diagnostics"]
    summary = route["summary"]
    return {
        "route_traces": summary["route_trace_count"],
        "selected_docs": summary["selected_doc_count"],
        "useful_selected_docs": summary["useful_selected_doc_count"],
        "missed_useful_docs": summary["missed_useful_doc_count"],
        "extra_lookup_docs": summary["extra_lookup_count"],
        "later_lookup_docs": summary.get("later_lookup_doc_count", summary["extra_lookup_count"]),
        "selected_but_unused_docs": summary.get("selected_but_unused_doc_count", 0),
        "selected_not_helpful_docs": summary.get("selected_not_helpful_doc_count", 0),
        "route_precision": summary["route_precision"],
        "route_recall_proxy": summary["route_recall_proxy"],
        "route_noise_rate": summary["route_noise_rate"],
        "average_packet_words": summary["avg_packet_words"],
        "average_selected_docs": summary["avg_selected_docs"],
        "recommendations": _build_route_recommendations(summary, since),
        "items": route.get("items", []),
    }


def _build_memory_quality(
    diagnostics_report: dict[str, Any],
    usefulness_report: dict[str, Any],
) -> dict[str, Any]:
    referenced = usefulness_report["referenced_documents"]
    total_events = sum(_as_count(item.get("total_events")) for item in referenced)
    useful_events = sum(
        _as_count(item.get("resolved_events")) + _as_count(item.get("partial_events"))
        for item in referenced
    )
    useful_ratio = useful_events / total_events if total_events else None
    recommendations: list[str] = []

    if diagnostics_report["high_roi_memory"]:
        recommendations.append("High-ROI docs exist: consider keeping them visible or reviewing promotion.")
    if diagnostics_report["noisy_memory"]:
        recommendations.append(
            "Noisy or not-helpful docs exist: review whether they are stale, too generic, wrong-scope, or missing detail."
        )
    if diagnostics_report["conflicting_memory"]:
        recommendations.append("Conflicting memory candidates require human review.")
    if not referenced:
        recommendations.append("No reuse evidence was recorded yet; memory quality cannot be judged.")
    if not recommendations:
        recommendations.append("No memory-quality recommendation triggered by the fixed heuristics.")

    return {
        "high_roi_docs": diagnostics_report["high_roi_memory"],
        "noisy_docs": diagnostics_report["noisy_memory"],
        "stale_candidates": diagnostics_report["stale_memory"],
        "conflicting_candidates": diagnostics_report["conflicting_memory"],
        "missed_memory": diagnostics_report["missed_memory"],
        "useful_reuse_ratio": useful_ratio,
        "referenced_documents": referenced,
        "recommendations": recommendations,
    }


def _build_draft_consolidation(
    consolidation_report: dict[str, Any],
    promotion_report: dict[str, Any],
    since: str | None,
) -> dict[str, Any]:
    queue_items = consolidation_report["queue_items"]
    duplicate_or_overlap = [
        item for item in queue_items if len(item.get("source_drafts", [])) > 1
    ]
    promotion_items = [
        item
        for item in queue_items
        if item.get("suggested_action") == "Promotion candidate"
    ]
    recommendations = [
        "Do not rewrite shared docs automatically; review the generated queue first.",
        f"Run `aiwiki-toolkit consolidate queue --since {since or '30d'}` for the detailed queue.",
    ]
    if promotion_report["summary"]["new_candidates"] or promotion_report["summary"]["already_marked"]:
        recommendations.append(
            "Review promotion candidates before moving any draft into shared conventions, problems, features, or review patterns."
        )
    return {
        "draft_clusters": consolidation_report["summary"]["queue_items"],
        "drafts_scanned": consolidation_report["summary"]["drafts_scanned"],
        "duplicate_overlap_candidates": len(duplicate_or_overlap),
        "promotion_candidates": len(promotion_items)
        + promotion_report["summary"]["new_candidates"]
        + promotion_report["summary"]["already_marked"],
        "human_review_needed_items": len(queue_items),
        "queue_items": queue_items,
        "promotion_summary": promotion_report["summary"],
        "recommendations": recommendations,
    }


def _read_json_or_empty(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    return payload if isinstance(payload, dict) else {}


def _load_impact_run_history(repo_wiki_dir: Path, max_items: int) -> list[dict[str, Any]]:
    payload = _read_json_or_empty(repo_wiki_dir / "_toolkit" / "evals" / "runs" / "index.json")
    runs = payload.get("runs")
    if not isinstance(runs, list):
        return []
    return [run for run in runs[-max_items:] if isinstance(run, dict)]


def _empty_impact_eval_readiness(reason: str, since: str | None) -> dict[str, Any]:
    return {
        "discovered_eval_candidates": 0,
        "existing_family_readiness": {
            "family_count": 0,
            "runnable_count": 0,
            "status_counts": {},
        },
        "run_history": [],
        "next_eval_commands": [
            f"aiwiki-toolkit eval impact discover --since {since or '30d'}",
            f"aiwiki-toolkit eval impact family candidates --since {since or '30d'}",
        ],
        "recommendations": [
            reason,
            "Diagnostics are available, but outcome-impact proof requires captured impact eval artifacts.",
        ],
    }


def _build_impact_eval_readiness(
    *,
    repo_root: Path,
    repo_wiki_dir: Path,
    handle: str,
    since: str | None,
    max_items: int,
) -> dict[str, Any]:
    try:
        families = discover_impact_eval_families(repo_root=repo_root)
        candidates = discover_impact_eval_family_candidates(
            repo_root=repo_root,
            repo_wiki_dir=repo_wiki_dir,
            handle=handle,
            since=since,
            max_items=max_items,
            include_not_ready=True,
        )
    except FileNotFoundError:
        return _empty_impact_eval_readiness(
            "No impact eval family specs were found in this repo.", since
        )

    status_counts = Counter(
        str(family.get("status") or "unknown")
        for family in families.get("families", [])
        if isinstance(family, dict)
    )
    candidate_count = candidates.get("summary", {}).get("candidate_count", 0)
    run_history = _load_impact_run_history(repo_wiki_dir, max_items)
    recommendations: list[str] = []
    if candidate_count:
        recommendations.append(
            "Eval candidates exist: review family draft/init/promote flow before making outcome claims."
        )
    if families.get("family_count", 0) and not run_history:
        recommendations.append(
            "Formal eval families exist, but no managed run history is indexed yet."
        )
    if not families.get("family_count", 0) and not candidate_count:
        recommendations.append(
            "Diagnostics are available, but outcome-impact proof is not yet available."
        )
    if not recommendations:
        recommendations.append("Impact eval readiness has enough artifacts for a human review pass.")

    return {
        "discovered_eval_candidates": candidate_count,
        "existing_family_readiness": {
            "family_count": families.get("family_count", 0),
            "runnable_count": families.get("runnable_count", 0),
            "status_counts": dict(sorted(status_counts.items())),
            "families": families.get("families", [])[:max_items],
        },
        "candidate_summary": candidates.get("summary", {}),
        "candidates": candidates.get("candidates", [])[:max_items],
        "run_history": run_history,
        "next_eval_commands": [
            f"aiwiki-toolkit eval impact discover --since {since or '30d'}",
            f"aiwiki-toolkit eval impact family candidates --since {since or '30d'}",
            "aiwiki-toolkit eval impact families",
        ],
        "recommendations": recommendations,
    }


def _recommended_form_for_text(text: str, default: str) -> str:
    lowered = text.lower()
    if any(word in lowered for word in ("automation", "monitor", "weekly", "daily", "schedule")):
        return "automation"
    if any(word in lowered for word in ("subagent", "specialist", "audit", "investigate")):
        return "subagent"
    if any(word in lowered for word in ("skill", "runtime", "trigger", "bounded", "script")):
        return "skill"
    if any(word in lowered for word in ("workflow", "process", "runbook", "release", "queue", "checklist")):
        return "workflow"
    if any(word in lowered for word in ("existing", "extend", "already covered")):
        return "extend_existing"
    return default


def _asset_recommendation_from_queue_item(
    item: dict[str, Any],
    *,
    since: str | None,
) -> RepoEvaluationRecommendation:
    title = str(item.get("cluster_title") or "Review draft cluster")
    weak_signals = item.get("weak_signals") if isinstance(item.get("weak_signals"), list) else []
    haystack = " ".join([title, *[str(signal) for signal in weak_signals]])
    form = _recommended_form_for_text(haystack, "note")
    action = str(item.get("suggested_action") or "")
    confidence = "high" if action == "Promotion candidate" else "medium"
    if form != "note" and action not in {"Conflict", "Supersession"}:
        confidence = "medium"
    return _recommendation(
        title=f"Review asset form for {title}",
        recommended_form=form,
        confidence=confidence,
        evidence={
            "source_drafts": item.get("source_drafts", []),
            "suggested_action": action,
            "weak_signals": weak_signals,
        },
        reason=(
            "Consolidation evidence suggests this repeated memory should be reviewed for the "
            "smallest useful asset form."
        ),
        suggested_next_command=f"aiwiki-toolkit consolidate queue --since {since or '30d'}",
    )


def _asset_recommendation_from_high_roi(item: dict[str, Any]) -> RepoEvaluationRecommendation:
    title = _safe_title(item)
    doc_id = str(item.get("doc_id") or "")
    form = _recommended_form_for_text(f"{title} {doc_id}", "note")
    return _recommendation(
        title=f"Keep high-ROI memory visible: {title}",
        recommended_form=form,
        confidence="medium",
        evidence={
            "doc_id": doc_id,
            "resolved_events": item.get("resolved_events", 0),
            "total_events": item.get("total_events", 0),
            "reuse_effects": item.get("reuse_effects", {}),
        },
        reason=(
            "This memory has useful reuse evidence. First review whether it should stay as a note, "
            "be promoted, or become a more operational asset."
        ),
        suggested_human_action="Review the source memory and any existing workflow or skill before creating a new asset.",
    )


def _asset_recommendation_from_impact_candidate(
    item: dict[str, Any],
) -> RepoEvaluationRecommendation:
    title = str(item.get("title") or item.get("candidate_id") or "impact eval candidate")
    return _recommendation(
        title=f"Review impact-eval candidate: {title}",
        recommended_form="subagent",
        confidence="low",
        evidence={
            "candidate_id": item.get("candidate_id"),
            "doc_id": item.get("doc_id"),
            "status": item.get("status"),
            "readiness": item.get("readiness", {}),
        },
        reason=(
            "Investigation, audit, and report specialist work may deserve a dedicated surface only "
            "after source incidents and eval artifacts are confirmed."
        ),
        suggested_next_command="aiwiki-toolkit eval impact family candidates",
    )


def _build_asset_selection_opportunities(
    *,
    consolidation_report: dict[str, Any],
    diagnostics_report: dict[str, Any],
    impact_eval_readiness: dict[str, Any],
    since: str | None,
    max_items: int,
) -> list[RepoEvaluationRecommendation]:
    recommendations: list[RepoEvaluationRecommendation] = []
    seen_titles: set[str] = set()

    for item in consolidation_report["queue_items"]:
        recommendation = _asset_recommendation_from_queue_item(item, since=since)
        if recommendation.title not in seen_titles:
            recommendations.append(recommendation)
            seen_titles.add(recommendation.title)
        if len(recommendations) >= max_items:
            return recommendations

    for item in diagnostics_report["high_roi_memory"]:
        recommendation = _asset_recommendation_from_high_roi(item)
        if recommendation.title not in seen_titles:
            recommendations.append(recommendation)
            seen_titles.add(recommendation.title)
        if len(recommendations) >= max_items:
            return recommendations

    for item in impact_eval_readiness.get("candidates", []):
        if not isinstance(item, dict):
            continue
        recommendation = _asset_recommendation_from_impact_candidate(item)
        if recommendation.title not in seen_titles:
            recommendations.append(recommendation)
            seen_titles.add(recommendation.title)
        if len(recommendations) >= max_items:
            return recommendations

    if not recommendations:
        recommendations.append(
            _recommendation(
                title="Do not create new assets yet",
                recommended_form="skip",
                confidence="high",
                evidence={
                    "draft_clusters": consolidation_report["summary"]["queue_items"],
                    "high_roi_docs": len(diagnostics_report["high_roi_memory"]),
                    "impact_eval_candidates": impact_eval_readiness.get(
                        "discovered_eval_candidates", 0
                    ),
                },
                reason=(
                    "No repeated, high-confidence asset evidence was detected. Continue collecting "
                    "reuse checks, route traces, and consolidation signals."
                ),
                suggested_human_action="Skip asset creation until repeated evidence appears.",
            )
        )
    return recommendations


def _recommended_next_commands(since: str | None, handle: str) -> list[str]:
    since_suffix = f" --since {since or '30d'}"
    handle_suffix = f" --handle {handle}" if handle else ""
    return [
        f"aiwiki-toolkit diagnose memory{since_suffix}{handle_suffix}",
        f"aiwiki-toolkit diagnose memory --focus route{since_suffix}{handle_suffix}",
        f"aiwiki-toolkit consolidate queue{since_suffix}{handle_suffix}",
        f"aiwiki-toolkit promote candidates{handle_suffix}",
        f"aiwiki-toolkit eval impact discover{since_suffix}{handle_suffix}",
        f"aiwiki-toolkit eval impact family candidates{since_suffix}{handle_suffix}",
        f"aiwiki-toolkit report usefulness{since_suffix}{handle_suffix}",
    ]


def _caveats() -> list[str]:
    return [
        "This is a local operator report, not a statistically powered benchmark.",
        "Route diagnostics are based on recorded route traces and downstream reuse evidence.",
        "Recall is a proxy because useful-but-unlooked-up docs remain unknown.",
        "Recommendations are review-first and do not mutate user-owned docs.",
        "Outcome claims require captured impact eval artifacts.",
    ]


def _overall_status(
    *,
    workflow_coverage: dict[str, Any],
    route_quality: dict[str, Any],
    impact_eval_readiness: dict[str, Any],
) -> str:
    if workflow_coverage["task_checks"] == 0 and workflow_coverage["reuse_events"] == 0:
        return "insufficient evidence"
    if workflow_coverage["coverage_gaps"] > 0:
        return "needs workflow evidence review"
    if route_quality["missed_useful_docs"] > 0 or route_quality["selected_but_unused_docs"] > 0:
        return "useful with route-quality review needed"
    if impact_eval_readiness["discovered_eval_candidates"] == 0 and not impact_eval_readiness[
        "run_history"
    ]:
        return "operator diagnostics available; impact proof pending"
    return "healthy with review opportunities"


def _top_opportunities(
    *,
    workflow_coverage: dict[str, Any],
    route_quality: dict[str, Any],
    memory_quality: dict[str, Any],
    draft_consolidation: dict[str, Any],
    impact_eval_readiness: dict[str, Any],
) -> list[str]:
    opportunities: list[str] = []
    if workflow_coverage["coverage_gaps"] > 0 or workflow_coverage["task_checks"] == 0:
        opportunities.append("Review task-end reuse/write-back evidence coverage.")
    if route_quality["missed_useful_docs"] > 0:
        opportunities.append("Review missed useful route docs and route hints.")
    if route_quality["selected_but_unused_docs"] > 0 or route_quality["selected_not_helpful_docs"] > 0:
        opportunities.append("Review route-selected docs that were unused or not helpful.")
    if memory_quality["high_roi_docs"]:
        opportunities.append("Promote or keep high-ROI memories visible after human review.")
    if memory_quality["noisy_docs"] or memory_quality["conflicting_candidates"]:
        opportunities.append("Clean up noisy, stale, or conflicting memories.")
    if draft_consolidation["human_review_needed_items"] > 0:
        opportunities.append("Review draft consolidation queue items.")
    if impact_eval_readiness["discovered_eval_candidates"] > 0:
        opportunities.append("Convert confirmed source incidents into impact eval families.")
    if not opportunities:
        opportunities.append("Collect more task checks, reuse events, route traces, and eval artifacts.")
    return opportunities[:5]


def _do_not_change_yet() -> list[str]:
    return [
        "Do not auto-optimize route policy from telemetry alone.",
        "Do not auto-create workflow, skill, subagent, or automation assets from this report.",
        "Do not rewrite user-owned AI wiki docs without explicit human review.",
    ]


def build_repo_evaluation(
    *,
    repo_root: Path,
    repo_wiki_dir: Path,
    handle: str,
    since: str | None = DEFAULT_REPO_EVALUATION_SINCE,
    max_items: int = DEFAULT_REPO_EVALUATION_MAX_ITEMS,
    generated_at: str | None = None,
) -> RepoEvaluationReport:
    """Build a deterministic repo evaluation report from local evidence."""
    generated_at = generated_at or _now_iso()
    diagnostics_report = build_memory_diagnostics_report(
        repo_wiki_dir,
        handle=handle,
        since=since,
        focus="all",
        max_items=max_items,
        generated_at=generated_at,
    )
    usefulness_report = build_usefulness_report(
        repo_wiki_dir,
        handle=handle,
        since=since,
        generated_at=generated_at,
    )
    consolidation_report = build_consolidation_queue_report(
        repo_wiki_dir,
        handle=handle,
        since=since,
        max_items=max_items,
        generated_at=generated_at,
    )
    promotion_report = build_promotion_candidates_report(
        repo_wiki_dir,
        handle=handle,
        since=since,
        resolved_task_threshold=DEFAULT_RESOLVED_TASK_THRESHOLD,
        generated_at=generated_at,
    )

    workflow_coverage = _build_workflow_coverage(diagnostics_report, usefulness_report)
    route_quality = _build_route_quality(diagnostics_report, since)
    memory_quality = _build_memory_quality(diagnostics_report, usefulness_report)
    draft_consolidation = _build_draft_consolidation(
        consolidation_report,
        promotion_report,
        since,
    )
    impact_eval_readiness = _build_impact_eval_readiness(
        repo_root=repo_root,
        repo_wiki_dir=repo_wiki_dir,
        handle=handle,
        since=since,
        max_items=max_items,
    )
    asset_selection_opportunities = _build_asset_selection_opportunities(
        consolidation_report=consolidation_report,
        diagnostics_report=diagnostics_report,
        impact_eval_readiness=impact_eval_readiness,
        since=since,
        max_items=max_items,
    )
    summary = RepoEvaluationSummary(
        overall_status=_overall_status(
            workflow_coverage=workflow_coverage,
            route_quality=route_quality,
            impact_eval_readiness=impact_eval_readiness,
        ),
        top_opportunities=_top_opportunities(
            workflow_coverage=workflow_coverage,
            route_quality=route_quality,
            memory_quality=memory_quality,
            draft_consolidation=draft_consolidation,
            impact_eval_readiness=impact_eval_readiness,
        ),
        do_not_change_yet=_do_not_change_yet(),
    )
    return RepoEvaluationReport(
        schema_version=REPO_EVALUATION_SCHEMA_VERSION,
        generated_at=generated_at,
        filters={
            "repo_root": str(repo_root),
            "wiki_dir": str(repo_wiki_dir),
            "handle": handle,
            "since": since,
            "max_items": max_items,
        },
        summary=summary,
        workflow_coverage=workflow_coverage,
        route_quality=route_quality,
        memory_quality=memory_quality,
        draft_consolidation=draft_consolidation,
        impact_eval_readiness=impact_eval_readiness,
        asset_selection_opportunities=asset_selection_opportunities,
        recommended_next_commands=_recommended_next_commands(since, handle),
        caveats=_caveats(),
    )


def _append_bullets(lines: list[str], values: list[str]) -> None:
    if not values:
        lines.append("- None detected.")
        return
    for value in values:
        lines.append(f"- {value}")


def _append_doc_items(lines: list[str], items: list[dict[str, Any]], *, empty: str) -> None:
    if not items:
        lines.append(f"- {empty}")
        return
    for item in items:
        label = item.get("path") or item.get("doc_id") or item.get("task_id") or "unknown"
        title = _safe_title(item)
        lines.append(f"- `{label}` - {title}")
        reason = item.get("reason")
        if isinstance(reason, str) and reason:
            lines.append(f"  - Reason: {reason}")
        total_events = item.get("total_events")
        if isinstance(total_events, int):
            lines.append(
                "  - Evidence: "
                f"{item.get('resolved_events', 0)} resolved / "
                f"{item.get('partial_events', 0)} partial / "
                f"{item.get('not_helpful_events', 0)} not helpful."
            )


def _render_workflow_coverage(report: RepoEvaluationReport) -> list[str]:
    coverage = report.workflow_coverage
    lines = [
        "## Workflow Coverage",
        "",
        f"- Checked tasks: {coverage['checked_tasks']}",
        f"- Task checks: {coverage['task_checks']}",
        f"- Reuse events: {coverage['reuse_events']}",
        f"- Documents with reuse: {coverage['documents_with_reuse']}",
        f"- Tasks with references: {coverage['tasks_with_references']}",
        f"- Coverage gaps: {coverage['coverage_gaps']}",
        f"- Source incident events: {coverage['source_incident_events']}",
        "",
        "### Missing Or Weak Workflow Evidence",
        "",
    ]
    _append_bullets(lines, coverage["missing_or_weak_workflow_evidence"])
    lines.extend(["", "### Recommendations", ""])
    _append_bullets(lines, coverage["recommendations"])
    lines.append("")
    return lines


def _render_route_quality(report: RepoEvaluationReport) -> list[str]:
    route = report.route_quality
    lines = [
        "## Route Quality",
        "",
        f"- Route traces: {route['route_traces']}",
        f"- Selected docs: {route['selected_docs']}",
        f"- Useful selected docs: {route['useful_selected_docs']}",
        f"- Missed useful docs: {route['missed_useful_docs']}",
        f"- Extra lookup docs: {route['extra_lookup_docs']}",
        f"- Later lookup docs: {route['later_lookup_docs']}",
        f"- Selected-but-unused docs: {route['selected_but_unused_docs']}",
        f"- Selected not-helpful docs: {route['selected_not_helpful_docs']}",
        f"- Route precision: `{_fmt_metric(route['route_precision'])}`",
        f"- Route recall proxy: `{_fmt_metric(route['route_recall_proxy'])}`",
        f"- Route noise rate: `{_fmt_metric(route['route_noise_rate'])}`",
        f"- Average packet words: `{_fmt_metric(route['average_packet_words'])}`",
        f"- Average selected docs: `{_fmt_metric(route['average_selected_docs'])}`",
        "",
        "### Recommendations",
        "",
    ]
    _append_bullets(lines, route["recommendations"])
    lines.append("")
    return lines


def _render_memory_quality(report: RepoEvaluationReport) -> list[str]:
    memory = report.memory_quality
    lines = [
        "## Memory Quality",
        "",
        f"- Useful reuse ratio: `{_fmt_metric(memory['useful_reuse_ratio'])}`",
        f"- High-ROI docs: {len(memory['high_roi_docs'])}",
        f"- Noisy docs: {len(memory['noisy_docs'])}",
        f"- Stale candidates: {len(memory['stale_candidates'])}",
        f"- Conflicting candidates: {len(memory['conflicting_candidates'])}",
        f"- Missed-memory signals: {len(memory['missed_memory'])}",
        "",
        "### High-ROI Memory",
        "",
    ]
    _append_doc_items(lines, memory["high_roi_docs"], empty="None detected.")
    lines.extend(["", "### Noisy Or Not-Helpful Memory", ""])
    _append_doc_items(lines, memory["noisy_docs"], empty="None detected.")
    lines.extend(["", "### Recommendations", ""])
    _append_bullets(lines, memory["recommendations"])
    lines.append("")
    return lines


def _render_draft_consolidation(report: RepoEvaluationReport) -> list[str]:
    draft = report.draft_consolidation
    lines = [
        "## Draft And Consolidation Queue",
        "",
        f"- Draft clusters: {draft['draft_clusters']}",
        f"- Drafts scanned: {draft['drafts_scanned']}",
        f"- Duplicate/overlap candidates: {draft['duplicate_overlap_candidates']}",
        f"- Promotion candidates: {draft['promotion_candidates']}",
        f"- Human-review-needed items: {draft['human_review_needed_items']}",
        "",
        "### Queue Items",
        "",
    ]
    if not draft["queue_items"]:
        lines.append("- None detected.")
    else:
        for item in draft["queue_items"]:
            lines.append(f"- {item['cluster_title']}")
            lines.append(f"  - Suggested action: {item['suggested_action']}")
            lines.append(f"  - Suggested target: `{item['suggested_target']}`")
    lines.extend(["", "### Recommendations", ""])
    _append_bullets(lines, draft["recommendations"])
    lines.append("")
    return lines


def _render_impact_eval_readiness(report: RepoEvaluationReport) -> list[str]:
    impact = report.impact_eval_readiness
    readiness = impact["existing_family_readiness"]
    lines = [
        "## Impact Eval Readiness",
        "",
        f"- Discovered eval candidates: {impact['discovered_eval_candidates']}",
        f"- Existing families: {readiness['family_count']}",
        f"- Runnable families: {readiness['runnable_count']}",
        f"- Family status counts: `{readiness['status_counts']}`",
        f"- Run history items: {len(impact['run_history'])}",
        "",
        "### Next Eval Commands",
        "",
    ]
    _append_bullets(lines, impact["next_eval_commands"])
    lines.extend(["", "### Recommendations", ""])
    _append_bullets(lines, impact["recommendations"])
    lines.append("")
    return lines


def _render_asset_selection(report: RepoEvaluationReport) -> list[str]:
    lines = [
        "## Asset Selection Opportunities",
        "",
    ]
    for index, item in enumerate(report.asset_selection_opportunities, start=1):
        lines.extend(
            [
                f"### {index}. {item.title}",
                "",
                f"- Recommended form: `{item.recommended_form}`",
                f"- Confidence: `{item.confidence}`",
                f"- Reason: {item.reason}",
                f"- Evidence: `{json.dumps(item.evidence, sort_keys=True)}`",
            ]
        )
        if item.suggested_next_command:
            lines.append(f"- Suggested next command: `{item.suggested_next_command}`")
        if item.suggested_human_action:
            lines.append(f"- Suggested human action: {item.suggested_human_action}")
        lines.append("")
    return lines


def render_repo_evaluation_markdown(report: RepoEvaluationReport) -> str:
    """Render a repo evaluation report as Markdown."""
    filters = report.filters
    lines = [
        "# AI Wiki Repo Evaluation",
        "",
        "## Executive Summary",
        "",
        f"- Overall status: {report.summary.overall_status}",
        f"- Generated at: `{report.generated_at}`",
        f"- Filters: handle=`{filters['handle']}`, since=`{filters['since'] or 'all'}`",
        "",
        "### Top Improvement Opportunities",
        "",
    ]
    _append_bullets(lines, report.summary.top_opportunities)
    lines.extend(["", "### What Not To Change Yet", ""])
    _append_bullets(lines, report.summary.do_not_change_yet)
    lines.append("")
    lines.extend(_render_workflow_coverage(report))
    lines.extend(_render_route_quality(report))
    lines.extend(_render_memory_quality(report))
    lines.extend(_render_draft_consolidation(report))
    lines.extend(_render_impact_eval_readiness(report))
    lines.extend(_render_asset_selection(report))
    lines.extend(["## Recommended Next Commands", ""])
    _append_bullets(lines, report.recommended_next_commands)
    lines.extend(["", "## Caveats", ""])
    _append_bullets(lines, report.caveats)
    lines.append("")
    return "\n".join(lines)


def serialize_repo_evaluation_json(report: RepoEvaluationReport) -> str:
    """Render a repo evaluation report as stable JSON."""
    return json.dumps(asdict(report), indent=2, sort_keys=True) + "\n"


def repo_evaluation_output_paths(repo_wiki_dir: Path, handle: str) -> tuple[Path, Path]:
    """Return default managed repo evaluation output paths."""
    report_dir = repo_wiki_dir / "_toolkit" / "reports" / "repo-evaluation" / handle
    return report_dir / "latest.md", report_dir / "latest.json"


def write_repo_evaluation_report(
    report: RepoEvaluationReport,
    *,
    repo_wiki_dir: Path,
    markdown: str | None = None,
    json_text: str | None = None,
) -> tuple[Path, Path]:
    """Write managed Markdown and JSON report outputs."""
    markdown_path, json_path = repo_evaluation_output_paths(
        repo_wiki_dir,
        str(report.filters["handle"]),
    )
    markdown_path.parent.mkdir(parents=True, exist_ok=True)
    markdown_path.write_text(markdown or render_repo_evaluation_markdown(report), encoding="utf-8")
    json_path.write_text(json_text or serialize_repo_evaluation_json(report), encoding="utf-8")
    return markdown_path, json_path


def generate_repo_evaluation(
    *,
    repo_root: Path,
    repo_wiki_dir: Path,
    handle: str,
    since: str | None = DEFAULT_REPO_EVALUATION_SINCE,
    max_items: int = DEFAULT_REPO_EVALUATION_MAX_ITEMS,
    write: bool = True,
) -> RepoEvaluationResult:
    """Generate and optionally write the managed repo evaluation report."""
    report = build_repo_evaluation(
        repo_root=repo_root,
        repo_wiki_dir=repo_wiki_dir,
        handle=handle,
        since=since,
        max_items=max_items,
    )
    markdown = render_repo_evaluation_markdown(report)
    json_text = serialize_repo_evaluation_json(report)
    markdown_path = None
    json_path = None
    if write:
        markdown_path, json_path = write_repo_evaluation_report(
            report,
            repo_wiki_dir=repo_wiki_dir,
            markdown=markdown,
            json_text=json_text,
        )
    return RepoEvaluationResult(
        report=report,
        markdown=markdown,
        json_text=json_text,
        markdown_path=markdown_path,
        json_path=json_path,
    )
