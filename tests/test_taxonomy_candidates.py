from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from ai_wiki_toolkit.cli import app

runner = CliRunner()


def _install(repo_env: dict[str, Path]) -> Path:
    result = runner.invoke(app, ["install", "--handle", "alice"])
    assert result.exit_code == 0
    return repo_env["repo"] / "ai-wiki"


def _record_evidence(
    *,
    task_id: str,
    task: str,
    signal_type: str,
    reason: str,
    candidate_category_hint: str | None = None,
    suggested_category_hint: str | None = None,
    wrong_category: str | None = None,
    selected_doc_ids: list[str] | None = None,
    used_doc_ids: list[str] | None = None,
    missed_doc_ids: list[str] | None = None,
    confidence: str = "high",
) -> None:
    args = [
        "record-taxonomy-evidence",
        "--task-id",
        task_id,
        "--task",
        task,
        "--signal-type",
        signal_type,
        "--reason",
        reason,
        "--confidence",
        confidence,
        "--handle",
        "alice",
    ]
    if candidate_category_hint is not None:
        args.extend(["--candidate-category-hint", candidate_category_hint])
    if suggested_category_hint is not None:
        args.extend(["--suggested-category-hint", suggested_category_hint])
    if wrong_category is not None:
        args.extend(["--wrong-category", wrong_category])
    for doc_id in selected_doc_ids or []:
        args.extend(["--selected-doc-id", doc_id])
    for doc_id in used_doc_ids or []:
        args.extend(["--used-doc-id", doc_id])
    for doc_id in missed_doc_ids or []:
        args.extend(["--missed-doc-id", doc_id])

    result = runner.invoke(app, args)
    assert result.exit_code == 0, result.output


def _candidate_report() -> dict[str, object]:
    result = runner.invoke(
        app,
        ["taxonomy", "candidates", "--handle", "alice", "--format", "json", "--no-write"],
    )
    assert result.exit_code == 0, result.output
    return json.loads(result.output)


def _assert_no_active_taxonomy(repo_wiki: Path) -> None:
    assert not (repo_wiki / "taxonomy").exists()
    assert not (repo_wiki / "_toolkit" / "taxonomy").exists()


def test_taxonomy_candidates_induce_proposed_candidate_from_repeated_evidence(
    repo_env: dict[str, Path],
) -> None:
    repo_wiki = _install(repo_env)
    _record_evidence(
        task_id="phase-plan-a",
        task="Plan-only prompt was routed as code because it mentioned bug_fix.",
        signal_type="user_correction",
        suggested_category_hint="route_phase_planning",
        wrong_category="bug_fix",
        selected_doc_ids=["people/alice/drafts/bug-fix-workflow"],
        reason="Mentioned label was treated as actual intent.",
    )
    _record_evidence(
        task_id="phase-plan-b",
        task="No-code planning request should stay in read-only route mode.",
        signal_type="unknown_task_language",
        candidate_category_hint="route_phase_planning",
        selected_doc_ids=["people/alice/drafts/code-workflow"],
        reason="The taxonomy has no stable category for phase-aware route planning.",
    )

    report = _candidate_report()

    assert report["summary"]["candidate_count"] == 1
    assert report["summary"]["active_taxonomy_changed"] is False
    candidate = report["candidates"][0]
    assert candidate["category_id"] == "tax_route-phase-planning"
    assert candidate["kind"] == "agent_runtime_taxonomy"
    assert candidate["status"] == "proposed"
    assert candidate["active"] is False
    assert candidate["gate1"]["status"] == "passed"
    assert candidate["gate1"]["evidence_count"] == 2
    assert candidate["gate2"]["status"] == "not_run"
    assert len(candidate["source_evidence_ids"]) == 2
    assert candidate["positive_examples"][0]["task_id"] == "phase-plan-a"
    _assert_no_active_taxonomy(repo_wiki)


def test_taxonomy_candidates_do_not_induce_from_single_evidence(
    repo_env: dict[str, Path],
) -> None:
    repo_wiki = _install(repo_env)
    _record_evidence(
        task_id="single-signal",
        task="One-off phrasing that may not represent a durable taxonomy gap.",
        signal_type="unknown_task_language",
        candidate_category_hint="one_off_language",
        reason="Only one signal exists.",
    )

    report = _candidate_report()

    assert report["summary"]["candidate_count"] == 0
    assert report["summary"]["rejected_cluster_count"] == 1
    assert report["rejected_clusters"][0]["reason"] == "insufficient_evidence"
    _assert_no_active_taxonomy(repo_wiki)


def test_taxonomy_candidates_gate2_pass_marks_shadow_not_active(
    repo_env: dict[str, Path],
) -> None:
    repo_wiki = _install(repo_env)
    _record_evidence(
        task_id="runtime-a",
        task="Validate whether Codex honors route packet permission boundaries.",
        signal_type="unknown_task_language",
        candidate_category_hint="agent_runtime_capability",
        reason="Runtime permission tests need a separate taxonomy category.",
    )
    _record_evidence(
        task_id="runtime-b",
        task="Plan/code/git/push boundaries need behavior tests.",
        signal_type="user_correction",
        suggested_category_hint="agent_runtime_capability",
        reason="The user corrected this away from generic route usefulness.",
    )
    validation_path = repo_env["repo"] / "validation.json"
    validation_path.write_text(
        json.dumps(
            {
                "tax_agent-runtime-capability": {
                    "status": "passed",
                    "improved": True,
                    "regressions": 0,
                    "method": "behavior_test",
                    "summary": "Behavior tests passed without known regression.",
                }
            }
        ),
        encoding="utf-8",
    )

    result = runner.invoke(
        app,
        [
            "taxonomy",
            "candidates",
            "--handle",
            "alice",
            "--shadow-validation-json",
            str(validation_path),
            "--format",
            "json",
            "--no-write",
        ],
    )

    assert result.exit_code == 0, result.output
    report = json.loads(result.output)
    candidate = report["candidates"][0]
    assert candidate["category_id"] == "tax_agent-runtime-capability"
    assert candidate["status"] == "shadow"
    assert candidate["active"] is False
    assert candidate["gate2"]["status"] == "passed"
    assert candidate["gate2"]["method"] == "behavior_test"
    _assert_no_active_taxonomy(repo_wiki)


def test_taxonomy_candidates_gate2_regression_keeps_candidate_proposed(
    repo_env: dict[str, Path],
) -> None:
    repo_wiki = _install(repo_env)
    _record_evidence(
        task_id="weekly-a",
        task="Weekly report routed to eval product docs instead of reuse metrics workflow.",
        signal_type="false_positive",
        candidate_category_hint="report_workflow_metrics",
        wrong_category="eval_product",
        selected_doc_ids=["people/alice/drafts/eval-product-mvp"],
        reason="Generic report language pulled in eval product docs.",
    )
    _record_evidence(
        task_id="weekly-b",
        task="Promotion summary should use task-check memory, not source incident timing.",
        signal_type="missed_useful",
        candidate_category_hint="report_workflow_metrics",
        wrong_category="source_incident_timing",
        missed_doc_ids=["people/alice/drafts/task-check-memory"],
        reason="Route missed the metrics workflow doc.",
    )
    validation_path = repo_env["repo"] / "validation.json"
    validation_path.write_text(
        json.dumps(
            {
                "tax_report-workflow-metrics": {
                    "status": "passed",
                    "improved": True,
                    "regressions": 1,
                    "method": "shadow_replay",
                    "summary": "Improved weekly reports but hurt release mixed-intent routing.",
                }
            }
        ),
        encoding="utf-8",
    )

    result = runner.invoke(
        app,
        [
            "taxonomy",
            "candidates",
            "--handle",
            "alice",
            "--shadow-validation-json",
            str(validation_path),
            "--format",
            "json",
            "--no-write",
        ],
    )

    assert result.exit_code == 0, result.output
    report = json.loads(result.output)
    candidate = report["candidates"][0]
    assert candidate["category_id"] == "tax_report-workflow-metrics"
    assert candidate["status"] == "proposed"
    assert candidate["active"] is False
    assert candidate["gate2"]["status"] == "failed"
    assert candidate["gate2"]["reason"] == "Regression detected; candidate must remain non-active."
    _assert_no_active_taxonomy(repo_wiki)


def test_taxonomy_candidates_write_managed_report_without_active_taxonomy(
    repo_env: dict[str, Path],
) -> None:
    repo_wiki = _install(repo_env)
    _record_evidence(
        task_id="route-quality-a",
        task="Route quality join needs its own taxonomy.",
        signal_type="missed_useful",
        candidate_category_hint="route_quality_join",
        missed_doc_ids=["people/alice/drafts/route-quality-join"],
        reason="Useful join doc was missed.",
    )
    _record_evidence(
        task_id="route-quality-b",
        task="Selected useful and missed useful docs should be joined.",
        signal_type="unknown_task_language",
        candidate_category_hint="route_quality_join",
        reason="No category for route quality evidence joins.",
    )

    result = runner.invoke(
        app,
        ["taxonomy", "candidates", "--handle", "alice", "--format", "json", "--write"],
    )

    assert result.exit_code == 0, result.output
    report = json.loads(result.output)
    assert report["summary"]["candidate_count"] == 1
    json_path = (
        repo_wiki
        / "_toolkit"
        / "reports"
        / "taxonomy-candidates"
        / "alice"
        / "latest.json"
    )
    markdown_path = json_path.with_suffix(".md")
    assert json_path.exists()
    assert markdown_path.exists()
    assert json.loads(json_path.read_text(encoding="utf-8"))["candidates"][0][
        "category_id"
    ] == "tax_route-quality-join"
    _assert_no_active_taxonomy(repo_wiki)
