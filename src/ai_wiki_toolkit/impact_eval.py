"""Impact-eval product reports from captured first-attempt artifacts."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path


CAPTURE_PHASES = {"first_pass", "final"}
PRIMARY_NO_AIWIKI_VARIANT = "no_aiwiki_workflow"
PRIMARY_AIWIKI_VARIANT = "aiwiki_ambient_memory_workflow"
SCORE_VALUES = {"success": 1.0, "partial": 0.5, "fail": 0.0}


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


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


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


def _assignment_variant_map(metadata: dict) -> dict[str, str]:
    assignment = metadata.get("assignment")
    if not isinstance(assignment, dict):
        return {}
    result: dict[str, str] = {}
    for item in assignment.get("slots", []):
        if not isinstance(item, dict):
            continue
        slot = item.get("slot")
        if isinstance(slot, str):
            variant = item.get("variant")
            result[slot] = variant if isinstance(variant, str) else slot
    return result


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
                avg_attempts=(sum(attempts) / len(attempts) if attempts else None),
                avg_human_nudges=(sum(nudges) / len(nudges) if nudges else None),
                avg_changed_files=(
                    sum(changed_files) / len(changed_files) if changed_files else None
                ),
                avg_untracked_files=(
                    sum(untracked_files) / len(untracked_files) if untracked_files else None
                ),
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
            "-",
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
                "final_message_present": record.final_message_present,
                "result_path": str(record.result_path),
            }
            for record in report.records
        ],
        "confounds": report.confounds,
    }


def render_impact_eval_report_json(report: ImpactEvalReport) -> str:
    return json.dumps(impact_eval_report_to_dict(report), indent=2) + "\n"
