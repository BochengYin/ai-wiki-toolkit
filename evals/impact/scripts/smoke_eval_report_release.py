"""Smoke-test a released aiwiki-toolkit binary against impact-eval reports."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess


EXPECTED_REPORT_SCHEMA_VERSION = "impact-eval-product-v1"
EXPECTED_MANIFEST_SCHEMA_VERSION = "impact-eval-run-manifest-v1"


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
    commands = {
        "families": (
            ["eval", "impact", "families", "--help"],
            (
                "List registered impact eval families and their readiness",
                "--format",
            ),
        ),
        "discover": (
            ["eval", "impact", "discover", "--help"],
            (
                "Refresh the managed impact eval candidate queue",
                "--repo-wiki-dir",
                "--format",
            ),
        ),
        "family show": (
            ["eval", "impact", "family", "show", "--help"],
            (
                "Show one impact eval family's spec, prompts, rubric status, and next commands",
                "--format",
            ),
        ),
        "family candidates": (
            ["eval", "impact", "family", "candidates", "--help"],
            (
                "Discover trial/error memory signals that may become future eval families",
                "--include-not-ready",
            ),
        ),
        "family init": (
            ["eval", "impact", "family", "init", "--help"],
            (
                "Create a draft impact eval family scaffold from a trial/error candidate",
                "--from-candidate",
                "--baseline-ref",
            ),
        ),
        "family draft": (
            ["eval", "impact", "family", "draft", "--help"],
            (
                "Generate managed draft files for a candidate family without promoting them",
                "--candidate",
                "--baseline-ref",
            ),
        ),
        "family promote": (
            ["eval", "impact", "family", "promote", "--help"],
            (
                "Check or apply promotion from a managed candidate draft to a formal family",
                "--candidate",
                "--apply",
            ),
        ),
        "plan": (
            ["eval", "impact", "plan", "--help"],
            (
                "Plan an impact eval run without preparing workspaces or invoking an agent",
                "--family",
                "--format",
            ),
        ),
        "prepare": (
            ["eval", "impact", "prepare", "--help"],
            (
                "Prepare impact eval workspaces and a run skeleton without invoking an agent",
                "--family",
                "--format",
            ),
        ),
        "run": (
            ["eval", "impact", "run", "--help"],
            (
                "Run impact eval slots with Codex CLI, capture artifacts, and produce a bundle",
                "--run-dir",
                "--all-slots",
                "--score-policy",
                "--rubric",
            ),
        ),
        "benchmark": (
            ["eval", "impact", "benchmark", "--help"],
            (
                "Prepare and run a whole impact eval family in one command",
                "--family",
                "--score-policy",
            ),
        ),
        "schedule report": (
            ["eval", "impact", "schedule", "report", "--help"],
            (
                "Generate a periodic impact eval report",
                "--period-id",
                "--handle",
                "managed candidate",
            ),
        ),
        "schedule run": (
            ["eval", "impact", "schedule", "run", "--help"],
            (
                "Run scheduled family benchmarks and update the trend/report store",
                "--family",
                "--if-due",
                "--handle",
                "--score-policy",
            ),
        ),
        "capture": (
            ["eval", "impact", "capture", "--help"],
            (
                "Capture first-pass or repaired impact eval artifacts from a local workspace",
                "--run-dir",
                "--slot",
                "--first-pass",
            ),
        ),
        "validate": (
            ["eval", "impact", "validate", "--help"],
            (
                "Validate session exports and confounds for a captured impact eval run",
                "--run-dir",
                "--format",
            ),
        ),
        "score": (
            ["eval", "impact", "score", "--help"],
            (
                "Write a manual score artifact and refresh the run manifest",
                "--run-dir",
                "--label",
            ),
        ),
        "report": (
            ["eval", "impact", "report", "--help"],
            (
                "Summarize first-attempt impact eval metrics",
                "--run-dir",
                "--format",
            ),
        ),
        "manifest": (
            ["eval", "impact", "manifest", "--help"],
            (
                "Describe a captured impact eval run identity and artifact inventory",
                "--run-dir",
                "--format",
            ),
        ),
    }
    for command_name, (command_args, required_fragments) in commands.items():
        result = run_tool(binary, command_args)
        require_success(result, context=f"{command_name} help smoke")
        output = result.stdout + result.stderr
        missing = [fragment for fragment in required_fragments if fragment not in output]
        if missing:
            raise SystemExit(
                f"help smoke did not expose the expected eval {command_name} command fragments: "
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


def manifest_command_args(
    run_dir: Path,
    *,
    output_format: str | None = None,
    output: Path | None = None,
) -> list[str]:
    args = ["eval", "impact", "manifest", "--run-dir", str(run_dir)]
    if output_format is not None:
        args.extend(["--format", output_format])
    if output is not None:
        args.extend(["--output", str(output)])
    return args


def load_json_payload(text: str, *, label: str) -> dict:
    try:
        payload = json.loads(text)
    except json.JSONDecodeError as exc:
        raise SystemExit(f"JSON {label} output is not valid JSON: {exc}") from exc
    if not isinstance(payload, dict):
        raise SystemExit(f"JSON {label} output is not an object.")
    return payload


def validate_report_payload(payload: dict) -> None:
    if payload.get("schema_version") != EXPECTED_REPORT_SCHEMA_VERSION:
        raise SystemExit(
            "JSON report schema mismatch: "
            f"expected {EXPECTED_REPORT_SCHEMA_VERSION}, found {payload.get('schema_version')!r}."
        )
    if not isinstance(payload.get("primary_comparison"), dict):
        raise SystemExit("JSON report is missing primary_comparison.")
    if not isinstance(payload.get("variant_metrics"), list):
        raise SystemExit("JSON report is missing variant_metrics.")
    records = payload.get("records")
    if not isinstance(records, list) or not records:
        raise SystemExit("JSON report does not contain any captured records.")


def validate_manifest_payload(payload: dict) -> None:
    if payload.get("schema_version") != EXPECTED_MANIFEST_SCHEMA_VERSION:
        raise SystemExit(
            "JSON manifest schema mismatch: "
            f"expected {EXPECTED_MANIFEST_SCHEMA_VERSION}, found {payload.get('schema_version')!r}."
        )
    if not isinstance(payload.get("slots"), list):
        raise SystemExit("JSON manifest is missing slots.")
    if not isinstance(payload.get("artifact_summary"), dict):
        raise SystemExit("JSON manifest is missing artifact_summary.")
    if not isinstance(payload.get("agent_command"), dict):
        raise SystemExit("JSON manifest is missing agent_command.")


def smoke_run_dir(binary: str, run_dir: Path, output_dir: Path | None = None) -> dict:
    run_dir = run_dir.resolve()
    if not run_dir.exists():
        raise SystemExit(f"Run directory does not exist: {run_dir}")

    if output_dir is None:
        report_result = run_tool(binary, report_command_args(run_dir, output_format="json"))
        require_success(report_result, context="json report smoke")
        report_payload = load_json_payload(report_result.stdout, label="report")
        validate_report_payload(report_payload)

        manifest_result = run_tool(binary, manifest_command_args(run_dir, output_format="json"))
        require_success(manifest_result, context="json manifest smoke")
        manifest_payload = load_json_payload(manifest_result.stdout, label="manifest")
        validate_manifest_payload(manifest_payload)
        return {"report": report_payload, "manifest": manifest_payload}

    output_dir = output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    markdown_path = output_dir / "impact-report.md"
    json_path = output_dir / "impact-report.json"
    manifest_markdown_path = output_dir / "impact-manifest.md"
    manifest_json_path = output_dir / "impact-manifest.json"

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

    report_payload = load_json_payload(json_path.read_text(encoding="utf-8"), label="report")
    validate_report_payload(report_payload)

    manifest_markdown_result = run_tool(
        binary,
        manifest_command_args(run_dir, output=manifest_markdown_path),
    )
    require_success(manifest_markdown_result, context="markdown manifest smoke")
    if (
        not manifest_markdown_path.exists()
        or not manifest_markdown_path.read_text(encoding="utf-8").strip()
    ):
        raise SystemExit(f"Markdown manifest was not written: {manifest_markdown_path}")

    manifest_json_result = run_tool(
        binary,
        manifest_command_args(
            run_dir,
            output_format="json",
            output=manifest_json_path,
        ),
    )
    require_success(manifest_json_result, context="json manifest file smoke")
    if not manifest_json_path.exists():
        raise SystemExit(f"JSON manifest was not written: {manifest_json_path}")

    manifest_payload = load_json_payload(
        manifest_json_path.read_text(encoding="utf-8"),
        label="manifest",
    )
    validate_manifest_payload(manifest_payload)
    return {"report": report_payload, "manifest": manifest_payload}


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
        comparison = payload["report"].get("primary_comparison", {})
        print(f"Outcome: {comparison.get('outcome', 'unknown')}")


if __name__ == "__main__":
    main()
