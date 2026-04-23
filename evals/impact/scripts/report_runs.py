"""Aggregate manual impact-eval results into a compact Markdown report."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


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


def format_paths(paths: list[str]) -> str:
    if not paths:
        return "-"
    return "<br>".join(paths)


def collect_results(run_dir: Path) -> list[dict]:
    results: list[dict] = []
    for result_path in sorted(run_dir.glob("*/*/result.json")):
        result = load_json(result_path)
        slot_dir = result_path.parent
        result["slot_dir"] = str(slot_dir)
        result["final_message_present"] = (slot_dir / "final_message.md").exists()
        results.append(result)
    return results


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
        if result.get("first_pass_success") is True:
            bucket["first_pass_successes"] += 1
        elif result.get("first_pass_success") is False:
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
            result["variant"],
            result["prompt_level"],
            format_first_pass(result.get("first_pass_success")),
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
    if metadata.get("notes"):
        lines.append(f'- Notes: `{metadata["notes"]}`')

    lines.extend(
        [
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
                    "variant",
                    "prompt_level",
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
