from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from ai_wiki_toolkit.cli import app

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


def _install(repo_env: dict[str, Path]) -> Path:
    result = runner.invoke(app, ["install", "--handle", "alice"])
    assert result.exit_code == 0
    return repo_env["repo"] / "ai-wiki"


def _write_route_trace(
    repo_wiki: Path,
    *,
    selected_doc_ids: list[str],
    task_id: str = "route-task",
    packet_words: int = 500,
) -> None:
    _write_jsonl(
        repo_wiki / "metrics" / "route-traces" / "alice.jsonl",
        [
            {
                "author_handle": "alice",
                "index_card_count": len(selected_doc_ids),
                "maybe_load_count": 0,
                "must_load_count": 0,
                "packet_words": packet_words,
                "routed_at": "2026-05-20T10:00:00+00:00",
                "schema_version": "route-trace-v1",
                "selected_doc_count": len(selected_doc_ids),
                "selected_doc_ids": selected_doc_ids,
                "task_id": task_id,
                "task_type": "scaffold_prompt_workflow",
                "trace_id": f"rt_{task_id}",
            }
        ],
    )


def _reuse_event(
    *,
    doc_id: str,
    task_id: str = "route-task",
    outcome: str = "resolved",
    retrieval_mode: str = "lookup",
    event_id: str,
) -> dict[str, object]:
    return {
        "author_handle": "alice",
        "doc_id": doc_id,
        "doc_kind": "draft",
        "event_id": event_id,
        "evidence_mode": "explicit",
        "observed_at": "2026-05-20T10:05:00+00:00",
        "retrieval_mode": retrieval_mode,
        "reuse_outcome": outcome,
        "schema_version": "reuse-v1",
        "task_id": task_id,
    }


def test_evaluate_repo_empty_telemetry_reports_insufficient_evidence(
    repo_env: dict[str, Path],
) -> None:
    _install(repo_env)

    result = runner.invoke(app, ["evaluate", "repo", "--handle", "alice", "--no-write"])

    assert result.exit_code == 0
    assert "# AI Wiki Repo Evaluation" in result.output
    assert "insufficient evidence" in result.output
    assert "No task-level reuse checks or document reuse events" in result.output
    assert "## Caveats" in result.output
    assert "aiwiki-toolkit diagnose memory --since 30d --handle alice" in result.output


def test_evaluate_repo_route_evidence_reports_route_quality_json(
    repo_env: dict[str, Path],
) -> None:
    repo_wiki = _install(repo_env)
    _write_route_trace(
        repo_wiki,
        selected_doc_ids=[
            "review-patterns/selected",
            "review-patterns/noisy",
            "review-patterns/unused",
        ],
    )
    _write_jsonl(
        repo_wiki / "metrics" / "reuse-events" / "alice.jsonl",
        [
            _reuse_event(
                doc_id="review-patterns/selected",
                retrieval_mode="preloaded",
                event_id="evt_selected",
            ),
            _reuse_event(
                doc_id="review-patterns/noisy",
                outcome="not_helpful",
                retrieval_mode="preloaded",
                event_id="evt_noisy",
            ),
            _reuse_event(doc_id="problems/missed", event_id="evt_missed"),
        ],
    )

    text_result = runner.invoke(
        app,
        ["evaluate", "repo", "--handle", "alice", "--since", "2000-01-01"],
    )
    assert text_result.exit_code == 0
    assert "Route precision: `0.33`" in text_result.output
    assert "Route recall proxy: `0.50`" in text_result.output
    assert "Route noise rate: `0.67`" in text_result.output

    json_result = runner.invoke(
        app,
        [
            "evaluate",
            "repo",
            "--handle",
            "alice",
            "--since",
            "2000-01-01",
            "--format",
            "json",
            "--no-write",
        ],
    )
    assert json_result.exit_code == 0
    report = json.loads(json_result.output)
    assert report["schema_version"] == "repo-evaluation-v1"
    assert report["route_quality"]["route_traces"] == 1
    assert report["route_quality"]["route_precision"] == 1 / 3
    assert report["route_quality"]["route_recall_proxy"] == 1 / 2
    assert report["route_quality"]["route_noise_rate"] == 2 / 3


def test_evaluate_repo_missed_useful_docs_recommendation(
    repo_env: dict[str, Path],
) -> None:
    repo_wiki = _install(repo_env)
    _write_route_trace(repo_wiki, selected_doc_ids=["review-patterns/selected"])
    _write_jsonl(
        repo_wiki / "metrics" / "reuse-events" / "alice.jsonl",
        [
            _reuse_event(
                doc_id="review-patterns/selected",
                retrieval_mode="preloaded",
                event_id="evt_selected",
            ),
            _reuse_event(doc_id="problems/missed", event_id="evt_missed"),
        ],
    )

    result = runner.invoke(
        app,
        ["evaluate", "repo", "--handle", "alice", "--since", "2000-01-01", "--no-write"],
    )

    assert result.exit_code == 0
    assert "Missed useful docs exist" in result.output
    assert "improve route hints, index cards" in result.output


def test_evaluate_repo_noisy_route_recommends_sparse_review_not_auto_change(
    repo_env: dict[str, Path],
) -> None:
    repo_wiki = _install(repo_env)
    _write_route_trace(
        repo_wiki,
        selected_doc_ids=[
            "review-patterns/selected",
            "review-patterns/noisy",
            "review-patterns/unused",
        ],
    )
    _write_jsonl(
        repo_wiki / "metrics" / "reuse-events" / "alice.jsonl",
        [
            _reuse_event(
                doc_id="review-patterns/selected",
                retrieval_mode="preloaded",
                event_id="evt_selected",
            ),
            _reuse_event(
                doc_id="review-patterns/noisy",
                outcome="not_helpful",
                retrieval_mode="preloaded",
                event_id="evt_noisy",
            ),
        ],
    )

    result = runner.invoke(
        app,
        ["evaluate", "repo", "--handle", "alice", "--since", "2000-01-01", "--no-write"],
    )

    assert result.exit_code == 0
    assert "sparse/index-card-first" in result.output
    assert "do not auto-change route policy" in result.output


def test_evaluate_repo_consolidation_and_promotion_evidence_recommends_asset_form(
    repo_env: dict[str, Path],
) -> None:
    repo_wiki = _install(repo_env)
    _write_doc(
        repo_wiki / "people" / "alice" / "drafts" / "release-workflow.md",
        "---\n"
        'title: "Release Workflow"\n'
        'source_kind: "feature_clarification"\n'
        'status: "draft"\n'
        "promotion_candidate: true\n"
        "---\n"
        "# Release Workflow\n",
    )

    result = runner.invoke(
        app,
        [
            "evaluate",
            "repo",
            "--handle",
            "alice",
            "--since",
            "2000-01-01",
            "--format",
            "json",
            "--no-write",
        ],
    )

    assert result.exit_code == 0
    report = json.loads(result.output)
    assert report["draft_consolidation"]["human_review_needed_items"] == 1
    assert report["draft_consolidation"]["promotion_candidates"] >= 1
    opportunity = report["asset_selection_opportunities"][0]
    assert opportunity["recommended_form"] == "workflow"
    assert opportunity["confidence"] in {"medium", "high"}


def test_evaluate_repo_no_write_does_not_create_repo_evaluation_outputs(
    repo_env: dict[str, Path],
) -> None:
    repo_wiki = _install(repo_env)

    result = runner.invoke(app, ["evaluate", "repo", "--handle", "alice", "--no-write"])

    assert result.exit_code == 0
    assert not (repo_wiki / "_toolkit" / "reports" / "repo-evaluation").exists()


def test_evaluate_repo_writes_handle_scoped_outputs(
    repo_env: dict[str, Path],
) -> None:
    repo_wiki = _install(repo_env)

    result = runner.invoke(app, ["evaluate", "repo", "--handle", "alice"])

    assert result.exit_code == 0
    markdown_path = repo_wiki / "_toolkit" / "reports" / "repo-evaluation" / "alice" / "latest.md"
    json_path = repo_wiki / "_toolkit" / "reports" / "repo-evaluation" / "alice" / "latest.json"
    assert markdown_path.exists()
    assert json_path.exists()
    assert markdown_path.read_text(encoding="utf-8") == result.output
    assert json.loads(json_path.read_text(encoding="utf-8"))["filters"]["handle"] == "alice"


def test_evaluate_repo_does_not_write_user_owned_ai_wiki_docs(
    repo_env: dict[str, Path],
) -> None:
    repo_wiki = _install(repo_env)
    watched_paths = [
        repo_wiki / "workflows.md",
        *sorted((repo_wiki / "conventions").glob("**/*.md")),
        *sorted((repo_wiki / "problems").glob("**/*.md")),
        *sorted((repo_wiki / "features").glob("**/*.md")),
    ]
    before = {path.relative_to(repo_wiki).as_posix(): path.read_text(encoding="utf-8") for path in watched_paths}

    result = runner.invoke(app, ["evaluate", "repo", "--handle", "alice"])

    assert result.exit_code == 0
    after_paths = [
        repo_wiki / "workflows.md",
        *sorted((repo_wiki / "conventions").glob("**/*.md")),
        *sorted((repo_wiki / "problems").glob("**/*.md")),
        *sorted((repo_wiki / "features").glob("**/*.md")),
    ]
    after = {path.relative_to(repo_wiki).as_posix(): path.read_text(encoding="utf-8") for path in after_paths}
    assert after == before


def test_evaluate_repo_help() -> None:
    result = runner.invoke(app, ["evaluate", "repo", "--help"], terminal_width=120)

    assert result.exit_code == 0
    assert "Generate a review-first repo evaluation" in result.output
    assert "--no-write" in result.output
