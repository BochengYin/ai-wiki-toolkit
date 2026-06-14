"""Induce inactive taxonomy candidates from post-hoc evidence."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
import json
from pathlib import Path
from typing import Any

from ai_wiki_toolkit.paths import slugify
from ai_wiki_toolkit.taxonomy_evidence import TAXONOMY_EVIDENCE_SCHEMA_VERSION

TAXONOMY_CANDIDATE_SCHEMA_VERSION = "taxonomy-candidate-report-v1"
DEFAULT_TAXONOMY_CANDIDATE_MIN_EVIDENCE = 2


@dataclass(frozen=True)
class TaxonomyCandidateInductionResult:
    """Rendered taxonomy candidate report and optional managed output paths."""

    report: dict[str, Any]
    markdown: str
    json_text: str
    markdown_path: Path | None = None
    json_path: Path | None = None


@dataclass(frozen=True)
class ClusterSeed:
    """Stable grouping key for evidence that may describe one taxonomy gap."""

    key: str
    label: str
    kind: str
    source_field: str


def _timestamp() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def _normalize_string(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    normalized = value.strip()
    return normalized or None


def _normalize_list(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    normalized: list[str] = []
    seen: set[str] = set()
    for item in value:
        if not isinstance(item, str):
            continue
        text = item.strip()
        if text and text not in seen:
            normalized.append(text)
            seen.add(text)
    return normalized


def _load_evidence_events(repo_wiki_dir: Path, *, handle: str | None) -> list[dict[str, Any]]:
    evidence_dir = repo_wiki_dir / "metrics" / "taxonomy-evidence"
    if not evidence_dir.exists():
        return []

    if handle:
        paths = [evidence_dir / f"{handle}.jsonl"]
    else:
        paths = sorted(evidence_dir.glob("*.jsonl"))

    events: list[dict[str, Any]] = []
    for path in paths:
        if not path.exists():
            continue
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            event = json.loads(line)
            if not isinstance(event, dict):
                continue
            if event.get("schema_version") != TAXONOMY_EVIDENCE_SCHEMA_VERSION:
                continue
            event = dict(event)
            event["_source_log"] = path.name
            events.append(event)

    return sorted(
        events,
        key=lambda item: (
            str(item.get("recorded_at") or ""),
            str(item.get("task_id") or ""),
            str(item.get("evidence_id") or ""),
        ),
    )


def _infer_kind(label: str) -> str:
    normalized = slugify(label)
    if normalized.startswith("boundary-"):
        return "boundary_refinement"
    if any(word in normalized for word in ("phase", "runtime", "mode", "permission")):
        return "agent_runtime_taxonomy"
    if "workflow" in normalized:
        return "workflow_taxonomy"
    if any(word in normalized for word in ("slot", "doc", "document")):
        return "document_slot_taxonomy"
    if any(word in normalized for word in ("route", "router", "routing")):
        return "route_taxonomy"
    return "task_taxonomy"


def _cluster_seed(event: Mapping[str, Any]) -> ClusterSeed | None:
    for field in ("suggested_category_hint", "candidate_category_hint"):
        value = _normalize_string(event.get(field))
        if value:
            key = slugify(value)
            return ClusterSeed(
                key=key,
                label=value,
                kind=_infer_kind(value),
                source_field=field,
            )

    missed_doc_ids = _normalize_list(event.get("missed_doc_ids"))
    if missed_doc_ids:
        label = f"missed_doc:{missed_doc_ids[0]}"
        key = f"missed-doc-{slugify(missed_doc_ids[0])}"
        return ClusterSeed(
            key=key,
            label=label,
            kind="document_slot_taxonomy",
            source_field="missed_doc_ids",
        )

    wrong_category = _normalize_string(event.get("wrong_category"))
    if wrong_category:
        label = f"boundary:{wrong_category}"
        key = f"boundary-{slugify(wrong_category)}"
        return ClusterSeed(
            key=key,
            label=label,
            kind="boundary_refinement",
            source_field="wrong_category",
        )

    return None


def _evidence_id(event: Mapping[str, Any]) -> str:
    value = _normalize_string(event.get("evidence_id"))
    return value or "unknown"


def _example_task(event: Mapping[str, Any]) -> dict[str, str]:
    return {
        "task_id": _normalize_string(event.get("task_id")) or "unknown",
        "task": _normalize_string(event.get("task")) or "unknown",
        "signal_type": _normalize_string(event.get("signal_type")) or "unknown",
        "reason": _normalize_string(event.get("reason")) or "No reason recorded.",
    }


def _negative_example(event: Mapping[str, Any]) -> dict[str, object] | None:
    wrong_category = _normalize_string(event.get("wrong_category"))
    selected_doc_ids = _normalize_list(event.get("selected_doc_ids"))
    missed_doc_ids = _normalize_list(event.get("missed_doc_ids"))
    if not wrong_category and not selected_doc_ids and not missed_doc_ids:
        return None
    return {
        "task_id": _normalize_string(event.get("task_id")) or "unknown",
        "wrong_category": wrong_category,
        "selected_doc_ids": selected_doc_ids,
        "missed_doc_ids": missed_doc_ids,
        "reason": _normalize_string(event.get("reason")) or "No reason recorded.",
    }


def _validation_for_candidate(
    validations: Mapping[str, Any],
    *,
    candidate_id: str,
    cluster_key: str,
) -> Mapping[str, Any] | None:
    direct = validations.get(candidate_id)
    if isinstance(direct, Mapping):
        return direct
    by_key = validations.get(cluster_key)
    if isinstance(by_key, Mapping):
        return by_key
    return None


def _coerce_nonnegative_int(value: object) -> int:
    if isinstance(value, bool):
        return 0
    if isinstance(value, int) and value >= 0:
        return value
    if isinstance(value, str) and value.strip().isdigit():
        return int(value)
    return 0


def _gate2_result(validation: Mapping[str, Any] | None) -> dict[str, Any]:
    if validation is None:
        return {
            "status": "not_run",
            "method": None,
            "improved": False,
            "regressions": None,
            "reason": "No shadow replay or behavior test result was supplied.",
        }

    raw_status = _normalize_string(validation.get("status"))
    improved = bool(validation.get("improved"))
    regressions = _coerce_nonnegative_int(validation.get("regressions"))
    method = _normalize_string(validation.get("method")) or "unknown"
    summary = _normalize_string(validation.get("summary")) or _normalize_string(
        validation.get("reason")
    )

    if raw_status == "passed" and improved and regressions == 0:
        return {
            "status": "passed",
            "method": method,
            "improved": True,
            "regressions": 0,
            "reason": summary or "Gate 2 passed without known regression.",
        }

    reason = summary or "Gate 2 did not prove improvement without regression."
    if raw_status == "passed" and regressions > 0:
        reason = "Regression detected; candidate must remain non-active."
    return {
        "status": "failed",
        "method": method,
        "improved": improved,
        "regressions": regressions,
        "reason": reason,
    }


def _unique_strings(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value in seen:
            continue
        result.append(value)
        seen.add(value)
    return result


def _candidate_text(label: str, events: list[dict[str, Any]]) -> tuple[str, str, str]:
    task_fragments = [
        _normalize_string(event.get("task")) or _normalize_string(event.get("reason")) or ""
        for event in events
    ]
    task_hint = next((text for text in task_fragments if text), label)
    when = (
        f"Use when repeated route evidence matches `{label}` language, for example: "
        f"{task_hint[:180]}"
    )
    do = (
        f"Classify this as `{slugify(label)}` in shadow mode, route against that category, "
        "and compare selected docs plus downstream behavior before activation."
    )
    excluding = (
        "Do not activate from this candidate until Gate 2 proves improvement without "
        "regression; do not use it when the task only mentions this label as an example."
    )
    return when, do, excluding


def _build_candidate(
    seed: ClusterSeed,
    events: list[dict[str, Any]],
    *,
    min_evidence: int,
    validations: Mapping[str, Any],
) -> dict[str, Any]:
    candidate_id = f"tax_{seed.key}"
    source_evidence_ids = [_evidence_id(event) for event in events]
    signal_types = _unique_strings(
        [
            _normalize_string(event.get("signal_type")) or "unknown"
            for event in events
        ]
    )
    confidence_values = _unique_strings(
        [
            _normalize_string(event.get("confidence")) or "unknown"
            for event in events
        ]
    )
    negative_examples = [
        example
        for example in (_negative_example(event) for event in events)
        if example is not None
    ]
    when, do, excluding = _candidate_text(seed.label, events)
    gate2 = _gate2_result(
        _validation_for_candidate(validations, candidate_id=candidate_id, cluster_key=seed.key)
    )
    status = "shadow" if gate2["status"] == "passed" else "proposed"
    return {
        "category_id": candidate_id,
        "cluster_key": seed.key,
        "kind": seed.kind,
        "status": status,
        "active": False,
        "active_taxonomy_changed": False,
        "when": when,
        "do": do,
        "excluding": excluding,
        "positive_examples": [_example_task(event) for event in events[:5]],
        "negative_examples": negative_examples[:5],
        "source_evidence_ids": source_evidence_ids,
        "source_field": seed.source_field,
        "gate1": {
            "status": "passed",
            "min_evidence": min_evidence,
            "evidence_count": len(events),
            "signal_types": signal_types,
            "confidence_values": confidence_values,
            "coherence": "coherent_cluster",
        },
        "gate2": gate2,
    }


def build_taxonomy_candidate_report(
    repo_wiki_dir: Path,
    *,
    handle: str | None = None,
    min_evidence: int = DEFAULT_TAXONOMY_CANDIDATE_MIN_EVIDENCE,
    shadow_validations: Mapping[str, Any] | None = None,
    generated_at: str | None = None,
) -> dict[str, Any]:
    """Build an inactive taxonomy candidate report from post-hoc evidence."""
    if min_evidence < 2:
        raise ValueError("min_evidence must be at least 2.")
    generated_at = generated_at or _timestamp()
    events = _load_evidence_events(repo_wiki_dir, handle=handle)
    validations = shadow_validations or {}

    grouped: dict[str, tuple[ClusterSeed, list[dict[str, Any]]]] = {}
    unclustered = 0
    for event in events:
        seed = _cluster_seed(event)
        if seed is None:
            unclustered += 1
            continue
        grouped.setdefault(seed.key, (seed, []))[1].append(event)

    candidates: list[dict[str, Any]] = []
    rejected_clusters: list[dict[str, Any]] = []
    for key, (seed, cluster_events) in sorted(grouped.items()):
        cluster_events = sorted(
            cluster_events,
            key=lambda item: (
                str(item.get("recorded_at") or ""),
                str(item.get("task_id") or ""),
                str(item.get("evidence_id") or ""),
            ),
        )
        confidences = {
            _normalize_string(event.get("confidence")) or "unknown"
            for event in cluster_events
        }
        if len(cluster_events) < min_evidence:
            rejected_clusters.append(
                {
                    "cluster_key": key,
                    "label": seed.label,
                    "reason": "insufficient_evidence",
                    "evidence_count": len(cluster_events),
                    "min_evidence": min_evidence,
                    "source_evidence_ids": [_evidence_id(event) for event in cluster_events],
                }
            )
            continue
        if confidences == {"low"}:
            rejected_clusters.append(
                {
                    "cluster_key": key,
                    "label": seed.label,
                    "reason": "low_confidence_only",
                    "evidence_count": len(cluster_events),
                    "min_evidence": min_evidence,
                    "source_evidence_ids": [_evidence_id(event) for event in cluster_events],
                }
            )
            continue
        candidates.append(
            _build_candidate(
                seed,
                cluster_events,
                min_evidence=min_evidence,
                validations=validations,
            )
        )

    candidates = sorted(
        candidates,
        key=lambda candidate: (
            -int(candidate["gate1"]["evidence_count"]),
            str(candidate["category_id"]),
        ),
    )
    return {
        "schema_version": TAXONOMY_CANDIDATE_SCHEMA_VERSION,
        "generated_at": generated_at,
        "filters": {
            "handle": handle or "all",
            "min_evidence": min_evidence,
        },
        "summary": {
            "evidence_events_scanned": len(events),
            "clusters_considered": len(grouped),
            "unclustered_events": unclustered,
            "candidate_count": len(candidates),
            "shadow_candidate_count": sum(
                1 for candidate in candidates if candidate["status"] == "shadow"
            ),
            "rejected_cluster_count": len(rejected_clusters),
            "active_taxonomy_changed": False,
        },
        "candidates": candidates,
        "rejected_clusters": rejected_clusters,
        "notes": [
            "This report induces TaxonomyCandidate records only; it never activates taxonomy.",
            "Gate 1 is repeated coherent local evidence.",
            "Gate 2 requires a supplied shadow replay or behavior test result that improves routing without regression.",
            "Candidates stay proposed when Gate 2 is missing or fails.",
        ],
    }


def render_taxonomy_candidate_report_json(report: dict[str, Any]) -> str:
    """Render a taxonomy candidate report as stable JSON."""
    return json.dumps(report, indent=2, sort_keys=True) + "\n"


def _render_bullets(lines: list[str], values: list[str]) -> None:
    if not values:
        lines.append("- None")
        return
    for value in values:
        lines.append(f"- {value}")


def render_taxonomy_candidate_report_markdown(
    report: dict[str, Any],
    *,
    markdown_path: Path | None = None,
    json_path: Path | None = None,
) -> str:
    """Render a taxonomy candidate report as Markdown."""
    filters = report["filters"]
    summary = report["summary"]
    lines = [
        "# Taxonomy Candidate Induction",
        "",
        f"Generated at: `{report['generated_at']}`",
        "",
        "## Filters",
        "",
        f"- Handle: `{filters['handle']}`",
        f"- Minimum evidence: {filters['min_evidence']}",
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
            f"- Evidence events scanned: {summary['evidence_events_scanned']}",
            f"- Clusters considered: {summary['clusters_considered']}",
            f"- Candidates: {summary['candidate_count']}",
            f"- Shadow candidates: {summary['shadow_candidate_count']}",
            f"- Rejected clusters: {summary['rejected_cluster_count']}",
            f"- Active taxonomy changed: {str(summary['active_taxonomy_changed']).lower()}",
            "",
            "## Candidates",
            "",
        ]
    )

    candidates = report["candidates"]
    if not candidates:
        lines.extend(["- None detected.", ""])
    for index, candidate in enumerate(candidates, start=1):
        lines.extend([f"### Candidate {index}: {candidate['category_id']}", ""])
        lines.extend(
            [
                f"- Kind: `{candidate['kind']}`",
                f"- Status: `{candidate['status']}`",
                f"- Active: `{str(candidate['active']).lower()}`",
                f"- Gate 1: `{candidate['gate1']['status']}` with {candidate['gate1']['evidence_count']} evidence events",
                f"- Gate 2: `{candidate['gate2']['status']}`",
                "",
                "When:",
                f"- {candidate['when']}",
                "",
                "Do:",
                f"- {candidate['do']}",
                "",
                "Excluding:",
                f"- {candidate['excluding']}",
                "",
                "Source evidence:",
            ]
        )
        _render_bullets(lines, [f"`{item}`" for item in candidate["source_evidence_ids"]])
        lines.append("")

    lines.extend(["## Rejected Clusters", ""])
    rejected_clusters = report["rejected_clusters"]
    if not rejected_clusters:
        lines.extend(["- None.", ""])
    for cluster in rejected_clusters:
        lines.append(
            f"- `{cluster['cluster_key']}` rejected: {cluster['reason']} "
            f"({cluster['evidence_count']}/{cluster['min_evidence']} evidence)."
        )
    lines.extend(["", "## Notes", ""])
    for note in report["notes"]:
        lines.append(f"- {note}")
    lines.append("")
    return "\n".join(lines)


def generate_taxonomy_candidate_report(
    repo_wiki_dir: Path,
    *,
    handle: str | None = None,
    min_evidence: int = DEFAULT_TAXONOMY_CANDIDATE_MIN_EVIDENCE,
    shadow_validations: Mapping[str, Any] | None = None,
    write: bool = True,
) -> TaxonomyCandidateInductionResult:
    """Generate and optionally write a managed taxonomy candidate report."""
    report = build_taxonomy_candidate_report(
        repo_wiki_dir,
        handle=handle,
        min_evidence=min_evidence,
        shadow_validations=shadow_validations,
    )
    handle_or_all = slugify(handle or "all")
    report_dir = repo_wiki_dir / "_toolkit" / "reports" / "taxonomy-candidates" / handle_or_all
    markdown_path = report_dir / "latest.md" if write else None
    json_path = report_dir / "latest.json" if write else None
    display_markdown_path = (
        Path(f"ai-wiki/_toolkit/reports/taxonomy-candidates/{handle_or_all}/latest.md")
        if write
        else None
    )
    display_json_path = (
        Path(f"ai-wiki/_toolkit/reports/taxonomy-candidates/{handle_or_all}/latest.json")
        if write
        else None
    )
    markdown = render_taxonomy_candidate_report_markdown(
        report,
        markdown_path=display_markdown_path,
        json_path=display_json_path,
    )
    json_text = render_taxonomy_candidate_report_json(report)
    if write:
        report_dir.mkdir(parents=True, exist_ok=True)
        assert markdown_path is not None
        assert json_path is not None
        markdown_path.write_text(markdown, encoding="utf-8")
        json_path.write_text(json_text, encoding="utf-8")
    return TaxonomyCandidateInductionResult(
        report=report,
        markdown=markdown,
        json_text=json_text,
        markdown_path=markdown_path,
        json_path=json_path,
    )
