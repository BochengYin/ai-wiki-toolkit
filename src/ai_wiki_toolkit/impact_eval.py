"""Impact-eval product reports from captured first-attempt artifacts."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import hashlib
import json
from pathlib import Path
import shlex
import shutil
import subprocess
import sys
import tomllib

from ai_wiki_toolkit.diagnostics import (
    DEFAULT_DIAGNOSTICS_MAX_ITEMS,
    build_memory_diagnostics_report,
)


CAPTURE_PHASES = {"first_pass", "final"}
PRIMARY_NO_AIWIKI_VARIANT = "no_aiwiki_workflow"
PRIMARY_AIWIKI_VARIANT = "aiwiki_ambient_memory_workflow"
SCORE_VALUES = {"success": 1.0, "partial": 0.5, "fail": 0.0}
SCORE_LABELS = tuple(SCORE_VALUES)
AI_WIKI_PREFIX = "ai-wiki/"
MANAGED_AI_WIKI_PREFIXES = ("ai-wiki/_toolkit/", "ai-wiki/metrics/")
DEFAULT_IMPACT_WORKDIR_ROOT = Path("/private/tmp") / "aiwiki_first_round"
DEFAULT_RUN_LABEL = "run_manual"
DEFAULT_SOURCE_MODE = "committed-head"
DEFAULT_WORKSPACE_LAYOUT = "neutral"
DEFAULT_PLAN_PROMPT_LEVELS = ("original",)
DEFAULT_PLAN_MODEL = "gpt-5.5"
DEFAULT_PLAN_REASONING_EFFORT = "xhigh"
DEFAULT_PLAN_EXECUTION_SURFACE = "codex-cli"
WORKFLOW_PRIMARY_VARIANTS = (
    "no_aiwiki_workflow",
    "aiwiki_ambient_memory_workflow",
)
WORKFLOW_VARIANTS = (
    "no_aiwiki_workflow",
    "aiwiki_scaffold_no_target_memory",
    "aiwiki_linked_raw_only",
    "aiwiki_linked_consolidated_only",
    "aiwiki_ambient_memory_workflow",
    "aiwiki_scaffold_no_adjacent_memory",
)
VALID_SOURCE_MODES = {"committed-head", "working-tree"}
RUN_SCORE_POLICIES = ("none", "command-exit", "rubric")
DEFAULT_RUN_SCORE_POLICY = "none"
RUBRIC_SCHEMA_VERSION = "impact-eval-rubric-v1"
RUBRIC_JUDGMENT_SCHEMA_VERSION = "impact-eval-rubric-judgment-v1"
FAMILY_DISCOVERY_SCHEMA_VERSION = "impact-eval-family-discovery-v1"
FAMILY_DETAIL_SCHEMA_VERSION = "impact-eval-family-detail-v1"
FAMILY_CANDIDATES_SCHEMA_VERSION = "impact-eval-family-candidates-v1"
FAMILY_INIT_SCHEMA_VERSION = "impact-eval-family-init-v1"
BENCHMARK_RESULT_SCHEMA_VERSION = "impact-eval-benchmark-result-v1"
CANDIDATE_QUEUE_SCHEMA_VERSION = "impact-eval-candidate-queue-v1"
CANDIDATE_DRAFT_SCHEMA_VERSION = "impact-eval-candidate-draft-v1"
CANDIDATE_PROMOTION_SCHEMA_VERSION = "impact-eval-candidate-promotion-v1"
SCHEDULE_REPORT_SCHEMA_VERSION = "impact-eval-schedule-report-v1"
SCHEDULE_RUN_SCHEMA_VERSION = "impact-eval-schedule-run-v1"
RUN_INDEX_SCHEMA_VERSION = "impact-eval-run-index-v1"


@dataclass(frozen=True)
class ImpactEvalRecord:
    slot: str
    variant: str
    prompt_level: str
    phase: str
    score_label: str | None
    first_pass_success: bool | None
    attempt: int
    human_nudges: int
    changed_files: tuple[str, ...]
    untracked_files: tuple[str, ...]
    final_message_present: bool
    notes: str
    result_path: Path

    @property
    def is_first_attempt(self) -> bool:
        return self.phase in {"first_pass", "legacy"}

    @property
    def first_attempt_success(self) -> bool | None:
        if not self.is_first_attempt:
            return None
        if self.first_pass_success is not None:
            return self.first_pass_success
        if self.score_label is None:
            return None
        return self.score_label == "success"

    @property
    def score_value(self) -> float | None:
        if self.score_label is None:
            return None
        return SCORE_VALUES.get(self.score_label)

    @property
    def project_changed_files(self) -> tuple[str, ...]:
        return tuple(path for path in self.changed_files if not _is_ai_wiki_path(path))

    @property
    def managed_wiki_changed_files(self) -> tuple[str, ...]:
        return tuple(path for path in self.changed_files if _is_managed_ai_wiki_path(path))

    @property
    def user_wiki_changed_files(self) -> tuple[str, ...]:
        return tuple(path for path in self.changed_files if _is_user_ai_wiki_path(path))

    @property
    def user_wiki_untracked_files(self) -> tuple[str, ...]:
        return tuple(path for path in self.untracked_files if _is_user_ai_wiki_path(path))


@dataclass(frozen=True)
class ImpactVariantSummary:
    variant: str
    recorded_results: int
    first_attempt_results: int
    first_attempt_successes: int
    first_attempt_failures: int
    first_attempt_pending: int
    score_successes: int
    score_partials: int
    score_failures: int
    score_pending: int
    avg_score: float | None
    avg_attempts: float | None
    avg_human_nudges: float | None
    avg_changed_files: float | None
    avg_untracked_files: float | None
    avg_project_changed_files: float | None
    avg_managed_wiki_changed_files: float | None
    avg_user_wiki_changed_files: float | None
    avg_user_wiki_untracked_files: float | None

    @property
    def known_first_attempt_results(self) -> int:
        return self.first_attempt_successes + self.first_attempt_failures

    @property
    def first_attempt_success_rate(self) -> float | None:
        known = self.known_first_attempt_results
        if known == 0:
            return None
        return self.first_attempt_successes / known


@dataclass(frozen=True)
class ImpactComparison:
    no_aiwiki: ImpactVariantSummary | None
    aiwiki: ImpactVariantSummary | None
    first_attempt_success_delta: float | None
    avg_score_delta: float | None
    outcome: str
    interpretation: str


@dataclass(frozen=True)
class ImpactEvalReport:
    run_dir: Path
    metadata: dict
    confounds: dict | None
    records: tuple[ImpactEvalRecord, ...]
    variant_summaries: tuple[ImpactVariantSummary, ...]
    primary_comparison: ImpactComparison

    @property
    def shareable_for_causal_claims(self) -> bool | None:
        if self.confounds is None:
            return None
        return bool(self.confounds.get("shareable_for_causal_claims"))


@dataclass(frozen=True)
class ImpactEvalRunSummary:
    run_dir: Path
    experiment: str
    outcome: str
    product_signal: str
    shareable_for_causal_claims: bool | None
    critical_confounds: int
    first_attempt_success_delta: float | None
    avg_score_delta: float | None
    avg_project_changed_files_delta: float | None
    avg_managed_wiki_changed_files_delta: float | None
    avg_user_wiki_changed_files_delta: float | None
    diagnostic_avg_project_changed_files: float | None
    diagnostic_avg_user_wiki_changed_files: float | None


@dataclass(frozen=True)
class ImpactEvalSummaryReport:
    run_summaries: tuple[ImpactEvalRunSummary, ...]

    @property
    def total_runs(self) -> int:
        return len(self.run_summaries)

    @property
    def shareable_runs(self) -> int:
        return sum(summary.shareable_for_causal_claims is True for summary in self.run_summaries)


def _metadata_assignment(metadata: dict) -> dict:
    assignment = metadata.get("assignment")
    return assignment if isinstance(assignment, dict) else {}


def _metadata_list(metadata: dict, key: str) -> tuple[str, ...]:
    value = metadata.get(key)
    if not isinstance(value, list):
        return ()
    return tuple(str(item) for item in value if str(item))


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _read_json_or_empty(path: Path) -> dict:
    if not path.exists():
        return {}
    return _read_json(path)


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def _read_run_metadata(run_dir: Path) -> dict:
    metadata_path = run_dir / "metadata.json"
    if not metadata_path.exists():
        raise FileNotFoundError(f"metadata.json not found under: {run_dir}")
    return _read_json(metadata_path)


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _timestamp_slug(now: datetime | None = None) -> str:
    return (now or datetime.now()).strftime("%Y%m%d-%H%M%S")


def _resolve_eval_repo_root(repo_root: Path | None = None) -> Path:
    if repo_root is not None:
        resolved = repo_root.resolve()
        if not (resolved / "evals" / "impact" / "families").exists():
            raise FileNotFoundError(
                "Impact eval family specs were not found under: "
                f"{resolved / 'evals' / 'impact' / 'families'}"
            )
        return resolved
    current = Path.cwd().resolve()
    for candidate in (current, *current.parents):
        if (candidate / "evals" / "impact" / "families").exists():
            return candidate
    raise FileNotFoundError(
        "Could not find evals/impact/families. Run from the repository root or pass --repo-root."
    )


def _read_family_spec(repo_root: Path, family: str) -> dict:
    spec_path = repo_root / "evals" / "impact" / "families" / family / "spec.toml"
    if not spec_path.exists():
        raise FileNotFoundError(f"Impact eval family spec not found: {spec_path}")
    payload = tomllib.loads(spec_path.read_text(encoding="utf-8"))
    payload["_spec_path"] = str(spec_path)
    return payload


def _csv(values: tuple[str, ...]) -> str:
    return ",".join(values)


def _command(*parts: object) -> list[str]:
    return [str(part) for part in parts]


def _command_text(command: list[str]) -> str:
    return shlex.join(command)


def _score_label(score: dict | None) -> str | None:
    if not score:
        return None
    label = score.get("label")
    return label if isinstance(label, str) else None


def _string_tuple(value: object) -> tuple[str, ...]:
    if not isinstance(value, list):
        return ()
    return tuple(str(item) for item in value if str(item))


def _int_or_zero(value: object) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


def _is_ai_wiki_path(path: str) -> bool:
    return path == "ai-wiki" or path.startswith(AI_WIKI_PREFIX)


def _is_managed_ai_wiki_path(path: str) -> bool:
    return any(path.startswith(prefix) for prefix in MANAGED_AI_WIKI_PREFIXES)


def _is_user_ai_wiki_path(path: str) -> bool:
    return _is_ai_wiki_path(path) and not _is_managed_ai_wiki_path(path)


def _avg_int(values: list[int]) -> float | None:
    return sum(values) / len(values) if values else None


def _avg_float(values: list[float]) -> float | None:
    return sum(values) / len(values) if values else None


def _assignment_variant_map(metadata: dict) -> dict[str, str]:
    assignment = _metadata_assignment(metadata)
    result: dict[str, str] = {}
    for item in assignment.get("slots", []):
        if not isinstance(item, dict):
            continue
        slot = item.get("slot")
        if isinstance(slot, str):
            variant = item.get("variant")
            result[slot] = variant if isinstance(variant, str) else slot
    return result


def _assignment_workspace_map(metadata: dict) -> dict[str, str]:
    assignment = _metadata_assignment(metadata)
    result: dict[str, str] = {}
    for item in assignment.get("slots", []):
        if not isinstance(item, dict):
            continue
        slot = item.get("slot")
        workspace = item.get("workspace")
        if isinstance(slot, str) and isinstance(workspace, str) and workspace:
            result[slot] = workspace
    return result


def _metadata_slots(metadata: dict) -> tuple[str, ...]:
    variants = _metadata_list(metadata, "variants")
    if variants:
        return variants
    return tuple(_assignment_variant_map(metadata))


def _metadata_prompt_level(metadata: dict) -> str:
    prompt_levels = _metadata_list(metadata, "prompt_levels")
    return prompt_levels[0] if prompt_levels else "original"


def _result_paths(run_dir: Path) -> list[Path]:
    paths = list(sorted(run_dir.glob("*/*/result.json")))
    paths.extend(
        path
        for path in sorted(run_dir.glob("*/*/*/result.json"))
        if path.parent.name in CAPTURE_PHASES
    )
    return paths


def _record_from_path(run_dir: Path, metadata: dict, result_path: Path) -> ImpactEvalRecord:
    result = _read_json(result_path)
    slot_dir = result_path.parent
    if slot_dir.name in CAPTURE_PHASES:
        prompt_level = slot_dir.parent.name
        slot = slot_dir.parent.parent.name
        phase = slot_dir.name
    else:
        prompt_level = slot_dir.name
        slot = slot_dir.parent.name
        phase = str(result.get("phase", "legacy"))

    score_path = run_dir / slot / prompt_level / "score.json"
    score = _read_json(score_path) if score_path.exists() else None
    assignment_map = _assignment_variant_map(metadata)
    variant = result.get("variant")
    if not isinstance(variant, str) or not variant:
        variant = assignment_map.get(slot, slot)

    changed_files = _string_tuple(result.get("changed_files"))
    untracked_files = _string_tuple(result.get("untracked_files"))
    first_pass_success = result.get("first_pass_success")
    if not isinstance(first_pass_success, bool):
        first_pass_success = None
    return ImpactEvalRecord(
        slot=slot,
        variant=variant,
        prompt_level=prompt_level,
        phase=phase,
        score_label=_score_label(score),
        first_pass_success=first_pass_success,
        attempt=_int_or_zero(result.get("attempt")),
        human_nudges=_int_or_zero(result.get("human_nudges")),
        changed_files=changed_files,
        untracked_files=untracked_files,
        final_message_present=(slot_dir / "final_message.md").exists(),
        notes=str(result.get("notes", "")),
        result_path=result_path,
    )


def collect_impact_eval_records(run_dir: Path, metadata: dict) -> tuple[ImpactEvalRecord, ...]:
    return tuple(_record_from_path(run_dir, metadata, path) for path in _result_paths(run_dir))


def _run_relative_path(run_dir: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(run_dir.resolve()).as_posix()
    except ValueError:
        return str(path)


def _artifact_path(run_dir: Path, path: Path) -> str | None:
    return _run_relative_path(run_dir, path) if path.exists() else None


def _record_artifacts(run_dir: Path, record: ImpactEvalRecord) -> dict[str, str]:
    result_dir = record.result_path.parent
    score_path = run_dir / record.slot / record.prompt_level / "score.json"
    candidates = {
        "result": record.result_path,
        "score": score_path,
        "final_message": result_dir / "final_message.md",
        "workspace_diff": result_dir / "workspace_diff.patch",
        "workspace_diff_stat": result_dir / "workspace_diff_stat.txt",
        "workspace_status": result_dir / "workspace_status.txt",
        "workspace_head": result_dir / "workspace_head.txt",
        "command_result": result_dir / "command_result.json",
    }
    return {
        name: path_value
        for name, path_value in (
            (name, _artifact_path(run_dir, path)) for name, path in candidates.items()
        )
        if path_value is not None
    }


def _session_export_manifest_path(metadata: dict) -> Path | None:
    workspace_root = metadata.get("workspace_root")
    if not isinstance(workspace_root, str) or not workspace_root:
        return None
    return Path(workspace_root) / "codex_sessions" / "manifest.json"


def _session_transcript_path(metadata: dict, slot: str) -> str | None:
    workspace_root = metadata.get("workspace_root")
    if not isinstance(workspace_root, str) or not workspace_root:
        return None
    transcript = Path(workspace_root) / "codex_sessions" / slot / "visible_transcript.md"
    return str(transcript) if transcript.exists() else None


def _prompt_manifest(metadata: dict) -> tuple[dict, ...]:
    prompt_hashes = metadata.get("prompt_hashes")
    if not isinstance(prompt_hashes, dict):
        prompt_hashes = {}
    prompt_levels = _metadata_list(metadata, "prompt_levels")
    return tuple(
        {
            "level": level,
            "sha256": str(prompt_hashes.get(level, "")) or None,
        }
        for level in prompt_levels
    )


def _slot_manifest(
    *,
    run_dir: Path,
    metadata: dict,
    records: tuple[ImpactEvalRecord, ...],
) -> tuple[dict, ...]:
    assignment_map = _assignment_variant_map(metadata)
    workspace_map = _assignment_workspace_map(metadata)
    record_slots = {record.slot for record in records}
    metadata_slots = _metadata_list(metadata, "variants")
    slots = tuple(dict.fromkeys((*metadata_slots, *assignment_map.keys(), *sorted(record_slots))))

    by_slot: dict[str, list[ImpactEvalRecord]] = {}
    for record in records:
        by_slot.setdefault(record.slot, []).append(record)

    result: list[dict] = []
    for slot in slots:
        slot_records = sorted(
            by_slot.get(slot, []),
            key=lambda record: (record.prompt_level, record.phase, str(record.result_path)),
        )
        variant = assignment_map.get(slot)
        if variant is None and slot_records:
            variant = slot_records[0].variant
        prompt_levels: dict[str, list[dict]] = {}
        for record in slot_records:
            prompt_levels.setdefault(record.prompt_level, []).append(
                {
                    "phase": record.phase,
                    "score_label": record.score_label,
                    "first_attempt_success": record.first_attempt_success,
                    "attempt": record.attempt,
                    "human_nudges": record.human_nudges,
                    "changed_file_count": len(record.changed_files),
                    "untracked_file_count": len(record.untracked_files),
                    "artifacts": _record_artifacts(run_dir, record),
                }
            )
        result.append(
            {
                "slot": slot,
                "variant": variant or slot,
                "workspace": workspace_map.get(slot),
                "visible_transcript": _session_transcript_path(metadata, slot),
                "prompt_levels": [
                    {"level": level, "captures": captures}
                    for level, captures in sorted(prompt_levels.items())
                ],
            }
        )
    return tuple(result)


def generate_impact_eval_manifest(run_dir: Path) -> dict:
    report = generate_impact_eval_report(run_dir)
    metadata = report.metadata
    assignment = _metadata_assignment(metadata)
    session_manifest = _session_export_manifest_path(metadata)
    confounds_path = report.run_dir / "confounds.json"
    prompts = list(_prompt_manifest(metadata))
    slots = list(
        _slot_manifest(
            run_dir=report.run_dir,
            metadata=metadata,
            records=report.records,
        )
    )
    return {
        "schema_version": "impact-eval-run-manifest-v1",
        "run_dir": str(report.run_dir),
        "experiment": metadata.get("experiment", "unknown"),
        "created_at": metadata.get("created_at"),
        "baseline_ref": assignment.get("baseline_ref") or metadata.get("baseline_ref"),
        "workspace_root": metadata.get("workspace_root"),
        "workspace_layout": assignment.get("workspace_layout"),
        "model": metadata.get("model_family"),
        "reasoning_effort": metadata.get("reasoning_effort"),
        "execution_surface": metadata.get("execution_surface"),
        "agent_command": {
            "surface": metadata.get("execution_surface"),
            "command_family": (
                "codex exec"
                if metadata.get("execution_surface") == "codex-cli"
                else metadata.get("execution_surface")
            ),
            "model": metadata.get("model_family"),
            "reasoning_effort": metadata.get("reasoning_effort"),
        },
        "primary_comparison": _metadata_list(metadata, "primary_comparison"),
        "diagnostic_variants": _metadata_list(metadata, "diagnostic_variants"),
        "prompts": prompts,
        "slots": slots,
        "session_export": {
            "manifest": str(session_manifest) if session_manifest is not None else None,
            "present": bool(session_manifest and session_manifest.exists()),
        },
        "confounds": {
            "path": _artifact_path(report.run_dir, confounds_path),
            "present": report.confounds is not None,
            "shareable_for_causal_claims": report.shareable_for_causal_claims,
            "critical_confounds": _critical_confound_count(report),
        },
        "artifact_summary": {
            "records": len(report.records),
            "first_attempt_records": sum(record.is_first_attempt for record in report.records),
            "variant_count": len(report.variant_summaries),
            "slot_count": len({slot["slot"] for slot in slots}),
        },
    }


def summarize_variants(records: tuple[ImpactEvalRecord, ...]) -> tuple[ImpactVariantSummary, ...]:
    by_variant: dict[str, list[ImpactEvalRecord]] = {}
    for record in records:
        by_variant.setdefault(record.variant, []).append(record)

    summaries: list[ImpactVariantSummary] = []
    for variant, variant_records in sorted(by_variant.items()):
        first_attempt_records = [record for record in variant_records if record.is_first_attempt]
        successes = sum(record.first_attempt_success is True for record in first_attempt_records)
        failures = sum(record.first_attempt_success is False for record in first_attempt_records)
        pending = sum(record.first_attempt_success is None for record in first_attempt_records)
        score_values = [
            record.score_value
            for record in first_attempt_records
            if record.score_value is not None
        ]
        attempts = [record.attempt for record in first_attempt_records if record.attempt > 0]
        nudges = [record.human_nudges for record in first_attempt_records]
        changed_files = [len(record.changed_files) for record in first_attempt_records]
        untracked_files = [len(record.untracked_files) for record in first_attempt_records]
        project_changed_files = [
            len(record.project_changed_files) for record in first_attempt_records
        ]
        managed_wiki_changed_files = [
            len(record.managed_wiki_changed_files) for record in first_attempt_records
        ]
        user_wiki_changed_files = [
            len(record.user_wiki_changed_files) for record in first_attempt_records
        ]
        user_wiki_untracked_files = [
            len(record.user_wiki_untracked_files) for record in first_attempt_records
        ]
        labels = [record.score_label for record in first_attempt_records]
        summaries.append(
            ImpactVariantSummary(
                variant=variant,
                recorded_results=len(variant_records),
                first_attempt_results=len(first_attempt_records),
                first_attempt_successes=successes,
                first_attempt_failures=failures,
                first_attempt_pending=pending,
                score_successes=sum(label == "success" for label in labels),
                score_partials=sum(label == "partial" for label in labels),
                score_failures=sum(label == "fail" for label in labels),
                score_pending=sum(label is None for label in labels),
                avg_score=(sum(score_values) / len(score_values) if score_values else None),
                avg_attempts=_avg_int(attempts),
                avg_human_nudges=_avg_int(nudges),
                avg_changed_files=_avg_int(changed_files),
                avg_untracked_files=_avg_int(untracked_files),
                avg_project_changed_files=_avg_int(project_changed_files),
                avg_managed_wiki_changed_files=_avg_int(managed_wiki_changed_files),
                avg_user_wiki_changed_files=_avg_int(user_wiki_changed_files),
                avg_user_wiki_untracked_files=_avg_int(user_wiki_untracked_files),
            )
        )
    return tuple(summaries)


def _find_summary(
    summaries: tuple[ImpactVariantSummary, ...],
    variant: str,
) -> ImpactVariantSummary | None:
    for summary in summaries:
        if summary.variant == variant:
            return summary
    return None


def compare_primary_variants(
    summaries: tuple[ImpactVariantSummary, ...],
    metadata: dict,
) -> ImpactComparison:
    primary_variants = metadata.get("primary_comparison")
    if not isinstance(primary_variants, list) or not primary_variants:
        primary_variants = [PRIMARY_NO_AIWIKI_VARIANT, PRIMARY_AIWIKI_VARIANT]

    no_variant = PRIMARY_NO_AIWIKI_VARIANT
    aiwiki_variant = PRIMARY_AIWIKI_VARIANT
    if len(primary_variants) >= 2:
        no_variant = str(primary_variants[0])
        aiwiki_variant = str(primary_variants[1])

    no_aiwiki = _find_summary(summaries, no_variant)
    aiwiki = _find_summary(summaries, aiwiki_variant)
    if no_aiwiki is None or aiwiki is None:
        return ImpactComparison(
            no_aiwiki=no_aiwiki,
            aiwiki=aiwiki,
            first_attempt_success_delta=None,
            avg_score_delta=None,
            outcome="incomplete",
            interpretation="Primary comparison is incomplete because one or both variants have no recorded first-attempt result.",
        )

    no_rate = no_aiwiki.first_attempt_success_rate
    aiwiki_rate = aiwiki.first_attempt_success_rate
    success_delta = None if no_rate is None or aiwiki_rate is None else aiwiki_rate - no_rate
    score_delta = (
        None
        if no_aiwiki.avg_score is None or aiwiki.avg_score is None
        else aiwiki.avg_score - no_aiwiki.avg_score
    )

    if success_delta is None and score_delta is None:
        outcome = "incomplete"
        interpretation = "Primary comparison has recorded artifacts but no known first-attempt success or score labels yet."
    elif (success_delta is not None and success_delta > 0) or (
        success_delta is None and score_delta is not None and score_delta > 0
    ):
        outcome = "positive_signal"
        interpretation = "Ambient AI wiki improved first-attempt outcome versus the no-AI-wiki workflow."
    elif (success_delta is not None and success_delta < 0) or (
        success_delta is None and score_delta is not None and score_delta < 0
    ):
        outcome = "regression_signal"
        interpretation = "Ambient AI wiki underperformed the no-AI-wiki workflow on first-attempt outcome."
    else:
        outcome = "neutral_signal"
        interpretation = "Ambient AI wiki matched the no-AI-wiki workflow on available first-attempt metrics."

    return ImpactComparison(
        no_aiwiki=no_aiwiki,
        aiwiki=aiwiki,
        first_attempt_success_delta=success_delta,
        avg_score_delta=score_delta,
        outcome=outcome,
        interpretation=interpretation,
    )


def generate_impact_eval_report(run_dir: Path) -> ImpactEvalReport:
    resolved_run_dir = run_dir.resolve()
    if not resolved_run_dir.exists():
        raise FileNotFoundError(f"Run directory does not exist: {resolved_run_dir}")
    metadata_path = resolved_run_dir / "metadata.json"
    if not metadata_path.exists():
        raise FileNotFoundError(f"metadata.json not found under: {resolved_run_dir}")
    metadata = _read_json(metadata_path)
    confounds_path = resolved_run_dir / "confounds.json"
    confounds = _read_json(confounds_path) if confounds_path.exists() else None
    records = collect_impact_eval_records(resolved_run_dir, metadata)
    summaries = summarize_variants(records)
    return ImpactEvalReport(
        run_dir=resolved_run_dir,
        metadata=metadata,
        confounds=confounds,
        records=records,
        variant_summaries=summaries,
        primary_comparison=compare_primary_variants(summaries, metadata),
    )


def _summary_value_delta(
    no_aiwiki: ImpactVariantSummary | None,
    aiwiki: ImpactVariantSummary | None,
    field_name: str,
) -> float | None:
    if no_aiwiki is None or aiwiki is None:
        return None
    no_value = getattr(no_aiwiki, field_name)
    aiwiki_value = getattr(aiwiki, field_name)
    if no_value is None or aiwiki_value is None:
        return None
    return aiwiki_value - no_value


def _diagnostic_variant_names(report: ImpactEvalReport) -> tuple[str, ...]:
    diagnostic_variants = report.metadata.get("diagnostic_variants")
    if isinstance(diagnostic_variants, list):
        return tuple(str(item) for item in diagnostic_variants if str(item))
    primary_variants = report.metadata.get("primary_comparison")
    if not isinstance(primary_variants, list):
        primary_variants = [PRIMARY_NO_AIWIKI_VARIANT, PRIMARY_AIWIKI_VARIANT]
    primary = {str(item) for item in primary_variants}
    return tuple(
        summary.variant for summary in report.variant_summaries if summary.variant not in primary
    )


def _diagnostic_avg(report: ImpactEvalReport, field_name: str) -> float | None:
    diagnostic_variants = set(_diagnostic_variant_names(report))
    values = [
        getattr(summary, field_name)
        for summary in report.variant_summaries
        if summary.variant in diagnostic_variants and getattr(summary, field_name) is not None
    ]
    return _avg_float(values)


def _critical_confound_count(report: ImpactEvalReport) -> int:
    if report.confounds is None:
        return 0
    critical_confounds = report.confounds.get("critical_confounds", [])
    if not isinstance(critical_confounds, list):
        return 0
    return len(critical_confounds)


def _product_signal(
    report: ImpactEvalReport,
    *,
    project_changed_files_delta: float | None,
    user_wiki_changed_files_delta: float | None,
    diagnostic_user_wiki_changed_files: float | None,
) -> str:
    outcome = report.primary_comparison.outcome
    if outcome == "positive_signal":
        return "success_uplift"
    if outcome == "regression_signal":
        return "success_regression"
    if outcome == "incomplete":
        return "incomplete"
    if (project_changed_files_delta is not None and project_changed_files_delta < 0) or (
        user_wiki_changed_files_delta is not None and user_wiki_changed_files_delta < 0
    ):
        return "quality_uplift"
    if diagnostic_user_wiki_changed_files is not None and diagnostic_user_wiki_changed_files > 0:
        return "diagnostic_quality_signal"
    return "neutral"


def summarize_impact_eval_report(report: ImpactEvalReport) -> ImpactEvalRunSummary:
    comparison = report.primary_comparison
    project_delta = _summary_value_delta(
        comparison.no_aiwiki,
        comparison.aiwiki,
        "avg_project_changed_files",
    )
    managed_wiki_delta = _summary_value_delta(
        comparison.no_aiwiki,
        comparison.aiwiki,
        "avg_managed_wiki_changed_files",
    )
    user_wiki_delta = _summary_value_delta(
        comparison.no_aiwiki,
        comparison.aiwiki,
        "avg_user_wiki_changed_files",
    )
    diagnostic_project = _diagnostic_avg(report, "avg_project_changed_files")
    diagnostic_user_wiki = _diagnostic_avg(report, "avg_user_wiki_changed_files")
    return ImpactEvalRunSummary(
        run_dir=report.run_dir,
        experiment=str(report.metadata.get("experiment", "unknown")),
        outcome=comparison.outcome,
        product_signal=_product_signal(
            report,
            project_changed_files_delta=project_delta,
            user_wiki_changed_files_delta=user_wiki_delta,
            diagnostic_user_wiki_changed_files=diagnostic_user_wiki,
        ),
        shareable_for_causal_claims=report.shareable_for_causal_claims,
        critical_confounds=_critical_confound_count(report),
        first_attempt_success_delta=comparison.first_attempt_success_delta,
        avg_score_delta=comparison.avg_score_delta,
        avg_project_changed_files_delta=project_delta,
        avg_managed_wiki_changed_files_delta=managed_wiki_delta,
        avg_user_wiki_changed_files_delta=user_wiki_delta,
        diagnostic_avg_project_changed_files=diagnostic_project,
        diagnostic_avg_user_wiki_changed_files=diagnostic_user_wiki,
    )


def generate_impact_eval_summary(run_dirs: list[Path] | tuple[Path, ...]) -> ImpactEvalSummaryReport:
    summaries = [
        summarize_impact_eval_report(generate_impact_eval_report(run_dir))
        for run_dir in run_dirs
    ]
    return ImpactEvalSummaryReport(run_summaries=tuple(summaries))


def load_impact_eval_run_dirs_from_file(path: Path) -> tuple[Path, ...]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(payload, list):
        values = payload
    elif isinstance(payload, dict):
        if isinstance(payload.get("run_dirs"), list):
            values = payload["run_dirs"]
        elif isinstance(payload.get("runs"), list):
            values = [
                item.get("run_dir") if isinstance(item, dict) else item
                for item in payload["runs"]
            ]
        else:
            raise ValueError("Runs file must contain `run_dirs` or `runs`.")
    else:
        raise ValueError("Runs file must be a JSON list or object.")

    run_dirs: list[Path] = []
    for value in values:
        if not isinstance(value, str) or not value.strip():
            raise ValueError("Run directory entries must be non-empty strings.")
        run_path = Path(value)
        if not run_path.is_absolute():
            run_path = path.parent / run_path
        run_dirs.append(run_path)
    return tuple(run_dirs)


def _family_specs_root(repo_root: Path) -> Path:
    return repo_root / "evals" / "impact" / "families"


def _prompt_root(repo_root: Path, prompt_family: str) -> Path:
    return repo_root / "evals" / "impact" / "prompts" / prompt_family


def _rubric_path(repo_root: Path, family: str) -> Path:
    return repo_root / "evals" / "impact" / "rubrics" / f"{family}.json"


def _spec_list(spec: dict, key: str) -> tuple[str, ...]:
    value = spec.get(key)
    if not isinstance(value, list):
        return ()
    return tuple(str(item) for item in value if str(item))


def _spec_table_count(spec: dict, key: str) -> int:
    value = spec.get(key)
    return len(value) if isinstance(value, list) else 0


def _prompt_levels(repo_root: Path, prompt_family: str) -> tuple[str, ...]:
    root = _prompt_root(repo_root, prompt_family)
    if not root.exists():
        return ()
    return tuple(
        path.stem
        for path in sorted(root.glob("*.md"))
        if path.stem.lower() != "task"
    )


def _family_name_from_doc_id(doc_id: str) -> str:
    cleaned = "".join(
        char.lower() if char.isalnum() else "_" for char in doc_id.replace(".md", "")
    )
    while "__" in cleaned:
        cleaned = cleaned.replace("__", "_")
    return cleaned.strip("_") or "new_family"


def _period_id(now: datetime | None = None) -> str:
    current = now or datetime.now()
    year, week, _ = current.isocalendar()
    return f"{year}-W{week:02d}"


def _now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def _repo_wiki_dir(repo_root: Path, repo_wiki_dir: Path | None = None) -> Path:
    return repo_wiki_dir.resolve() if repo_wiki_dir is not None else repo_root / "ai-wiki"


def _managed_evals_root(repo_root: Path, repo_wiki_dir: Path | None = None) -> Path:
    return _repo_wiki_dir(repo_root, repo_wiki_dir) / "_toolkit" / "evals"


def _candidate_queue_paths(repo_root: Path, repo_wiki_dir: Path | None = None) -> dict[str, Path]:
    root = _managed_evals_root(repo_root, repo_wiki_dir) / "candidates"
    return {
        "root": root,
        "latest_json": root / "latest.json",
        "latest_markdown": root / "latest.md",
        "state": root / "state.json",
    }


def _candidate_draft_dir(
    repo_root: Path,
    candidate_id: str,
    repo_wiki_dir: Path | None = None,
) -> Path:
    return _managed_evals_root(repo_root, repo_wiki_dir) / "drafts" / candidate_id


def _run_index_path(repo_root: Path, repo_wiki_dir: Path | None = None) -> Path:
    return _managed_evals_root(repo_root, repo_wiki_dir) / "runs" / "index.json"


def _schedule_state_path(repo_root: Path, repo_wiki_dir: Path | None = None) -> Path:
    return _managed_evals_root(repo_root, repo_wiki_dir) / "schedule" / "state.json"


def _schedule_report_paths(
    repo_root: Path,
    period_id: str,
    repo_wiki_dir: Path | None = None,
) -> dict[str, Path]:
    root = _managed_evals_root(repo_root, repo_wiki_dir) / "reports"
    period_dir = root / period_id
    return {
        "root": root,
        "period_dir": period_dir,
        "json": period_dir / "report.json",
        "markdown": period_dir / "report.md",
        "latest_json": root / "latest.json",
        "latest_markdown": root / "latest.md",
    }


def _doc_id_to_aiwiki_path(doc_id: str) -> str:
    normalized = doc_id[:-3] if doc_id.endswith(".md") else doc_id
    if normalized.startswith("ai-wiki/"):
        return normalized if normalized.endswith(".md") else f"{normalized}.md"
    return f"ai-wiki/{normalized}.md"


def _family_referenced_docs(spec: dict) -> tuple[str, ...]:
    docs = [
        *_spec_list(spec, "raw_docs"),
        *_spec_list(spec, "consolidated_docs"),
    ]
    for table_name in ("raw_overlays", "consolidated_overlays"):
        value = spec.get(table_name)
        if not isinstance(value, list):
            continue
        for item in value:
            if isinstance(item, dict) and isinstance(item.get("destination"), str):
                docs.append(str(item["destination"]))
    return tuple(docs)


def _family_next_commands(family: str, *, rubric_present: bool) -> dict:
    benchmark_command = [
        "aiwiki-toolkit",
        "eval",
        "impact",
        "benchmark",
        "--family",
        family,
    ]
    if rubric_present:
        benchmark_command.extend(["--score-policy", "rubric"])
    return {
        "plan": ["aiwiki-toolkit", "eval", "impact", "plan", "--family", family],
        "prepare": ["aiwiki-toolkit", "eval", "impact", "prepare", "--family", family],
        "benchmark": benchmark_command,
    }


def _impact_eval_family_summary(repo_root: Path, family: str) -> dict:
    spec = _read_family_spec(repo_root, family)
    name = str(spec.get("name") or family)
    prompt_family = str(spec.get("prompt_family") or name)
    prompt_root = _prompt_root(repo_root, prompt_family)
    prompt_levels = _prompt_levels(repo_root, prompt_family)
    original_prompt = prompt_root / "original.md"
    rubric_path = _rubric_path(repo_root, name)
    missing: list[str] = []
    if not original_prompt.exists():
        missing.append("prompt:original")
    status = "runnable" if not missing else "not_ready"
    raw_docs = _spec_list(spec, "raw_docs")
    consolidated_docs = _spec_list(spec, "consolidated_docs")
    raw_overlays = _spec_table_count(spec, "raw_overlays")
    consolidated_overlays = _spec_table_count(spec, "consolidated_overlays")
    return {
        "name": name,
        "status": status,
        "missing": missing,
        "spec_path": spec["_spec_path"],
        "prompt_family": prompt_family,
        "prompt_root": str(prompt_root),
        "prompt_levels": list(prompt_levels),
        "prompt_present": original_prompt.exists(),
        "rubric_path": str(rubric_path),
        "rubric_present": rubric_path.exists(),
        "historical_issue": str(spec.get("historical_issue") or ""),
        "baseline_ref": str(spec.get("baseline_ref") or ""),
        "memory_fixtures": {
            "raw_docs": len(raw_docs),
            "raw_overlays": raw_overlays,
            "consolidated_docs": len(consolidated_docs),
            "consolidated_overlays": consolidated_overlays,
            "ambient_exclude_paths": len(_spec_list(spec, "ambient_exclude_paths")),
            "strict_scaffold_exclude_paths": len(
                _spec_list(spec, "strict_scaffold_exclude_paths")
            ),
        },
        "next_commands": _family_next_commands(name, rubric_present=rubric_path.exists()),
    }


def discover_impact_eval_families(*, repo_root: Path | None = None) -> dict:
    resolved_repo_root = _resolve_eval_repo_root(repo_root)
    families_root = _family_specs_root(resolved_repo_root)
    families = [
        _impact_eval_family_summary(resolved_repo_root, spec_path.parent.name)
        for spec_path in sorted(families_root.glob("*/spec.toml"))
    ]
    return {
        "schema_version": FAMILY_DISCOVERY_SCHEMA_VERSION,
        "repo_root": str(resolved_repo_root),
        "families_root": str(families_root),
        "family_count": len(families),
        "runnable_count": sum(family["status"] == "runnable" for family in families),
        "families": families,
    }


def show_impact_eval_family(*, family: str, repo_root: Path | None = None) -> dict:
    resolved_repo_root = _resolve_eval_repo_root(repo_root)
    spec = _read_family_spec(resolved_repo_root, family)
    summary = _impact_eval_family_summary(resolved_repo_root, family)
    prompt_family = str(summary["prompt_family"])
    prompt_root = _prompt_root(resolved_repo_root, prompt_family)
    prompts = [
        {
            "level": path.stem,
            "path": str(path),
            "sha256": _sha256_text(path.read_text(encoding="utf-8")),
        }
        for path in sorted(prompt_root.glob("*.md"))
        if path.stem.lower() != "task"
    ]
    detail = {
        "schema_version": FAMILY_DETAIL_SCHEMA_VERSION,
        "repo_root": str(resolved_repo_root),
        "family": summary,
        "raw_docs": list(_spec_list(spec, "raw_docs")),
        "consolidated_docs": list(_spec_list(spec, "consolidated_docs")),
        "ambient_exclude_paths": list(_spec_list(spec, "ambient_exclude_paths")),
        "strict_scaffold_exclude_paths": list(
            _spec_list(spec, "strict_scaffold_exclude_paths")
        ),
        "raw_overlays": spec.get("raw_overlays", [])
        if isinstance(spec.get("raw_overlays"), list)
        else [],
        "consolidated_overlays": spec.get("consolidated_overlays", [])
        if isinstance(spec.get("consolidated_overlays"), list)
        else [],
        "prompts": prompts,
    }
    return detail


def _registered_family_by_doc(repo_root: Path) -> dict[str, str]:
    result: dict[str, str] = {}
    families_root = _family_specs_root(repo_root)
    for spec_path in sorted(families_root.glob("*/spec.toml")):
        spec = _read_family_spec(repo_root, spec_path.parent.name)
        family = str(spec.get("name") or spec_path.parent.name)
        for path in _family_referenced_docs(spec):
            normalized = path[:-3] if path.endswith(".md") else path
            if normalized.startswith("ai-wiki/"):
                normalized = normalized[len("ai-wiki/") :]
            result[normalized] = family
    return result


def _candidate_readiness(candidate: dict, registered_family: str | None) -> dict:
    doc_kind = str(candidate.get("doc_kind") or "")
    doc_id = str(candidate.get("doc_id") or "")
    concrete_memory_kind = doc_kind in {
        "feature",
        "features",
        "problem",
        "problems",
        "review-pattern",
        "review-patterns",
        "people",
        "person",
        "draft",
    } or "/drafts/" in doc_id
    source_incident_present = bool(
        candidate.get("source_task_ids")
        or candidate.get("source_session_ids")
        or candidate.get("tasks")
    )
    present = ["replayable_memory_evidence"]
    missing: list[str] = []
    if source_incident_present:
        present.append("source_incident")
    else:
        missing.append("source_incident")
    if concrete_memory_kind or registered_family:
        present.append("concrete_memory_doc")
    else:
        missing.append("concrete_memory_doc")
    if registered_family:
        present.extend(["baseline_ref", "prompt", "rubric_or_manual_scoring"])
    else:
        missing.extend(["baseline_ref", "prompt", "rubric"])
    status = "runnable" if registered_family else "candidate"
    if not source_incident_present or not concrete_memory_kind:
        status = "not_ready"
    return {
        "status": status,
        "present": present,
        "missing": missing,
    }


def discover_impact_eval_family_candidates(
    *,
    repo_root: Path | None = None,
    repo_wiki_dir: Path | None = None,
    handle: str | None = None,
    since: str | None = None,
    max_items: int = DEFAULT_DIAGNOSTICS_MAX_ITEMS,
    include_not_ready: bool = False,
) -> dict:
    resolved_repo_root = _resolve_eval_repo_root(repo_root)
    selected_repo_wiki_dir = (
        repo_wiki_dir.resolve() if repo_wiki_dir is not None else resolved_repo_root / "ai-wiki"
    )
    diagnostics = build_memory_diagnostics_report(
        selected_repo_wiki_dir,
        handle=handle,
        since=since,
        focus="trial-error",
        max_items=max_items,
    )
    section = diagnostics["trial_error_reduction"]
    registered = _registered_family_by_doc(resolved_repo_root)
    raw_candidates = list(section.get("replay_candidates", []))
    if include_not_ready:
        raw_candidates.extend(section.get("missed_or_repeated_issue_signals", []))

    candidates: list[dict] = []
    for item in raw_candidates:
        if not isinstance(item, dict):
            continue
        doc_id = str(item.get("doc_id") or "")
        task_id = str(item.get("task_id") or "")
        identity = doc_id or task_id
        if not identity:
            continue
        registered_family = registered.get(doc_id) if doc_id else None
        readiness = _candidate_readiness(item, registered_family)
        if readiness["status"] == "not_ready" and not include_not_ready:
            continue
        suggested_family = _family_name_from_doc_id(identity)
        candidates.append(
            {
                "candidate_id": suggested_family,
                "status": readiness["status"],
                "doc_id": doc_id or None,
                "task_id": task_id or None,
                "title": item.get("title"),
                "path": item.get("path"),
                "suggested_family": suggested_family,
                "registered_family": registered_family,
                "readiness": readiness,
                "evidence": {
                    "reason": item.get("reason"),
                    "trial_error_effects": item.get("trial_error_effects", {}),
                    "trial_error_signal_count": item.get("trial_error_signal_count", 0),
                    "resolved_events": item.get("resolved_events", 0),
                    "total_events": item.get("total_events", 0),
                    "tasks": item.get("tasks", []),
                    "source_task_ids": item.get("source_task_ids", []),
                    "source_session_ids": item.get("source_session_ids", []),
                    "source_incident_timing": item.get(
                        "source_incident_timing",
                        {
                            "active_seconds": 0,
                            "active_minutes": 0.0,
                            "evidence_count": 0,
                            "event_count": 0,
                            "sources": [],
                            "status": "not_recorded",
                        },
                    ),
                },
                "next_commands": {
                    "init": [
                        "aiwiki-toolkit",
                        "eval",
                        "impact",
                        "family",
                        "init",
                        "--name",
                        suggested_family,
                        "--from-candidate",
                        identity,
                        "--baseline-ref",
                        "<baseline-ref>",
                    ],
                    "show_registered": [
                        "aiwiki-toolkit",
                        "eval",
                        "impact",
                        "family",
                        "show",
                        registered_family or "<family>",
                    ],
                },
            }
        )
    return {
        "schema_version": FAMILY_CANDIDATES_SCHEMA_VERSION,
        "repo_root": str(resolved_repo_root),
        "repo_wiki_dir": str(selected_repo_wiki_dir),
        "filters": {
            "handle": handle,
            "since": since,
            "include_not_ready": include_not_ready,
            "max_items": max_items,
        },
        "summary": {
            "candidate_count": len(candidates),
            "diagnostic_replay_candidates": section["summary"]["replay_candidate_count"],
            "missed_or_repeated_issue_count": section["summary"][
                "missed_or_repeated_issue_count"
            ],
        },
        "candidates": candidates,
        "diagnostics_summary": section["summary"],
    }


def _load_candidate_state(path: Path) -> dict:
    payload = _read_json_or_empty(path)
    if payload.get("schema_version") != CANDIDATE_QUEUE_SCHEMA_VERSION:
        return {"schema_version": CANDIDATE_QUEUE_SCHEMA_VERSION, "candidates": {}}
    candidates = payload.get("candidates")
    if not isinstance(candidates, dict):
        payload["candidates"] = {}
    return payload


def _candidate_draft_manifest_path(
    repo_root: Path,
    candidate_id: str,
    repo_wiki_dir: Path | None,
) -> Path:
    return _candidate_draft_dir(repo_root, candidate_id, repo_wiki_dir) / "manifest.json"


def _candidate_status(repo_root: Path, candidate: dict, repo_wiki_dir: Path | None) -> str:
    if candidate.get("registered_family"):
        return "promoted"
    candidate_id = str(candidate.get("candidate_id") or "")
    draft_manifest = (
        _read_json_or_empty(
            _candidate_draft_manifest_path(repo_root, candidate_id, repo_wiki_dir)
        )
        if candidate_id
        else {}
    )
    draft_readiness = draft_manifest.get("readiness")
    if isinstance(draft_readiness, dict) and not draft_readiness.get("missing"):
        return "ready"
    if candidate.get("status") == "candidate":
        return "candidate"
    return "observed"


def _queue_candidate_item(
    *,
    repo_root: Path,
    candidate: dict,
    previous: dict,
    refreshed_at: str,
    repo_wiki_dir: Path | None,
) -> dict:
    candidate_id = str(candidate.get("candidate_id") or "")
    previous_seen_count = previous.get("seen_count", 0)
    seen_count = int(previous_seen_count) + 1 if isinstance(previous_seen_count, int) else 1
    status = _candidate_status(repo_root, candidate, repo_wiki_dir)
    evidence = candidate.get("evidence", {})
    if not isinstance(evidence, dict):
        evidence = {}
    readiness = candidate.get("readiness", {})
    if not isinstance(readiness, dict):
        readiness = {}
    suggested_family = candidate.get("suggested_family")
    next_commands = candidate.get("next_commands", {})
    if not isinstance(next_commands, dict):
        next_commands = {}
    next_commands = {
        **next_commands,
        "draft": [
            "aiwiki-toolkit",
            "eval",
            "impact",
            "family",
            "draft",
            "--candidate",
            candidate_id,
            "--baseline-ref",
            "<baseline-ref>",
        ],
        "promote_check": [
            "aiwiki-toolkit",
            "eval",
            "impact",
            "family",
            "promote",
            "--candidate",
            candidate_id,
        ],
        "schedule_report": [
            "aiwiki-toolkit",
            "eval",
            "impact",
            "schedule",
            "report",
        ],
    }
    return {
        "candidate_id": candidate_id,
        "status": status,
        "first_seen_at": previous.get("first_seen_at") or refreshed_at,
        "last_seen_at": refreshed_at,
        "seen_count": seen_count,
        "doc_id": candidate.get("doc_id"),
        "task_id": candidate.get("task_id"),
        "title": candidate.get("title"),
        "path": candidate.get("path"),
        "suggested_family": suggested_family,
        "registered_family": candidate.get("registered_family"),
        "readiness": readiness,
        "evidence": evidence,
        "next_commands": next_commands,
    }


def refresh_impact_eval_candidate_queue(
    *,
    repo_root: Path | None = None,
    repo_wiki_dir: Path | None = None,
    handle: str | None = None,
    since: str | None = None,
    max_items: int = DEFAULT_DIAGNOSTICS_MAX_ITEMS,
    include_not_ready: bool = True,
) -> dict:
    resolved_repo_root = _resolve_eval_repo_root(repo_root)
    selected_repo_wiki_dir = _repo_wiki_dir(resolved_repo_root, repo_wiki_dir)
    paths = _candidate_queue_paths(resolved_repo_root, selected_repo_wiki_dir)
    refreshed_at = _now_iso()
    discovery = discover_impact_eval_family_candidates(
        repo_root=resolved_repo_root,
        repo_wiki_dir=selected_repo_wiki_dir,
        handle=handle,
        since=since,
        max_items=max_items,
        include_not_ready=include_not_ready,
    )
    state = _load_candidate_state(paths["state"])
    previous_candidates = state.get("candidates", {})
    if not isinstance(previous_candidates, dict):
        previous_candidates = {}

    queue_items: list[dict] = []
    next_state_candidates: dict[str, dict] = {}
    for candidate in discovery.get("candidates", []):
        if not isinstance(candidate, dict):
            continue
        candidate_id = str(candidate.get("candidate_id") or "")
        if not candidate_id:
            continue
        previous = previous_candidates.get(candidate_id, {})
        if not isinstance(previous, dict):
            previous = {}
        item = _queue_candidate_item(
            repo_root=resolved_repo_root,
            candidate=candidate,
            previous=previous,
            refreshed_at=refreshed_at,
            repo_wiki_dir=selected_repo_wiki_dir,
        )
        queue_items.append(item)
        next_state_candidates[candidate_id] = item

    stale_candidates = [
        {
            **item,
            "status": "stale",
        }
        for candidate_id, item in previous_candidates.items()
        if candidate_id not in next_state_candidates and isinstance(item, dict)
    ]

    status_counts: dict[str, int] = {}
    for item in [*queue_items, *stale_candidates]:
        status = str(item.get("status") or "unknown")
        status_counts[status] = status_counts.get(status, 0) + 1

    payload = {
        "schema_version": CANDIDATE_QUEUE_SCHEMA_VERSION,
        "generated_at": refreshed_at,
        "repo_root": str(resolved_repo_root),
        "repo_wiki_dir": str(selected_repo_wiki_dir),
        "filters": discovery["filters"],
        "summary": {
            "active_count": len(queue_items),
            "stale_count": len(stale_candidates),
            "status_counts": dict(sorted(status_counts.items())),
        },
        "candidates": sorted(
            queue_items,
            key=lambda item: (
                {"ready": 0, "candidate": 1, "observed": 2, "promoted": 3}.get(
                    str(item.get("status")),
                    9,
                ),
                str(item.get("candidate_id")),
            ),
        ),
        "stale_candidates": sorted(
            stale_candidates,
            key=lambda item: str(item.get("candidate_id")),
        ),
        "outputs": {
            "latest_json": str(paths["latest_json"]),
            "latest_markdown": str(paths["latest_markdown"]),
            "state": str(paths["state"]),
        },
    }
    next_state_candidates.update(
        {
            str(item.get("candidate_id") or ""): item
            for item in stale_candidates
            if str(item.get("candidate_id") or "")
        }
    )
    next_state = {
        "schema_version": CANDIDATE_QUEUE_SCHEMA_VERSION,
        "generated_at": refreshed_at,
        "candidates": next_state_candidates,
    }
    _write_json(paths["latest_json"], payload)
    paths["latest_markdown"].parent.mkdir(parents=True, exist_ok=True)
    paths["latest_markdown"].write_text(
        render_impact_eval_candidate_queue(payload),
        encoding="utf-8",
    )
    _write_json(paths["state"], next_state)
    return payload


def init_impact_eval_family_from_candidate(
    *,
    name: str,
    from_candidate: str,
    baseline_ref: str,
    historical_issue: str | None = None,
    repo_root: Path | None = None,
    force: bool = False,
) -> dict:
    if not name.strip():
        raise ValueError("Family name must be non-empty.")
    if not baseline_ref.strip():
        raise ValueError("--baseline-ref is required.")
    resolved_repo_root = _resolve_eval_repo_root(repo_root)
    family_name = _family_name_from_doc_id(name)
    prompt_family = family_name
    family_dir = _family_specs_root(resolved_repo_root) / family_name
    prompt_dir = _prompt_root(resolved_repo_root, prompt_family)
    rubric_path = _rubric_path(resolved_repo_root, family_name)
    paths = (
        family_dir / "spec.toml",
        prompt_dir / "original.md",
        rubric_path,
    )
    existing = [str(path) for path in paths if path.exists()]
    if existing and not force:
        raise FileExistsError(
            "Impact eval family scaffold already exists. Pass --force to overwrite: "
            + ", ".join(existing)
        )
    source_doc = _doc_id_to_aiwiki_path(from_candidate)
    issue = historical_issue or (
        f"Replay candidate derived from AI wiki memory `{from_candidate}`."
    )
    spec_text = "\n".join(
        [
            f'name = "{family_name}"',
            f'prompt_family = "{prompt_family}"',
            f'baseline_ref = "{baseline_ref}"',
            f'historical_issue = "{issue}"',
            "",
            "raw_docs = [",
            f'  "{source_doc}",',
            "]",
            "",
            "consolidated_docs = []",
            "",
        ]
    )
    prompt_text = "\n".join(
        [
            "# Original Task Prompt",
            "",
            "TODO: Replace this with the original historical task request.",
            "",
            "Do not name the expected solution, target memory, or preferred implementation surface",
            "unless the benchmark explicitly measures behavior inside that already-known surface.",
            "",
        ]
    )
    rubric = {
        "schema_version": RUBRIC_SCHEMA_VERSION,
        "name": family_name,
        "success": [
            {
                "id": "captures-change",
                "artifact": "workspace_diff",
                "contains": "diff --git",
                "description": "The run produces an artifact-backed workspace change.",
            }
        ],
        "partial": [],
        "fail": [],
    }
    family_dir.mkdir(parents=True, exist_ok=True)
    prompt_dir.mkdir(parents=True, exist_ok=True)
    (family_dir / "spec.toml").write_text(spec_text, encoding="utf-8")
    (prompt_dir / "original.md").write_text(prompt_text, encoding="utf-8")
    _write_json(rubric_path, rubric)
    return {
        "schema_version": FAMILY_INIT_SCHEMA_VERSION,
        "family": family_name,
        "from_candidate": from_candidate,
        "baseline_ref": baseline_ref,
        "created_or_updated": [str(path) for path in paths],
        "next_commands": {
            "show": [
                "aiwiki-toolkit",
                "eval",
                "impact",
                "family",
                "show",
                family_name,
            ],
            "plan": ["aiwiki-toolkit", "eval", "impact", "plan", "--family", family_name],
            "benchmark": [
                "aiwiki-toolkit",
                "eval",
                "impact",
                "benchmark",
                "--family",
                family_name,
                "--score-policy",
                "rubric",
            ],
        },
    }


def _candidate_queue_item_by_id(
    *,
    repo_root: Path,
    repo_wiki_dir: Path | None,
    candidate_id: str,
) -> dict:
    paths = _candidate_queue_paths(repo_root, repo_wiki_dir)
    payload = _read_json_or_empty(paths["latest_json"])
    if not payload:
        payload = refresh_impact_eval_candidate_queue(
            repo_root=repo_root,
            repo_wiki_dir=repo_wiki_dir,
            include_not_ready=True,
        )
    candidates = payload.get("candidates", [])
    if not isinstance(candidates, list):
        candidates = []
    for candidate in candidates:
        if not isinstance(candidate, dict):
            continue
        keys = {
            str(candidate.get("candidate_id") or ""),
            str(candidate.get("doc_id") or ""),
            str(candidate.get("task_id") or ""),
            str(candidate.get("suggested_family") or ""),
        }
        if candidate_id in keys:
            return candidate
    raise ValueError(f"Impact eval candidate not found in managed queue: {candidate_id}")


def _candidate_source(candidate: dict) -> str:
    return str(candidate.get("doc_id") or candidate.get("task_id") or candidate.get("candidate_id"))


def _candidate_historical_issue(candidate: dict) -> str:
    title = candidate.get("title")
    reason = candidate.get("evidence", {}).get("reason") if isinstance(candidate.get("evidence"), dict) else None
    if isinstance(title, str) and title.strip():
        return title.strip()
    if isinstance(reason, str) and reason.strip():
        return reason.strip()
    return f"Replay candidate derived from `{_candidate_source(candidate)}`."


def _candidate_draft_readiness(*, baseline_ref: str | None) -> dict:
    present = ["source_incident", "replayable_memory_evidence", "prompt_draft", "rubric_draft"]
    missing: list[str] = []
    if baseline_ref and baseline_ref != "<baseline-ref>":
        present.append("baseline_ref")
    else:
        missing.append("baseline_ref")
    return {"present": present, "missing": missing}


def draft_impact_eval_family_candidate(
    *,
    candidate_id: str,
    family_name: str | None = None,
    baseline_ref: str | None = None,
    repo_root: Path | None = None,
    repo_wiki_dir: Path | None = None,
    force: bool = False,
) -> dict:
    resolved_repo_root = _resolve_eval_repo_root(repo_root)
    selected_repo_wiki_dir = _repo_wiki_dir(resolved_repo_root, repo_wiki_dir)
    candidate = _candidate_queue_item_by_id(
        repo_root=resolved_repo_root,
        repo_wiki_dir=selected_repo_wiki_dir,
        candidate_id=candidate_id,
    )
    selected_family_name = _family_name_from_doc_id(
        family_name or str(candidate.get("suggested_family") or candidate.get("candidate_id"))
    )
    selected_baseline_ref = baseline_ref or "<baseline-ref>"
    draft_dir = _candidate_draft_dir(
        resolved_repo_root,
        str(candidate.get("candidate_id")),
        selected_repo_wiki_dir,
    )
    spec_path = draft_dir / "spec.toml"
    prompt_path = draft_dir / "original.md"
    rubric_path = draft_dir / "rubric.json"
    manifest_path = draft_dir / "manifest.json"
    existing = [str(path) for path in (spec_path, prompt_path, rubric_path, manifest_path) if path.exists()]
    if existing and not force:
        raise FileExistsError(
            "Managed candidate draft already exists. Pass --force to overwrite: "
            + ", ".join(existing)
        )
    source = _candidate_source(candidate)
    source_doc = _doc_id_to_aiwiki_path(source) if "/" in source else source
    historical_issue = _candidate_historical_issue(candidate)
    spec_text = "\n".join(
        [
            f'name = "{selected_family_name}"',
            f'prompt_family = "{selected_family_name}"',
            f'baseline_ref = "{selected_baseline_ref}"',
            f'historical_issue = "{historical_issue}"',
            "",
            "raw_docs = [",
            f'  "{source_doc}",',
            "]",
            "",
            "consolidated_docs = []",
            "",
        ]
    )
    prompt_text = "\n".join(
        [
            "# Original Task Prompt",
            "",
            "TODO: Replace this with the original historical request that produced the source incident.",
            "",
            "Constraints for the final prompt:",
            "",
            "- backsolve from concrete repo history",
            "- do not name the expected solution or target memory",
            "- do not name the preferred implementation surface unless that surface is part of the task",
            "- keep the task realistic enough that a future agent could have received it naturally",
            "",
        ]
    )
    rubric = {
        "schema_version": RUBRIC_SCHEMA_VERSION,
        "name": selected_family_name,
        "success": [
            {
                "id": "artifact-backed-change",
                "artifact": "workspace_diff",
                "contains": "diff --git",
                "description": "The run produces an artifact-backed workspace change.",
            }
        ],
        "partial": [],
        "fail": [],
    }
    readiness = _candidate_draft_readiness(baseline_ref=selected_baseline_ref)
    manifest = {
        "schema_version": CANDIDATE_DRAFT_SCHEMA_VERSION,
        "candidate_id": candidate.get("candidate_id"),
        "family": selected_family_name,
        "source": source,
        "baseline_ref": selected_baseline_ref,
        "historical_issue": historical_issue,
        "generated_at": _now_iso(),
        "readiness": readiness,
        "paths": {
            "draft_dir": str(draft_dir),
            "spec": str(spec_path),
            "prompt": str(prompt_path),
            "rubric": str(rubric_path),
            "manifest": str(manifest_path),
        },
        "candidate": candidate,
    }
    draft_dir.mkdir(parents=True, exist_ok=True)
    spec_path.write_text(spec_text, encoding="utf-8")
    prompt_path.write_text(prompt_text, encoding="utf-8")
    _write_json(rubric_path, rubric)
    _write_json(manifest_path, manifest)
    return {
        "schema_version": CANDIDATE_DRAFT_SCHEMA_VERSION,
        "candidate_id": candidate.get("candidate_id"),
        "family": selected_family_name,
        "status": "ready" if not readiness["missing"] else "drafted",
        "readiness": readiness,
        "paths": manifest["paths"],
        "next_commands": {
            "promote_check": [
                "aiwiki-toolkit",
                "eval",
                "impact",
                "family",
                "promote",
                "--candidate",
                str(candidate.get("candidate_id")),
            ],
            "promote_apply": [
                "aiwiki-toolkit",
                "eval",
                "impact",
                "family",
                "promote",
                "--candidate",
                str(candidate.get("candidate_id")),
                "--apply",
            ],
        },
    }


def promote_impact_eval_family_candidate(
    *,
    candidate_id: str,
    family_name: str | None = None,
    baseline_ref: str | None = None,
    repo_root: Path | None = None,
    repo_wiki_dir: Path | None = None,
    apply: bool = False,
    force: bool = False,
) -> dict:
    resolved_repo_root = _resolve_eval_repo_root(repo_root)
    selected_repo_wiki_dir = _repo_wiki_dir(resolved_repo_root, repo_wiki_dir)
    candidate = _candidate_queue_item_by_id(
        repo_root=resolved_repo_root,
        repo_wiki_dir=selected_repo_wiki_dir,
        candidate_id=candidate_id,
    )
    manifest_path = _candidate_draft_manifest_path(
        resolved_repo_root,
        str(candidate.get("candidate_id")),
        selected_repo_wiki_dir,
    )
    manifest = _read_json_or_empty(manifest_path)
    blockers: list[str] = []
    if manifest.get("schema_version") != CANDIDATE_DRAFT_SCHEMA_VERSION:
        blockers.append("managed_draft_missing")
    selected_family = _family_name_from_doc_id(
        family_name or str(manifest.get("family") or candidate.get("suggested_family") or candidate.get("candidate_id"))
    )
    selected_baseline = baseline_ref or str(manifest.get("baseline_ref") or "")
    if not selected_baseline or selected_baseline == "<baseline-ref>":
        blockers.append("baseline_ref_missing")
    paths = manifest.get("paths") if isinstance(manifest.get("paths"), dict) else {}
    draft_spec = Path(str(paths.get("spec", ""))) if paths.get("spec") else None
    draft_prompt = Path(str(paths.get("prompt", ""))) if paths.get("prompt") else None
    draft_rubric = Path(str(paths.get("rubric", ""))) if paths.get("rubric") else None
    for label, path in (("spec", draft_spec), ("prompt", draft_prompt), ("rubric", draft_rubric)):
        if path is None or not path.exists():
            blockers.append(f"{label}_draft_missing")
    formal_spec = _family_specs_root(resolved_repo_root) / selected_family / "spec.toml"
    formal_prompt = _prompt_root(resolved_repo_root, selected_family) / "original.md"
    formal_rubric = _rubric_path(resolved_repo_root, selected_family)
    existing = [str(path) for path in (formal_spec, formal_prompt, formal_rubric) if path.exists()]
    if existing and not force:
        blockers.append("formal_family_files_exist")
    result = {
        "schema_version": CANDIDATE_PROMOTION_SCHEMA_VERSION,
        "candidate_id": candidate.get("candidate_id"),
        "family": selected_family,
        "apply": apply,
        "promotable": not blockers,
        "blockers": blockers,
        "formal_paths": {
            "spec": str(formal_spec),
            "prompt": str(formal_prompt),
            "rubric": str(formal_rubric),
        },
        "draft_manifest": str(manifest_path),
    }
    if blockers or not apply:
        return result
    assert draft_spec is not None
    assert draft_prompt is not None
    assert draft_rubric is not None
    spec_text = draft_spec.read_text(encoding="utf-8")
    spec_text = spec_text.replace('baseline_ref = "<baseline-ref>"', f'baseline_ref = "{selected_baseline}"')
    if family_name:
        old_family = str(manifest.get("family") or "")
        spec_text = spec_text.replace(f'name = "{old_family}"', f'name = "{selected_family}"')
        spec_text = spec_text.replace(f'prompt_family = "{old_family}"', f'prompt_family = "{selected_family}"')
    formal_spec.parent.mkdir(parents=True, exist_ok=True)
    formal_prompt.parent.mkdir(parents=True, exist_ok=True)
    formal_rubric.parent.mkdir(parents=True, exist_ok=True)
    formal_spec.write_text(spec_text, encoding="utf-8")
    formal_prompt.write_text(draft_prompt.read_text(encoding="utf-8"), encoding="utf-8")
    formal_rubric.write_text(draft_rubric.read_text(encoding="utf-8"), encoding="utf-8")
    result["promoted"] = True
    return result


def generate_impact_eval_run_plan(
    *,
    family: str,
    repo_root: Path | None = None,
    prompt_levels: tuple[str, ...] = DEFAULT_PLAN_PROMPT_LEVELS,
    run_label: str = DEFAULT_RUN_LABEL,
    workspace_root: Path | None = None,
    output_root: Path | None = None,
    model_family: str = DEFAULT_PLAN_MODEL,
    reasoning_effort: str = DEFAULT_PLAN_REASONING_EFFORT,
    execution_surface: str = DEFAULT_PLAN_EXECUTION_SURFACE,
    source_mode: str = DEFAULT_SOURCE_MODE,
    baseline_ref: str | None = None,
) -> dict:
    if source_mode not in VALID_SOURCE_MODES:
        raise ValueError(
            "Invalid source mode. Expected one of: " + ", ".join(sorted(VALID_SOURCE_MODES))
        )
    if not prompt_levels:
        raise ValueError("At least one prompt level is required.")
    clean_prompt_levels = tuple(level.strip() for level in prompt_levels if level.strip())
    if not clean_prompt_levels:
        raise ValueError("At least one non-empty prompt level is required.")

    resolved_repo_root = _resolve_eval_repo_root(repo_root)
    spec = _read_family_spec(resolved_repo_root, family)
    prompt_family = str(spec.get("prompt_family") or spec.get("name") or family)
    selected_baseline_ref = baseline_ref or str(spec.get("baseline_ref") or "HEAD")
    selected_workspace_root = (
        workspace_root
        if workspace_root is not None
        else DEFAULT_IMPACT_WORKDIR_ROOT / family / "workspaces" / "latest"
    )
    selected_output_root = (
        output_root
        if output_root is not None
        else DEFAULT_IMPACT_WORKDIR_ROOT / family / "runs"
    )
    run_dir = selected_output_root / run_label

    prompt_root = resolved_repo_root / "evals" / "impact" / "prompts" / prompt_family
    prompts: list[dict] = []
    for prompt_level in clean_prompt_levels:
        prompt_path = prompt_root / f"{prompt_level}.md"
        if not prompt_path.exists():
            raise FileNotFoundError(f"Impact eval prompt not found: {prompt_path}")
        prompt_text = prompt_path.read_text(encoding="utf-8")
        prompts.append(
            {
                "level": prompt_level,
                "path": str(prompt_path),
                "sha256": _sha256_text(prompt_text),
            }
        )

    prepare_command = _command(
        "uv",
        "run",
        "python",
        "evals/impact/scripts/prepare_variants.py",
        "--experiment",
        family,
        "--source-mode",
        source_mode,
        "--baseline-ref",
        selected_baseline_ref,
        "--output-root",
        selected_workspace_root,
        "--workspace-layout",
        DEFAULT_WORKSPACE_LAYOUT,
    )
    init_command = _command(
        "uv",
        "run",
        "python",
        "evals/impact/scripts/init_run.py",
        "--experiment",
        family,
        "--workspace-root",
        selected_workspace_root,
        "--output-root",
        selected_output_root,
        "--run-label",
        run_label,
        "--prompt-levels",
        _csv(clean_prompt_levels),
        "--model-family",
        model_family,
        "--reasoning-effort",
        reasoning_effort,
        "--execution-surface",
        execution_surface,
    )
    run_commands = [
        _command(
            "uv",
            "run",
            "python",
            "evals/impact/scripts/run_cli_slots.py",
            "--run-dir",
            run_dir,
            "--prompt-level",
            prompt_level,
        )
        for prompt_level in clean_prompt_levels
    ]
    post_run_commands = [
        _command(
            "uv",
            "run",
            "python",
            "evals/impact/scripts/export_codex_sessions.py",
            "--workspace-root",
            selected_workspace_root,
        ),
        _command(
            "aiwiki-toolkit",
            "eval",
            "impact",
            "validate",
            "--run-dir",
            run_dir,
        ),
        _command(
            "aiwiki-toolkit",
            "eval",
            "impact",
            "manifest",
            "--run-dir",
            run_dir,
        ),
        _command(
            "aiwiki-toolkit",
            "eval",
            "impact",
            "report",
            "--run-dir",
            run_dir,
        ),
    ]

    raw_docs = tuple(str(item) for item in spec.get("raw_docs", []) if str(item))
    consolidated_docs = tuple(
        str(item) for item in spec.get("consolidated_docs", []) if str(item)
    )
    diagnostic_variants = tuple(
        variant for variant in WORKFLOW_VARIANTS if variant not in WORKFLOW_PRIMARY_VARIANTS
    )
    return {
        "schema_version": "impact-eval-run-plan-v1",
        "family": family,
        "repo_root": str(resolved_repo_root),
        "family_spec": {
            "path": spec["_spec_path"],
            "prompt_family": prompt_family,
            "historical_issue": spec.get("historical_issue", ""),
            "baseline_ref": selected_baseline_ref,
            "raw_docs": list(raw_docs),
            "consolidated_docs": list(consolidated_docs),
        },
        "workspace": {
            "source_mode": source_mode,
            "workspace_layout": DEFAULT_WORKSPACE_LAYOUT,
            "workspace_root": str(selected_workspace_root),
            "output_root": str(selected_output_root),
            "run_label": run_label,
            "run_dir": str(run_dir),
        },
        "execution": {
            "model": model_family,
            "reasoning_effort": reasoning_effort,
            "execution_surface": execution_surface,
            "auto_invokes_agent": False,
        },
        "comparison": {
            "primary": list(WORKFLOW_PRIMARY_VARIANTS),
            "diagnostic": list(diagnostic_variants),
            "variants": list(WORKFLOW_VARIANTS),
        },
        "prompts": prompts,
        "commands": {
            "prepare_variants": prepare_command,
            "init_run": init_command,
            "run_slots": run_commands,
            "run_all_slots": _command(
                "aiwiki-toolkit",
                "eval",
                "impact",
                "run",
                "--run-dir",
                run_dir,
                "--all-slots",
            ),
            "manual_capture_template": _command(
                "aiwiki-toolkit",
                "eval",
                "impact",
                "capture",
                "--run-dir",
                run_dir,
                "--slot",
                "<slot>",
                "--prompt-level",
                clean_prompt_levels[0],
                "--phase",
                "first_pass",
                "--first-pass-success",
            ),
            "manual_score_template": _command(
                "aiwiki-toolkit",
                "eval",
                "impact",
                "score",
                "--run-dir",
                run_dir,
                "--slot",
                "<slot>",
                "--prompt-level",
                clean_prompt_levels[0],
                "--label",
                "success|partial|fail",
            ),
            "post_run": post_run_commands,
        },
        "manual_steps": [
            "Run prepare_variants to create neutral slot workspaces.",
            "Run init_run to create the captured run directory and metadata.",
            "Run `aiwiki-toolkit eval impact run --all-slots`, or execute equivalent fresh agent sessions.",
            "For manual sessions, capture each first-pass result with `aiwiki-toolkit eval impact capture`.",
            "Export Codex visible sessions before making shareable workflow or causal claims.",
            "Validate confounds with `aiwiki-toolkit eval impact validate` before publishing claims.",
            "Score each slot with `aiwiki-toolkit eval impact score` before treating report metrics as final.",
            "Generate manifest and report from the captured artifacts.",
        ],
    }


def _python_script_executable() -> str:
    executable_name = Path(sys.executable).name.lower()
    if executable_name.startswith("python"):
        return sys.executable
    for candidate in ("python3", "python"):
        executable = shutil.which(candidate)
        if executable:
            return executable
    return sys.executable


def _script_command(repo_root: Path, script_name: str, *args: object) -> list[str]:
    return [
        _python_script_executable(),
        str(repo_root / "evals" / "impact" / "scripts" / script_name),
        *(str(arg) for arg in args),
    ]


def _run_cli_slots_command(
    *,
    repo_root: Path,
    run_dir: Path,
    slots: tuple[str, ...],
    prompt_level: str,
    codex_bin: str,
    sleep_guard: bool,
) -> list[str]:
    command = _script_command(
        repo_root,
        "run_cli_slots.py",
        "--run-dir",
        run_dir,
        "--prompt-level",
        prompt_level,
        "--codex-bin",
        codex_bin,
    )
    if slots:
        command.extend(["--slots", _csv(slots)])
    if not sleep_guard:
        command.append("--no-sleep-guard")
    return command


def _export_sessions_command(
    *,
    repo_root: Path,
    workspace_root: Path,
    output_dir: Path | None = None,
    sessions_root: Path | None = None,
    session_index: Path | None = None,
    match_workspace_root: Path | None = None,
    slots: tuple[str, ...] = (),
    export_all_sessions: bool = False,
) -> list[str]:
    command = _script_command(
        repo_root,
        "export_codex_sessions.py",
        "--workspace-root",
        workspace_root,
    )
    if output_dir is not None:
        command.extend(["--output-dir", str(output_dir)])
    if sessions_root is not None:
        command.extend(["--sessions-root", str(sessions_root)])
    if session_index is not None:
        command.extend(["--session-index", str(session_index)])
    if match_workspace_root is not None:
        command.extend(["--match-workspace-root", str(match_workspace_root)])
    if slots:
        command.extend(["--variants", _csv(slots)])
    if export_all_sessions:
        command.append("--all-sessions")
    return command


def _prepare_script_commands(plan: dict) -> tuple[tuple[str, list[str]], ...]:
    repo_root = Path(str(plan["repo_root"]))
    family = str(plan["family"])
    family_spec = plan["family_spec"]
    workspace = plan["workspace"]
    execution = plan["execution"]
    prompt_levels = tuple(
        str(prompt["level"])
        for prompt in plan.get("prompts", [])
        if isinstance(prompt, dict) and prompt.get("level")
    )
    prepare_command = _script_command(
        repo_root,
        "prepare_variants.py",
        "--experiment",
        family,
        "--source-root",
        repo_root,
        "--source-mode",
        workspace["source_mode"],
        "--baseline-ref",
        family_spec["baseline_ref"],
        "--output-root",
        workspace["workspace_root"],
        "--workspace-layout",
        workspace["workspace_layout"],
    )
    init_command = _script_command(
        repo_root,
        "init_run.py",
        "--experiment",
        family,
        "--workspace-root",
        workspace["workspace_root"],
        "--output-root",
        workspace["output_root"],
        "--run-label",
        workspace["run_label"],
        "--prompt-levels",
        _csv(prompt_levels),
        "--model-family",
        execution["model"],
        "--reasoning-effort",
        execution["reasoning_effort"],
        "--execution-surface",
        execution["execution_surface"],
    )
    return (("prepare_variants", prepare_command), ("init_run", init_command))


def _run_prepare_command(
    *,
    name: str,
    command: list[str],
    cwd: Path,
) -> dict:
    result = subprocess.run(
        command,
        cwd=cwd,
        check=False,
        capture_output=True,
        text=True,
    )
    payload = {
        "name": name,
        "command": command,
        "returncode": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr,
    }
    if result.returncode != 0:
        details = "\n".join(part for part in (result.stdout, result.stderr) if part.strip())
        raise RuntimeError(
            f"Impact eval prepare step failed: {name} exited with {result.returncode}.\n"
            + details
        )
    return payload


def _run_eval_script_command(
    *,
    name: str,
    command: list[str],
    cwd: Path,
    check: bool = True,
) -> dict:
    result = subprocess.run(
        command,
        cwd=cwd,
        check=False,
        capture_output=True,
        text=True,
    )
    payload = {
        "name": name,
        "command": command,
        "returncode": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr,
    }
    if check and result.returncode != 0:
        details = "\n".join(part for part in (result.stdout, result.stderr) if part.strip())
        raise RuntimeError(
            f"Impact eval {name} step failed with exit code {result.returncode}.\n"
            + details
        )
    return payload


def _skipped_command_result(name: str, reason: str, command: list[str] | None = None) -> dict:
    return {
        "name": name,
        "command": command or [],
        "returncode": None,
        "stdout": "",
        "stderr": reason,
        "skipped": True,
    }


def _write_impact_eval_manifest_files(run_dir: Path) -> dict:
    manifest = generate_impact_eval_manifest(run_dir)
    manifest_json_path = run_dir / "manifest.json"
    manifest_md_path = run_dir / "manifest.md"
    manifest_json_path.write_text(render_impact_eval_manifest_json(manifest), encoding="utf-8")
    manifest_md_path.write_text(render_impact_eval_manifest(manifest), encoding="utf-8")
    return {
        "json": str(manifest_json_path),
        "markdown": str(manifest_md_path),
        "schema_version": manifest["schema_version"],
    }


def _path_from_stdout(stdout: str, fallback: Path) -> Path:
    lines = [line.strip() for line in stdout.splitlines() if line.strip()]
    if not lines:
        return fallback
    return Path(lines[-1])


def _result_artifacts(result_dir: Path, score_path: Path | None = None) -> dict[str, str]:
    candidates = {
        "result": result_dir / "result.json",
        "final_message": result_dir / "final_message.md",
        "workspace_diff": result_dir / "workspace_diff.patch",
        "workspace_diff_stat": result_dir / "workspace_diff_stat.txt",
        "workspace_status": result_dir / "workspace_status.txt",
        "workspace_head": result_dir / "workspace_head.txt",
        "command_result": result_dir / "command_result.json",
    }
    if score_path is not None:
        candidates["score"] = score_path
    return {
        name: str(path)
        for name, path in candidates.items()
        if path.exists()
    }


def prepare_impact_eval_run(
    *,
    family: str,
    repo_root: Path | None = None,
    prompt_levels: tuple[str, ...] = DEFAULT_PLAN_PROMPT_LEVELS,
    run_label: str | None = None,
    workspace_root: Path | None = None,
    output_root: Path | None = None,
    model_family: str = DEFAULT_PLAN_MODEL,
    reasoning_effort: str = DEFAULT_PLAN_REASONING_EFFORT,
    execution_surface: str = DEFAULT_PLAN_EXECUTION_SURFACE,
    source_mode: str = DEFAULT_SOURCE_MODE,
    baseline_ref: str | None = None,
) -> dict:
    timestamp = _timestamp_slug()
    resolved_workspace_root = (
        workspace_root
        if workspace_root is not None
        else DEFAULT_IMPACT_WORKDIR_ROOT / family / "workspaces" / timestamp
    )
    resolved_run_label = run_label or f"run_{timestamp}"
    plan = generate_impact_eval_run_plan(
        family=family,
        repo_root=repo_root,
        prompt_levels=prompt_levels,
        run_label=resolved_run_label,
        workspace_root=resolved_workspace_root,
        output_root=output_root,
        model_family=model_family,
        reasoning_effort=reasoning_effort,
        execution_surface=execution_surface,
        source_mode=source_mode,
        baseline_ref=baseline_ref,
    )
    repo_root_path = Path(str(plan["repo_root"]))
    command_results = [
        _run_prepare_command(name=name, command=command, cwd=repo_root_path)
        for name, command in _prepare_script_commands(plan)
    ]

    run_dir = Path(str(plan["workspace"]["run_dir"]))
    manifest_info = _write_impact_eval_manifest_files(run_dir)

    return {
        "schema_version": "impact-eval-prepare-result-v1",
        "family": family,
        "workspace_root": plan["workspace"]["workspace_root"],
        "run_dir": str(run_dir),
        "manifest": manifest_info,
        "commands": command_results,
        "plan": plan,
        "next_steps": [
            "Run the listed run_cli_slots command for each prompt level, or run equivalent fresh agent sessions.",
            "Export visible sessions before making workflow or causal claims.",
            "Run capture, validate, score, manifest, and report after first-pass sessions exist.",
        ],
    }


def capture_impact_eval_result(
    *,
    run_dir: Path,
    slot: str,
    prompt_level: str,
    workspace: Path | None = None,
    variant: str | None = None,
    phase: str = "first_pass",
    final_message: Path | None = None,
    attempt: int = 1,
    human_nudges: int = 0,
    first_pass_success: bool | None = None,
    notes: str = "",
    repo_root: Path | None = None,
) -> dict:
    resolved_run_dir = run_dir.resolve()
    if phase not in CAPTURE_PHASES:
        raise ValueError("Invalid phase. Expected one of: " + ", ".join(sorted(CAPTURE_PHASES)))
    if attempt < 1:
        raise ValueError("--attempt must be >= 1")
    if human_nudges < 0:
        raise ValueError("--human-nudges must be >= 0")
    metadata = _read_run_metadata(resolved_run_dir)
    variant_map = _assignment_variant_map(metadata)
    workspace_map = _assignment_workspace_map(metadata)
    selected_variant = variant or variant_map.get(slot)
    if not selected_variant:
        raise ValueError(
            f"Could not infer variant for slot {slot!r}. Pass --variant or check metadata.json."
        )
    selected_workspace = workspace or (
        Path(workspace_map[slot]) if slot in workspace_map else None
    )
    if selected_workspace is None:
        raise ValueError(
            f"Could not infer workspace for slot {slot!r}. Pass --workspace or check metadata.json."
        )

    repo_root_path = _resolve_eval_repo_root(repo_root)
    command = _script_command(
        repo_root_path,
        "save_result.py",
        "--run-dir",
        resolved_run_dir,
        "--variant",
        selected_variant,
        "--slot",
        slot,
        "--prompt-level",
        prompt_level,
        "--workspace",
        selected_workspace,
        "--phase",
        phase,
        "--attempt",
        attempt,
        "--human-nudges",
        human_nudges,
    )
    if final_message is not None:
        command.extend(["--final-message", str(final_message)])
    if first_pass_success is True:
        command.append("--first-pass-success")
    elif first_pass_success is False:
        command.append("--first-pass-failure")
    if notes:
        command.extend(["--notes", notes])

    command_result = _run_eval_script_command(
        name="capture",
        command=command,
        cwd=repo_root_path,
    )
    fallback_dir = resolved_run_dir / slot / prompt_level / phase
    result_dir = _path_from_stdout(command_result["stdout"], fallback_dir)
    score_path = resolved_run_dir / slot / prompt_level / "score.json"
    manifest_info = _write_impact_eval_manifest_files(resolved_run_dir)
    return {
        "schema_version": "impact-eval-capture-result-v1",
        "run_dir": str(resolved_run_dir),
        "slot": slot,
        "variant": selected_variant,
        "prompt_level": prompt_level,
        "phase": phase,
        "workspace": str(selected_workspace),
        "result_dir": str(result_dir),
        "artifacts": _result_artifacts(result_dir, score_path),
        "manifest": manifest_info,
        "command": command_result,
        "next_steps": [
            "Score the slot with `aiwiki-toolkit eval impact score` once the first-pass outcome is known.",
            "Export visible sessions and run `aiwiki-toolkit eval impact validate` before making causal claims.",
            "Run `aiwiki-toolkit eval impact report` to inspect first-attempt product metrics.",
        ],
    }


def validate_impact_eval_run(
    *,
    run_dir: Path,
    session_export_root: Path | None = None,
    repo_root: Path | None = None,
) -> dict:
    resolved_run_dir = run_dir.resolve()
    _read_run_metadata(resolved_run_dir)
    repo_root_path = _resolve_eval_repo_root(repo_root)
    command = _script_command(
        repo_root_path,
        "validate_run.py",
        "--run-dir",
        resolved_run_dir,
    )
    if session_export_root is not None:
        command.extend(["--session-export-root", str(session_export_root)])

    command_result = _run_eval_script_command(
        name="validate",
        command=command,
        cwd=repo_root_path,
    )
    confounds_path = resolved_run_dir / "confounds.json"
    confounds = _read_json(confounds_path) if confounds_path.exists() else {}
    manifest_info = _write_impact_eval_manifest_files(resolved_run_dir)
    critical_confounds = confounds.get("critical_confounds", [])
    if not isinstance(critical_confounds, list):
        critical_confounds = []
    warnings = confounds.get("warnings", [])
    if not isinstance(warnings, list):
        warnings = []
    return {
        "schema_version": "impact-eval-validate-result-v1",
        "run_dir": str(resolved_run_dir),
        "session_export_root": confounds.get(
            "session_export_root",
            str(session_export_root) if session_export_root is not None else None,
        ),
        "confounds_path": str(confounds_path),
        "shareable_for_causal_claims": confounds.get("shareable_for_causal_claims"),
        "critical_confounds": len(critical_confounds),
        "warnings": len(warnings),
        "manifest": manifest_info,
        "command": command_result,
    }


def score_impact_eval_result(
    *,
    run_dir: Path,
    slot: str,
    prompt_level: str,
    label: str,
    rubric_refs: tuple[str, ...] = (),
    evidence: tuple[str, ...] = (),
    notes: str = "",
    repo_root: Path | None = None,
) -> dict:
    if label not in SCORE_LABELS:
        raise ValueError("Invalid score label. Expected one of: " + ", ".join(SCORE_LABELS))
    resolved_run_dir = run_dir.resolve()
    _read_run_metadata(resolved_run_dir)
    repo_root_path = _resolve_eval_repo_root(repo_root)
    command = _script_command(
        repo_root_path,
        "score_run.py",
        "--run-dir",
        resolved_run_dir,
        "--slot",
        slot,
        "--prompt-level",
        prompt_level,
        "--label",
        label,
    )
    if rubric_refs:
        command.extend(["--rubric-refs", _csv(rubric_refs)])
    if evidence:
        command.extend(["--evidence", _csv(evidence)])
    if notes:
        command.extend(["--notes", notes])

    command_result = _run_eval_script_command(
        name="score",
        command=command,
        cwd=repo_root_path,
    )
    fallback_path = resolved_run_dir / slot / prompt_level / "score.json"
    score_path = _path_from_stdout(command_result["stdout"], fallback_path)
    manifest_info = _write_impact_eval_manifest_files(resolved_run_dir)
    return {
        "schema_version": "impact-eval-score-result-v1",
        "run_dir": str(resolved_run_dir),
        "slot": slot,
        "prompt_level": prompt_level,
        "label": label,
        "score_path": str(score_path),
        "rubric_refs": list(rubric_refs),
        "evidence": list(evidence),
        "manifest": manifest_info,
        "command": command_result,
        "next_steps": [
            "Run `aiwiki-toolkit eval impact manifest` to audit artifact coverage.",
            "Run `aiwiki-toolkit eval impact report` after primary slots have scores.",
        ],
    }


def _read_slot_command_results(run_dir: Path) -> list[dict]:
    path = run_dir / "slot_command_results.json"
    if not path.exists():
        return []
    payload = _read_json(path)
    results = payload.get("results")
    if not isinstance(results, list):
        return []
    return [item for item in results if isinstance(item, dict)]


def _score_policy_label(slot_result: dict) -> str:
    codex_returncode = _int_or_zero(slot_result.get("codex_returncode"))
    save_result_returncode = _int_or_zero(slot_result.get("save_result_returncode"))
    return "success" if codex_returncode == 0 and save_result_returncode == 0 else "fail"


def _default_rubric_path(repo_root: Path, metadata: dict) -> Path:
    experiment = str(metadata.get("experiment", ""))
    return repo_root / "evals" / "impact" / "rubrics" / f"{experiment}.json"


def _load_rubric(path: Path) -> dict:
    if not path.exists():
        raise FileNotFoundError(f"Rubric file does not exist: {path}")
    rubric = _read_json(path)
    schema_version = rubric.get("schema_version")
    if schema_version != RUBRIC_SCHEMA_VERSION:
        raise ValueError(
            f"Unsupported rubric schema_version in {path}: {schema_version!r}. "
            f"Expected {RUBRIC_SCHEMA_VERSION!r}."
        )
    success = rubric.get("success")
    if not isinstance(success, list) or not success:
        raise ValueError("Rubric must contain a non-empty `success` criterion list.")
    return rubric


def _artifact_text_for_rubric(
    *,
    run_dir: Path,
    slot: str,
    prompt_level: str,
    criterion: dict,
) -> str:
    phase = str(criterion.get("phase") or "first_pass")
    result_dir = run_dir / slot / prompt_level / phase
    artifact = str(criterion.get("artifact") or "workspace_diff")
    if artifact == "workspace_diff":
        path = result_dir / "workspace_diff.patch"
        return path.read_text(encoding="utf-8") if path.exists() else ""
    if artifact == "workspace_diff_stat":
        path = result_dir / "workspace_diff_stat.txt"
        return path.read_text(encoding="utf-8") if path.exists() else ""
    if artifact == "workspace_status":
        path = result_dir / "workspace_status.txt"
        return path.read_text(encoding="utf-8") if path.exists() else ""
    if artifact == "final_message":
        path = result_dir / "final_message.md"
        return path.read_text(encoding="utf-8") if path.exists() else ""
    if artifact in {"result", "changed_files", "untracked_files"}:
        path = result_dir / "result.json"
        if not path.exists():
            return ""
        result = _read_json(path)
        if artifact == "result":
            return json.dumps(result, indent=2)
        value = result.get(artifact)
        if isinstance(value, list):
            return "\n".join(str(item) for item in value)
        return ""
    raise ValueError(f"Unsupported rubric criterion artifact: {artifact}")


def _evaluate_rubric_criterion(
    *,
    run_dir: Path,
    slot: str,
    prompt_level: str,
    criterion: dict,
) -> dict:
    if not isinstance(criterion, dict):
        raise ValueError("Rubric criteria must be objects.")
    text = _artifact_text_for_rubric(
        run_dir=run_dir,
        slot=slot,
        prompt_level=prompt_level,
        criterion=criterion,
    )
    checks: list[bool] = []
    contains = criterion.get("contains")
    if isinstance(contains, str):
        checks.append(contains in text)
    not_contains = criterion.get("not_contains")
    if isinstance(not_contains, str):
        checks.append(not_contains not in text)
    changed_file = criterion.get("changed_file")
    if isinstance(changed_file, str):
        checks.append(changed_file in text.splitlines())
    changed_file_prefix = criterion.get("changed_file_prefix")
    if isinstance(changed_file_prefix, str):
        checks.append(any(line.startswith(changed_file_prefix) for line in text.splitlines()))
    untracked_file = criterion.get("untracked_file")
    if isinstance(untracked_file, str):
        checks.append(untracked_file in text.splitlines())
    untracked_file_prefix = criterion.get("untracked_file_prefix")
    if isinstance(untracked_file_prefix, str):
        checks.append(any(line.startswith(untracked_file_prefix) for line in text.splitlines()))
    if not checks:
        raise ValueError(
            "Rubric criterion must include at least one supported check: "
            "contains, not_contains, changed_file, changed_file_prefix, "
            "untracked_file, or untracked_file_prefix."
        )
    return {
        "id": criterion.get("id"),
        "description": criterion.get("description"),
        "artifact": criterion.get("artifact", "workspace_diff"),
        "phase": criterion.get("phase", "first_pass"),
        "matched": all(checks),
    }


def _evaluate_rubric_section(
    *,
    rubric: dict,
    section: str,
    run_dir: Path,
    slot: str,
    prompt_level: str,
) -> tuple[dict, ...]:
    criteria = rubric.get(section, [])
    if not isinstance(criteria, list):
        raise ValueError(f"Rubric section `{section}` must be a list.")
    return tuple(
        _evaluate_rubric_criterion(
            run_dir=run_dir,
            slot=slot,
            prompt_level=prompt_level,
            criterion=criterion,
        )
        for criterion in criteria
    )


def _rubric_label(*, success: tuple[dict, ...], partial: tuple[dict, ...], fail: tuple[dict, ...]) -> str:
    if any(item["matched"] for item in fail):
        return "fail"
    if success and all(item["matched"] for item in success):
        return "success"
    if any(item["matched"] for item in partial) or any(item["matched"] for item in success):
        return "partial"
    return "fail"


def _write_rubric_judgment(
    *,
    run_dir: Path,
    slot: str,
    prompt_level: str,
    rubric_path: Path,
    rubric: dict,
) -> dict:
    success = _evaluate_rubric_section(
        rubric=rubric,
        section="success",
        run_dir=run_dir,
        slot=slot,
        prompt_level=prompt_level,
    )
    partial = _evaluate_rubric_section(
        rubric=rubric,
        section="partial",
        run_dir=run_dir,
        slot=slot,
        prompt_level=prompt_level,
    )
    fail = _evaluate_rubric_section(
        rubric=rubric,
        section="fail",
        run_dir=run_dir,
        slot=slot,
        prompt_level=prompt_level,
    )
    label = _rubric_label(success=success, partial=partial, fail=fail)
    judgment_path = run_dir / slot / prompt_level / "rubric_judgment.json"
    payload = {
        "schema_version": RUBRIC_JUDGMENT_SCHEMA_VERSION,
        "rubric_path": str(rubric_path),
        "rubric_name": rubric.get("name"),
        "slot": slot,
        "prompt_level": prompt_level,
        "label": label,
        "judged_at": datetime.now().isoformat(timespec="seconds"),
        "criteria": {
            "success": list(success),
            "partial": list(partial),
            "fail": list(fail),
        },
    }
    _write_json(judgment_path, payload)
    payload["path"] = str(judgment_path)
    return payload


def _apply_run_score_policy(
    *,
    run_dir: Path,
    prompt_level: str,
    score_policy: str,
    rubric_path: Path | None,
    repo_root: Path,
) -> tuple[dict, ...]:
    if score_policy == "none":
        return ()
    if score_policy not in {"command-exit", "rubric"}:
        raise ValueError(
            "Invalid score policy. Expected one of: " + ", ".join(RUN_SCORE_POLICIES)
        )
    metadata = _read_run_metadata(run_dir)
    selected_rubric_path: Path | None = None
    rubric: dict | None = None
    if score_policy == "rubric":
        selected_rubric_path = rubric_path or _default_rubric_path(repo_root, metadata)
        rubric = _load_rubric(selected_rubric_path)

    score_results: list[dict] = []
    for slot_result in _read_slot_command_results(run_dir):
        slot = slot_result.get("slot")
        if not isinstance(slot, str) or not slot:
            continue
        result_prompt_level = slot_result.get("prompt_level")
        if isinstance(result_prompt_level, str) and result_prompt_level:
            selected_prompt_level = result_prompt_level
        else:
            selected_prompt_level = prompt_level
        judgment = None
        if score_policy == "rubric":
            assert selected_rubric_path is not None
            assert rubric is not None
            judgment = _write_rubric_judgment(
                run_dir=run_dir,
                slot=slot,
                prompt_level=selected_prompt_level,
                rubric_path=selected_rubric_path,
                rubric=rubric,
            )
            label = str(judgment["label"])
            rubric_refs = (str(selected_rubric_path),)
            evidence = (
                f"{slot}/{selected_prompt_level}/rubric_judgment.json",
                f"{slot}/{selected_prompt_level}/first_pass/workspace_diff.patch",
                f"{slot}/{selected_prompt_level}/first_pass/result.json",
            )
            notes = "Automatically scored by eval impact run with score_policy=rubric."
        else:
            label = _score_policy_label(slot_result)
            rubric_refs = ()
            evidence = (f"{slot}/{selected_prompt_level}/first_pass/workspace_diff.patch",)
            notes = (
                "Automatically scored by eval impact run with "
                "score_policy=command-exit. This measures Codex/save_result command "
                "completion, not semantic task correctness."
            )
        score_results.append(
            score_impact_eval_result(
                run_dir=run_dir,
                slot=slot,
                prompt_level=selected_prompt_level,
                label=label,
                rubric_refs=rubric_refs,
                evidence=evidence,
                notes=notes,
                repo_root=repo_root,
            )
        )
        if judgment is not None:
            score_results[-1]["rubric_judgment"] = judgment
    return tuple(score_results)


def _write_report_bundle(
    *,
    run_dir: Path,
    bundle_dir: Path,
    run_result: dict,
) -> dict:
    bundle_dir.mkdir(parents=True, exist_ok=True)
    manifest = generate_impact_eval_manifest(run_dir)
    report = generate_impact_eval_report(run_dir)
    paths = {
        "manifest_json": bundle_dir / "impact-manifest.json",
        "manifest_markdown": bundle_dir / "impact-manifest.md",
        "report_json": bundle_dir / "impact-report.json",
        "report_markdown": bundle_dir / "impact-report.md",
        "run_result_json": bundle_dir / "run-result.json",
    }
    paths["manifest_json"].write_text(render_impact_eval_manifest_json(manifest), encoding="utf-8")
    paths["manifest_markdown"].write_text(render_impact_eval_manifest(manifest), encoding="utf-8")
    paths["report_json"].write_text(render_impact_eval_report_json(report), encoding="utf-8")
    paths["report_markdown"].write_text(render_impact_eval_report(report), encoding="utf-8")
    paths["run_result_json"].write_text(json.dumps(run_result, indent=2) + "\n", encoding="utf-8")
    return {
        "dir": str(bundle_dir),
        "manifest_json": str(paths["manifest_json"]),
        "manifest_markdown": str(paths["manifest_markdown"]),
        "report_json": str(paths["report_json"]),
        "report_markdown": str(paths["report_markdown"]),
        "run_result_json": str(paths["run_result_json"]),
        "primary_comparison": impact_eval_report_to_dict(report)["primary_comparison"],
    }


def run_impact_eval(
    *,
    run_dir: Path,
    slots: tuple[str, ...] = (),
    all_slots: bool = False,
    prompt_level: str | None = None,
    codex_bin: str = "codex",
    sleep_guard: bool = True,
    export_sessions: bool = True,
    validate: bool = True,
    score_policy: str = DEFAULT_RUN_SCORE_POLICY,
    rubric_path: Path | None = None,
    report: bool = True,
    bundle_dir: Path | None = None,
    sessions_root: Path | None = None,
    session_index: Path | None = None,
    match_workspace_root: Path | None = None,
    export_all_sessions: bool = False,
    repo_root: Path | None = None,
) -> dict:
    if all_slots and slots:
        raise ValueError("Use either --all-slots or one or more --slot values, not both.")
    if not all_slots and not slots:
        raise ValueError("Pass --slot for a single-slot run or --all-slots for a full run.")
    if score_policy not in RUN_SCORE_POLICIES:
        raise ValueError(
            "Invalid score policy. Expected one of: " + ", ".join(RUN_SCORE_POLICIES)
        )

    resolved_run_dir = run_dir.resolve()
    metadata = _read_run_metadata(resolved_run_dir)
    selected_prompt_level = prompt_level or _metadata_prompt_level(metadata)
    selected_slots = _metadata_slots(metadata) if all_slots else tuple(slots)
    if not selected_slots:
        raise ValueError("No slots found to run.")

    repo_root_path = _resolve_eval_repo_root(repo_root)
    selected_rubric_path = None
    if score_policy == "rubric":
        selected_rubric_path = rubric_path or _default_rubric_path(repo_root_path, metadata)
    runner_command = _run_cli_slots_command(
        repo_root=repo_root_path,
        run_dir=resolved_run_dir,
        slots=selected_slots,
        prompt_level=selected_prompt_level,
        codex_bin=codex_bin,
        sleep_guard=sleep_guard,
    )
    runner_result = _run_eval_script_command(
        name="run",
        command=runner_command,
        cwd=repo_root_path,
        check=False,
    )

    score_results = _apply_run_score_policy(
        run_dir=resolved_run_dir,
        prompt_level=selected_prompt_level,
        score_policy=score_policy,
        rubric_path=selected_rubric_path,
        repo_root=repo_root_path,
    )

    workspace_root_value = metadata.get("workspace_root")
    workspace_root = Path(str(workspace_root_value)) if workspace_root_value else None
    export_result: dict | None = None
    if export_sessions:
        if workspace_root is None:
            export_result = _skipped_command_result(
                "export_sessions",
                "metadata.json does not contain workspace_root.",
            )
        else:
            selected_sessions_root = (
                sessions_root.expanduser()
                if sessions_root is not None
                else Path.home() / ".codex" / "sessions"
            )
            export_command = _export_sessions_command(
                repo_root=repo_root_path,
                workspace_root=workspace_root,
                sessions_root=sessions_root,
                session_index=session_index,
                match_workspace_root=match_workspace_root,
                slots=selected_slots,
                export_all_sessions=export_all_sessions,
            )
            if not selected_sessions_root.exists():
                export_result = _skipped_command_result(
                    "export_sessions",
                    f"Codex sessions root does not exist: {selected_sessions_root}",
                    export_command,
                )
            else:
                export_result = _run_eval_script_command(
                    name="export_sessions",
                    command=export_command,
                    cwd=repo_root_path,
                    check=False,
                )

    validate_result = (
        validate_impact_eval_run(run_dir=resolved_run_dir, repo_root=repo_root_path)
        if validate
        else None
    )
    manifest_info = _write_impact_eval_manifest_files(resolved_run_dir)
    report_payload = None
    if report:
        generated_report = generate_impact_eval_report(resolved_run_dir)
        report_payload = {
            "schema_version": "impact-eval-product-v1",
            "primary_comparison": impact_eval_report_to_dict(generated_report)[
                "primary_comparison"
            ],
            "shareable_for_causal_claims": generated_report.shareable_for_causal_claims,
            "records": len(generated_report.records),
        }

    result: dict = {
        "schema_version": "impact-eval-run-result-v1",
        "run_dir": str(resolved_run_dir),
        "slots": list(selected_slots),
        "prompt_level": selected_prompt_level,
        "codex_bin": codex_bin,
        "sleep_guard": sleep_guard,
        "score_policy": score_policy,
        "rubric_path": str(selected_rubric_path) if selected_rubric_path is not None else None,
        "runner_success": runner_result["returncode"] == 0,
        "runner_returncode": runner_result["returncode"],
        "manifest": manifest_info,
        "commands": {
            "run": runner_result,
            "export_sessions": export_result,
            "validate": validate_result.get("command") if isinstance(validate_result, dict) else None,
            "score": [item.get("command") for item in score_results],
        },
        "score_results": list(score_results),
        "validation": validate_result,
        "report": report_payload,
        "next_steps": [
            "Inspect command_result.json and final_message.md for each slot.",
            "Use semantic scoring before making research-quality correctness claims if score_policy=command-exit was used.",
            "Confirm session export and validation before publishing causal claims.",
        ],
    }
    if report:
        selected_bundle_dir = bundle_dir or (resolved_run_dir / "report_bundle")
        result["bundle"] = _write_report_bundle(
            run_dir=resolved_run_dir,
            bundle_dir=selected_bundle_dir,
            run_result=result,
        )
    return result


def run_impact_eval_benchmark(
    *,
    family: str,
    repo_root: Path | None = None,
    prompt_levels: tuple[str, ...] = DEFAULT_PLAN_PROMPT_LEVELS,
    run_label: str | None = None,
    workspace_root: Path | None = None,
    output_root: Path | None = None,
    model_family: str = DEFAULT_PLAN_MODEL,
    reasoning_effort: str = DEFAULT_PLAN_REASONING_EFFORT,
    execution_surface: str = DEFAULT_PLAN_EXECUTION_SURFACE,
    source_mode: str = DEFAULT_SOURCE_MODE,
    baseline_ref: str | None = None,
    codex_bin: str = "codex",
    sleep_guard: bool = True,
    export_sessions: bool = True,
    validate: bool = True,
    score_policy: str = DEFAULT_RUN_SCORE_POLICY,
    rubric_path: Path | None = None,
    report: bool = True,
    bundle_dir: Path | None = None,
    sessions_root: Path | None = None,
    session_index: Path | None = None,
    match_workspace_root: Path | None = None,
    export_all_sessions: bool = False,
) -> dict:
    prepare_result = prepare_impact_eval_run(
        family=family,
        repo_root=repo_root,
        prompt_levels=prompt_levels,
        run_label=run_label,
        workspace_root=workspace_root,
        output_root=output_root,
        model_family=model_family,
        reasoning_effort=reasoning_effort,
        execution_surface=execution_surface,
        source_mode=source_mode,
        baseline_ref=baseline_ref,
    )
    run_result = run_impact_eval(
        run_dir=Path(str(prepare_result["run_dir"])),
        all_slots=True,
        codex_bin=codex_bin,
        sleep_guard=sleep_guard,
        export_sessions=export_sessions,
        validate=validate,
        score_policy=score_policy,
        rubric_path=rubric_path,
        report=report,
        bundle_dir=bundle_dir,
        sessions_root=sessions_root,
        session_index=session_index,
        match_workspace_root=match_workspace_root,
        export_all_sessions=export_all_sessions,
        repo_root=repo_root,
    )
    return {
        "schema_version": BENCHMARK_RESULT_SCHEMA_VERSION,
        "family": family,
        "run_dir": prepare_result["run_dir"],
        "workspace_root": prepare_result["workspace_root"],
        "score_policy": score_policy,
        "runner_success": run_result["runner_success"],
        "prepare": prepare_result,
        "run": run_result,
        "report": run_result.get("report"),
        "bundle": run_result.get("bundle"),
        "next_steps": [
            "Inspect report_bundle/run-result.json and impact-report.md.",
            "Confirm session export and validation before publishing workflow or causal claims.",
        ],
    }


def _load_run_index(path: Path) -> dict:
    payload = _read_json_or_empty(path)
    if payload.get("schema_version") != RUN_INDEX_SCHEMA_VERSION:
        return {"schema_version": RUN_INDEX_SCHEMA_VERSION, "runs": []}
    runs = payload.get("runs")
    if not isinstance(runs, list):
        payload["runs"] = []
    return payload


def _run_index_item(*, period_id: str, result: dict, generated_at: str) -> dict:
    report = result.get("report", {})
    if not isinstance(report, dict):
        report = {}
    primary = report.get("primary_comparison", {})
    if not isinstance(primary, dict):
        primary = {}
    return {
        "period_id": period_id,
        "recorded_at": generated_at,
        "family": result.get("family"),
        "run_dir": result.get("run_dir"),
        "score_policy": result.get("score_policy"),
        "runner_success": result.get("runner_success"),
        "primary_outcome": primary.get("outcome"),
        "first_attempt_success_delta": primary.get("first_attempt_success_delta"),
        "avg_score_delta": primary.get("avg_score_delta"),
        "records": report.get("records"),
        "bundle_dir": result.get("bundle", {}).get("dir") if isinstance(result.get("bundle"), dict) else None,
    }


def _write_run_index(
    *,
    repo_root: Path,
    repo_wiki_dir: Path | None,
    items: list[dict],
) -> dict:
    path = _run_index_path(repo_root, repo_wiki_dir)
    index = _load_run_index(path)
    runs = index.get("runs", [])
    if not isinstance(runs, list):
        runs = []
    runs.extend(items)
    payload = {
        "schema_version": RUN_INDEX_SCHEMA_VERSION,
        "updated_at": _now_iso(),
        "runs": runs,
    }
    _write_json(path, payload)
    return {"path": str(path), "run_count": len(runs)}


def generate_impact_eval_schedule_report(
    *,
    repo_root: Path | None = None,
    repo_wiki_dir: Path | None = None,
    period_id: str | None = None,
    refresh_candidates: bool = True,
    handle: str | None = None,
    since: str | None = None,
    candidate_max_items: int = DEFAULT_DIAGNOSTICS_MAX_ITEMS,
    include_not_ready: bool = True,
    max_recent_runs: int = 20,
) -> dict:
    resolved_repo_root = _resolve_eval_repo_root(repo_root)
    selected_repo_wiki_dir = _repo_wiki_dir(resolved_repo_root, repo_wiki_dir)
    selected_period_id = period_id or _period_id()
    generated_at = _now_iso()
    families = discover_impact_eval_families(repo_root=resolved_repo_root)
    queue = (
        refresh_impact_eval_candidate_queue(
            repo_root=resolved_repo_root,
            repo_wiki_dir=selected_repo_wiki_dir,
            handle=handle,
            since=since,
            max_items=candidate_max_items,
            include_not_ready=include_not_ready,
        )
        if refresh_candidates
        else _read_json_or_empty(_candidate_queue_paths(resolved_repo_root, selected_repo_wiki_dir)["latest_json"])
    )
    run_index = _load_run_index(_run_index_path(resolved_repo_root, selected_repo_wiki_dir))
    runs = run_index.get("runs", [])
    if not isinstance(runs, list):
        runs = []
    recent_runs = runs[-max_recent_runs:]
    paths = _schedule_report_paths(resolved_repo_root, selected_period_id, selected_repo_wiki_dir)
    status_counts = queue.get("summary", {}).get("status_counts", {}) if isinstance(queue, dict) else {}
    if not isinstance(status_counts, dict):
        status_counts = {}
    payload = {
        "schema_version": SCHEDULE_REPORT_SCHEMA_VERSION,
        "generated_at": generated_at,
        "period_id": selected_period_id,
        "repo_root": str(resolved_repo_root),
        "repo_wiki_dir": str(selected_repo_wiki_dir),
        "summary": {
            "formal_family_count": families["family_count"],
            "runnable_family_count": families["runnable_count"],
            "candidate_status_counts": dict(sorted(status_counts.items())),
            "indexed_run_count": len(runs),
            "recent_run_count": len(recent_runs),
        },
        "candidate_filters": {
            "handle": handle,
            "since": since,
            "max_items": candidate_max_items,
            "include_not_ready": include_not_ready,
            "refreshed": refresh_candidates,
        },
        "families": families["families"],
        "candidate_queue": {
            "summary": queue.get("summary", {}) if isinstance(queue, dict) else {},
            "outputs": queue.get("outputs", {}) if isinstance(queue, dict) else {},
        },
        "recent_runs": recent_runs,
        "outputs": {
            "json": str(paths["json"]),
            "markdown": str(paths["markdown"]),
            "latest_json": str(paths["latest_json"]),
            "latest_markdown": str(paths["latest_markdown"]),
        },
    }
    _write_json(paths["json"], payload)
    rendered = render_impact_eval_schedule_report(payload)
    paths["markdown"].parent.mkdir(parents=True, exist_ok=True)
    paths["markdown"].write_text(rendered, encoding="utf-8")
    _write_json(paths["latest_json"], payload)
    paths["latest_markdown"].write_text(rendered, encoding="utf-8")
    return payload


def run_impact_eval_schedule(
    *,
    repo_root: Path | None = None,
    repo_wiki_dir: Path | None = None,
    families: tuple[str, ...] = (),
    all_runnable: bool = False,
    period_id: str | None = None,
    if_due: bool = False,
    force: bool = False,
    handle: str | None = None,
    since: str | None = None,
    candidate_max_items: int = DEFAULT_DIAGNOSTICS_MAX_ITEMS,
    include_not_ready: bool = True,
    prompt_levels: tuple[str, ...] = DEFAULT_PLAN_PROMPT_LEVELS,
    model_family: str = DEFAULT_PLAN_MODEL,
    reasoning_effort: str = DEFAULT_PLAN_REASONING_EFFORT,
    source_mode: str = DEFAULT_SOURCE_MODE,
    codex_bin: str = "codex",
    sleep_guard: bool = True,
    export_sessions: bool = True,
    validate: bool = True,
    score_policy: str = DEFAULT_RUN_SCORE_POLICY,
    rubric_path: Path | None = None,
    sessions_root: Path | None = None,
    session_index: Path | None = None,
    match_workspace_root: Path | None = None,
    export_all_sessions: bool = False,
) -> dict:
    if all_runnable and families:
        raise ValueError("Use either --all-runnable or one or more --family values, not both.")
    if not all_runnable and not families:
        raise ValueError("Pass --family or --all-runnable.")
    resolved_repo_root = _resolve_eval_repo_root(repo_root)
    selected_repo_wiki_dir = _repo_wiki_dir(resolved_repo_root, repo_wiki_dir)
    selected_period_id = period_id or _period_id()
    state_path = _schedule_state_path(resolved_repo_root, selected_repo_wiki_dir)
    state = _read_json_or_empty(state_path)
    if (
        if_due
        and not force
        and state.get("last_period_id") == selected_period_id
    ):
        report = generate_impact_eval_schedule_report(
            repo_root=resolved_repo_root,
            repo_wiki_dir=selected_repo_wiki_dir,
            period_id=selected_period_id,
            refresh_candidates=True,
            handle=handle,
            since=since,
            candidate_max_items=candidate_max_items,
            include_not_ready=include_not_ready,
        )
        return {
            "schema_version": SCHEDULE_RUN_SCHEMA_VERSION,
            "status": "skipped",
            "reason": "schedule already ran for this period",
            "period_id": selected_period_id,
            "report": report,
            "runs": [],
        }
    if all_runnable:
        discovery = discover_impact_eval_families(repo_root=resolved_repo_root)
        selected_families = tuple(
            str(family["name"])
            for family in discovery["families"]
            if isinstance(family, dict) and family.get("status") == "runnable"
        )
    else:
        selected_families = families
    generated_at = _now_iso()
    run_results: list[dict] = []
    index_items: list[dict] = []
    for family in selected_families:
        result = run_impact_eval_benchmark(
            family=family,
            repo_root=resolved_repo_root,
            prompt_levels=prompt_levels,
            run_label=f"{selected_period_id}-{family}",
            model_family=model_family,
            reasoning_effort=reasoning_effort,
            source_mode=source_mode,
            codex_bin=codex_bin,
            sleep_guard=sleep_guard,
            export_sessions=export_sessions,
            validate=validate,
            score_policy=score_policy,
            rubric_path=rubric_path,
            sessions_root=sessions_root,
            session_index=session_index,
            match_workspace_root=match_workspace_root,
            export_all_sessions=export_all_sessions,
        )
        run_results.append(result)
        index_items.append(
            _run_index_item(
                period_id=selected_period_id,
                result=result,
                generated_at=generated_at,
            )
        )
    run_index = _write_run_index(
        repo_root=resolved_repo_root,
        repo_wiki_dir=selected_repo_wiki_dir,
        items=index_items,
    )
    report = generate_impact_eval_schedule_report(
        repo_root=resolved_repo_root,
        repo_wiki_dir=selected_repo_wiki_dir,
        period_id=selected_period_id,
        refresh_candidates=True,
        handle=handle,
        since=since,
        candidate_max_items=candidate_max_items,
        include_not_ready=include_not_ready,
    )
    _write_json(
        state_path,
        {
            "schema_version": SCHEDULE_RUN_SCHEMA_VERSION,
            "last_period_id": selected_period_id,
            "last_ran_at": generated_at,
            "families": list(selected_families),
            "run_index": run_index,
            "report": report["outputs"],
        },
    )
    return {
        "schema_version": SCHEDULE_RUN_SCHEMA_VERSION,
        "status": "ran",
        "period_id": selected_period_id,
        "families": list(selected_families),
        "runs": run_results,
        "run_index": run_index,
        "report": report,
    }


def _format_rate(summary: ImpactVariantSummary | None) -> str:
    if summary is None:
        return "-"
    rate = summary.first_attempt_success_rate
    if rate is None:
        return "pending"
    return f"{summary.first_attempt_successes}/{summary.known_first_attempt_results} ({rate:.0%})"


def _format_float(value: float | None) -> str:
    if value is None:
        return "-"
    return f"{value:.2f}"


def _format_delta(value: float | None, *, percent: bool = False) -> str:
    if value is None:
        return "-"
    if percent:
        return f"{value:+.0%}"
    return f"{value:+.2f}"


def _format_bool(value: bool | None) -> str:
    if value is True:
        return "yes"
    if value is False:
        return "no"
    return "pending"


def _summary_delta(
    no_aiwiki: ImpactVariantSummary | None,
    aiwiki: ImpactVariantSummary | None,
    field_name: str,
) -> float | None:
    if no_aiwiki is None or aiwiki is None:
        return None
    no_value = getattr(no_aiwiki, field_name)
    aiwiki_value = getattr(aiwiki, field_name)
    if no_value is None or aiwiki_value is None:
        return None
    return aiwiki_value - no_value


def _signal_counts(summaries: tuple[ImpactEvalRunSummary, ...], field_name: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for summary in summaries:
        value = str(getattr(summary, field_name))
        counts[value] = counts.get(value, 0) + 1
    return dict(sorted(counts.items()))


def _format_counts(counts: dict[str, int]) -> str:
    if not counts:
        return "-"
    return ", ".join(f"{key}={value}" for key, value in counts.items())


def _markdown_table(headers: list[str], rows: list[list[str]]) -> str:
    if not rows:
        return "_No rows._"
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]
    lines.extend(
        "| " + " | ".join(cell.replace("|", "\\|") for cell in row) + " |"
        for row in rows
    )
    return "\n".join(lines)


def render_impact_eval_manifest(manifest: dict) -> str:
    prompts = manifest.get("prompts", [])
    prompt_rows = [
        [str(prompt.get("level", "")), str(prompt.get("sha256") or "-")]
        for prompt in prompts
        if isinstance(prompt, dict)
    ]

    slot_rows: list[list[str]] = []
    for slot in manifest.get("slots", []):
        if not isinstance(slot, dict):
            continue
        for prompt_level in slot.get("prompt_levels", []):
            if not isinstance(prompt_level, dict):
                continue
            level = str(prompt_level.get("level", ""))
            captures = prompt_level.get("captures", [])
            if not isinstance(captures, list):
                continue
            for capture in captures:
                if not isinstance(capture, dict):
                    continue
                artifacts = capture.get("artifacts", {})
                if not isinstance(artifacts, dict):
                    artifacts = {}
                slot_rows.append(
                    [
                        str(slot.get("slot", "")),
                        str(slot.get("variant", "")),
                        level,
                        str(capture.get("phase", "")),
                        str(capture.get("score_label") or "-"),
                        _format_bool(capture.get("first_attempt_success")),
                        str(capture.get("changed_file_count", 0)),
                        str(capture.get("untracked_file_count", 0)),
                        str(artifacts.get("result") or "-"),
                        str(artifacts.get("score") or "-"),
                        str(artifacts.get("workspace_diff") or "-"),
                        str(slot.get("visible_transcript") or "-"),
                    ]
                )

    slot_mapping_rows = [
        [
            str(slot.get("slot", "")),
            str(slot.get("variant", "")),
            str(slot.get("workspace") or "-"),
        ]
        for slot in manifest.get("slots", [])
        if isinstance(slot, dict)
    ]
    agent_command = manifest.get("agent_command", {})
    if not isinstance(agent_command, dict):
        agent_command = {}
    confounds = manifest.get("confounds", {})
    if not isinstance(confounds, dict):
        confounds = {}
    artifact_summary = manifest.get("artifact_summary", {})
    if not isinstance(artifact_summary, dict):
        artifact_summary = {}

    lines = [
        "# AI Wiki Impact Eval Run Manifest",
        "",
        f"- Run dir: `{manifest.get('run_dir')}`",
        f"- Experiment: `{manifest.get('experiment', 'unknown')}`",
        f"- Baseline ref: `{manifest.get('baseline_ref') or 'unknown'}`",
        f"- Workspace layout: `{manifest.get('workspace_layout') or 'unknown'}`",
        f"- Model: `{manifest.get('model') or 'unknown'}`",
        f"- Reasoning effort: `{manifest.get('reasoning_effort') or 'unknown'}`",
        f"- Execution surface: `{manifest.get('execution_surface') or 'unknown'}`",
        f"- Agent command family: `{agent_command.get('command_family') or 'unknown'}`",
        f"- Primary comparison: `{', '.join(manifest.get('primary_comparison', [])) or 'unknown'}`",
        f"- Diagnostic variants: `{', '.join(manifest.get('diagnostic_variants', [])) or 'none'}`",
        f"- Captured records: `{artifact_summary.get('records', 0)}`",
        f"- First-attempt records: `{artifact_summary.get('first_attempt_records', 0)}`",
        f"- Causal claims ready: `{_format_bool(confounds.get('shareable_for_causal_claims'))}`",
        f"- Critical confounds: `{confounds.get('critical_confounds', 0)}`",
        "",
        "## Prompts",
        "",
        _markdown_table(["level", "sha256"], prompt_rows),
        "",
        "## Slot Mapping",
        "",
        _markdown_table(["slot", "variant", "workspace"], slot_mapping_rows),
        "",
        "## Captured Artifacts",
        "",
        _markdown_table(
            [
                "slot",
                "variant",
                "prompt",
                "phase",
                "score",
                "first_attempt_success",
                "changed_files",
                "untracked_files",
                "result",
                "score_file",
                "workspace_diff",
                "visible_transcript",
            ],
            slot_rows,
        ),
        "",
    ]
    return "\n".join(lines)


def render_impact_eval_manifest_json(manifest: dict) -> str:
    return json.dumps(manifest, indent=2) + "\n"


def _command_block(command: list[str]) -> str:
    return "```bash\n" + _command_text(command) + "\n```"


def _source_incident_active_mins(value: object) -> str:
    if not isinstance(value, dict):
        return "not_recorded"
    if value.get("status") != "measured":
        return "not_recorded"
    seconds = value.get("active_seconds")
    if not isinstance(seconds, int):
        return "not_recorded"
    return f"{seconds / 60:.1f}"


def _candidate_source_incident_active_mins(candidate: dict) -> str:
    evidence = candidate.get("evidence")
    if not isinstance(evidence, dict):
        return "not_recorded"
    return _source_incident_active_mins(evidence.get("source_incident_timing"))


def render_impact_eval_candidate_queue(result: dict) -> str:
    rows = [
        [
            str(item.get("candidate_id", "")),
            str(item.get("status", "")),
            str(item.get("doc_id") or item.get("task_id") or ""),
            _candidate_source_incident_active_mins(item),
            str(item.get("seen_count", "")),
            ", ".join(item.get("readiness", {}).get("missing", []))
            if isinstance(item.get("readiness"), dict)
            else "",
        ]
        for item in result.get("candidates", [])
        if isinstance(item, dict)
    ]
    lines = [
        "# AI Wiki Impact Eval Candidate Queue",
        "",
        f"- Generated at: `{result.get('generated_at')}`",
        f"- Repo root: `{result.get('repo_root')}`",
        f"- Active candidates: `{result.get('summary', {}).get('active_count')}`",
        f"- Stale candidates: `{result.get('summary', {}).get('stale_count')}`",
        f"- Status counts: `{result.get('summary', {}).get('status_counts')}`",
        "",
        _markdown_table(
            ["candidate", "status", "source", "source_active_mins", "seen_count", "missing"],
            rows,
        ),
        "",
    ]
    return "\n".join(lines)


def render_impact_eval_candidate_queue_json(result: dict) -> str:
    return json.dumps(result, indent=2) + "\n"


def render_impact_eval_candidate_draft_result(result: dict) -> str:
    paths = result.get("paths", {})
    if not isinstance(paths, dict):
        paths = {}
    readiness = result.get("readiness", {})
    if not isinstance(readiness, dict):
        readiness = {}
    lines = [
        "# AI Wiki Impact Eval Candidate Draft",
        "",
        f"- Candidate: `{result.get('candidate_id')}`",
        f"- Family: `{result.get('family')}`",
        f"- Status: `{result.get('status')}`",
        f"- Missing: `{', '.join(readiness.get('missing', [])) or 'none'}`",
        "",
        "## Paths",
        "",
        _markdown_table(["artifact", "path"], [[str(name), str(path)] for name, path in sorted(paths.items())]),
        "",
    ]
    return "\n".join(lines)


def render_impact_eval_candidate_draft_result_json(result: dict) -> str:
    return json.dumps(result, indent=2) + "\n"


def render_impact_eval_candidate_promotion_result(result: dict) -> str:
    paths = result.get("formal_paths", {})
    if not isinstance(paths, dict):
        paths = {}
    lines = [
        "# AI Wiki Impact Eval Candidate Promotion",
        "",
        f"- Candidate: `{result.get('candidate_id')}`",
        f"- Family: `{result.get('family')}`",
        f"- Apply: `{_format_bool(result.get('apply'))}`",
        f"- Promotable: `{_format_bool(result.get('promotable'))}`",
        f"- Blockers: `{', '.join(result.get('blockers', [])) or 'none'}`",
        "",
        "## Formal Paths",
        "",
        _markdown_table(["artifact", "path"], [[str(name), str(path)] for name, path in sorted(paths.items())]),
        "",
    ]
    return "\n".join(lines)


def render_impact_eval_candidate_promotion_result_json(result: dict) -> str:
    return json.dumps(result, indent=2) + "\n"


def render_impact_eval_families(result: dict) -> str:
    rows = [
        [
            str(family.get("name", "")),
            str(family.get("status", "")),
            "yes" if family.get("prompt_present") else "no",
            "yes" if family.get("rubric_present") else "no",
            str(family.get("baseline_ref", "")),
            str(family.get("historical_issue", "")),
        ]
        for family in result.get("families", [])
        if isinstance(family, dict)
    ]
    lines = [
        "# AI Wiki Impact Eval Families",
        "",
        f"- Repo root: `{result.get('repo_root')}`",
        f"- Families root: `{result.get('families_root')}`",
        f"- Families: `{result.get('family_count')}`",
        f"- Runnable: `{result.get('runnable_count')}`",
        "",
        _markdown_table(
            ["family", "status", "prompt", "rubric", "baseline", "historical_issue"],
            rows,
        ),
        "",
        "Use `aiwiki-toolkit eval impact family show <family>` for details.",
        "",
    ]
    return "\n".join(lines)


def render_impact_eval_families_json(result: dict) -> str:
    return json.dumps(result, indent=2) + "\n"


def render_impact_eval_family_detail(result: dict) -> str:
    family = result.get("family", {})
    if not isinstance(family, dict):
        family = {}
    fixtures = family.get("memory_fixtures", {})
    if not isinstance(fixtures, dict):
        fixtures = {}
    prompts = result.get("prompts", [])
    prompt_rows = [
        [str(prompt.get("level", "")), str(prompt.get("sha256", "")), str(prompt.get("path", ""))]
        for prompt in prompts
        if isinstance(prompt, dict)
    ]
    command_rows = [
        [str(name), _command_text(command) if isinstance(command, list) else ""]
        for name, command in sorted(family.get("next_commands", {}).items())
    ]
    lines = [
        "# AI Wiki Impact Eval Family",
        "",
        f"- Family: `{family.get('name')}`",
        f"- Status: `{family.get('status')}`",
        f"- Spec: `{family.get('spec_path')}`",
        f"- Baseline ref: `{family.get('baseline_ref')}`",
        f"- Historical issue: {family.get('historical_issue') or '-'}",
        f"- Prompt family: `{family.get('prompt_family')}`",
        f"- Prompt present: `{_format_bool(family.get('prompt_present'))}`",
        f"- Rubric present: `{_format_bool(family.get('rubric_present'))}`",
        f"- Rubric path: `{family.get('rubric_path')}`",
        "",
        "## Memory Fixtures",
        "",
        _markdown_table(
            ["fixture", "count"],
            [[str(name), str(value)] for name, value in sorted(fixtures.items())],
        ),
        "",
        "## Prompts",
        "",
        _markdown_table(["level", "sha256", "path"], prompt_rows),
        "",
        "## Next Commands",
        "",
        _markdown_table(["name", "command"], command_rows),
        "",
    ]
    return "\n".join(lines)


def render_impact_eval_family_detail_json(result: dict) -> str:
    return json.dumps(result, indent=2) + "\n"


def render_impact_eval_family_candidates(result: dict) -> str:
    rows = [
        [
            str(candidate.get("candidate_id", "")),
            str(candidate.get("status", "")),
            str(candidate.get("doc_id") or candidate.get("task_id") or ""),
            _candidate_source_incident_active_mins(candidate),
            ", ".join(candidate.get("readiness", {}).get("missing", [])),
        ]
        for candidate in result.get("candidates", [])
        if isinstance(candidate, dict)
    ]
    lines = [
        "# AI Wiki Impact Eval Family Candidates",
        "",
        f"- Repo root: `{result.get('repo_root')}`",
        f"- Repo wiki: `{result.get('repo_wiki_dir')}`",
        f"- Candidates: `{result.get('summary', {}).get('candidate_count')}`",
        "",
        _markdown_table(
            ["candidate", "status", "source", "source_active_mins", "missing"],
            rows,
        ),
        "",
        "Candidates are discovery hints. Create formal families only after confirming the source incident, baseline, prompt, and rubric.",
        "",
    ]
    return "\n".join(lines)


def render_impact_eval_family_candidates_json(result: dict) -> str:
    return json.dumps(result, indent=2) + "\n"


def render_impact_eval_family_init_result(result: dict) -> str:
    lines = [
        "# AI Wiki Impact Eval Family Init",
        "",
        f"- Family: `{result.get('family')}`",
        f"- From candidate: `{result.get('from_candidate')}`",
        f"- Baseline ref: `{result.get('baseline_ref')}`",
        "",
        "## Created Or Updated",
        "",
        "\n".join(f"- `{path}`" for path in result.get("created_or_updated", [])),
        "",
        "## Next Commands",
        "",
        _markdown_table(
            ["name", "command"],
            [
                [str(name), _command_text(command) if isinstance(command, list) else ""]
                for name, command in sorted(result.get("next_commands", {}).items())
            ],
        ),
        "",
    ]
    return "\n".join(lines)


def render_impact_eval_family_init_result_json(result: dict) -> str:
    return json.dumps(result, indent=2) + "\n"


def render_impact_eval_benchmark_result(result: dict) -> str:
    run = result.get("run", {})
    if not isinstance(run, dict):
        run = {}
    report = result.get("report", {})
    if not isinstance(report, dict):
        report = {}
    primary = report.get("primary_comparison", {})
    if not isinstance(primary, dict):
        primary = {}
    lines = [
        "# AI Wiki Impact Eval Benchmark Result",
        "",
        f"- Family: `{result.get('family')}`",
        f"- Run dir: `{result.get('run_dir')}`",
        f"- Workspace root: `{result.get('workspace_root')}`",
        f"- Score policy: `{result.get('score_policy')}`",
        f"- Runner success: `{_format_bool(result.get('runner_success'))}`",
        f"- Primary outcome: `{primary.get('outcome', 'pending')}`",
        f"- First-attempt success delta: `{_format_delta(primary.get('first_attempt_success_delta'), percent=True)}`",
        f"- Bundle: `{(result.get('bundle') or {}).get('dir') if isinstance(result.get('bundle'), dict) else '-'}`",
        "",
        "## Next Steps",
        "",
        "\n".join(f"{index}. {step}" for index, step in enumerate(result.get("next_steps", []), start=1)),
        "",
    ]
    return "\n".join(lines)


def render_impact_eval_benchmark_result_json(result: dict) -> str:
    return json.dumps(result, indent=2) + "\n"


def render_impact_eval_schedule_report(result: dict) -> str:
    summary = result.get("summary", {})
    if not isinstance(summary, dict):
        summary = {}
    recent_rows = [
        [
            str(item.get("period_id", "")),
            str(item.get("family", "")),
            str(item.get("runner_success", "")),
            str(item.get("primary_outcome", "")),
            str(item.get("run_dir", "")),
        ]
        for item in result.get("recent_runs", [])
        if isinstance(item, dict)
    ]
    lines = [
        "# AI Wiki Impact Eval Schedule Report",
        "",
        f"- Period: `{result.get('period_id')}`",
        f"- Generated at: `{result.get('generated_at')}`",
        f"- Runnable families: `{summary.get('runnable_family_count')}`",
        f"- Candidate status counts: `{summary.get('candidate_status_counts')}`",
        f"- Indexed runs: `{summary.get('indexed_run_count')}`",
    ]
    filters = result.get("candidate_filters", {})
    if isinstance(filters, dict):
        lines.extend(
            [
                f"- Candidate handle: `{filters.get('handle') or 'all'}`",
                f"- Candidate max items: `{filters.get('max_items')}`",
            ]
        )
    lines.extend(
        [
            "",
            "## Recent Runs",
            "",
            _markdown_table(
                ["period", "family", "success", "outcome", "run_dir"],
                recent_rows,
            ),
            "",
        ]
    )
    return "\n".join(lines)


def render_impact_eval_schedule_report_json(result: dict) -> str:
    return json.dumps(result, indent=2) + "\n"


def render_impact_eval_schedule_run_result(result: dict) -> str:
    rows = [
        [
            str(item.get("family", "")),
            str(item.get("runner_success", "")),
            str(item.get("run_dir", "")),
        ]
        for item in result.get("runs", [])
        if isinstance(item, dict)
    ]
    lines = [
        "# AI Wiki Impact Eval Schedule Run",
        "",
        f"- Status: `{result.get('status')}`",
        f"- Period: `{result.get('period_id')}`",
        f"- Families: `{', '.join(result.get('families', []))}`",
        f"- Reason: `{result.get('reason') or '-'}`",
        "",
        _markdown_table(["family", "success", "run_dir"], rows),
        "",
    ]
    return "\n".join(lines)


def render_impact_eval_schedule_run_result_json(result: dict) -> str:
    return json.dumps(result, indent=2) + "\n"


def render_impact_eval_run_plan(plan: dict) -> str:
    family_spec = plan.get("family_spec", {})
    workspace = plan.get("workspace", {})
    execution = plan.get("execution", {})
    comparison = plan.get("comparison", {})
    commands = plan.get("commands", {})
    prompts = plan.get("prompts", [])
    manual_steps = plan.get("manual_steps", [])
    if not isinstance(family_spec, dict):
        family_spec = {}
    if not isinstance(workspace, dict):
        workspace = {}
    if not isinstance(execution, dict):
        execution = {}
    if not isinstance(comparison, dict):
        comparison = {}
    if not isinstance(commands, dict):
        commands = {}
    prompt_rows = [
        [
            str(prompt.get("level", "")),
            str(prompt.get("sha256", "")),
            str(prompt.get("path", "")),
        ]
        for prompt in prompts
        if isinstance(prompt, dict)
    ]
    command_sections: list[str] = []
    for label in (
        "prepare_variants",
        "init_run",
        "run_all_slots",
        "manual_capture_template",
        "manual_score_template",
    ):
        command = commands.get(label)
        if isinstance(command, list):
            command_sections.extend([f"### {label}", "", _command_block(command), ""])
    run_commands = commands.get("run_slots")
    if isinstance(run_commands, list):
        for index, command in enumerate(run_commands, start=1):
            if isinstance(command, list):
                command_sections.extend(
                    [f"### run_slots {index}", "", _command_block(command), ""]
                )
    post_run = commands.get("post_run")
    if isinstance(post_run, list):
        for command in post_run:
            if isinstance(command, list):
                command_sections.extend(["### post_run", "", _command_block(command), ""])

    lines = [
        "# AI Wiki Impact Eval Run Plan",
        "",
        f"- Family: `{plan.get('family')}`",
        f"- Repo root: `{plan.get('repo_root')}`",
        f"- Spec: `{family_spec.get('path')}`",
        f"- Baseline ref: `{family_spec.get('baseline_ref')}`",
        f"- Historical issue: {family_spec.get('historical_issue') or '-'}",
        f"- Workspace root: `{workspace.get('workspace_root')}`",
        f"- Run dir: `{workspace.get('run_dir')}`",
        f"- Source mode: `{workspace.get('source_mode')}`",
        f"- Workspace layout: `{workspace.get('workspace_layout')}`",
        f"- Model: `{execution.get('model')}`",
        f"- Reasoning effort: `{execution.get('reasoning_effort')}`",
        f"- Execution surface: `{execution.get('execution_surface')}`",
        f"- Auto-invokes agent: `{_format_bool(execution.get('auto_invokes_agent'))}`",
        f"- Primary comparison: `{', '.join(comparison.get('primary', [])) or 'unknown'}`",
        f"- Diagnostic variants: `{', '.join(comparison.get('diagnostic', [])) or 'none'}`",
        "",
        "## Prompts",
        "",
        _markdown_table(["level", "sha256", "path"], prompt_rows),
        "",
        "## Commands",
        "",
        *command_sections,
        "## Manual Steps",
        "",
        "\n".join(f"{index}. {step}" for index, step in enumerate(manual_steps, start=1)),
        "",
    ]
    return "\n".join(lines)


def render_impact_eval_run_plan_json(plan: dict) -> str:
    return json.dumps(plan, indent=2) + "\n"


def render_impact_eval_prepare_result(result: dict) -> str:
    manifest = result.get("manifest", {})
    commands = result.get("commands", [])
    next_steps = result.get("next_steps", [])
    if not isinstance(manifest, dict):
        manifest = {}
    command_rows = [
        [
            str(command.get("name", "")),
            str(command.get("returncode", "")),
            _command_text(command.get("command", []))
            if isinstance(command.get("command"), list)
            else "",
        ]
        for command in commands
        if isinstance(command, dict)
    ]
    lines = [
        "# AI Wiki Impact Eval Prepare Result",
        "",
        f"- Family: `{result.get('family')}`",
        f"- Workspace root: `{result.get('workspace_root')}`",
        f"- Run dir: `{result.get('run_dir')}`",
        f"- Manifest JSON: `{manifest.get('json')}`",
        f"- Manifest Markdown: `{manifest.get('markdown')}`",
        "",
        "## Commands",
        "",
        _markdown_table(["step", "returncode", "command"], command_rows),
        "",
        "## Next Steps",
        "",
        "\n".join(f"{index}. {step}" for index, step in enumerate(next_steps, start=1)),
        "",
    ]
    return "\n".join(lines)


def render_impact_eval_prepare_result_json(result: dict) -> str:
    return json.dumps(result, indent=2) + "\n"


def _render_manifest_lines(result: dict) -> list[str]:
    manifest = result.get("manifest", {})
    if not isinstance(manifest, dict):
        manifest = {}
    return [
        f"- Manifest JSON: `{manifest.get('json')}`",
        f"- Manifest Markdown: `{manifest.get('markdown')}`",
    ]


def _render_command_lines(result: dict) -> list[str]:
    command = result.get("command", {})
    if not isinstance(command, dict):
        return []
    raw_command = command.get("command", [])
    command_text = _command_text(raw_command) if isinstance(raw_command, list) else ""
    return [
        "## Command",
        "",
        _markdown_table(
            ["step", "returncode", "command"],
            [[str(command.get("name", "")), str(command.get("returncode", "")), command_text]],
        ),
        "",
    ]


def render_impact_eval_capture_result(result: dict) -> str:
    artifacts = result.get("artifacts", {})
    next_steps = result.get("next_steps", [])
    if not isinstance(artifacts, dict):
        artifacts = {}
    artifact_rows = [[str(name), str(path)] for name, path in sorted(artifacts.items())]
    lines = [
        "# AI Wiki Impact Eval Capture Result",
        "",
        f"- Run dir: `{result.get('run_dir')}`",
        f"- Slot: `{result.get('slot')}`",
        f"- Variant: `{result.get('variant')}`",
        f"- Prompt level: `{result.get('prompt_level')}`",
        f"- Phase: `{result.get('phase')}`",
        f"- Workspace: `{result.get('workspace')}`",
        f"- Result dir: `{result.get('result_dir')}`",
        *_render_manifest_lines(result),
        "",
        "## Artifacts",
        "",
        _markdown_table(["artifact", "path"], artifact_rows),
        "",
        *_render_command_lines(result),
        "## Next Steps",
        "",
        "\n".join(f"{index}. {step}" for index, step in enumerate(next_steps, start=1)),
        "",
    ]
    return "\n".join(lines)


def render_impact_eval_capture_result_json(result: dict) -> str:
    return json.dumps(result, indent=2) + "\n"


def render_impact_eval_validate_result(result: dict) -> str:
    lines = [
        "# AI Wiki Impact Eval Validate Result",
        "",
        f"- Run dir: `{result.get('run_dir')}`",
        f"- Session export root: `{result.get('session_export_root') or 'default'}`",
        f"- Confounds path: `{result.get('confounds_path')}`",
        f"- Causal claims ready: `{_format_bool(result.get('shareable_for_causal_claims'))}`",
        f"- Critical confounds: `{result.get('critical_confounds')}`",
        f"- Warnings: `{result.get('warnings')}`",
        *_render_manifest_lines(result),
        "",
        *_render_command_lines(result),
    ]
    return "\n".join(lines)


def render_impact_eval_validate_result_json(result: dict) -> str:
    return json.dumps(result, indent=2) + "\n"


def render_impact_eval_score_result(result: dict) -> str:
    next_steps = result.get("next_steps", [])
    lines = [
        "# AI Wiki Impact Eval Score Result",
        "",
        f"- Run dir: `{result.get('run_dir')}`",
        f"- Slot: `{result.get('slot')}`",
        f"- Prompt level: `{result.get('prompt_level')}`",
        f"- Label: `{result.get('label')}`",
        f"- Score path: `{result.get('score_path')}`",
        *_render_manifest_lines(result),
        "",
        *_render_command_lines(result),
        "## Next Steps",
        "",
        "\n".join(f"{index}. {step}" for index, step in enumerate(next_steps, start=1)),
        "",
    ]
    return "\n".join(lines)


def render_impact_eval_score_result_json(result: dict) -> str:
    return json.dumps(result, indent=2) + "\n"


def render_impact_eval_run_result(result: dict) -> str:
    commands = result.get("commands", {})
    if not isinstance(commands, dict):
        commands = {}
    run_command = commands.get("run", {})
    if not isinstance(run_command, dict):
        run_command = {}
    validation = result.get("validation")
    if not isinstance(validation, dict):
        validation = {}
    report = result.get("report")
    if not isinstance(report, dict):
        report = {}
    bundle = result.get("bundle")
    if not isinstance(bundle, dict):
        bundle = {}
    score_results = result.get("score_results", [])
    if not isinstance(score_results, list):
        score_results = []
    score_rows = [
        [
            str(item.get("slot", "")),
            str(item.get("prompt_level", "")),
            str(item.get("label", "")),
            str(item.get("score_path", "")),
        ]
        for item in score_results
        if isinstance(item, dict)
    ]
    primary = report.get("primary_comparison", {})
    if not isinstance(primary, dict):
        primary = {}
    lines = [
        "# AI Wiki Impact Eval Run Result",
        "",
        f"- Run dir: `{result.get('run_dir')}`",
        f"- Slots: `{', '.join(result.get('slots', []))}`",
        f"- Prompt level: `{result.get('prompt_level')}`",
        f"- Codex bin: `{result.get('codex_bin')}`",
        f"- Sleep guard: `{_format_bool(result.get('sleep_guard'))}`",
        f"- Score policy: `{result.get('score_policy')}`",
        f"- Rubric path: `{result.get('rubric_path') or '-'}`",
        f"- Runner success: `{_format_bool(result.get('runner_success'))}`",
        f"- Runner return code: `{result.get('runner_returncode')}`",
        f"- Causal claims ready: `{_format_bool(validation.get('shareable_for_causal_claims'))}`",
        f"- Critical confounds: `{validation.get('critical_confounds', '-')}`",
        f"- Primary outcome: `{primary.get('outcome', 'pending')}`",
        f"- First-attempt success delta: `{_format_delta(primary.get('first_attempt_success_delta'), percent=True)}`",
        "",
        "## Run Command",
        "",
        _markdown_table(
            ["step", "returncode", "command"],
            [
                [
                    str(run_command.get("name", "run")),
                    str(run_command.get("returncode", "")),
                    _command_text(run_command.get("command", []))
                    if isinstance(run_command.get("command"), list)
                    else "",
                ]
            ],
        ),
        "",
        "## Score Results",
        "",
        _markdown_table(["slot", "prompt", "label", "score_path"], score_rows),
        "",
        "## Bundle",
        "",
        _markdown_table(
            ["artifact", "path"],
            [[str(name), str(path)] for name, path in sorted(bundle.items())],
        ),
        "",
    ]
    return "\n".join(lines)


def render_impact_eval_run_result_json(result: dict) -> str:
    return json.dumps(result, indent=2) + "\n"


def render_impact_eval_report(report: ImpactEvalReport) -> str:
    metadata = report.metadata
    comparison = report.primary_comparison
    shareable = report.shareable_for_causal_claims
    no_aiwiki = comparison.no_aiwiki
    aiwiki = comparison.aiwiki
    no_aiwiki_label = no_aiwiki.variant if no_aiwiki else PRIMARY_NO_AIWIKI_VARIANT
    aiwiki_label = aiwiki.variant if aiwiki else PRIMARY_AIWIKI_VARIANT

    primary_rows = [
        [
            "first_attempt_success_rate",
            _format_rate(no_aiwiki),
            _format_rate(aiwiki),
            _format_delta(comparison.first_attempt_success_delta, percent=True),
        ],
        [
            "avg_score",
            _format_float(no_aiwiki.avg_score if no_aiwiki else None),
            _format_float(aiwiki.avg_score if aiwiki else None),
            _format_delta(comparison.avg_score_delta),
        ],
        [
            "avg_human_nudges",
            _format_float(no_aiwiki.avg_human_nudges if no_aiwiki else None),
            _format_float(aiwiki.avg_human_nudges if aiwiki else None),
            _format_delta(_summary_delta(no_aiwiki, aiwiki, "avg_human_nudges")),
        ],
        [
            "avg_project_changed_files",
            _format_float(no_aiwiki.avg_project_changed_files if no_aiwiki else None),
            _format_float(aiwiki.avg_project_changed_files if aiwiki else None),
            _format_delta(_summary_delta(no_aiwiki, aiwiki, "avg_project_changed_files")),
        ],
        [
            "avg_managed_wiki_changed_files",
            _format_float(no_aiwiki.avg_managed_wiki_changed_files if no_aiwiki else None),
            _format_float(aiwiki.avg_managed_wiki_changed_files if aiwiki else None),
            _format_delta(
                _summary_delta(no_aiwiki, aiwiki, "avg_managed_wiki_changed_files")
            ),
        ],
        [
            "avg_user_wiki_changed_files",
            _format_float(no_aiwiki.avg_user_wiki_changed_files if no_aiwiki else None),
            _format_float(aiwiki.avg_user_wiki_changed_files if aiwiki else None),
            _format_delta(_summary_delta(no_aiwiki, aiwiki, "avg_user_wiki_changed_files")),
        ],
    ]
    summary_rows = [
        [
            summary.variant,
            str(summary.first_attempt_results),
            str(summary.recorded_results),
            _format_rate(summary),
            f"{summary.score_successes}/{summary.score_partials}/{summary.score_failures}/{summary.score_pending}",
            _format_float(summary.avg_score),
            _format_float(summary.avg_attempts),
            _format_float(summary.avg_human_nudges),
            _format_float(summary.avg_changed_files),
            _format_float(summary.avg_untracked_files),
            _format_float(summary.avg_project_changed_files),
            _format_float(summary.avg_managed_wiki_changed_files),
            _format_float(summary.avg_user_wiki_changed_files),
            _format_float(summary.avg_user_wiki_untracked_files),
        ]
        for summary in report.variant_summaries
    ]
    record_rows = [
        [
            record.slot,
            record.variant,
            record.prompt_level,
            record.phase,
            record.score_label or "-",
            _format_bool(record.first_attempt_success),
            str(record.attempt or "-"),
            str(record.human_nudges),
            str(len(record.changed_files)),
            str(len(record.untracked_files)),
            str(len(record.project_changed_files)),
            str(len(record.managed_wiki_changed_files)),
            str(len(record.user_wiki_changed_files)),
            _format_bool(record.final_message_present),
        ]
        for record in report.records
    ]
    critical_confounds = []
    if report.confounds is not None:
        critical_confounds = report.confounds.get("critical_confounds", []) or []
    confound_rows = [
        [str(item.get("slot", "-")), str(item.get("kind", "")), str(item.get("detail", ""))]
        for item in critical_confounds
        if isinstance(item, dict)
    ]

    lines = [
        "# AI Wiki Impact Eval Product Report",
        "",
        f"- Run dir: `{report.run_dir}`",
        f'- Experiment: `{metadata.get("experiment", "unknown")}`',
        "- First-attempt policy: grade `first_pass` captures; `final` repair captures are diagnostic only.",
        f"- Causal claims ready: `{_format_bool(shareable)}`",
        f"- AI wiki first-attempt signal: `{comparison.outcome}`",
        f"- Interpretation: {comparison.interpretation}",
        "",
        "## Primary Comparison",
        "",
        _markdown_table(
            ["metric", no_aiwiki_label, aiwiki_label, "delta"],
            primary_rows,
        ),
        "",
        "## Variant Metrics",
        "",
        _markdown_table(
            [
                "variant",
                "first_attempt_results",
                "recorded_results",
                "first_attempt_success_rate",
                "score success/partial/fail/pending",
                "avg_score",
                "avg_attempts",
                "avg_human_nudges",
                "avg_changed_files",
                "avg_untracked_files",
                "avg_project_changed_files",
                "avg_managed_wiki_changed_files",
                "avg_user_wiki_changed_files",
                "avg_user_wiki_untracked_files",
            ],
            summary_rows,
        ),
        "",
        "## Recorded Attempts",
        "",
        _markdown_table(
            [
                "slot",
                "variant",
                "prompt_level",
                "phase",
                "score",
                "first_attempt_success",
                "attempt",
                "human_nudges",
                "changed_files",
                "untracked_files",
                "project_changed_files",
                "managed_wiki_changed_files",
                "user_wiki_changed_files",
                "final_message",
            ],
            record_rows,
        ),
        "",
        "## Confounds",
        "",
        _markdown_table(["slot", "kind", "detail"], confound_rows),
        "",
    ]
    return "\n".join(lines)


def impact_eval_report_to_dict(report: ImpactEvalReport) -> dict:
    comparison = report.primary_comparison
    return {
        "schema_version": "impact-eval-product-v1",
        "run_dir": str(report.run_dir),
        "experiment": report.metadata.get("experiment", "unknown"),
        "first_attempt_policy": "grade first_pass captures; final repair captures are diagnostic only",
        "shareable_for_causal_claims": report.shareable_for_causal_claims,
        "primary_comparison": {
            "no_aiwiki_variant": comparison.no_aiwiki.variant if comparison.no_aiwiki else None,
            "aiwiki_variant": comparison.aiwiki.variant if comparison.aiwiki else None,
            "first_attempt_success_delta": comparison.first_attempt_success_delta,
            "avg_score_delta": comparison.avg_score_delta,
            "outcome": comparison.outcome,
            "interpretation": comparison.interpretation,
        },
        "variant_metrics": [
            {
                "variant": summary.variant,
                "recorded_results": summary.recorded_results,
                "first_attempt_results": summary.first_attempt_results,
                "first_attempt_successes": summary.first_attempt_successes,
                "first_attempt_failures": summary.first_attempt_failures,
                "first_attempt_pending": summary.first_attempt_pending,
                "first_attempt_success_rate": summary.first_attempt_success_rate,
                "score_successes": summary.score_successes,
                "score_partials": summary.score_partials,
                "score_failures": summary.score_failures,
                "score_pending": summary.score_pending,
                "avg_score": summary.avg_score,
                "avg_attempts": summary.avg_attempts,
                "avg_human_nudges": summary.avg_human_nudges,
                "avg_changed_files": summary.avg_changed_files,
                "avg_untracked_files": summary.avg_untracked_files,
                "avg_project_changed_files": summary.avg_project_changed_files,
                "avg_managed_wiki_changed_files": summary.avg_managed_wiki_changed_files,
                "avg_user_wiki_changed_files": summary.avg_user_wiki_changed_files,
                "avg_user_wiki_untracked_files": summary.avg_user_wiki_untracked_files,
            }
            for summary in report.variant_summaries
        ],
        "records": [
            {
                "slot": record.slot,
                "variant": record.variant,
                "prompt_level": record.prompt_level,
                "phase": record.phase,
                "score_label": record.score_label,
                "first_pass_success": record.first_pass_success,
                "first_attempt_success": record.first_attempt_success,
                "attempt": record.attempt,
                "human_nudges": record.human_nudges,
                "changed_file_count": len(record.changed_files),
                "untracked_file_count": len(record.untracked_files),
                "project_changed_file_count": len(record.project_changed_files),
                "managed_wiki_changed_file_count": len(record.managed_wiki_changed_files),
                "user_wiki_changed_file_count": len(record.user_wiki_changed_files),
                "user_wiki_untracked_file_count": len(record.user_wiki_untracked_files),
                "final_message_present": record.final_message_present,
                "result_path": str(record.result_path),
            }
            for record in report.records
        ],
        "confounds": report.confounds,
    }


def render_impact_eval_report_json(report: ImpactEvalReport) -> str:
    return json.dumps(impact_eval_report_to_dict(report), indent=2) + "\n"


def render_impact_eval_summary(report: ImpactEvalSummaryReport) -> str:
    rows = [
        [
            summary.experiment,
            summary.outcome,
            summary.product_signal,
            _format_bool(summary.shareable_for_causal_claims),
            str(summary.critical_confounds),
            _format_delta(summary.first_attempt_success_delta, percent=True),
            _format_delta(summary.avg_score_delta),
            _format_delta(summary.avg_project_changed_files_delta),
            _format_delta(summary.avg_user_wiki_changed_files_delta),
            _format_delta(summary.avg_managed_wiki_changed_files_delta),
            _format_float(summary.diagnostic_avg_user_wiki_changed_files),
        ]
        for summary in report.run_summaries
    ]
    outcome_counts = _signal_counts(report.run_summaries, "outcome")
    product_signal_counts = _signal_counts(report.run_summaries, "product_signal")
    lines = [
        "# AI Wiki Impact Eval Cross-Run Summary",
        "",
        f"- Runs: `{report.total_runs}`",
        f"- Causal-claim-ready runs: `{report.shareable_runs}/{report.total_runs}`",
        f"- Primary outcomes: `{_format_counts(outcome_counts)}`",
        f"- Product signals: `{_format_counts(product_signal_counts)}`",
        "",
        "## Runs",
        "",
        _markdown_table(
            [
                "experiment",
                "primary_outcome",
                "product_signal",
                "shareable",
                "critical_confounds",
                "success_delta",
                "score_delta",
                "project_files_delta",
                "user_wiki_delta",
                "managed_wiki_delta",
                "diagnostic_user_wiki_avg",
            ],
            rows,
        ),
        "",
        "## Interpretation",
        "",
        "- `success_uplift` means the ambient AI wiki primary treatment beat the no-AI-wiki primary control.",
        "- `diagnostic_quality_signal` means primary success was neutral, but diagnostic variants exposed quality or wiki-churn differences.",
        "- Change-profile deltas are ambient AI wiki minus no-AI-wiki for the primary comparison.",
        "- Managed wiki telemetry is reported separately from user-owned AI wiki churn.",
        "",
    ]
    return "\n".join(lines)


def impact_eval_summary_to_dict(report: ImpactEvalSummaryReport) -> dict:
    return {
        "schema_version": "impact-eval-cross-run-summary-v1",
        "total_runs": report.total_runs,
        "shareable_runs": report.shareable_runs,
        "outcome_counts": _signal_counts(report.run_summaries, "outcome"),
        "product_signal_counts": _signal_counts(report.run_summaries, "product_signal"),
        "runs": [
            {
                "run_dir": str(summary.run_dir),
                "experiment": summary.experiment,
                "primary_outcome": summary.outcome,
                "product_signal": summary.product_signal,
                "shareable_for_causal_claims": summary.shareable_for_causal_claims,
                "critical_confounds": summary.critical_confounds,
                "first_attempt_success_delta": summary.first_attempt_success_delta,
                "avg_score_delta": summary.avg_score_delta,
                "avg_project_changed_files_delta": summary.avg_project_changed_files_delta,
                "avg_managed_wiki_changed_files_delta": (
                    summary.avg_managed_wiki_changed_files_delta
                ),
                "avg_user_wiki_changed_files_delta": (
                    summary.avg_user_wiki_changed_files_delta
                ),
                "diagnostic_avg_project_changed_files": (
                    summary.diagnostic_avg_project_changed_files
                ),
                "diagnostic_avg_user_wiki_changed_files": (
                    summary.diagnostic_avg_user_wiki_changed_files
                ),
            }
            for summary in report.run_summaries
        ],
    }


def render_impact_eval_summary_json(report: ImpactEvalSummaryReport) -> str:
    return json.dumps(impact_eval_summary_to_dict(report), indent=2) + "\n"
