from __future__ import annotations

import json
from pathlib import Path

from ai_wiki_toolkit.wiki_schema import (
    build_document_stats,
    build_repo_catalog,
    build_task_stats,
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


def test_build_document_stats_aggregates_reuse_events(tmp_path: Path) -> None:
    repo_wiki = tmp_path / "ai-wiki"
    (repo_wiki / "metrics").mkdir(parents=True)
    (repo_wiki / "metrics" / "reuse-events.jsonl").write_text(
        "\n".join(
            [
                json.dumps(
                    {
                        "doc_id": "review-patterns/prompt-file-rule",
                        "observed_at": "2026-04-20T10:00:00+10:00",
                        "retrieval_mode": "preloaded",
                        "reuse_outcome": "resolved",
                    }
                ),
                json.dumps(
                    {
                        "doc_id": "review-patterns/prompt-file-rule",
                        "observed_at": "2026-04-20T11:00:00+10:00",
                        "retrieval_mode": "lookup",
                        "reuse_outcome": "partial",
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
    (repo_wiki / "metrics").mkdir(parents=True)
    (repo_wiki / "metrics" / "reuse-events.jsonl").write_text(
        "\n".join(
            [
                json.dumps(
                    {
                        "task_id": "task-1",
                        "doc_id": "review-patterns/prompt-file-rule",
                        "retrieval_mode": "preloaded",
                        "reuse_outcome": "resolved",
                        "estimated_savings": {"saved_tokens": 1200, "saved_seconds": 30},
                    }
                ),
                json.dumps(
                    {
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

    stats = build_task_stats(repo_wiki)

    assert stats == {
        "schema_version": "reuse-v1",
        "skipped_event_lines": 0,
        "tasks": {
            "task-1": {
                "effective_reuse_count": 1,
                "estimated_seconds_saved": 40,
                "estimated_token_savings": 1500,
                "lookup_reuse_count": 1,
                "preloaded_reuse_count": 1,
                "reused_docs": 2,
                "total_events": 2,
            }
        },
    }
