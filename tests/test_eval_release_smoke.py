from __future__ import annotations

from importlib.util import module_from_spec, spec_from_file_location
import json
from pathlib import Path
import subprocess
import sys


def _load_script(script_name: str):
    script_path = (
        Path(__file__).resolve().parents[1]
        / "evals"
        / "impact"
        / "scripts"
        / script_name
    )
    spec = spec_from_file_location(script_name.replace(".py", ""), script_path)
    assert spec is not None
    module = module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _completed(stdout: str = "", stderr: str = "", returncode: int = 0):
    return subprocess.CompletedProcess(
        args=["aiwiki-toolkit"],
        returncode=returncode,
        stdout=stdout,
        stderr=stderr,
    )


def _report_payload() -> dict:
    return {
        "schema_version": "impact-eval-product-v1",
        "primary_comparison": {"outcome": "positive_signal"},
        "variant_metrics": [{"variant": "aiwiki_ambient_memory_workflow"}],
        "records": [{"slot": "s01"}],
    }


def _manifest_payload() -> dict:
    return {
        "schema_version": "impact-eval-run-manifest-v1",
        "slots": [{"slot": "s01", "variant": "no_aiwiki_workflow"}],
        "artifact_summary": {"records": 1},
        "agent_command": {"command_family": "codex exec"},
    }


def test_smoke_help_requires_eval_report_fragments(monkeypatch) -> None:
    module = _load_script("smoke_eval_report_release.py")
    calls: list[list[str]] = []

    def fake_run_tool(binary: str, args: list[str]):
        calls.append([binary, *args])
        if args[2] == "families":
            return _completed(
                "List registered impact eval families and their readiness\n--format\n"
            )
        if args[2] == "discover":
            return _completed(
                "Refresh the managed impact eval candidate queue\n--repo-wiki-dir\n--format\n"
            )
        if args[2:4] == ["family", "show"]:
            return _completed(
                "Show one impact eval family's spec, prompts, rubric status, and next commands\n--format\n"
            )
        if args[2:4] == ["family", "candidates"]:
            return _completed(
                "Discover trial/error memory signals that may become future eval families\n--include-not-ready\n"
            )
        if args[2:4] == ["family", "init"]:
            return _completed(
                "Create a draft impact eval family scaffold from a trial/error candidate\n--from-candidate\n--baseline-ref\n"
            )
        if args[2:4] == ["family", "draft"]:
            return _completed(
                "Generate managed draft files for a candidate family without promoting them\n--candidate\n--baseline-ref\n"
            )
        if args[2:4] == ["family", "promote"]:
            return _completed(
                "Check or apply promotion from a managed candidate draft to a formal family\n--candidate\n--apply\n"
            )
        if args[2] == "plan":
            return _completed(
                "Plan an impact eval run without preparing workspaces or invoking an agent\n--family\n--format\n"
            )
        if args[2] == "prepare":
            return _completed(
                "Prepare impact eval workspaces and a run skeleton without invoking an agent\n--family\n--format\n"
            )
        if args[2] == "run":
            return _completed(
                "Run impact eval slots with Codex CLI, capture artifacts, and produce a bundle\n--run-dir\n--all-slots\n--score-policy\n--rubric\n"
            )
        if args[2] == "benchmark":
            return _completed(
                "Prepare and run a whole impact eval family in one command\n--family\n--score-policy\n"
            )
        if args[2:4] == ["schedule", "report"]:
            return _completed(
                "Generate a periodic impact eval report\n--period-id\n--handle\nmanaged candidate\n"
            )
        if args[2:4] == ["schedule", "run"]:
            return _completed(
                "Run scheduled family benchmarks and update the trend/report store\n--family\n--if-due\n--handle\n--score-policy\n"
            )
        if args[2] == "capture":
            return _completed(
                "Capture first-pass or repaired impact eval artifacts from a local workspace\n--run-dir\n--slot\n--first-pass\n"
            )
        if args[2] == "validate":
            return _completed(
                "Validate session exports and confounds for a captured impact eval run\n--run-dir\n--format\n"
            )
        if args[2] == "score":
            return _completed(
                "Write a manual score artifact and refresh the run manifest\n--run-dir\n--label\n"
            )
        if args[2] == "manifest":
            return _completed(
                "Describe a captured impact eval run identity and artifact inventory\n--run-dir\n--format\n"
            )
        return _completed("Summarize first-attempt impact eval metrics\n--run-dir\n--format\n")

    monkeypatch.setattr(module, "run_tool", fake_run_tool)

    module.smoke_help("aiwiki-toolkit")

    assert calls == [
        ["aiwiki-toolkit", "eval", "impact", "families", "--help"],
        ["aiwiki-toolkit", "eval", "impact", "discover", "--help"],
        ["aiwiki-toolkit", "eval", "impact", "family", "show", "--help"],
        ["aiwiki-toolkit", "eval", "impact", "family", "candidates", "--help"],
        ["aiwiki-toolkit", "eval", "impact", "family", "init", "--help"],
        ["aiwiki-toolkit", "eval", "impact", "family", "draft", "--help"],
        ["aiwiki-toolkit", "eval", "impact", "family", "promote", "--help"],
        ["aiwiki-toolkit", "eval", "impact", "plan", "--help"],
        ["aiwiki-toolkit", "eval", "impact", "prepare", "--help"],
        ["aiwiki-toolkit", "eval", "impact", "run", "--help"],
        ["aiwiki-toolkit", "eval", "impact", "benchmark", "--help"],
        ["aiwiki-toolkit", "eval", "impact", "schedule", "report", "--help"],
        ["aiwiki-toolkit", "eval", "impact", "schedule", "run", "--help"],
        ["aiwiki-toolkit", "eval", "impact", "capture", "--help"],
        ["aiwiki-toolkit", "eval", "impact", "validate", "--help"],
        ["aiwiki-toolkit", "eval", "impact", "score", "--help"],
        ["aiwiki-toolkit", "eval", "impact", "report", "--help"],
        ["aiwiki-toolkit", "eval", "impact", "manifest", "--help"],
    ]


def test_smoke_run_dir_validates_stdout_json(monkeypatch, tmp_path: Path) -> None:
    module = _load_script("smoke_eval_report_release.py")
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    calls: list[list[str]] = []

    def fake_run_tool(binary: str, args: list[str]):
        calls.append([binary, *args])
        payload = _manifest_payload() if args[2] == "manifest" else _report_payload()
        return _completed(json.dumps(payload) + "\n")

    monkeypatch.setattr(module, "run_tool", fake_run_tool)

    payload = module.smoke_run_dir("aiwiki-toolkit", run_dir)

    assert payload["report"]["primary_comparison"]["outcome"] == "positive_signal"
    assert payload["manifest"]["schema_version"] == "impact-eval-run-manifest-v1"
    assert calls == [
        [
            "aiwiki-toolkit",
            "eval",
            "impact",
            "report",
            "--run-dir",
            str(run_dir.resolve()),
            "--format",
            "json",
        ],
        [
            "aiwiki-toolkit",
            "eval",
            "impact",
            "manifest",
            "--run-dir",
            str(run_dir.resolve()),
            "--format",
            "json",
        ],
    ]


def test_smoke_run_dir_writes_markdown_and_json_outputs(monkeypatch, tmp_path: Path) -> None:
    module = _load_script("smoke_eval_report_release.py")
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    output_dir = tmp_path / "reports"
    calls: list[list[str]] = []

    def fake_run_tool(binary: str, args: list[str]):
        calls.append([binary, *args])
        if "--output" in args:
            output_path = Path(args[args.index("--output") + 1])
            if "--format" in args and args[args.index("--format") + 1] == "json":
                payload = _manifest_payload() if args[2] == "manifest" else _report_payload()
                output_path.write_text(json.dumps(payload) + "\n", encoding="utf-8")
            elif args[2] == "manifest":
                output_path.write_text("# AI Wiki Impact Eval Run Manifest\n", encoding="utf-8")
            else:
                output_path.write_text("# AI Wiki Impact Eval Product Report\n", encoding="utf-8")
        return _completed()

    monkeypatch.setattr(module, "run_tool", fake_run_tool)

    payload = module.smoke_run_dir("aiwiki-toolkit", run_dir, output_dir)

    assert payload["report"]["schema_version"] == "impact-eval-product-v1"
    assert payload["manifest"]["schema_version"] == "impact-eval-run-manifest-v1"
    assert (output_dir / "impact-report.md").exists()
    assert (output_dir / "impact-report.json").exists()
    assert (output_dir / "impact-manifest.md").exists()
    assert (output_dir / "impact-manifest.json").exists()
    assert calls == [
        [
            "aiwiki-toolkit",
            "eval",
            "impact",
            "report",
            "--run-dir",
            str(run_dir.resolve()),
            "--output",
            str((output_dir / "impact-report.md").resolve()),
        ],
        [
            "aiwiki-toolkit",
            "eval",
            "impact",
            "report",
            "--run-dir",
            str(run_dir.resolve()),
            "--format",
            "json",
            "--output",
            str((output_dir / "impact-report.json").resolve()),
        ],
        [
            "aiwiki-toolkit",
            "eval",
            "impact",
            "manifest",
            "--run-dir",
            str(run_dir.resolve()),
            "--output",
            str((output_dir / "impact-manifest.md").resolve()),
        ],
        [
            "aiwiki-toolkit",
            "eval",
            "impact",
            "manifest",
            "--run-dir",
            str(run_dir.resolve()),
            "--format",
            "json",
            "--output",
            str((output_dir / "impact-manifest.json").resolve()),
        ],
    ]
