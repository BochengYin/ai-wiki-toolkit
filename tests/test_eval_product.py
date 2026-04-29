from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from ai_wiki_toolkit.cli import app
from ai_wiki_toolkit.impact_eval import (
    generate_impact_eval_report,
    render_impact_eval_report,
)


runner = CliRunner()


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def _write_result(
    run_dir: Path,
    *,
    slot: str,
    variant: str,
    score: str,
    first_pass_success: bool,
    phase: str = "first_pass",
) -> None:
    result_dir = run_dir / slot / "original" / phase
    _write_json(
        result_dir / "result.json",
        {
            "slot": slot,
            "variant": variant,
            "prompt_level": "original",
            "phase": phase,
            "attempt": 1,
            "human_nudges": 0,
            "first_pass_success": first_pass_success,
            "changed_files": ["scripts/example.py"],
            "untracked_files": [],
            "notes": "",
        },
    )
    (result_dir / "final_message.md").write_text("done\n", encoding="utf-8")
    _write_json(
        run_dir / slot / "original" / "score.json",
        {
            "schema_version": 2,
            "slot": slot,
            "prompt_level": "original",
            "label": score,
            "rubric_refs": [],
            "evidence": [f"{slot}/original/{phase}/workspace_diff.patch"],
            "notes": "",
        },
    )


def _make_run_dir(tmp_path: Path) -> Path:
    run_dir = tmp_path / "runs" / "run_001"
    _write_json(
        run_dir / "metadata.json",
        {
            "schema_version": 2,
            "experiment": "scaffold_prompt_workflow_compliance",
            "workspace_root": "/tmp/workspaces",
            "variants": ["s01", "s02", "s03"],
            "prompt_levels": ["original"],
            "created_at": "2026-04-29T10:00:00",
            "primary_comparison": [
                "no_aiwiki_workflow",
                "aiwiki_ambient_memory_workflow",
            ],
            "diagnostic_variants": ["aiwiki_linked_raw_only"],
            "assignment": {
                "slots": [
                    {"slot": "s01", "variant": "no_aiwiki_workflow"},
                    {"slot": "s02", "variant": "aiwiki_ambient_memory_workflow"},
                    {"slot": "s03", "variant": "aiwiki_linked_raw_only"},
                ]
            },
        },
    )
    _write_json(
        run_dir / "confounds.json",
        {
            "shareable_for_causal_claims": True,
            "critical_confounds": [],
        },
    )
    _write_result(
        run_dir,
        slot="s01",
        variant="no_aiwiki_workflow",
        score="fail",
        first_pass_success=False,
    )
    _write_result(
        run_dir,
        slot="s02",
        variant="aiwiki_ambient_memory_workflow",
        score="success",
        first_pass_success=True,
    )
    _write_result(
        run_dir,
        slot="s03",
        variant="aiwiki_linked_raw_only",
        score="success",
        first_pass_success=True,
    )
    _write_result(
        run_dir,
        slot="s02",
        variant="aiwiki_ambient_memory_workflow",
        score="success",
        first_pass_success=True,
        phase="final",
    )
    return run_dir


def test_impact_eval_report_computes_first_attempt_primary_signal(tmp_path: Path) -> None:
    run_dir = _make_run_dir(tmp_path)

    report = generate_impact_eval_report(run_dir)

    assert report.primary_comparison.outcome == "positive_signal"
    assert report.primary_comparison.first_attempt_success_delta == 1.0
    assert report.primary_comparison.avg_score_delta == 1.0
    ambient = {
        summary.variant: summary for summary in report.variant_summaries
    }["aiwiki_ambient_memory_workflow"]
    assert ambient.first_attempt_results == 1
    assert ambient.recorded_results == 2
    assert ambient.avg_changed_files == 1.0
    assert ambient.avg_untracked_files == 0.0


def test_impact_eval_report_render_names_first_attempt_policy(tmp_path: Path) -> None:
    run_dir = _make_run_dir(tmp_path)
    report_text = render_impact_eval_report(generate_impact_eval_report(run_dir))

    assert "AI wiki first-attempt signal: `positive_signal`" in report_text
    assert "grade `first_pass` captures; `final` repair captures are diagnostic only" in report_text
    assert "| first_attempt_success_rate | 0/1 (0%) | 1/1 (100%) | +100% |" in report_text
    assert "aiwiki_linked_raw_only" in report_text


def test_eval_impact_report_cli_outputs_json_and_writes_text(tmp_path: Path) -> None:
    run_dir = _make_run_dir(tmp_path)

    json_result = runner.invoke(
        app,
        ["eval", "impact", "report", "--run-dir", str(run_dir), "--format", "json"],
    )

    assert json_result.exit_code == 0
    payload = json.loads(json_result.output)
    assert payload["schema_version"] == "impact-eval-product-v1"
    assert payload["primary_comparison"]["outcome"] == "positive_signal"
    assert payload["shareable_for_causal_claims"] is True
    ambient_metrics = {
        item["variant"]: item for item in payload["variant_metrics"]
    }["aiwiki_ambient_memory_workflow"]
    assert ambient_metrics["avg_changed_files"] == 1.0

    output_path = tmp_path / "report.md"
    text_result = runner.invoke(
        app,
        [
            "eval",
            "impact",
            "report",
            "--run-dir",
            str(run_dir),
            "--output",
            str(output_path),
        ],
    )

    assert text_result.exit_code == 0
    assert text_result.output.strip() == str(output_path)
    assert output_path.read_text(encoding="utf-8").startswith(
        "# AI Wiki Impact Eval Product Report"
    )
