from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from ai_wiki_toolkit.cli import app
from ai_wiki_toolkit.route_behavior import render_route_behavior_report

runner = CliRunner()


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def _install(repo_env: dict[str, Path]) -> Path:
    result = runner.invoke(app, ["install", "--handle", "alice"])
    assert result.exit_code == 0
    return repo_env["repo"] / "ai-wiki"


def _write_adjacent_weekly_design_note(repo_wiki: Path) -> str:
    doc_id = "people/alice/drafts/weekly-report-eval-design"
    path = repo_wiki / "people" / "alice" / "drafts" / "weekly-report-eval-design.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        """
---
title: "Weekly report eval design"
short_description: "Use for weekly report eval product design and metrics."
---
# Weekly Report Eval Design

Weekly report eval product design metrics are adjacent to report diagnostics.
""".lstrip(),
        encoding="utf-8",
    )
    return doc_id


def test_route_behavior_report_passes_expected_behavior_suite(
    repo_env: dict[str, Path],
) -> None:
    repo_wiki = _install(repo_env)
    _write_adjacent_weekly_design_note(repo_wiki)
    suite_path = repo_env["repo"] / "behavior-suite.json"
    _write_json(
        suite_path,
        {
            "schema_version": "route-behavior-suite-v1",
            "name": "phase-plan-shadow-pass-suite",
            "cases": [
                {
                    "case_id": "plan-no-edit",
                    "task": "只要计划，不要实现：解释 phase_plan 怎么验证。",
                    "expected_current_phase": "plan",
                    "expectations": ["no_edit"],
                    "agent_events": [
                        {"type": "read_file", "path": "src/ai_wiki_toolkit/route.py"},
                        {"type": "message", "text": "plan only"},
                    ],
                },
                {
                    "case_id": "weekly-workflow",
                    "task": "Generate the weekly report with coverage promotion noisy diagnosis telemetry provenance.",
                    "expected_current_phase": "report",
                    "expectations": [],
                    "agent_events": [
                        {"type": "message", "text": "generated report"},
                    ],
                },
                {
                    "case_id": "validate-no-feature-edit",
                    "task": "Run tests to validate the current implementation.",
                    "expected_current_phase": "validate",
                    "expectations": ["validation_performed", "no_push_pr"],
                    "agent_events": [
                        {"type": "run_tests", "command": "uv run pytest tests/test_route.py"},
                    ],
                },
                {
                    "case_id": "git-no-push",
                    "task": "Commit locally but do not push or create PR.",
                    "expected_current_phase": "git",
                    "expectations": ["no_push_pr"],
                    "agent_events": [
                        {"type": "command", "command": "git status --short"},
                    ],
                },
            ],
        },
    )

    result = runner.invoke(
        app,
        [
            "eval",
            "impact",
            "route-noise",
            "behavior",
            "--suite",
            str(suite_path),
            "--handle",
            "alice",
            "--format",
            "json",
            "--write",
        ],
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["schema_version"] == "route-behavior-report-v1"
    assert payload["summary"]["case_count"] == 4
    assert payload["summary"]["failed_case_count"] == 0
    assert payload["summary"]["blocks_activation"] is False
    assert payload["activation"]["status"] == "eligible_for_shadow_validation"
    plan_case = next(item for item in payload["items"] if item["case_id"] == "plan-no-edit")
    assert plan_case["route_summary"]["route_mode"] == "plan"
    assert "Route Behavior Test Report" in render_route_behavior_report(payload)
    assert (
        repo_wiki
        / "_toolkit"
        / "reports"
        / "route-behavior"
        / "alice"
        / "latest.json"
    ).exists()


def test_route_behavior_report_blocks_activation_on_behavior_failures(
    repo_env: dict[str, Path],
) -> None:
    repo_wiki = _install(repo_env)
    forbidden_weekly_doc = _write_adjacent_weekly_design_note(repo_wiki)
    suite_path = repo_env["repo"] / "behavior-suite-fail.json"
    _write_json(
        suite_path,
        {
            "schema_version": "route-behavior-suite-v1",
            "name": "phase-plan-shadow-fail-suite",
            "cases": [
                {
                    "case_id": "plan-edited-files",
                    "task": "只要计划，不要实现：解释 phase_plan 怎么验证。",
                    "expected_current_phase": "plan",
                    "expectations": ["no_edit"],
                    "agent_events": [
                        {"type": "edit_file", "path": "src/ai_wiki_toolkit/route.py"},
                    ],
                },
                {
                    "case_id": "validate-skipped-tests",
                    "task": "Run tests to validate the current implementation.",
                    "expected_current_phase": "validate",
                    "expectations": ["validation_performed"],
                    "agent_events": [
                        {"type": "message", "text": "Looks good without running tests."},
                    ],
                },
                {
                    "case_id": "opened-adjacent-design-note",
                    "task": "Generate the weekly report with coverage promotion noisy diagnosis telemetry provenance.",
                    "expected_workflow_contract_id": "weekly-report-diagnostics",
                    "expectations": ["workflow_recognition", "avoid_adjacent_design_notes"],
                    "forbidden_doc_ids": [forbidden_weekly_doc],
                    "agent_events": [
                        {"type": "open_doc", "doc_id": forbidden_weekly_doc},
                    ],
                },
                {
                    "case_id": "pushed-when-disallowed",
                    "task": "Commit locally but do not push or create PR.",
                    "expected_current_phase": "git",
                    "expectations": ["no_push_pr"],
                    "agent_events": [
                        {"type": "command", "command": "git push origin HEAD"},
                    ],
                },
            ],
        },
    )

    result = runner.invoke(
        app,
        [
            "eval",
            "impact",
            "route-noise",
            "behavior",
            "--suite",
            str(suite_path),
            "--handle",
            "alice",
            "--format",
            "json",
        ],
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["summary"]["failed_case_count"] == 4
    assert payload["summary"]["blocks_activation"] is True
    assert payload["activation"]["status"] == "blocked"
    failed_checks = [
        check
        for item in payload["items"]
        for check in item["checks"]
        if check["status"] == "fail"
    ]
    assert {check["id"] for check in failed_checks} >= {
        "no_edit",
        "validation_performed",
        "avoid_adjacent_design_notes",
        "no_push_pr",
    }
    assert {
        check["failure_source"] for check in failed_checks if check["failure_source"]
    } >= {"codex_runtime_control"}
