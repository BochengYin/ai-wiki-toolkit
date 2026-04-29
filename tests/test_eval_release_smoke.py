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


def test_smoke_help_requires_eval_report_fragments(monkeypatch) -> None:
    module = _load_script("smoke_eval_report_release.py")
    calls: list[list[str]] = []

    def fake_run_tool(binary: str, args: list[str]):
        calls.append([binary, *args])
        return _completed(
            "Summarize first-attempt impact eval metrics\n--run-dir\n--format\n"
        )

    monkeypatch.setattr(module, "run_tool", fake_run_tool)

    module.smoke_help("aiwiki-toolkit")

    assert calls == [["aiwiki-toolkit", "eval", "impact", "report", "--help"]]


def test_smoke_run_dir_validates_stdout_json(monkeypatch, tmp_path: Path) -> None:
    module = _load_script("smoke_eval_report_release.py")
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    calls: list[list[str]] = []

    def fake_run_tool(binary: str, args: list[str]):
        calls.append([binary, *args])
        return _completed(json.dumps(_report_payload()) + "\n")

    monkeypatch.setattr(module, "run_tool", fake_run_tool)

    payload = module.smoke_run_dir("aiwiki-toolkit", run_dir)

    assert payload["primary_comparison"]["outcome"] == "positive_signal"
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
        ]
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
                output_path.write_text(json.dumps(_report_payload()) + "\n", encoding="utf-8")
            else:
                output_path.write_text("# AI Wiki Impact Eval Product Report\n", encoding="utf-8")
        return _completed()

    monkeypatch.setattr(module, "run_tool", fake_run_tool)

    payload = module.smoke_run_dir("aiwiki-toolkit", run_dir, output_dir)

    assert payload["schema_version"] == "impact-eval-product-v1"
    assert (output_dir / "impact-report.md").exists()
    assert (output_dir / "impact-report.json").exists()
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
    ]
