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


def _taxonomy_events(repo_wiki: Path) -> list[dict[str, object]]:
    log_path = repo_wiki / "metrics" / "taxonomy-evidence" / "alice.jsonl"
    return [json.loads(line) for line in log_path.read_text(encoding="utf-8").splitlines()]


def _assert_no_active_taxonomy_change(repo_wiki: Path, event: dict[str, object]) -> None:
    assert event["active_taxonomy_changed"] is False
    assert not (repo_wiki / "_toolkit" / "taxonomy").exists()
    assert not (repo_wiki / "taxonomy").exists()


def test_record_taxonomy_evidence_unknown_task_language_records_agent_runtime_gap(
    repo_env: dict[str, Path],
) -> None:
    repo_wiki = _install(repo_env)

    result = runner.invoke(
        app,
        [
            "record-taxonomy-evidence",
            "--task-id",
            "runtime-boundary-audit",
            "--task",
            "Audit Codex runtime permission boundaries across plan, edit, validate, git, and push phases.",
            "--signal-type",
            "unknown_task_language",
            "--candidate-category-hint",
            "agent_runtime_capability",
            "--selected-doc-id",
            "people/alice/drafts/route-usefulness",
            "--reason",
            "The task asks about runtime phase and permission behavior, but no active taxonomy category covers it.",
            "--confidence",
            "medium",
            "--recorded-at",
            "2026-06-06T10:00:00+00:00",
            "--handle",
            "alice",
        ],
    )

    assert result.exit_code == 0
    events = _taxonomy_events(repo_wiki)
    assert len(events) == 1
    event = events[0]
    assert event == {
        "active_taxonomy_changed": False,
        "author_handle": "alice",
        "candidate_category_hint": "agent_runtime_capability",
        "confidence": "medium",
        "evidence_id": event["evidence_id"],
        "missed_doc_ids": [],
        "model": "unknown",
        "reason": "The task asks about runtime phase and permission behavior, but no active taxonomy category covers it.",
        "recorded_at": "2026-06-06T10:00:00+00:00",
        "schema_version": "taxonomy-evidence-v1",
        "selected_doc_ids": ["people/alice/drafts/route-usefulness"],
        "signal_type": "unknown_task_language",
        "task": "Audit Codex runtime permission boundaries across plan, edit, validate, git, and push phases.",
        "task_id": "runtime-boundary-audit",
        "used_doc_ids": [],
    }
    assert event["evidence_id"].startswith("txe_")
    _assert_no_active_taxonomy_change(repo_wiki, event)


def test_record_taxonomy_evidence_false_positive_records_selected_unused_docs(
    repo_env: dict[str, Path],
) -> None:
    repo_wiki = _install(repo_env)

    result = runner.invoke(
        app,
        [
            "record-taxonomy-evidence",
            "--task-id",
            "taxonomy-test-design",
            "--task",
            "Discuss how to test taxonomy post-hoc evidence without implementing induction.",
            "--signal-type",
            "false_positive",
            "--selected-doc-id",
            "people/alice/drafts/source-incident-timing",
            "--selected-doc-id",
            "people/alice/drafts/report-quality",
            "--used-doc-id",
            "people/alice/drafts/route-precision-next-method",
            "--wrong-category",
            "source_incident_timing",
            "--candidate-category-hint",
            "taxonomy_posthoc_evidence",
            "--reason",
            "The selected docs matched generic evidence and diagnosis terms, but the task was taxonomy test design.",
            "--confidence",
            "high",
            "--handle",
            "alice",
        ],
    )

    assert result.exit_code == 0
    event = _taxonomy_events(repo_wiki)[0]
    assert event["signal_type"] == "false_positive"
    assert event["selected_doc_ids"] == [
        "people/alice/drafts/source-incident-timing",
        "people/alice/drafts/report-quality",
    ]
    assert event["used_doc_ids"] == ["people/alice/drafts/route-precision-next-method"]
    assert event["missed_doc_ids"] == []
    assert event["wrong_category"] == "source_incident_timing"
    assert event["candidate_category_hint"] == "taxonomy_posthoc_evidence"
    assert event["confidence"] == "high"
    _assert_no_active_taxonomy_change(repo_wiki, event)


def test_record_taxonomy_evidence_missed_useful_records_lookup_doc(
    repo_env: dict[str, Path],
) -> None:
    repo_wiki = _install(repo_env)

    result = runner.invoke(
        app,
        [
            "record-taxonomy-evidence",
            "--task-id",
            "route-quality-join",
            "--task",
            "Explain how selected docs, useful docs, and missed useful docs join into route quality.",
            "--signal-type",
            "missed_useful",
            "--selected-doc-id",
            "people/alice/drafts/eval-product-mvp",
            "--used-doc-id",
            "people/alice/drafts/route-usefulness-eval-needs-route-traces-and-actual-use-comparison",
            "--missed-doc-id",
            "people/alice/drafts/route-usefulness-eval-needs-route-traces-and-actual-use-comparison",
            "--candidate-category-hint",
            "route_quality_join",
            "--reason",
            "The useful lookup doc explaining route trace versus actual use was not selected by route.",
            "--confidence",
            "high",
            "--handle",
            "alice",
        ],
    )

    assert result.exit_code == 0
    event = _taxonomy_events(repo_wiki)[0]
    assert event["signal_type"] == "missed_useful"
    assert event["candidate_category_hint"] == "route_quality_join"
    assert event["missed_doc_ids"] == [
        "people/alice/drafts/route-usefulness-eval-needs-route-traces-and-actual-use-comparison"
    ]
    assert event["used_doc_ids"] == [
        "people/alice/drafts/route-usefulness-eval-needs-route-traces-and-actual-use-comparison"
    ]
    _assert_no_active_taxonomy_change(repo_wiki, event)


def test_record_taxonomy_evidence_user_correction_records_wrong_and_suggested_category(
    repo_env: dict[str, Path],
) -> None:
    repo_wiki = _install(repo_env)

    first = runner.invoke(
        app,
        [
            "record-taxonomy-evidence",
            "--task-id",
            "taxonomy-correction",
            "--task",
            "This is not diagnostics provenance; it is taxonomy post-hoc evidence.",
            "--signal-type",
            "user_correction",
            "--selected-doc-id",
            "people/alice/drafts/source-incident-timing",
            "--wrong-category",
            "source_incident_timing",
            "--suggested-category-hint",
            "taxonomy_posthoc_evidence",
            "--reason",
            "The user explicitly corrected the route interpretation.",
            "--confidence",
            "high",
            "--handle",
            "alice",
        ],
    )
    second = runner.invoke(
        app,
        [
            "record-taxonomy-evidence",
            "--task-id",
            "taxonomy-correction-followup",
            "--task",
            "Runtime permission boundaries should be grouped separately from route usefulness.",
            "--signal-type",
            "user_correction",
            "--selected-doc-id",
            "people/alice/drafts/route-usefulness",
            "--wrong-category",
            "route_usefulness",
            "--suggested-category-hint",
            "agent_runtime_capability",
            "--reason",
            "The user corrected a phase behavior task away from route-usefulness taxonomy.",
            "--confidence",
            "high",
            "--handle",
            "alice",
        ],
    )

    assert first.exit_code == 0
    assert second.exit_code == 0
    events = _taxonomy_events(repo_wiki)
    assert len(events) == 2
    assert events[0]["task_id"] == "taxonomy-correction"
    assert events[1]["task_id"] == "taxonomy-correction-followup"
    assert events[0]["wrong_category"] == "source_incident_timing"
    assert events[0]["suggested_category_hint"] == "taxonomy_posthoc_evidence"
    assert events[1]["wrong_category"] == "route_usefulness"
    assert events[1]["suggested_category_hint"] == "agent_runtime_capability"
    for event in events:
        _assert_no_active_taxonomy_change(repo_wiki, event)
