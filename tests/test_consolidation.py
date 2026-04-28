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


def test_consolidate_queue_writes_generated_review_queue(
    repo_env: dict[str, Path],
) -> None:
    install_result = runner.invoke(app, ["install", "--handle", "alice"])
    assert install_result.exit_code == 0

    repo_wiki = repo_env["repo"] / "ai-wiki"
    drafts_dir = repo_wiki / "people" / "alice" / "drafts"
    _write_doc(
        drafts_dir / "prefer-stable-prompt-blocks.md",
        "---\n"
        'title: "Prefer Stable Prompt Blocks"\n'
        'source_kind: "review"\n'
        'status: "draft"\n'
        "promotion_candidate: true\n"
        "---\n"
        "# Prefer Stable Prompt Blocks\n",
    )
    _write_doc(
        drafts_dir / "old-routing-rule.md",
        "---\n"
        'title: "Old Routing Rule"\n'
        'source_kind: "review"\n'
        'status: "superseded"\n'
        "---\n"
        "# Old Routing Rule\n",
    )
    _write_doc(
        drafts_dir / "conflicting-memory.md",
        "---\n"
        'title: "Conflicting Memory"\n'
        'source_kind: "feature_clarification"\n'
        'status: "draft"\n'
        "---\n"
        "# Conflicting Memory\n\nThis conflicts with an active decision.\n",
    )

    result = runner.invoke(app, ["consolidate", "queue", "--handle", "alice"])

    assert result.exit_code == 0
    assert "# AI Wiki Draft Consolidation" in result.output
    assert "## Draft Clusters" in result.output
    assert "- Promotion candidate" in result.output
    assert "- Supersession" in result.output
    assert "- Conflict" in result.output
    assert "`ai-wiki/review-patterns/prefer-stable-prompt-blocks.md`" in result.output
    assert not (repo_wiki / "review-patterns" / "prefer-stable-prompt-blocks.md").exists()

    markdown_path = repo_wiki / "_toolkit" / "consolidation" / "queue.md"
    json_path = repo_wiki / "_toolkit" / "consolidation" / "queue.json"
    assert markdown_path.read_text(encoding="utf-8") == result.output
    report = json.loads(json_path.read_text(encoding="utf-8"))
    assert report["schema_version"] == "consolidation-queue-v1"
    assert report["summary"]["drafts_scanned"] == 3
    assert report["summary"]["queue_items"] == 3
    actions = {item["suggested_action"] for item in report["queue_items"]}
    assert actions == {"Promotion candidate", "Supersession", "Conflict"}


def test_consolidate_queue_uses_diagnostics_high_roi_signal_without_write(
    repo_env: dict[str, Path],
) -> None:
    install_result = runner.invoke(app, ["install", "--handle", "alice"])
    assert install_result.exit_code == 0

    repo_wiki = repo_env["repo"] / "ai-wiki"
    _write_doc(
        repo_wiki / "people" / "alice" / "drafts" / "route-clarity.md",
        "---\n"
        'title: "Route Clarity"\n'
        'source_kind: "feature_clarification"\n'
        'status: "draft"\n'
        "promotion_candidate: false\n"
        "---\n"
        "# Route Clarity\n",
    )
    _write_jsonl(
        repo_wiki / "metrics" / "reuse-events" / "alice.jsonl",
        [
            {
                "author_handle": "alice",
                "doc_id": "people/alice/drafts/route-clarity",
                "doc_kind": "draft",
                "event_id": "evt_1",
                "evidence_mode": "explicit",
                "observed_at": "2026-04-20T10:00:00+00:00",
                "retrieval_mode": "lookup",
                "reuse_outcome": "resolved",
                "schema_version": "reuse-v1",
                "task_id": "task-1",
            },
            {
                "author_handle": "alice",
                "doc_id": "people/alice/drafts/route-clarity",
                "doc_kind": "draft",
                "event_id": "evt_2",
                "evidence_mode": "explicit",
                "observed_at": "2026-04-21T10:00:00+00:00",
                "retrieval_mode": "lookup",
                "reuse_outcome": "resolved",
                "schema_version": "reuse-v1",
                "task_id": "task-2",
            },
        ],
    )

    result = runner.invoke(
        app,
        ["consolidate", "queue", "--handle", "alice", "--format", "json", "--no-write"],
    )

    assert result.exit_code == 0
    report = json.loads(result.output)
    assert report["summary"]["queue_items"] == 1
    item = report["queue_items"][0]
    assert item["suggested_action"] == "Promotion candidate"
    assert item["suggested_target"] == "ai-wiki/features/route-clarity.md"
    assert "high_roi_memory" in item["weak_signals"][0]
    assert not (repo_wiki / "_toolkit" / "consolidation").exists()


def test_consolidate_queue_requires_initialized_repo_wiki(
    repo_env: dict[str, Path],
) -> None:
    result = runner.invoke(app, ["consolidate", "queue", "--handle", "alice"])

    assert result.exit_code == 1
    assert "Repo AI wiki is not initialized. Run `aiwiki-toolkit install` first." in result.output
