"""Weekly AI wiki HTML report helpers."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, time, timedelta, timezone
from html import escape
import json
from pathlib import Path
import re
import tomllib
from typing import Any

from ai_wiki_toolkit.frontmatter import parse_frontmatter
from ai_wiki_toolkit.promotion import build_promotion_candidates_report
from ai_wiki_toolkit.usefulness import build_usefulness_report
from ai_wiki_toolkit.wiki_schema import doc_id_for_relative_path, infer_doc_kind

WEEKLY_REPORT_SCHEMA_VERSION = "weekly-report-v1"
REPORT_STATE_SCHEMA_VERSION = "reports-state-v1"
DEFAULT_MAX_WEEKLY_DOCUMENTS = 30
IMPACT_EFFICIENCY_SOURCE = "evals/impact/public/ai_wiki_impact_eval_pilot.md"
IMPACT_FAMILY_SPECS_DIR = "evals/impact/families"
GENERIC_POLICY_DOC_PATHS = {
    "ai-wiki/constraints.md",
    "ai-wiki/decisions.md",
    "ai-wiki/index.md",
    "ai-wiki/workflows.md",
}
NON_COVERAGE_DIRS = {"_toolkit", "metrics", "work"}
DIRECT_IMPACT_ROLES = {
    "consolidated_doc",
    "consolidated_overlay_destination",
    "raw_doc",
    "raw_overlay_destination",
}


@dataclass(frozen=True)
class WeeklyReportResult:
    """Rendered weekly report and generated output paths."""

    report: dict[str, Any]
    html: str
    json_text: str
    html_path: Path | None = None
    json_path: Path | None = None
    latest_html_path: Path | None = None
    latest_json_path: Path | None = None
    state_path: Path | None = None


def _local_now(now: datetime | None = None) -> datetime:
    if now is None:
        return datetime.now().astimezone()
    current = now
    if current.tzinfo is None:
        return current.replace(tzinfo=timezone.utc)
    return current


def _iso_week_period(now: datetime) -> dict[str, str]:
    local = _local_now(now)
    iso_year, iso_week, iso_weekday = local.date().isocalendar()
    start_date = local.date() - timedelta(days=iso_weekday - 1)
    start = datetime.combine(start_date, time.min, tzinfo=local.tzinfo)
    end = start + timedelta(days=7)
    return {
        "period_id": f"{iso_year}-W{iso_week:02d}",
        "period_start": start.isoformat(timespec="seconds"),
        "period_end": end.isoformat(timespec="seconds"),
    }


def _display_path(repo_wiki_dir: Path, path: Path | None) -> str | None:
    if path is None:
        return None
    return f"ai-wiki/{path.relative_to(repo_wiki_dir).as_posix()}"


def _state_path(repo_wiki_dir: Path, *, handle: str) -> Path:
    return repo_wiki_dir / "_toolkit" / "reports" / "weekly" / handle / "state.json"


def _empty_state() -> dict[str, Any]:
    return {
        "schema_version": REPORT_STATE_SCHEMA_VERSION,
        "updated_at": None,
        "weekly": {},
    }


def _load_state(path: Path) -> dict[str, Any]:
    if not path.exists():
        return _empty_state()
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return _empty_state()
    if not isinstance(payload, dict):
        return _empty_state()
    payload.setdefault("schema_version", REPORT_STATE_SCHEMA_VERSION)
    weekly = payload.get("weekly")
    if not isinstance(weekly, dict):
        payload["weekly"] = {}
    return payload


def _write_state(path: Path, state: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _weekly_paths(repo_wiki_dir: Path, *, handle: str, period_id: str) -> dict[str, Path]:
    weekly_dir = repo_wiki_dir / "_toolkit" / "reports" / "weekly" / handle
    period_dir = weekly_dir / period_id
    return {
        "html": period_dir / "report.html",
        "json": period_dir / "report.json",
        "latest_html": weekly_dir / "latest.html",
        "latest_json": weekly_dir / "latest.json",
    }


def _previous_weekly_state(state: dict[str, Any], handle: str) -> dict[str, Any] | None:
    weekly = state.get("weekly")
    if not isinstance(weekly, dict):
        return None
    previous = weekly.get(handle)
    return previous if isinstance(previous, dict) else None


def _format_seconds(value: int | None) -> str:
    if value is None:
        return "unknown"
    if value <= 0:
        return "0s"
    minutes, seconds = divmod(value, 60)
    if minutes == 0:
        return f"{value}s"
    hours, minutes = divmod(minutes, 60)
    if hours == 0:
        return f"{value}s ({minutes}m {seconds}s)"
    return f"{value}s ({hours}h {minutes}m {seconds}s)"


def _format_minutes(value: float | int | None) -> str:
    if value is None:
        return "unknown"
    numeric = float(value)
    if numeric.is_integer():
        return f"{int(numeric)} min"
    return f"{numeric:.1f} min"


def _parse_float(value: str) -> float | None:
    try:
        return float(value)
    except ValueError:
        return None


def _first_number(text: str) -> float | None:
    match = re.search(r"[-+]?\d+(?:\.\d+)?", text)
    return _parse_float(match.group(0)) if match else None


def _normalize_impact_doc_path(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    normalized = value.strip()
    if not normalized:
        return None
    normalized = normalized.removeprefix("./")
    if normalized.startswith("/"):
        return None
    if normalized.startswith("_toolkit/") or normalized.startswith("ai-wiki/_toolkit/"):
        return None
    if not normalized.startswith("ai-wiki/"):
        normalized = f"ai-wiki/{normalized}"
    if not normalized.endswith(".md"):
        normalized = f"{normalized}.md"
    parts = normalized.split("/")
    if any(part in {"", ".", ".."} for part in parts):
        return None
    return normalized


def _doc_id_from_impact_path(path: str) -> str:
    return path.removeprefix("ai-wiki/").removesuffix(".md")


def _repo_relative(path: Path, repo_wiki_dir: Path) -> str:
    return path.relative_to(repo_wiki_dir).as_posix()


def _document_title(metadata: dict[str, object], body: str, path: Path) -> str:
    title = metadata.get("title")
    if isinstance(title, str) and title.strip():
        return title.strip()
    for line in body.splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return path.stem.replace("-", " ").replace("_", " ").strip() or path.stem


def _document_status(metadata: dict[str, object]) -> str | None:
    status = metadata.get("status")
    return status.strip().lower() if isinstance(status, str) and status.strip() else None


def _is_eligible_markdown_path(path: Path, repo_wiki_dir: Path) -> bool:
    relative = path.relative_to(repo_wiki_dir)
    parts = relative.parts
    if not parts:
        return False
    if any(part in NON_COVERAGE_DIRS for part in parts):
        return False
    if path.name == "index.md":
        return False
    return path.suffix == ".md"


def _load_eligible_documents(repo_wiki_dir: Path, *, handle: str) -> list[dict[str, Any]]:
    documents: list[dict[str, Any]] = []
    draft_prefix = f"people/{handle}/drafts/"
    for path in sorted(repo_wiki_dir.rglob("*.md")):
        if not _is_eligible_markdown_path(path, repo_wiki_dir):
            continue
        relative = _repo_relative(path, repo_wiki_dir)
        text = path.read_text(encoding="utf-8")
        metadata, body = parse_frontmatter(text)
        doc_id = doc_id_for_relative_path(relative)
        doc_kind = infer_doc_kind(relative)
        documents.append(
            {
                "doc_id": doc_id,
                "doc_kind": doc_kind,
                "path": f"ai-wiki/{relative}",
                "status": _document_status(metadata),
                "title": _document_title(metadata, body, path),
                "is_personal_draft": doc_id.startswith(draft_prefix),
            }
        )
    return documents


def _build_coverage(
    eligible_documents: list[dict[str, Any]],
    referenced_documents: list[dict[str, Any]],
) -> dict[str, Any]:
    referenced_ids = {item["doc_id"] for item in referenced_documents}
    referenced_eligible = [
        item | {"referenced": True} for item in eligible_documents if item["doc_id"] in referenced_ids
    ]
    unreferenced = [
        item | {"referenced": False} for item in eligible_documents if item["doc_id"] not in referenced_ids
    ]
    personal_drafts = [item for item in eligible_documents if item["is_personal_draft"]]
    referenced_personal_drafts = [
        item for item in personal_drafts if item["doc_id"] in referenced_ids
    ]
    by_kind: dict[str, dict[str, int]] = {}
    for item in eligible_documents:
        kind = item["doc_kind"]
        stats = by_kind.setdefault(kind, {"eligible": 0, "referenced": 0, "unreferenced": 0})
        stats["eligible"] += 1
        if item["doc_id"] in referenced_ids:
            stats["referenced"] += 1
        else:
            stats["unreferenced"] += 1
    return {
        "summary": {
            "eligible_documents": len(eligible_documents),
            "referenced_eligible_documents": len(referenced_eligible),
            "unreferenced_eligible_documents": len(unreferenced),
            "personal_drafts": len(personal_drafts),
            "referenced_personal_drafts": len(referenced_personal_drafts),
            "unreferenced_personal_drafts": len(personal_drafts)
            - len(referenced_personal_drafts),
        },
        "by_kind": [
            {"doc_kind": kind, **stats} for kind, stats in sorted(by_kind.items())
        ],
        "referenced_eligible_documents": sorted(
            referenced_eligible, key=lambda item: (item["doc_kind"], item["path"])
        ),
        "unreferenced_documents": sorted(
            unreferenced, key=lambda item: (item["doc_kind"], item["path"])
        ),
        "notes": [
            "Coverage counts user-owned Markdown files outside _toolkit, metrics, work, and index files.",
            "Unreferenced files are not automatically bad; they are a review queue for stale, hidden, or niche memory.",
        ],
    }


def _is_generic_policy_doc(path: str) -> bool:
    if path in GENERIC_POLICY_DOC_PATHS:
        return True
    return path.endswith("/index.md")


def _extract_markdown_table(text: str, header: str) -> list[list[str]]:
    lines = text.splitlines()
    rows: list[list[str]] = []
    in_table = False
    for line in lines:
        if line.strip() == header:
            in_table = True
            continue
        if not in_table:
            continue
        stripped = line.strip()
        if not stripped.startswith("|"):
            if rows:
                break
            continue
        cells = [cell.strip() for cell in stripped.strip("|").split("|")]
        if cells and all(set(cell) <= {"-", ":"} for cell in cells):
            continue
        rows.append(cells)
    return rows


def _load_impact_efficiency(repo_wiki_dir: Path) -> dict[str, Any]:
    source_path = repo_wiki_dir.parent / IMPACT_EFFICIENCY_SOURCE
    if not source_path.exists():
        return {
            "available": False,
            "source_path": IMPACT_EFFICIENCY_SOURCE,
            "summary": {},
            "families": [],
            "notes": ["No impact-efficiency source report was found."],
        }

    text = source_path.read_text(encoding="utf-8")
    family_rows = _extract_markdown_table(
        text,
        "| family | source active-turn estimate | ambient AI wiki replay | estimated saved active mins using ambient AI wiki | interpretation |",
    )
    families: list[dict[str, Any]] = []
    for cells in family_rows:
        if len(cells) < 5 or cells[0] == "family":
            continue
        family = cells[0].strip("`")
        families.append(
            {
                "family": family,
                "source_active_turn_estimate": cells[1],
                "source_active_turn_minutes": _first_number(cells[1]),
                "ambient_aiwiki_replay": cells[2],
                "ambient_aiwiki_replay_minutes": _first_number(cells[2]),
                "estimated_saved_active_mins": cells[3],
                "estimated_saved_active_minutes": _first_number(cells[3]),
                "interpretation": cells[4],
            }
        )

    core_match = re.search(
        r"against about [0-9.]+ minutes of source active-turn cost, or about `([0-9.]+)` estimated saved active",
        text,
    )
    extended_match = re.search(
        r"giving about `([0-9.]+)`\s+estimated saved active minutes in the extended context",
        text,
        re.MULTILINE,
    )
    weekly_match = re.search(
        r"\| \*\*Total\*\* \| \| \| \*\*([0-9.]+), rounded to ([0-9.]+)\*\* \|",
        text,
    )
    summary = {
        "conservative_saved_active_minutes": (
            _parse_float(core_match.group(1)) if core_match else None
        ),
        "extended_saved_active_minutes": (
            _parse_float(extended_match.group(1)) if extended_match else None
        ),
        "fermi_weekly_saved_active_minutes": (
            _parse_float(weekly_match.group(2)) if weekly_match else None
        ),
        "fermi_weekly_saved_active_minutes_raw": (
            _parse_float(weekly_match.group(1)) if weekly_match else None
        ),
    }
    return {
        "available": True,
        "source_path": IMPACT_EFFICIENCY_SOURCE,
        "summary": summary,
        "families": families,
        "notes": [
            "Impact-efficiency values come from source incident active-turn estimates and formal ambient AI wiki replays.",
            "These are artifact-derived active-time estimates, not exact human time-saved measurements.",
        ],
    }


def _family_row_index(impact_efficiency: dict[str, Any]) -> dict[str, dict[str, Any]]:
    rows = impact_efficiency.get("families")
    if not isinstance(rows, list):
        return {}
    indexed: dict[str, dict[str, Any]] = {}
    for row in rows:
        if not isinstance(row, dict):
            continue
        family = row.get("family")
        if isinstance(family, str) and family:
            indexed[family] = row
    return indexed


def _role_paths(payload: dict[str, Any], field: str, role: str) -> list[tuple[str, str]]:
    values = payload.get(field)
    if not isinstance(values, list):
        return []
    paths: list[tuple[str, str]] = []
    for value in values:
        path = _normalize_impact_doc_path(value)
        if path is not None:
            paths.append((path, role))
    return paths


def _overlay_paths(payload: dict[str, Any], field: str, role: str) -> list[tuple[str, str]]:
    values = payload.get(field)
    if not isinstance(values, list):
        return []
    paths: list[tuple[str, str]] = []
    for value in values:
        if not isinstance(value, dict):
            continue
        destination = _normalize_impact_doc_path(value.get("destination"))
        if destination is not None:
            paths.append((destination, role))
    return paths


def _index_entry_paths(payload: dict[str, Any], field: str, role: str) -> list[tuple[str, str]]:
    values = payload.get(field)
    if not isinstance(values, list):
        return []
    paths: list[tuple[str, str]] = []
    for value in values:
        if not isinstance(value, dict):
            continue
        path = _normalize_impact_doc_path(value.get("path"))
        if path is not None:
            paths.append((path, role))
    return paths


def _family_spec_doc_roles(payload: dict[str, Any]) -> list[tuple[str, str]]:
    roles: list[tuple[str, str]] = []
    roles.extend(_role_paths(payload, "raw_docs", "raw_doc"))
    roles.extend(_role_paths(payload, "consolidated_docs", "consolidated_doc"))
    roles.extend(_overlay_paths(payload, "raw_overlays", "raw_overlay_destination"))
    roles.extend(_overlay_paths(payload, "consolidated_overlays", "consolidated_overlay_destination"))
    roles.extend(_role_paths(payload, "ambient_exclude_paths", "ambient_context"))
    roles.extend(_role_paths(payload, "strict_scaffold_exclude_paths", "adjacent_context"))
    roles.extend(_index_entry_paths(payload, "consolidated_index_entries", "index_entry"))
    roles.extend(_index_entry_paths(payload, "strict_scaffold_index_tokens", "index_token"))
    return roles


def _build_impact_document_attributions(
    repo_wiki_dir: Path,
    impact_efficiency: dict[str, Any],
) -> list[dict[str, Any]]:
    """Join impact family estimates to the Markdown files named by family specs."""
    specs_dir = repo_wiki_dir.parent / IMPACT_FAMILY_SPECS_DIR
    if not specs_dir.exists():
        return []

    families = _family_row_index(impact_efficiency)
    attributions: list[dict[str, Any]] = []
    for spec_path in sorted(specs_dir.glob("*/spec.toml")):
        try:
            payload = tomllib.loads(spec_path.read_text(encoding="utf-8"))
        except tomllib.TOMLDecodeError:
            continue
        family = payload.get("name")
        if not isinstance(family, str) or not family:
            family = spec_path.parent.name
        estimate = families.get(family)
        for path, role in _family_spec_doc_roles(payload):
            is_direct = role in DIRECT_IMPACT_ROLES
            is_generic = _is_generic_policy_doc(path)
            has_estimate = estimate is not None
            calculable = is_direct and has_estimate and not is_generic
            if calculable:
                attribution_level = "measured_family_target"
                confidence = "high"
                note = (
                    "Family-level estimate from source incident active-turn cost minus ambient "
                    "AI wiki replay duration; not an exact per-file human time saving."
                )
            elif is_generic:
                attribution_level = "generic_policy"
                confidence = "none"
                note = (
                    "Broad policy or index file; reuse is tracked, but family saved time is not "
                    "assigned to this file."
                )
            elif is_direct:
                attribution_level = "unmeasured_family_target"
                confidence = "none"
                note = "Target memory in a family spec, but no saved-time estimate is available yet."
            else:
                attribution_level = "adjacent_context"
                confidence = "low"
                note = (
                    "Adjacent or excluded context for an impact family; not a direct saved-time "
                    "target."
                )

            row: dict[str, Any] = {
                "path": path,
                "doc_id": _doc_id_from_impact_path(path),
                "family": family,
                "role": role,
                "attribution_level": attribution_level,
                "confidence": confidence,
                "calculable": calculable,
                "spec_path": spec_path.relative_to(repo_wiki_dir.parent).as_posix(),
                "source_path": impact_efficiency.get("source_path"),
                "note": note,
            }
            if estimate:
                row.update(
                    {
                        "source_active_turn_estimate": estimate.get(
                            "source_active_turn_estimate"
                        ),
                        "source_active_turn_minutes": estimate.get(
                            "source_active_turn_minutes"
                        ),
                        "ambient_aiwiki_replay": estimate.get("ambient_aiwiki_replay"),
                        "ambient_aiwiki_replay_minutes": estimate.get(
                            "ambient_aiwiki_replay_minutes"
                        ),
                        "estimated_saved_active_mins": estimate.get(
                            "estimated_saved_active_mins"
                        ),
                        "estimated_saved_active_minutes": estimate.get(
                            "estimated_saved_active_minutes"
                        ),
                        "interpretation": estimate.get("interpretation"),
                    }
                )
            attributions.append(row)
    return sorted(
        attributions,
        key=lambda item: (
            item["path"],
            0 if item["calculable"] else 1,
            item["family"],
            item["role"],
        ),
    )


def _impact_attribution_summary(attributions: list[dict[str, Any]]) -> dict[str, Any]:
    calculable = [item for item in attributions if item["calculable"]]
    direct_unmeasured = [
        item
        for item in attributions
        if item["attribution_level"] == "unmeasured_family_target"
    ]
    generic = [item for item in attributions if item["attribution_level"] == "generic_policy"]
    adjacent = [item for item in attributions if item["attribution_level"] == "adjacent_context"]
    return {
        "calculable_files": len({item["path"] for item in calculable}),
        "calculable_family_links": len(calculable),
        "direct_unmeasured_family_links": len(direct_unmeasured),
        "generic_or_index_links": len(generic),
        "adjacent_context_links": len(adjacent),
    }


def _enrich_documents_with_impact_attribution(
    documents: list[dict[str, Any]],
    attributions: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    by_path: dict[str, list[dict[str, Any]]] = {}
    for attribution in attributions:
        by_path.setdefault(attribution["path"], []).append(attribution)

    enriched: list[dict[str, Any]] = []
    for document in documents:
        path = _normalize_impact_doc_path(document.get("path"))
        matches = by_path.get(path or "", [])
        calculable = [item for item in matches if item["calculable"]]
        if calculable:
            status = "calculated"
            note = "One or more impact families provide artifact-derived saved-time estimates."
        elif any(item["attribution_level"] == "generic_policy" for item in matches):
            status = "generic_policy"
            note = "Broad policy or index file; no per-file saved-time estimate is assigned."
        elif any(item["attribution_level"] == "unmeasured_family_target" for item in matches):
            status = "not_measured"
            note = "Family target exists, but no saved-time estimate is available yet."
        elif matches:
            status = "adjacent_context"
            note = "Only adjacent impact-family context is available."
        elif path and _is_generic_policy_doc(path):
            status = "generic_policy"
            note = "Broad policy or index file; no per-file saved-time estimate is assigned."
        else:
            status = "not_measured"
            note = "No impact-family saved-time attribution is available."
        enriched.append(
            document
            | {
                "impact_attribution": {
                    "status": status,
                    "note": note,
                    "families": matches,
                }
            }
        )
    return enriched


def _summary_cards(report: dict[str, Any]) -> str:
    documents = report["usefulness"]["referenced_documents"]
    promotion_count = len(report["promotion_candidates"]["new_candidates"]) + len(
        report["promotion_candidates"]["already_marked"]
    )
    diagnosis_count = len(report["diagnosis"]["needs_improvement"])
    not_helpful_count = sum(item["not_helpful_events"] for item in documents)
    candidate_not_helpful_count = sum(
        item.get("candidate_not_helpful_events", 0) for item in documents
    )
    cards = [
        ("Promotion Review", promotion_count),
        ("Draft Diagnosis", diagnosis_count),
        ("Not Helpful Signals", not_helpful_count),
        ("Candidate Signals", candidate_not_helpful_count),
    ]
    return "".join(
        f'<article class="card"><span>{escape(label)}</span><strong>{escape(str(value))}</strong></article>'
        for label, value in cards
    )


def _document_rows(documents: list[dict[str, Any]], *, max_items: int) -> str:
    if not documents:
        return '<tr><td colspan="6">No referenced files recorded for this period.</td></tr>'
    rows: list[str] = []
    for item in documents[:max_items]:
        rows.append(
            "<tr>"
            f"<td><code>{escape(item['path'])}</code></td>"
            f"<td>{escape(item['title'])}</td>"
            f"<td>{item['total_events']}</td>"
            f"<td>{item['resolved_events']}</td>"
            f"<td>{item['partial_events']}</td>"
            f"<td>{item['not_helpful_events']}</td>"
            "</tr>"
        )
    return "".join(rows)


def _coverage_kind_rows(items: list[dict[str, Any]]) -> str:
    if not items:
        return '<tr><td colspan="4">No eligible user-owned Markdown files found.</td></tr>'
    return "".join(
        "<tr>"
        f"<td><code>{escape(item['doc_kind'])}</code></td>"
        f"<td>{item['eligible']}</td>"
        f"<td>{item['referenced']}</td>"
        f"<td>{item['unreferenced']}</td>"
        "</tr>"
        for item in items
    )


def _unreferenced_rows(documents: list[dict[str, Any]], *, max_items: int) -> str:
    if not documents:
        return '<tr><td colspan="4">All eligible files were referenced during this period.</td></tr>'
    rows: list[str] = []
    for item in documents[:max_items]:
        rows.append(
            "<tr>"
            f"<td><code>{escape(item['path'])}</code></td>"
            f"<td>{escape(item['title'])}</td>"
            f"<td><code>{escape(item['doc_kind'])}</code></td>"
            f"<td>{escape(item['status'] or '')}</td>"
            "</tr>"
        )
    return "".join(rows)


def _clean_markdown_inline(value: object) -> str:
    if value is None:
        return ""
    return str(value).replace("`", "")


def _compact_minutes_summary(value: object, *, labels: tuple[str, str] = ("core", "extended")) -> str:
    text = _clean_markdown_inline(value)
    values = re.findall(r"[-+]?\d+(?:\.\d+)?(?=\s*min)", text)
    if not values:
        return text
    if len(values) == 1:
        return f"{values[0]} min"
    return f"{values[0]} min {labels[0]} / {values[1]} min {labels[1]}"


def _not_helpful_rows(documents: list[dict[str, Any]]) -> str:
    noisy = [item for item in documents if item["not_helpful_events"] > 0]
    if not noisy:
        return '<tr><td colspan="7">No not_helpful file references recorded for this period.</td></tr>'
    rows: list[str] = []
    for item in sorted(noisy, key=lambda row: (-row["not_helpful_events"], row["path"]))[:20]:
        reasons = item.get("not_helpful_reasons") or {}
        reason_text = ", ".join(
            f"{reason}: {count}" for reason, count in sorted(reasons.items())
        )
        rows.append(
            "<tr>"
            f"<td><code>{escape(item['path'])}</code></td>"
            f"<td>{escape(item['title'])}</td>"
            f"<td>{item['not_helpful_events']}</td>"
            f"<td>{item.get('confirmed_not_helpful_events', item['not_helpful_events'])}</td>"
            f"<td>{item.get('candidate_not_helpful_events', 0)}</td>"
            f"<td>{item['partial_events']}</td>"
            f"<td>{escape(reason_text)}</td>"
            "</tr>"
        )
    return "".join(rows)


def _is_personal_draft(doc_id: str, handle: str) -> bool:
    return doc_id.startswith(f"people/{handle}/drafts/")


def _build_needs_improvement(
    documents: list[dict[str, Any]], *, handle: str
) -> list[dict[str, Any]]:
    items: list[tuple[int, str, dict[str, Any]]] = []
    for document in documents:
        if not _is_personal_draft(document["doc_id"], handle):
            continue
        reasons: list[str] = []
        suggested_action = "review"
        confirmed_not_helpful = document.get(
            "confirmed_not_helpful_events", document["not_helpful_events"]
        )
        candidate_not_helpful = document.get("candidate_not_helpful_events", 0)
        if confirmed_not_helpful:
            reasons.append(f"{confirmed_not_helpful} confirmed not_helpful signal(s)")
            suggested_action = "rewrite_or_archive"
        if candidate_not_helpful:
            reasons.append(f"{candidate_not_helpful} candidate not_helpful signal(s)")
            if suggested_action == "review":
                suggested_action = "human_review"
        if document["total_events"] >= 2 and document["resolved_events"] == 0:
            reasons.append("reused repeatedly without resolved outcome")
            if suggested_action == "review":
                suggested_action = "add_examples_or_split"
        elif (
            document["total_events"] >= 3
            and document["partial_events"] + document["not_helpful_events"]
            >= document["resolved_events"]
        ):
            reasons.append("partial/not_helpful signals dominate resolved reuse")
            if suggested_action == "review":
                suggested_action = "refine_scope"
        if not reasons:
            continue
        score = confirmed_not_helpful * 4 + candidate_not_helpful * 2 + document["partial_events"]
        items.append(
            (
                score,
                document["path"],
                document
                | {
                    "reasons": reasons,
                    "suggested_action": suggested_action,
                    "source_session_ids": document.get("source_session_ids", []),
                    "session_ids": document.get("session_ids", []),
                    "superseded_by_doc_ids": document.get("superseded_by_doc_ids", []),
                    "resolved_by_doc_ids": document.get("resolved_by_doc_ids", []),
                },
            )
        )
    return [item for _, _, item in sorted(items, key=lambda row: (-row[0], row[1]))]


def _needs_improvement_rows(items: list[dict[str, Any]]) -> str:
    if not items:
        return '<tr><td colspan="7">No personal drafts need diagnosis from this period.</td></tr>'
    rows: list[str] = []
    for item in items[:20]:
        rows.append(
            "<tr>"
            f"<td><code>{escape(item['path'])}</code></td>"
            f"<td>{escape(item['title'])}</td>"
            f"<td>{item['total_events']}</td>"
            f"<td>{item['resolved_events']}</td>"
            f"<td>{item['partial_events']}</td>"
            f"<td>{item['not_helpful_events']}</td>"
            f"<td>{escape('; '.join(item['reasons']))}<br><span class=\"muted\">{escape(item['suggested_action'])}</span></td>"
            "</tr>"
        )
    return "".join(rows)


def _candidate_rows(items: list[dict[str, Any]]) -> str:
    if not items:
        return '<tr><td colspan="4">No promotion candidates detected by the current gate.</td></tr>'
    rows: list[str] = []
    for item in items[:20]:
        rows.append(
            "<tr>"
            f"<td><code>{escape(item['path'])}</code></td>"
            f"<td>{escape(item['title'])}</td>"
            f"<td>{item['resolved_task_count']}</td>"
            f"<td>{escape(item['reason'])}</td>"
            "</tr>"
        )
    return "".join(rows)


def _impact_efficiency_rows(items: list[dict[str, Any]]) -> str:
    if not items:
        return '<tr><td colspan="5">No impact-efficiency family estimates found.</td></tr>'
    rows: list[str] = []
    for item in items:
        rows.append(
            "<tr>"
            f"<td><code>{escape(item['family'])}</code></td>"
            f"<td>{escape(item['source_active_turn_estimate'])}</td>"
            f"<td>{escape(item['ambient_aiwiki_replay'])}</td>"
            f"<td>{escape(item['estimated_saved_active_mins'])}</td>"
            f"<td>{escape(item['interpretation'])}</td>"
            "</tr>"
        )
    return "".join(rows)


def _impact_family_cards(documents: list[dict[str, Any]]) -> str:
    families_by_name: dict[str, dict[str, Any]] = {}
    for document in documents:
        impact = document.get("impact_attribution")
        if not isinstance(impact, dict):
            continue
        attributions = impact.get("families")
        if not isinstance(attributions, list):
            continue
        for attribution in attributions:
            if not isinstance(attribution, dict) or not attribution.get("calculable"):
                continue
            family_name = str(attribution["family"])
            family = families_by_name.setdefault(
                family_name,
                {
                    "family": family_name,
                    "source_active_turn_estimate": attribution.get(
                        "source_active_turn_estimate"
                    ),
                    "ambient_aiwiki_replay": attribution.get("ambient_aiwiki_replay"),
                    "estimated_saved_active_mins": attribution.get(
                        "estimated_saved_active_mins"
                    ),
                    "documents": {},
                },
            )
            family["documents"][document["doc_id"]] = {
                "path": document["path"],
                "role": attribution["role"],
                "title": document["title"],
                "total_events": document["total_events"],
                "resolved_events": document["resolved_events"],
                "partial_events": document["partial_events"],
                "not_helpful_events": document["not_helpful_events"],
            }
    cards: list[str] = []
    for family in sorted(families_by_name.values(), key=lambda item: item["family"]):
        documents_for_family = sorted(
            family["documents"].values(),
            key=lambda item: (-item["total_events"], item["path"]),
        )
        total_refs = sum(item["total_events"] for item in documents_for_family)
        not_helpful = sum(item["not_helpful_events"] for item in documents_for_family)
        warning = (
            '<p class="warning">One or more referenced files in this family has a recent not_helpful signal.</p>'
            if not_helpful
            else ""
        )
        file_rows = "".join(
            "<tr>"
            f"<td><strong>{escape(str(item['title']))}</strong><br><code>{escape(str(item['path']))}</code></td>"
            f"<td>{escape(str(item['role']))}</td>"
            f"<td>{item['total_events']}</td>"
            f"<td>{item['resolved_events']}</td>"
            f"<td>{item['partial_events']}</td>"
            f"<td>{item['not_helpful_events']}</td>"
            "</tr>"
            for item in documents_for_family
        )
        cards.append(
            '<article class="impact-family-card">'
            '<div class="impact-doc-head">'
            "<div>"
            f'<h3><code>{escape(str(family["family"]))}</code></h3>'
            "</div>"
            '<div class="impact-counts">'
            f'<span><strong>{len(documents_for_family)}</strong>Files</span>'
            f'<span><strong>{total_refs}</strong>Total refs</span>'
            f'<span><strong>{not_helpful}</strong>Not helpful</span>'
            "</div>"
            "</div>"
            '<dl class="impact-metrics family-metrics">'
            "<div>"
            "<dt>Source</dt>"
            f"<dd>{escape(_compact_minutes_summary(family.get('source_active_turn_estimate')))}</dd>"
            "</div>"
            "<div>"
            "<dt>Replay</dt>"
            f"<dd>{escape(_clean_markdown_inline(family.get('ambient_aiwiki_replay')))}</dd>"
            "</div>"
            "<div>"
            "<dt>Saved</dt>"
            f"<dd>{escape(_compact_minutes_summary(family.get('estimated_saved_active_mins')))}</dd>"
            "</div>"
            "</dl>"
            f"{warning}"
            '<div class="impact-files">'
            "<table>"
            "<thead><tr><th>Referenced File</th><th>Role</th><th>Total</th><th>Resolved</th><th>Partial</th><th>Not Helpful</th></tr></thead>"
            f"<tbody>{file_rows}</tbody>"
            "</table>"
            "</div>"
            "</article>"
        )
    if not cards:
        return (
            '<div class="empty">No referenced files map to impact families with saved-time '
            "estimates for this period.</div>"
        )
    return "".join(cards)


def render_weekly_report_html(report: dict[str, Any], *, max_documents: int = DEFAULT_MAX_WEEKLY_DOCUMENTS) -> str:
    """Render the weekly report as a standalone HTML file."""
    period = report["period"]
    previous = report["state"]["previous"]
    documents = report["usefulness"]["referenced_documents"]
    promotion = report["promotion_candidates"]
    diagnosis = report["diagnosis"]
    last_generated = previous.get("last_generated_at") if previous else "never"
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>AI Wiki Weekly Review Queue {escape(period['period_id'])}</title>
  <style>
    :root {{
      color-scheme: light;
      --bg: #f6f7f9;
      --panel: #ffffff;
      --text: #17202a;
      --muted: #5f6b7a;
      --line: #d8dee7;
      --accent: #136f63;
      --warn: #a64b00;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      background: var(--bg);
      color: var(--text);
      font-family: ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      line-height: 1.45;
    }}
    main {{ max-width: 1040px; margin: 0 auto; padding: 28px; }}
    header {{ margin-bottom: 24px; }}
    h1 {{ margin: 0 0 8px; font-size: 30px; letter-spacing: 0; }}
    h2 {{ margin: 28px 0 12px; font-size: 18px; letter-spacing: 0; }}
    p {{ margin: 0 0 8px; color: var(--muted); }}
    .meta {{ display: flex; flex-wrap: wrap; gap: 10px 18px; color: var(--muted); font-size: 14px; }}
    .cards {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(170px, 1fr)); gap: 12px; }}
    .card {{ background: var(--panel); border: 1px solid var(--line); border-radius: 8px; padding: 14px; }}
    .card span {{ display: block; color: var(--muted); font-size: 13px; }}
    .card strong {{ display: block; margin-top: 6px; font-size: 22px; }}
    .panel {{ background: var(--panel); border: 1px solid var(--line); border-radius: 8px; overflow: hidden; }}
    table {{ width: 100%; border-collapse: collapse; font-size: 14px; }}
    th, td {{ padding: 10px 12px; border-bottom: 1px solid var(--line); text-align: left; vertical-align: top; }}
    th {{ background: #eef2f5; color: #29333d; font-weight: 650; }}
    tr:last-child td {{ border-bottom: 0; }}
    code {{ font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; font-size: 12px; overflow-wrap: anywhere; }}
    .status {{ color: var(--accent); font-weight: 650; }}
    .warn {{ color: var(--warn); font-weight: 650; }}
    .warning {{ margin: 10px 0 0; color: var(--warn); font-size: 13px; }}
    .muted {{ color: var(--muted); }}
    .empty {{ padding: 14px; color: var(--muted); }}
    @media (max-width: 760px) {{
      main {{ padding: 18px; }}
    }}
  </style>
</head>
<body>
<main>
  <header>
    <h1>AI Wiki Weekly Review Queue</h1>
    <p>Generated local review view for <strong>{escape(report['filters']['handle'])}</strong>. This page only shows items that need human judgment: promotion decisions, draft diagnosis, and not-helpful signals.</p>
    <div class="meta">
      <span>Period: <strong>{escape(period['period_id'])}</strong></span>
      <span>Window: <code>{escape(period['period_start'])}</code> to <code>{escape(period['period_end'])}</code></span>
      <span>Generated: <code>{escape(report['generated_at'])}</code></span>
      <span>Previous run: <code>{escape(str(last_generated))}</code></span>
    </div>
  </header>

  <section class="cards">{_summary_cards(report)}</section>

  <h2>Promotion Candidates</h2>
  <p>Candidate gate: {escape(promotion['filters']['candidate_gate'])}. These are suggestions only; shared-memory promotion still needs human approval.</p>
  <section class="panel">
    <table>
      <thead><tr><th>File</th><th>Title</th><th>Resolved Tasks</th><th>Reason</th></tr></thead>
      <tbody>{_candidate_rows(promotion['new_candidates'] + promotion['already_marked'])}</tbody>
    </table>
  </section>

  <h2>Personal Drafts Needing Diagnosis</h2>
  <p>Drafts listed here were reused but the local evidence suggests they may need rewriting, splitting, merging, or archiving.</p>
  <section class="panel">
    <table>
      <thead><tr><th>File</th><th>Title</th><th>Total</th><th>Resolved</th><th>Partial</th><th>Not Helpful</th><th>Suggestion</th></tr></thead>
      <tbody>{_needs_improvement_rows(diagnosis['needs_improvement'])}</tbody>
    </table>
  </section>

  <h2>Not Helpful Signals</h2>
  <p>Confirmed signals come from explicit logged outcomes. Candidate signals are generated or inferred hints that still need human review.</p>
  <section class="panel">
    <table>
      <thead><tr><th>File</th><th>Title</th><th>Total</th><th>Confirmed</th><th>Candidate</th><th>Partial</th><th>Reasons</th></tr></thead>
      <tbody>{_not_helpful_rows(documents)}</tbody>
    </table>
  </section>
</main>
</body>
</html>
"""


def render_weekly_report_json(report: dict[str, Any]) -> str:
    """Render weekly report JSON."""
    return json.dumps(report, indent=2, sort_keys=True) + "\n"


def _skipped_report(
    *,
    repo_wiki_dir: Path,
    handle: str,
    generated_at: str,
    period: dict[str, str],
    previous: dict[str, Any],
    state_path: Path,
) -> WeeklyReportResult:
    report = {
        "schema_version": WEEKLY_REPORT_SCHEMA_VERSION,
        "generated_at": generated_at,
        "status": "skipped",
        "filters": {"handle": handle},
        "period": period,
        "state": {"previous": previous},
        "outputs": {
            "html": previous.get("last_report_path"),
            "json": previous.get("last_json_path"),
            "latest_html": previous.get("last_latest_html_path"),
            "latest_json": previous.get("last_latest_json_path"),
            "state": _display_path(repo_wiki_dir, state_path),
        },
        "reason": "weekly report for this period already exists",
    }
    return WeeklyReportResult(
        report=report,
        html="",
        json_text=render_weekly_report_json(report),
        html_path=(
            repo_wiki_dir / previous["last_report_path"].removeprefix("ai-wiki/")
            if previous.get("last_report_path")
            else None
        ),
        json_path=(
            repo_wiki_dir / previous["last_json_path"].removeprefix("ai-wiki/")
            if previous.get("last_json_path")
            else None
        ),
        latest_html_path=(
            repo_wiki_dir / previous["last_latest_html_path"].removeprefix("ai-wiki/")
            if previous.get("last_latest_html_path")
            else None
        ),
        latest_json_path=(
            repo_wiki_dir / previous["last_latest_json_path"].removeprefix("ai-wiki/")
            if previous.get("last_latest_json_path")
            else None
        ),
        state_path=state_path,
    )


def generate_weekly_report(
    repo_wiki_dir: Path,
    *,
    handle: str,
    now: datetime | None = None,
    if_due: bool = False,
    force: bool = False,
    max_documents: int = DEFAULT_MAX_WEEKLY_DOCUMENTS,
) -> WeeklyReportResult:
    """Generate a weekly HTML review queue and JSON evidence report."""
    current = _local_now(now)
    generated_at = current.isoformat(timespec="seconds")
    period = _iso_week_period(current)
    state_file = _state_path(repo_wiki_dir, handle=handle)
    state = _load_state(state_file)
    previous = _previous_weekly_state(state, handle)
    if if_due and not force and previous and previous.get("last_period_id") == period["period_id"]:
        return _skipped_report(
            repo_wiki_dir=repo_wiki_dir,
            handle=handle,
            generated_at=generated_at,
            period=period,
            previous=previous,
            state_path=state_file,
        )

    paths = _weekly_paths(repo_wiki_dir, handle=handle, period_id=period["period_id"])
    usefulness = build_usefulness_report(
        repo_wiki_dir,
        handle=handle,
        since=period["period_start"],
        until=period["period_end"],
        generated_at=generated_at,
    )
    promotion_candidates = build_promotion_candidates_report(
        repo_wiki_dir,
        handle=handle,
        generated_at=generated_at,
    )
    eligible_documents = _load_eligible_documents(repo_wiki_dir, handle=handle)
    coverage = _build_coverage(eligible_documents, usefulness["referenced_documents"])
    diagnosis = {
        "needs_improvement": _build_needs_improvement(
            usefulness["referenced_documents"],
            handle=handle,
        ),
        "notes": [
            "Noisy-memory diagnosis is suggestion-only unless an event is logged as a confirmed signal.",
            "Use source_session_id and session_id fields to compare memory creation context with later reuse context.",
        ],
    }
    report = {
        "schema_version": WEEKLY_REPORT_SCHEMA_VERSION,
        "generated_at": generated_at,
        "status": "generated",
        "filters": {"handle": handle},
        "period": period,
        "state": {"previous": previous},
        "outputs": {
            "html": _display_path(repo_wiki_dir, paths["html"]),
            "json": _display_path(repo_wiki_dir, paths["json"]),
            "latest_html": _display_path(repo_wiki_dir, paths["latest_html"]),
            "latest_json": _display_path(repo_wiki_dir, paths["latest_json"]),
            "state": _display_path(repo_wiki_dir, state_file),
        },
        "usefulness": usefulness,
        "coverage": coverage,
        "diagnosis": diagnosis,
        "promotion_candidates": promotion_candidates,
    }
    html = render_weekly_report_html(report, max_documents=max_documents)
    json_text = render_weekly_report_json(report)
    for path, content in (
        (paths["html"], html),
        (paths["latest_html"], html),
        (paths["json"], json_text),
        (paths["latest_json"], json_text),
    ):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    state.setdefault("weekly", {})[handle] = {
        "last_generated_at": generated_at,
        "last_period_id": period["period_id"],
        "last_period_start": period["period_start"],
        "last_period_end": period["period_end"],
        "last_report_path": report["outputs"]["html"],
        "last_json_path": report["outputs"]["json"],
        "last_latest_html_path": report["outputs"]["latest_html"],
        "last_latest_json_path": report["outputs"]["latest_json"],
    }
    state["schema_version"] = REPORT_STATE_SCHEMA_VERSION
    state["updated_at"] = generated_at
    _write_state(state_file, state)

    return WeeklyReportResult(
        report=report,
        html=html,
        json_text=json_text,
        html_path=paths["html"],
        json_path=paths["json"],
        latest_html_path=paths["latest_html"],
        latest_json_path=paths["latest_json"],
        state_path=state_file,
    )
