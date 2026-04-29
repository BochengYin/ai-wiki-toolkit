"""Smoke-test a released aiwiki-toolkit binary against impact-eval reports."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess


EXPECTED_SCHEMA_VERSION = "impact-eval-product-v1"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--binary",
        default="aiwiki-toolkit",
        help="Released aiwiki-toolkit binary or wrapper to test. Defaults to PATH lookup.",
    )
    parser.add_argument(
        "--run-dir",
        type=Path,
        default=None,
        help="Optional captured impact-eval run directory to report on.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Optional directory for generated markdown/json reports.",
    )
    return parser.parse_args()


def run_tool(binary: str, args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [binary, *args],
        check=False,
        capture_output=True,
        text=True,
    )


def require_success(result: subprocess.CompletedProcess[str], *, context: str) -> None:
    if result.returncode == 0:
        return
    details = "\n".join(
        part
        for part in (
            result.stdout.strip(),
            result.stderr.strip(),
        )
        if part
    )
    raise SystemExit(f"{context} failed with exit code {result.returncode}.\n{details}")


def smoke_help(binary: str) -> None:
    result = run_tool(binary, ["eval", "impact", "report", "--help"])
    require_success(result, context="help smoke")
    output = result.stdout + result.stderr
    required_fragments = (
        "Summarize first-attempt impact eval metrics",
        "--run-dir",
        "--format",
    )
    missing = [fragment for fragment in required_fragments if fragment not in output]
    if missing:
        raise SystemExit(
            "help smoke did not expose the expected eval report command fragments: "
            + ", ".join(missing)
        )


def report_command_args(
    run_dir: Path,
    *,
    output_format: str | None = None,
    output: Path | None = None,
) -> list[str]:
    args = ["eval", "impact", "report", "--run-dir", str(run_dir)]
    if output_format is not None:
        args.extend(["--format", output_format])
    if output is not None:
        args.extend(["--output", str(output)])
    return args


def load_report_payload(text: str) -> dict:
    try:
        payload = json.loads(text)
    except json.JSONDecodeError as exc:
        raise SystemExit(f"JSON report output is not valid JSON: {exc}") from exc
    if not isinstance(payload, dict):
        raise SystemExit("JSON report output is not an object.")
    return payload


def validate_report_payload(payload: dict) -> None:
    if payload.get("schema_version") != EXPECTED_SCHEMA_VERSION:
        raise SystemExit(
            "JSON report schema mismatch: "
            f"expected {EXPECTED_SCHEMA_VERSION}, found {payload.get('schema_version')!r}."
        )
    if not isinstance(payload.get("primary_comparison"), dict):
        raise SystemExit("JSON report is missing primary_comparison.")
    if not isinstance(payload.get("variant_metrics"), list):
        raise SystemExit("JSON report is missing variant_metrics.")
    records = payload.get("records")
    if not isinstance(records, list) or not records:
        raise SystemExit("JSON report does not contain any captured records.")


def smoke_run_dir(binary: str, run_dir: Path, output_dir: Path | None = None) -> dict:
    run_dir = run_dir.resolve()
    if not run_dir.exists():
        raise SystemExit(f"Run directory does not exist: {run_dir}")

    if output_dir is None:
        result = run_tool(binary, report_command_args(run_dir, output_format="json"))
        require_success(result, context="json report smoke")
        payload = load_report_payload(result.stdout)
        validate_report_payload(payload)
        return payload

    output_dir = output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    markdown_path = output_dir / "impact-report.md"
    json_path = output_dir / "impact-report.json"

    markdown_result = run_tool(binary, report_command_args(run_dir, output=markdown_path))
    require_success(markdown_result, context="markdown report smoke")
    if not markdown_path.exists() or not markdown_path.read_text(encoding="utf-8").strip():
        raise SystemExit(f"Markdown report was not written: {markdown_path}")

    json_result = run_tool(
        binary,
        report_command_args(run_dir, output_format="json", output=json_path),
    )
    require_success(json_result, context="json report file smoke")
    if not json_path.exists():
        raise SystemExit(f"JSON report was not written: {json_path}")

    payload = load_report_payload(json_path.read_text(encoding="utf-8"))
    validate_report_payload(payload)
    return payload


def main() -> None:
    args = parse_args()
    smoke_help(args.binary)

    payload = None
    if args.run_dir is not None:
        payload = smoke_run_dir(args.binary, args.run_dir, args.output_dir)

    print("Post-release eval report smoke passed.")
    print(f"Binary: {args.binary}")
    if args.run_dir is not None:
        print(f"Run dir: {args.run_dir.resolve()}")
    if args.output_dir is not None:
        print(f"Output dir: {args.output_dir.resolve()}")
    if payload is not None:
        comparison = payload.get("primary_comparison", {})
        print(f"Outcome: {comparison.get('outcome', 'unknown')}")


if __name__ == "__main__":
    main()
