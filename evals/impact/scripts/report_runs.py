"""Aggregate manual impact-eval results into a compact Markdown report."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

CAPTURE_PHASES = {"first_pass", "final"}
SCORE_FIRST_PASS_SUCCESS = {
    "success": True,
    "partial": False,
    "fail": False,
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", type=Path, required=True, help="Run directory created by init_run.py.")
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Optional output path. Defaults to <run-dir>/report.md.",
    )
    return parser.parse_args()


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def format_bool(value: bool) -> str:
    return "yes" if value else "no"


def format_first_pass(value: bool | None) -> str:
    if value is True:
        return "yes"
    if value is False:
        return "no"
    return "pending"


def effective_first_pass_success(result: dict) -> bool | None:
    explicit = result.get("first_pass_success")
    if explicit is True or explicit is False:
        return explicit
    if result.get("phase") == "final":
        return None
    score = result.get("score")
    if not isinstance(score, dict):
        return None
    return SCORE_FIRST_PASS_SUCCESS.get(score.get("label"))


def format_paths(paths: list[str]) -> str:
    if not paths:
        return "-"
    return "<br>".join(paths)


def collect_results(run_dir: Path) -> list[dict]:
    results: list[dict] = []
    result_paths = list(sorted(run_dir.glob("*/*/result.json")))
    result_paths.extend(
        path
        for path in sorted(run_dir.glob("*/*/*/result.json"))
        if path.parent.name in CAPTURE_PHASES
    )
    for result_path in result_paths:
        result = load_json(result_path)
        slot_dir = result_path.parent
        if slot_dir.name in CAPTURE_PHASES:
            prompt_level = slot_dir.parent.name
            slot = slot_dir.parent.parent.name
            phase = slot_dir.name
        else:
            prompt_level = slot_dir.name
            slot = slot_dir.parent.name
            phase = result.get("phase", "legacy")
        result.setdefault("slot", slot)
        result.setdefault("prompt_level", prompt_level)
        result.setdefault("phase", phase)
        result["slot_dir"] = str(slot_dir)
        result["final_message_present"] = (slot_dir / "final_message.md").exists()
        score_path = run_dir / slot / prompt_level / "score.json"
        result["score"] = load_json(score_path) if score_path.exists() else None
        results.append(result)
    return results


def load_confounds(run_dir: Path) -> dict | None:
    confounds_path = run_dir / "confounds.json"
    if not confounds_path.exists():
        return None
    return load_json(confounds_path)


def assignment_variant_map(metadata: dict) -> dict[str, str]:
    assignment = metadata.get("assignment")
    if not isinstance(assignment, dict):
        return {}
    return {
        item["slot"]: item.get("variant", item["slot"])
        for item in assignment.get("slots", [])
    }


def variant_for_result(metadata: dict, result: dict) -> str:
    if result.get("variant"):
        return result["variant"]
    return assignment_variant_map(metadata).get(result.get("slot", ""), result.get("slot", ""))


def summarize_by_variant(results: list[dict]) -> list[dict]:
    grouped: dict[str, dict] = {}
    for result in results:
        bucket = grouped.setdefault(
            result["variant"],
            {
                "variant": result["variant"],
                "recorded_slots": 0,
                "first_pass_successes": 0,
                "first_pass_failures": 0,
                "first_pass_pending": 0,
                "total_attempts": 0,
                "total_human_nudges": 0,
            },
        )
        bucket["recorded_slots"] += 1
        first_pass_success = effective_first_pass_success(result)
        if first_pass_success is True:
            bucket["first_pass_successes"] += 1
        elif first_pass_success is False:
            bucket["first_pass_failures"] += 1
        else:
            bucket["first_pass_pending"] += 1
        bucket["total_attempts"] += int(result.get("attempt", 0))
        bucket["total_human_nudges"] += int(result.get("human_nudges", 0))

    summary = []
    for bucket in grouped.values():
        slots = bucket["recorded_slots"]
        summary.append(
            {
                "variant": bucket["variant"],
                "recorded_slots": slots,
                "first_pass_successes": bucket["first_pass_successes"],
                "first_pass_failures": bucket["first_pass_failures"],
                "first_pass_pending": bucket["first_pass_pending"],
                "avg_attempts": round(bucket["total_attempts"] / slots, 2) if slots else 0.0,
                "avg_human_nudges": round(bucket["total_human_nudges"] / slots, 2) if slots else 0.0,
            }
        )
    return sorted(summary, key=lambda item: item["variant"])


def markdown_table(headers: list[str], rows: list[list[str]]) -> str:
    if not rows:
        return "_No rows._"
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(row) + " |")
    return "\n".join(lines)


def render_report(run_dir: Path, metadata: dict, results: list[dict]) -> str:
    confounds = load_confounds(run_dir)
    primary_variants = set(metadata.get("primary_comparison", []))
    diagnostic_variants = set(metadata.get("diagnostic_variants", []))
    variant_map = assignment_variant_map(metadata)
    for result in results:
        result["variant"] = variant_for_result(metadata, result)
    summary_rows = [
        [
            item["variant"],
            str(item["recorded_slots"]),
            str(item["first_pass_successes"]),
            str(item["first_pass_failures"]),
            str(item["first_pass_pending"]),
            f'{item["avg_attempts"]:.2f}',
            f'{item["avg_human_nudges"]:.2f}',
        ]
        for item in summarize_by_variant(results)
    ]
    detail_rows = [
        [
            result.get("slot", ""),
            result["variant"],
            result["prompt_level"],
            result.get("phase", ""),
            result.get("score", {}).get("label", "-") if result.get("score") else "-",
            format_first_pass(effective_first_pass_success(result)),
            str(result.get("attempt", "")),
            str(result.get("human_nudges", "")),
            str(len(result.get("changed_files", []))),
            format_paths(result.get("changed_files", [])),
            format_paths(result.get("untracked_files", [])),
            format_bool(bool(result.get("final_message_present"))),
            result.get("notes", ""),
        ]
        for result in results
    ]
    workflow_rows = [
        [
            result.get("slot", ""),
            result["variant"],
            result["prompt_level"],
            result.get("score", {}).get("label", "-") if result.get("score") else "-",
            format_first_pass(effective_first_pass_success(result)),
            str(len(result.get("changed_files", []))),
        ]
        for result in results
        if result["variant"] in primary_variants
    ]
    diagnostic_rows = [
        [
            result.get("slot", ""),
            result["variant"],
            result["prompt_level"],
            result.get("score", {}).get("label", "-") if result.get("score") else "-",
            format_first_pass(effective_first_pass_success(result)),
            str(len(result.get("changed_files", []))),
        ]
        for result in results
        if result["variant"] in diagnostic_variants
    ]

    lines = [
        "# Impact Eval Report",
        "",
        f"- Run dir: `{run_dir}`",
        f'- Experiment: `{metadata.get("experiment", "unknown")}`',
        f'- Workspace root: `{metadata.get("workspace_root", "unknown")}`',
        f'- Variants: `{", ".join(metadata.get("variants", []))}`',
        f'- Prompt levels: `{", ".join(metadata.get("prompt_levels", []))}`',
        f'- Created at: `{metadata.get("created_at", "unknown")}`',
    ]
    if variant_map:
        lines.append("- Layout: `workflow-primary neutral slots`")
    if confounds is not None:
        shareable = "yes" if confounds.get("shareable_for_causal_claims") else "no"
        lines.append(f"- Shareable for causal claims: `{shareable}`")
    if metadata.get("notes"):
        lines.append(f'- Notes: `{metadata["notes"]}`')

    lines.extend(
        [
            "",
            "## Workflow Result",
            "",
            markdown_table(
                [
                    "slot",
                    "variant",
                    "prompt_level",
                    "score",
                    "first_pass_success",
                    "changed_file_count",
                ],
                workflow_rows,
            ),
            "",
            "## Diagnostic Result",
            "",
            markdown_table(
                [
                    "slot",
                    "variant",
                    "prompt_level",
                    "score",
                    "first_pass_success",
                    "changed_file_count",
                ],
                diagnostic_rows,
            ),
            "",
            "## Variant Summary",
            "",
            markdown_table(
                [
                    "variant",
                    "recorded_slots",
                    "first_pass_successes",
                    "first_pass_failures",
                    "first_pass_pending",
                    "avg_attempts",
                    "avg_human_nudges",
                ],
                summary_rows,
            ),
            "",
            "## Recorded Results",
            "",
            markdown_table(
                [
                    "slot",
                    "variant",
                    "prompt_level",
                    "phase",
                    "score",
                    "first_pass_success",
                    "attempt",
                    "human_nudges",
                    "changed_file_count",
                    "changed_files",
                    "untracked_files",
                    "final_message_present",
                    "notes",
                ],
                detail_rows,
            ),
            "",
        ]
    )
    if confounds is not None:
        critical_rows = [
            [
                item.get("slot", "-"),
                item.get("kind", ""),
                item.get("detail", ""),
            ]
            for item in confounds.get("critical_confounds", [])
        ]
        lines.extend(
            [
                "## Confounds",
                "",
                markdown_table(["slot", "kind", "detail"], critical_rows),
                "",
            ]
        )
    return "\n".join(lines)


def main() -> None:
    args = parse_args()
    run_dir = args.run_dir.resolve()
    if not run_dir.exists():
        raise SystemExit(f"Run directory does not exist: {run_dir}")
    metadata_path = run_dir / "metadata.json"
    if not metadata_path.exists():
        raise SystemExit(f"metadata.json not found under: {run_dir}")
    metadata = load_json(metadata_path)
    results = collect_results(run_dir)
    report_text = render_report(run_dir, metadata, results)
    output_path = (args.output or (run_dir / "report.md")).resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(report_text, encoding="utf-8")
    print(output_path)


if __name__ == "__main__":
    main()
