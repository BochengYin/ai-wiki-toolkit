from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path

from typer.testing import CliRunner

from ai_wiki_toolkit.cli import app
from ai_wiki_toolkit.weekly_report import generate_weekly_report

runner = CliRunner()


def _write_jsonl(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )


def _write_doc(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def test_weekly_report_writes_html_json_latest_and_state(
    repo_env: dict[str, Path],
) -> None:
    install_result = runner.invoke(app, ["install", "--handle", "alice"])
    assert install_result.exit_code == 0

    repo_wiki = repo_env["repo"] / "ai-wiki"
    _write_doc(
        repo_wiki / "problems" / "release-check.md",
        "---\n"
        'title: "Release Check"\n'
        "---\n"
        "# Release Check\n",
    )
    _write_jsonl(
        repo_wiki / "metrics" / "reuse-events" / "alice.jsonl",
        [
            {
                "author_handle": "alice",
                "doc_id": "problems/release-check",
                "doc_kind": "problem",
                "estimated_savings": {"saved_seconds": 90, "saved_tokens": 1200},
                "event_id": "evt_inside",
                "evidence_mode": "explicit",
                "observed_at": "2026-05-13T10:00:00+00:00",
                "retrieval_mode": "lookup",
                "reuse_effects": ["avoided_retry"],
                "reuse_outcome": "resolved",
                "schema_version": "reuse-v1",
                "task_id": "task-inside",
            },
            {
                "author_handle": "alice",
                "doc_id": "problems/release-check",
                "doc_kind": "problem",
                "estimated_savings": {"saved_seconds": 999, "saved_tokens": 999},
                "event_id": "evt_outside",
                "evidence_mode": "explicit",
                "observed_at": "2026-05-09T10:00:00+00:00",
                "retrieval_mode": "lookup",
                "reuse_outcome": "resolved",
                "schema_version": "reuse-v1",
                "task_id": "task-outside",
            },
        ],
    )
    _write_jsonl(
        repo_wiki / "metrics" / "task-checks" / "alice.jsonl",
        [
            {
                "author_handle": "alice",
                "check_id": "check_inside",
                "check_outcome": "wiki_used",
                "checked_at": "2026-05-13T10:05:00+00:00",
                "schema_version": "reuse-v1",
                "task_id": "task-inside",
            },
            {
                "author_handle": "alice",
                "check_id": "check_outside",
                "check_outcome": "wiki_used",
                "checked_at": "2026-05-09T10:05:00+00:00",
                "schema_version": "reuse-v1",
                "task_id": "task-outside",
            },
        ],
    )

    result = generate_weekly_report(
        repo_wiki,
        handle="alice",
        now=datetime(2026, 5, 17, 12, 0, tzinfo=timezone.utc),
        if_due=True,
    )

    assert result.report["schema_version"] == "weekly-report-v1"
    assert result.report["status"] == "generated"
    assert result.report["period"]["period_id"] == "2026-W20"
    assert result.report["usefulness"]["summary"]["reuse_events"] == 1
    assert result.report["usefulness"]["summary"]["task_checks"] == 1
    assert result.report["usefulness"]["summary"]["total_estimated_seconds_saved"] == 90
    assert result.report["coverage"]["summary"]["referenced_eligible_documents"] == 1
    assert result.report["coverage"]["summary"]["unreferenced_eligible_documents"] >= 1
    assert "<!doctype html>" in result.html
    assert "AI Wiki Weekly Review Queue" in result.html
    assert "Release Check" not in result.html
    assert "Coverage" not in result.html
    assert "Referenced Files" not in result.html
    assert "Unreferenced Files" not in result.html
    assert "Weekly Log Saved" not in result.html

    html_path = repo_wiki / "_toolkit" / "reports" / "weekly" / "alice" / "2026-W20" / "report.html"
    json_path = repo_wiki / "_toolkit" / "reports" / "weekly" / "alice" / "2026-W20" / "report.json"
    latest_html = repo_wiki / "_toolkit" / "reports" / "weekly" / "alice" / "latest.html"
    latest_json = repo_wiki / "_toolkit" / "reports" / "weekly" / "alice" / "latest.json"
    state_path = repo_wiki / "_toolkit" / "reports" / "weekly" / "alice" / "state.json"
    assert html_path.read_text(encoding="utf-8") == result.html
    assert latest_html.read_text(encoding="utf-8") == result.html
    assert json.loads(json_path.read_text(encoding="utf-8"))["period"]["period_id"] == "2026-W20"
    assert json.loads(latest_json.read_text(encoding="utf-8"))["period"]["period_id"] == "2026-W20"
    state = json.loads(state_path.read_text(encoding="utf-8"))
    assert state["weekly"]["alice"]["last_period_id"] == "2026-W20"
    assert state["weekly"]["alice"]["last_report_path"] == (
        "ai-wiki/_toolkit/reports/weekly/alice/2026-W20/report.html"
    )

    skipped = generate_weekly_report(
        repo_wiki,
        handle="alice",
        now=datetime(2026, 5, 17, 13, 0, tzinfo=timezone.utc),
        if_due=True,
    )

    assert skipped.report["status"] == "skipped"
    assert skipped.report["reason"] == "weekly report for this period already exists"
    assert skipped.html == ""


def test_weekly_report_omits_saved_time_and_reports_coverage(
    repo_env: dict[str, Path],
) -> None:
    install_result = runner.invoke(app, ["install", "--handle", "alice"])
    assert install_result.exit_code == 0

    repo = repo_env["repo"]
    repo_wiki = repo / "ai-wiki"
    _write_doc(repo_wiki / "problems" / "referenced.md", "# Referenced\n")
    _write_doc(repo_wiki / "problems" / "unreferenced.md", "# Unreferenced\n")
    _write_jsonl(
        repo_wiki / "metrics" / "reuse-events" / "alice.jsonl",
        [
            {
                "author_handle": "alice",
                "doc_id": "problems/referenced",
                "doc_kind": "problem",
                "event_id": "evt_referenced",
                "evidence_mode": "explicit",
                "observed_at": "2026-05-13T10:00:00+00:00",
                "retrieval_mode": "lookup",
                "reuse_outcome": "resolved",
                "schema_version": "reuse-v1",
                "task_id": "task-referenced",
            },
        ],
    )

    report = generate_weekly_report(
        repo / "ai-wiki",
        handle="alice",
        now=datetime(2026, 5, 17, 12, 0, tzinfo=timezone.utc),
    )

    assert "impact_efficiency" not in report.report
    assert report.report["coverage"]["summary"]["referenced_eligible_documents"] == 1
    assert any(
        item["doc_id"] == "problems/unreferenced"
        for item in report.report["coverage"]["unreferenced_documents"]
    )
    assert "Impact Eval Efficiency" not in report.html
    assert "Estimated Saved" not in report.html
    assert "ai-wiki/problems/referenced.md" not in report.html
    assert "ai-wiki/problems/unreferenced.md" not in report.html
    assert "Coverage" not in report.html
    assert "Referenced Files" not in report.html
    assert "Unreferenced Files" not in report.html


def test_weekly_report_reports_personal_drafts_needing_diagnosis(
    repo_env: dict[str, Path],
) -> None:
    install_result = runner.invoke(app, ["install", "--handle", "alice"])
    assert install_result.exit_code == 0

    repo = repo_env["repo"]
    repo_wiki = repo / "ai-wiki"
    _write_doc(
        repo_wiki / "people" / "alice" / "drafts" / "noisy-draft.md",
        "---\n"
        'title: "Noisy Draft"\n'
        "---\n"
        "# Noisy Draft\n",
    )
    _write_jsonl(
        repo_wiki / "metrics" / "reuse-events" / "alice.jsonl",
        [
            {
                "author_handle": "alice",
                "doc_id": "people/alice/drafts/noisy-draft",
                "doc_kind": "draft",
                "event_id": "evt_partial",
                "evidence_mode": "explicit",
                "observed_at": "2026-05-13T10:00:00+00:00",
                "retrieval_mode": "lookup",
                "reuse_outcome": "partial",
                "schema_version": "reuse-v1",
                "session_id": "reuse-session-1",
                "source_session_id": "source-session-1",
                "task_id": "task-noisy-1",
            },
            {
                "author_handle": "alice",
                "doc_id": "people/alice/drafts/noisy-draft",
                "doc_kind": "draft",
                "event_id": "evt_candidate",
                "evidence_mode": "inferred",
                "not_helpful_reason": "superseded_by_later_doc",
                "observed_at": "2026-05-13T10:05:00+00:00",
                "retrieval_mode": "lookup",
                "reuse_outcome": "not_helpful",
                "schema_version": "reuse-v1",
                "signal_status": "candidate",
                "superseded_by_doc_id": "problems/better-doc",
                "task_id": "task-noisy-2",
            },
        ],
    )

    report = generate_weekly_report(
        repo_wiki,
        handle="alice",
        now=datetime(2026, 5, 17, 12, 0, tzinfo=timezone.utc),
    )

    doc = report.report["usefulness"]["referenced_documents"][0]
    assert doc["candidate_not_helpful_events"] == 1
    assert doc["confirmed_not_helpful_events"] == 0
    assert doc["not_helpful_reasons"] == {"superseded_by_later_doc": 1}
    assert doc["source_session_ids"] == ["source-session-1"]
    needs_improvement = report.report["diagnosis"]["needs_improvement"]
    assert needs_improvement[0]["doc_id"] == "people/alice/drafts/noisy-draft"
    assert needs_improvement[0]["suggested_action"] == "human_review"
    assert "Personal Drafts Needing Diagnosis" in report.html
    assert "candidate not_helpful" in report.html
    assert "superseded_by_later_doc" in report.html


def test_weekly_report_cli_generates_json(
    repo_env: dict[str, Path],
) -> None:
    install_result = runner.invoke(app, ["install", "--handle", "alice"])
    assert install_result.exit_code == 0

    result = runner.invoke(app, ["report", "weekly", "--handle", "alice", "--format", "json"])

    assert result.exit_code == 0
    report = json.loads(result.output)
    assert report["schema_version"] == "weekly-report-v1"
    assert report["status"] == "generated"
    assert report["outputs"]["latest_html"] == "ai-wiki/_toolkit/reports/weekly/alice/latest.html"


def test_weekly_report_requires_initialized_repo_wiki(
    repo_env: dict[str, Path],
) -> None:
    result = runner.invoke(app, ["report", "weekly", "--handle", "alice"])

    assert result.exit_code == 1
    assert "Repo AI wiki is not initialized. Run `aiwiki-toolkit install` first." in result.output
