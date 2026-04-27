from __future__ import annotations

import json
from pathlib import Path

from ai_wiki_toolkit.wiki_schema import (
    build_document_stats,
    build_repo_catalog,
    build_task_stats,
    infer_doc_kind,
)


def test_build_repo_catalog_includes_user_owned_markdown_only(tmp_path: Path) -> None:
    repo_wiki = tmp_path / "ai-wiki"
    (repo_wiki / "review-patterns").mkdir(parents=True)
    (repo_wiki / "_toolkit").mkdir(parents=True)
    (repo_wiki / "index.md").write_text("# Project AI Wiki Index\n", encoding="utf-8")
    (repo_wiki / "review-patterns" / "index.md").write_text("# Review Patterns Index\n", encoding="utf-8")
    (repo_wiki / "_toolkit" / "system.md").write_text("# Managed\n", encoding="utf-8")
    (repo_wiki / "metrics").mkdir()
    (repo_wiki / "metrics" / "reuse-events.jsonl").write_text("{}", encoding="utf-8")

    catalog = build_repo_catalog(repo_wiki)

    assert catalog == {
        "schema_version": "reuse-v1",
        "documents": [
            {
                "doc_id": "index",
                "kind": "repo_index",
                "path": f"ai-wiki/{'index.md'}",
                "source": "user_owned",
                "title": "Project AI Wiki Index",
            },
            {
                "doc_id": "review-patterns/index",
                "kind": "review_pattern_index",
                "path": "ai-wiki/review-patterns/index.md",
                "source": "user_owned",
                "title": "Review Patterns Index",
            },
        ],
    }


def test_build_repo_catalog_prefers_frontmatter_title(tmp_path: Path) -> None:
    repo_wiki = tmp_path / "ai-wiki"
    (repo_wiki / "people" / "alice" / "drafts").mkdir(parents=True)
    (repo_wiki / "people" / "alice" / "drafts" / "release-note.md").write_text(
        "\n".join(
            [
                "---",
                'title: "Release note edge case"',
                "---",
                "",
                "# Review Draft",
                "",
                "Body",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    catalog = build_repo_catalog(repo_wiki)

    assert catalog == {
        "schema_version": "reuse-v1",
        "documents": [
            {
                "doc_id": "people/alice/drafts/release-note",
                "kind": "draft",
                "path": "ai-wiki/people/alice/drafts/release-note.md",
                "source": "user_owned",
                "title": "Release note edge case",
            }
        ],
    }


def test_infer_doc_kind_recognizes_team_memory_docs() -> None:
    assert infer_doc_kind("conventions/index.md") == "convention_index"
    assert infer_doc_kind("conventions/python-typing.md") == "convention"
    assert infer_doc_kind("problems/index.md") == "problem_index"
    assert infer_doc_kind("problems/async-notification-tests-flaky.md") == "problem"
    assert infer_doc_kind("features/index.md") == "feature_index"
    assert infer_doc_kind("features/bulk-invoice-upload.md") == "feature"
    assert infer_doc_kind("review-patterns/index.md") == "review_pattern_index"
    assert infer_doc_kind("trails/release-debugging.md") == "trail"
    assert infer_doc_kind("work/index.md") == "work_index"
    assert infer_doc_kind("work/events/alice.jsonl") == "work"
    assert infer_doc_kind("people/alice/index.md") == "person_index"
    assert infer_doc_kind("decisions.md") == "decisions"


def test_build_repo_catalog_includes_team_memory_kinds(tmp_path: Path) -> None:
    repo_wiki = tmp_path / "ai-wiki"
    (repo_wiki / "conventions").mkdir(parents=True)
    (repo_wiki / "problems").mkdir(parents=True)
    (repo_wiki / "features").mkdir(parents=True)
    (repo_wiki / "conventions" / "index.md").write_text("# Conventions Index\n", encoding="utf-8")
    (repo_wiki / "conventions" / "python-typing.md").write_text("# Python Typing\n", encoding="utf-8")
    (repo_wiki / "problems" / "index.md").write_text("# Problems Index\n", encoding="utf-8")
    (repo_wiki / "problems" / "async-notification-tests-flaky.md").write_text(
        "# Async notification tests\n",
        encoding="utf-8",
    )
    (repo_wiki / "features" / "index.md").write_text("# Features Index\n", encoding="utf-8")
    (repo_wiki / "features" / "bulk-invoice-upload.md").write_text(
        "# Bulk invoice upload\n",
        encoding="utf-8",
    )

    catalog = build_repo_catalog(repo_wiki)

    assert catalog == {
        "schema_version": "reuse-v1",
        "documents": [
            {
                "doc_id": "conventions/index",
                "kind": "convention_index",
                "path": "ai-wiki/conventions/index.md",
                "source": "user_owned",
                "title": "Conventions Index",
            },
            {
                "doc_id": "conventions/python-typing",
                "kind": "convention",
                "path": "ai-wiki/conventions/python-typing.md",
                "source": "user_owned",
                "title": "Python Typing",
            },
            {
                "doc_id": "features/bulk-invoice-upload",
                "kind": "feature",
                "path": "ai-wiki/features/bulk-invoice-upload.md",
                "source": "user_owned",
                "title": "Bulk invoice upload",
            },
            {
                "doc_id": "features/index",
                "kind": "feature_index",
                "path": "ai-wiki/features/index.md",
                "source": "user_owned",
                "title": "Features Index",
            },
            {
                "doc_id": "problems/async-notification-tests-flaky",
                "kind": "problem",
                "path": "ai-wiki/problems/async-notification-tests-flaky.md",
                "source": "user_owned",
                "title": "Async notification tests",
            },
            {
                "doc_id": "problems/index",
                "kind": "problem_index",
                "path": "ai-wiki/problems/index.md",
                "source": "user_owned",
                "title": "Problems Index",
            },
        ],
    }


def test_build_document_stats_aggregates_reuse_events(tmp_path: Path) -> None:
    repo_wiki = tmp_path / "ai-wiki"
    (repo_wiki / "metrics" / "reuse-events").mkdir(parents=True)
    (repo_wiki / "metrics" / "reuse-events" / "alice.jsonl").write_text(
        "\n".join(
            [
                json.dumps(
                    {
                        "author_handle": "alice",
                        "doc_id": "review-patterns/prompt-file-rule",
                        "observed_at": "2026-04-20T10:00:00+10:00",
                        "retrieval_mode": "preloaded",
                        "reuse_outcome": "resolved",
                    }
                ),
                json.dumps(
                    {
                        "author_handle": "alice",
                        "doc_id": "review-patterns/prompt-file-rule",
                        "observed_at": "2026-04-20T11:00:00+10:00",
                        "retrieval_mode": "lookup",
                        "reuse_outcome": "partial",
                    }
                ),
                json.dumps(
                    {
                        "author_handle": "alice",
                        "doc_id": "_toolkit/system",
                        "observed_at": "2026-04-20T12:00:00+10:00",
                        "retrieval_mode": "preloaded",
                        "reuse_outcome": "resolved",
                    }
                ),
                "not-json",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    stats = build_document_stats(repo_wiki)

    assert stats == {
        "schema_version": "reuse-v1",
        "skipped_event_lines": 1,
        "documents": {
            "review-patterns/prompt-file-rule": {
                "effective_reuse_count": 1,
                "last_effective_at": "2026-04-20T10:00:00+10:00",
                "last_observed_at": "2026-04-20T11:00:00+10:00",
                "lookup_reuse_count": 1,
                "preloaded_reuse_count": 1,
                "total_events": 2,
            }
        },
    }


def test_build_task_stats_sums_estimated_savings(tmp_path: Path) -> None:
    repo_wiki = tmp_path / "ai-wiki"
    (repo_wiki / "metrics" / "reuse-events").mkdir(parents=True)
    (repo_wiki / "metrics" / "reuse-events" / "alice.jsonl").write_text(
        "\n".join(
            [
                json.dumps(
                    {
                        "author_handle": "alice",
                        "task_id": "task-1",
                        "doc_id": "review-patterns/prompt-file-rule",
                        "retrieval_mode": "preloaded",
                        "reuse_outcome": "resolved",
                        "estimated_savings": {"saved_tokens": 1200, "saved_seconds": 30},
                    }
                ),
                json.dumps(
                    {
                        "author_handle": "alice",
                        "task_id": "task-1",
                        "doc_id": "trails/release-debugging",
                        "retrieval_mode": "lookup",
                        "reuse_outcome": "partial",
                        "estimated_savings": {"saved_tokens": 300, "saved_seconds": 10},
                    }
                ),
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (repo_wiki / "metrics" / "task-checks").mkdir(parents=True)
    (repo_wiki / "metrics" / "task-checks" / "alice.jsonl").write_text(
        json.dumps(
            {
                "author_handle": "alice",
                "task_id": "task-1",
                "checked_at": "2026-04-20T12:00:00+10:00",
                "check_outcome": "wiki_used",
            }
        )
        + "\n",
        encoding="utf-8",
    )

    stats = build_task_stats(repo_wiki)

    assert stats == {
        "schema_version": "reuse-v1",
        "skipped_check_lines": 0,
        "skipped_event_lines": 0,
        "summary": {
            "checked_tasks": 1,
            "tasks_with_events_but_no_check": 0,
            "tasks_with_wiki_use": 1,
            "tasks_without_wiki_use": 0,
        },
        "tasks": {
            "task-1": {
                "check_count": 1,
                "effective_reuse_count": 1,
                "estimated_seconds_saved": 40,
                "estimated_token_savings": 1500,
                "last_check_outcome": "wiki_used",
                "last_checked_at": "2026-04-20T12:00:00+10:00",
                "lookup_reuse_count": 1,
                "preloaded_reuse_count": 1,
                "reuse_checked": True,
                "reused_docs": 2,
                "total_events": 2,
            }
        },
    }


def test_build_task_stats_includes_checked_tasks_with_no_reuse(tmp_path: Path) -> None:
    repo_wiki = tmp_path / "ai-wiki"
    (repo_wiki / "metrics" / "task-checks").mkdir(parents=True)
    (repo_wiki / "metrics" / "task-checks" / "alice.jsonl").write_text(
        json.dumps(
            {
                "author_handle": "alice",
                "task_id": "task-2",
                "checked_at": "2026-04-20T13:00:00+10:00",
                "check_outcome": "no_wiki_use",
            }
        )
        + "\n",
        encoding="utf-8",
    )

    stats = build_task_stats(repo_wiki)

    assert stats == {
        "schema_version": "reuse-v1",
        "skipped_check_lines": 0,
        "skipped_event_lines": 0,
        "summary": {
            "checked_tasks": 1,
            "tasks_with_events_but_no_check": 0,
            "tasks_with_wiki_use": 0,
            "tasks_without_wiki_use": 1,
        },
        "tasks": {
            "task-2": {
                "check_count": 1,
                "effective_reuse_count": 0,
                "estimated_seconds_saved": 0,
                "estimated_token_savings": 0,
                "last_check_outcome": "no_wiki_use",
                "last_checked_at": "2026-04-20T13:00:00+10:00",
                "lookup_reuse_count": 0,
                "preloaded_reuse_count": 0,
                "reuse_checked": True,
                "reused_docs": 0,
                "total_events": 0,
            }
        },
    }


def test_build_task_stats_reads_legacy_flat_logs_for_compatibility(tmp_path: Path) -> None:
    repo_wiki = tmp_path / "ai-wiki"
    (repo_wiki / "metrics").mkdir(parents=True)
    (repo_wiki / "metrics" / "reuse-events.jsonl").write_text(
        json.dumps(
            {
                "task_id": "task-legacy",
                "doc_id": "workflows",
                "retrieval_mode": "preloaded",
                "reuse_outcome": "resolved",
            }
        )
        + "\n",
        encoding="utf-8",
    )
    (repo_wiki / "metrics" / "task-checks.jsonl").write_text(
        json.dumps(
            {
                "task_id": "task-legacy",
                "checked_at": "2026-04-20T14:00:00+10:00",
                "check_outcome": "wiki_used",
            }
        )
        + "\n",
        encoding="utf-8",
    )

    stats = build_task_stats(repo_wiki)

    assert stats["summary"] == {
        "checked_tasks": 1,
        "tasks_with_events_but_no_check": 0,
        "tasks_with_wiki_use": 1,
        "tasks_without_wiki_use": 0,
    }
    assert stats["tasks"]["task-legacy"]["reused_docs"] == 1
