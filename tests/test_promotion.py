from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from ai_wiki_toolkit.cli import app
from ai_wiki_toolkit.frontmatter import parse_frontmatter

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


def _event(doc_id: str, suffix: str, *, outcome: str = "resolved") -> dict[str, object]:
    return {
        "author_handle": "alice",
        "doc_id": doc_id,
        "doc_kind": "draft",
        "estimated_savings": {"saved_seconds": 60, "saved_tokens": 1000},
        "event_id": f"evt_{doc_id.rsplit('/', maxsplit=1)[-1]}_{suffix}",
        "evidence_mode": "explicit",
        "observed_at": f"2026-04-2{suffix}T10:00:00+00:00",
        "retrieval_mode": "lookup",
        "reuse_outcome": outcome,
        "schema_version": "reuse-v1",
        "task_id": f"task-{suffix}",
    }


def test_promote_candidates_apply_marks_only_clean_useful_reuse(
    repo_env: dict[str, Path],
) -> None:
    install_result = runner.invoke(app, ["install", "--handle", "alice"])
    assert install_result.exit_code == 0

    repo_wiki = repo_env["repo"] / "ai-wiki"
    drafts = repo_wiki / "people" / "alice" / "drafts"
    _write_doc(
        drafts / "clean-draft.md",
        "---\n"
        'title: "Clean Draft"\n'
        'status: "draft"\n'
        "promotion_candidate: false\n"
        'promotion_basis: "none"\n'
        "---\n"
        "# Clean Draft\n",
    )
    _write_doc(
        drafts / "mixed-draft.md",
        "---\n"
        'title: "Mixed Draft"\n'
        'status: "draft"\n'
        "promotion_candidate: false\n"
        "---\n"
        "# Mixed Draft\n",
    )
    _write_doc(
        drafts / "already-marked.md",
        "---\n"
        'title: "Already Marked"\n'
        'status: "draft"\n'
        "promotion_candidate: true\n"
        'promotion_basis: "Auto-marked from reuse log: 4 resolved useful reuses across 4 distinct tasks (>3); no not_helpful events."\n'
        "---\n"
        "# Already Marked\n",
    )

    rows: list[dict[str, object]] = []
    for suffix in ("1", "2", "3", "4"):
        rows.append(_event("people/alice/drafts/clean-draft", suffix))
        rows.append(_event("people/alice/drafts/mixed-draft", suffix))
        rows.append(_event("people/alice/drafts/already-marked", suffix))
        rows.append(_event("people/alice/drafts/missing-draft", suffix))
    rows.append(_event("people/alice/drafts/mixed-draft", "5", outcome="not_helpful"))
    _write_jsonl(repo_wiki / "metrics" / "reuse-events" / "alice.jsonl", rows)

    result = runner.invoke(
        app,
        ["promote", "candidates", "--handle", "alice", "--apply", "--format", "json"],
    )

    assert result.exit_code == 0
    report = json.loads(result.output)
    assert report["schema_version"] == "promotion-candidates-v1"
    assert report["summary"]["new_candidates"] == 1
    assert report["new_candidates"][0]["doc_id"] == "people/alice/drafts/clean-draft"
    assert report["apply"]["drafts_marked"] == 1
    assert report["apply"]["index_updated"] is True

    clean_metadata, _ = parse_frontmatter((drafts / "clean-draft.md").read_text(encoding="utf-8"))
    assert clean_metadata["promotion_candidate"] is True
    assert clean_metadata["promotion_basis"].startswith("Auto-marked from useful resolved reuse threshold")
    assert "4 resolved" not in clean_metadata["promotion_basis"]

    mixed_metadata, _ = parse_frontmatter((drafts / "mixed-draft.md").read_text(encoding="utf-8"))
    assert mixed_metadata["promotion_candidate"] is False

    already_metadata, _ = parse_frontmatter(
        (drafts / "already-marked.md").read_text(encoding="utf-8")
    )
    assert already_metadata["promotion_basis"].startswith(
        "Auto-marked from useful resolved reuse threshold"
    )
    assert "4 resolved" not in already_metadata["promotion_basis"]

    index_text = (repo_wiki / "people" / "alice" / "index.md").read_text(encoding="utf-8")
    assert "## Promotion Candidates" in index_text
    assert "- [Already Marked](drafts/already-marked.md)" in index_text
    assert "- [Clean Draft](drafts/clean-draft.md)" in index_text
    assert "resolved tasks" not in index_text
    assert "4 resolved" not in index_text

    markdown_path = (
        repo_wiki / "_toolkit" / "reports" / "promotion-candidates" / "alice" / "latest.md"
    )
    json_path = (
        repo_wiki / "_toolkit" / "reports" / "promotion-candidates" / "alice" / "latest.json"
    )
    assert markdown_path.exists()
    assert json.loads(json_path.read_text(encoding="utf-8"))["summary"]["new_candidates"] == 1
    assert "4 resolved tasks" in markdown_path.read_text(encoding="utf-8")


def test_promote_candidates_no_apply_no_write_does_not_edit_user_docs(
    repo_env: dict[str, Path],
) -> None:
    install_result = runner.invoke(app, ["install", "--handle", "alice"])
    assert install_result.exit_code == 0

    repo_wiki = repo_env["repo"] / "ai-wiki"
    draft = repo_wiki / "people" / "alice" / "drafts" / "clean-draft.md"
    _write_doc(
        draft,
        "---\n"
        'title: "Clean Draft"\n'
        'status: "draft"\n'
        "promotion_candidate: false\n"
        "---\n"
        "# Clean Draft\n",
    )
    _write_jsonl(
        repo_wiki / "metrics" / "reuse-events" / "alice.jsonl",
        [_event("people/alice/drafts/clean-draft", suffix) for suffix in ("1", "2", "3", "4")],
    )
    before_draft = draft.read_text(encoding="utf-8")
    index_path = repo_wiki / "people" / "alice" / "index.md"
    before_index = index_path.read_text(encoding="utf-8")

    result = runner.invoke(
        app,
        [
            "promote",
            "candidates",
            "--handle",
            "alice",
            "--no-apply",
            "--no-write",
            "--format",
            "json",
        ],
    )

    assert result.exit_code == 0
    report = json.loads(result.output)
    assert report["summary"]["new_candidates"] == 1
    assert draft.read_text(encoding="utf-8") == before_draft
    assert index_path.read_text(encoding="utf-8") == before_index
    assert not (repo_wiki / "_toolkit" / "reports").exists()


def test_promote_candidates_requires_initialized_repo_wiki(
    repo_env: dict[str, Path],
) -> None:
    result = runner.invoke(app, ["promote", "candidates", "--handle", "alice"])

    assert result.exit_code == 1
    assert "Repo AI wiki is not initialized. Run `aiwiki-toolkit install` first." in result.output
