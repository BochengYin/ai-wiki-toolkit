from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from ai_wiki_toolkit.cli import app
from helpers import snapshot_tree, strip_margin, write_git_config

runner = CliRunner()


def test_init_empty_repo_creates_expected_tree(repo_env: dict[str, Path]) -> None:
    result = runner.invoke(app, ["init", "--handle", "By"])

    assert result.exit_code == 0
    assert snapshot_tree(repo_env["repo"]) == [
        ".agents/",
        ".agents/skills/",
        ".agents/skills/ai-wiki-reuse-check/",
        ".agents/skills/ai-wiki-reuse-check/SKILL.md",
        ".agents/skills/ai-wiki-reuse-check/agents/",
        ".agents/skills/ai-wiki-reuse-check/agents/openai.yaml",
        ".agents/skills/ai-wiki-reuse-check/references/",
        ".agents/skills/ai-wiki-reuse-check/references/decision-rules.md",
        ".agents/skills/ai-wiki-reuse-check/references/output-contract.md",
        ".agents/skills/ai-wiki-update-check/",
        ".agents/skills/ai-wiki-update-check/SKILL.md",
        ".agents/skills/ai-wiki-update-check/agents/",
        ".agents/skills/ai-wiki-update-check/agents/openai.yaml",
        ".agents/skills/ai-wiki-update-check/references/",
        ".agents/skills/ai-wiki-update-check/references/decision-rules.md",
        ".agents/skills/ai-wiki-update-check/references/output-contract.md",
        ".git/",
        ".git/config",
        "AGENT.md",
        "ai-wiki/",
        "ai-wiki/_toolkit/",
        "ai-wiki/_toolkit/catalog.json",
        "ai-wiki/_toolkit/index.md",
        "ai-wiki/_toolkit/metrics/",
        "ai-wiki/_toolkit/metrics/document-stats.json",
        "ai-wiki/_toolkit/metrics/task-stats.json",
        "ai-wiki/_toolkit/schema/",
        "ai-wiki/_toolkit/schema/reuse-v1.md",
        "ai-wiki/_toolkit/system.md",
        "ai-wiki/_toolkit/workflows.md",
        "ai-wiki/constraints.md",
        "ai-wiki/decisions.md",
        "ai-wiki/index.md",
        "ai-wiki/metrics/",
        "ai-wiki/metrics/index.md",
        "ai-wiki/metrics/reuse-events/",
        "ai-wiki/metrics/task-checks/",
        "ai-wiki/people/",
        "ai-wiki/people/by/",
        "ai-wiki/people/by/drafts/",
        "ai-wiki/people/by/index.md",
        "ai-wiki/review-patterns/",
        "ai-wiki/review-patterns/index.md",
        "ai-wiki/trails/",
        "ai-wiki/trails/index.md",
        "ai-wiki/workflows.md",
    ]
    assert snapshot_tree(repo_env["home_dir"]) == [
        "system/",
        "system/_toolkit/",
        "system/_toolkit/system.md",
        "system/index.md",
        "system/playbooks/",
        "system/preferences.md",
        "system/templates/",
    ]


def test_init_writes_expected_agent_snapshot(repo_env: dict[str, Path]) -> None:
    result = runner.invoke(app, ["init", "--handle", "alice"])

    assert result.exit_code == 0
    assert (repo_env["repo"] / "AGENT.md").read_text(encoding="utf-8") == strip_margin(
        """
        <!-- aiwiki-toolkit:start -->
        ## AI Wiki Toolkit

        Before starting work:

        1. Read `ai-wiki/_toolkit/index.md`.
        2. Read `ai-wiki/index.md`.
        3. Read `ai-wiki/review-patterns/index.md` before implementation or review work.
        4. Read your own folder index under `ai-wiki/people/<handle>/index.md` when continuing draft notes.
        5. If repo docs are not enough, read `<home>/ai-wiki/system/_toolkit/system.md` and then `<home>/ai-wiki/system/index.md`.
        6. Keep project-specific notes in `ai-wiki/`.
        7. Keep cross-project reusable notes in `<home>/ai-wiki/system/`.
        8. Only suggest promotion from a draft to a shared pattern when the two-signal gate is satisfied.
        9. Agents may suggest promotion candidates, but humans confirm shared patterns.
        10. If `ai-wiki-reuse-check` and `ai-wiki-update-check` skills are available, use them for the end-of-task AI wiki checks.

        ## End Of Task

        1. Run one AI wiki reuse check for every completed task, even if no AI wiki docs were used.
        2. If any user-owned AI wiki docs were consulted, record one `aiwiki-toolkit record-reuse` event per consulted doc.
        3. If a managed `_toolkit/**` doc materially changed the plan or behavior, cite its path in a progress update or final note, but do not log it with `record-reuse`.
        4. If a user-owned AI wiki doc materially changed the plan or behavior, cite its path in a progress update or final note.
        5. Record one `aiwiki-toolkit record-reuse-check` entry for the task using `wiki_used` or `no_wiki_use`.
        6. Run one AI wiki update check for every completed task, even if the result is `None`.
        7. Choose exactly one result: `None`, `Draft`, or `PromotionCandidate`.
        8. If the result is `Draft`, record the lesson under `ai-wiki/people/<handle>/drafts/` and print `AI Wiki Update Path: <path>`.
        9. If the result is `PromotionCandidate`, mark or update the draft as a promotion candidate, print `AI Wiki Update Path: <path>`, and ask for human confirmation before creating `ai-wiki/review-patterns/*.md`.
        10. Always print exactly one final status line:
           - `AI Wiki Update Candidate: None`
           - `AI Wiki Update Candidate: Draft`
           - `AI Wiki Update Candidate: PromotionCandidate`
        <!-- aiwiki-toolkit:end -->
        """
    )


def test_init_writes_expected_repo_index_snapshot(repo_env: dict[str, Path]) -> None:
    result = runner.invoke(app, ["init", "--handle", "alice"])

    assert result.exit_code == 0
    assert (repo_env["repo"] / "ai-wiki" / "index.md").read_text(encoding="utf-8") == strip_margin(
        """
        # Project AI Wiki Index

        This is the user-owned entrypoint for project-specific AI wiki content.

        ## Read Order

        1. Read `_toolkit/index.md` for package-managed collaboration rules and baseline workflows.
        2. Read `constraints.md` for hard constraints and non-negotiables.
        3. Read `workflows.md` for repo-specific workflows that extend the managed baseline.
        4. Read `decisions.md` for durable project decisions and tradeoffs.
        5. Read `review-patterns/index.md` before individual review patterns.
        6. Read `trails/index.md` when task-specific chronology or dead ends may help.
        7. Read `people/<handle>/index.md` when continuing or recording personal draft notes.

        ## Areas

        - `_toolkit/index.md` maps package-managed collaboration rules, baseline workflows, and schemas.
        - `review-patterns/index.md` maps shared, reusable review rules.
        - `trails/index.md` maps task-specific chronology, dead ends, and release trails.
        - `people/<handle>/index.md` maps handle-local draft notes and working history.
        - `metrics/` contains user-owned evidence logs such as `reuse-events/<handle>.jsonl` and `task-checks/<handle>.jsonl`.
        """
    )
    assert (repo_env["repo"] / "ai-wiki" / "workflows.md").read_text(encoding="utf-8") == strip_margin(
        """
        # Project Workflows

        Capture repeatable repo-specific workflows here.

        See also `_toolkit/workflows.md` for package-managed baseline workflows that ship with `ai-wiki-toolkit`.
        """
    )


def test_init_writes_expected_toolkit_managed_files(repo_env: dict[str, Path]) -> None:
    result = runner.invoke(app, ["init", "--handle", "alice"])

    assert result.exit_code == 0
    assert (
        repo_env["repo"] / "ai-wiki" / "_toolkit" / "index.md"
    ).read_text(encoding="utf-8") == strip_margin(
        """
        # Toolkit Managed Index

        This directory is managed by ai-wiki-toolkit. Future package versions may update it.

        ## Read Order

        1. Read `system.md` for package-managed collaboration rules.
        2. Read `workflows.md` for package-managed baseline workflows.
        3. Read `schema/reuse-v1.md` only when reuse metrics, logging, or schema questions matter.

        ## Generated Outputs

        - `catalog.json` and `metrics/*.json` are generated outputs, not guidance docs.
        - Regenerate those outputs with `aiwiki-toolkit refresh-metrics` instead of hand-merging them.
        """
    )
    assert (
        repo_env["repo"] / "ai-wiki" / "_toolkit" / "system.md"
    ).read_text(encoding="utf-8") == strip_margin(
        """
        # Toolkit Managed System Rules

        This file is managed by ai-wiki-toolkit. Future package versions may update it.

        ## Start Of Task

        1. Read `ai-wiki/_toolkit/index.md`.
        2. Read `ai-wiki/index.md`.
        3. Read `ai-wiki/review-patterns/index.md` before implementation or review work.
        4. Read `ai-wiki/people/<handle>/index.md` when continuing draft work.
        5. If repo docs are not enough, read `<home>/ai-wiki/system/_toolkit/system.md` and then `<home>/ai-wiki/system/index.md`.
        6. If `ai-wiki-reuse-check` and `ai-wiki-update-check` skills are available, use them for end-of-task AI wiki checks.

        ## AI Wiki Reuse Check

        1. Run one AI wiki reuse check at the end of every completed task, even when no wiki docs were used.
        2. If any user-owned repo or system AI wiki docs were consulted, record one `aiwiki-toolkit record-reuse` event per consulted document.
        3. If a managed `_toolkit/**` doc changed the plan or behavior, cite its path in a progress update or final note, but do not record it with `record-reuse`.
        4. When a user-owned AI wiki doc materially changes the plan or behavior, cite its path in a progress update or final note.
        5. Use `reuse_outcome=not_helpful` when a consulted user-owned AI wiki document did not help materially but still influenced the search path.
        6. Record one `aiwiki-toolkit record-reuse-check` entry for the task with:
           - `wiki_used` when one or more AI wiki document events were recorded
           - `no_wiki_use` when no AI wiki document events were needed for the task

        ## AI Wiki Update Check

        1. Run one AI wiki update check at the end of every completed task, even when you expect the result to be `None`.
        2. Choose exactly one outcome:
           - `None`: you checked and found no durable lesson worth recording.
           - `Draft`: you found a durable lesson, recorded it under `ai-wiki/people/<handle>/drafts/`, and it is not yet ready for shared promotion.
           - `PromotionCandidate`: you recorded or updated a draft, the two-signal gate is satisfied, and human confirmation is still required before creating `ai-wiki/review-patterns/*.md`.
        3. Always print exactly one final status line:
           - `AI Wiki Update Candidate: None`
           - `AI Wiki Update Candidate: Draft`
           - `AI Wiki Update Candidate: PromotionCandidate`
        4. If the outcome is `Draft` or `PromotionCandidate`, also print:
           - `AI Wiki Update Path: <path>`

        ## Review Draft Workflow

        1. Record new review findings in `ai-wiki/people/<handle>/drafts/`.
        2. A draft becomes a promotion candidate only when either:
           - the same issue has been observed at least twice
           - a reviewer judges it reusable and can write a stable rule
        3. Agents may mark a draft as a promotion candidate, but shared patterns require human confirmation.

        ## Shared Pattern Workflow

        1. Put reusable review rules in `ai-wiki/review-patterns/`.
        2. Shared patterns must use the standard sections:
           - `Problem Pattern`
           - `Why It Happens`
           - `Bad Example`
           - `Preferred Pattern`
           - `Review Checklist`
        3. Each shared pattern should point back to its source draft via `derived_from`.

        ## Structured Note Metadata

        Review drafts and shared patterns use YAML frontmatter with:

        - `title`
        - `author_handle`
        - `model`
        - `source_kind`
        - `status`
        - `created_at`
        - `updated_at`

        Review drafts also include:

        - `promotion_candidate`
        - `promotion_basis`

        Shared patterns also include:

        - `derived_from`
        """
    )
    assert (
        repo_env["repo"] / "ai-wiki" / "_toolkit" / "workflows.md"
    ).read_text(encoding="utf-8") == strip_margin(
        """
        # Toolkit Managed Workflows

        This file is managed by ai-wiki-toolkit. Future package versions may update it.

        ## AI Wiki Maintenance

        1. Run one AI wiki reuse check at the end of every completed task, even when no AI wiki docs were used.
        2. If any user-owned repo or system AI wiki docs were consulted, record one `aiwiki-toolkit record-reuse` event per consulted doc.
        3. Do not log managed `_toolkit/**` docs with `record-reuse`; if they changed the plan or behavior, cite their paths in a progress update or the final note instead.
        4. Record one `aiwiki-toolkit record-reuse-check` entry for the task using `wiki_used` or `no_wiki_use`.
        5. Metrics logs should shard by handle under `ai-wiki/metrics/reuse-events/<handle>.jsonl` and `ai-wiki/metrics/task-checks/<handle>.jsonl` to reduce merge conflicts in team workflows.
        6. If generated files under `ai-wiki/_toolkit/catalog.json` or `ai-wiki/_toolkit/metrics/*.json` drift or conflict after a merge, rerun `aiwiki-toolkit refresh-metrics` instead of hand-merging them.
        7. Run one AI wiki update check at the end of every completed task, even when the result is `None`.
        8. Always end with exactly one status line: `AI Wiki Update Candidate: None`, `Draft`, or `PromotionCandidate`.
        9. If the result is `Draft` or `PromotionCandidate`, also print `AI Wiki Update Path: <path>`.
        10. Put reusable repo-specific lessons in `ai-wiki/review-patterns/`.
        11. Put task-specific chronology and dead ends in `ai-wiki/trails/`.
        12. Put raw personal draft notes in `ai-wiki/people/<handle>/drafts/`.
        13. Promote only stable, reviewable rules into shared patterns.
        """
    )
    assert (
        repo_env["home_dir"] / "system" / "_toolkit" / "system.md"
    ).read_text(encoding="utf-8") == strip_margin(
        """
        # Toolkit Managed Cross-Project Rules

        This file is managed by ai-wiki-toolkit. Future package versions may update it.

        ## Cross-Project Usage

        1. Keep reusable debugging, review, and workflow guidance under `<home>/ai-wiki/system/`.
        2. Keep package-managed rules under `<home>/ai-wiki/system/_toolkit/`.
        3. Keep user-owned preferences, playbooks, and templates outside `_toolkit/`.

        ## Review Pattern Reuse

        - Only move knowledge here when it is clearly reusable beyond a single repository.
        - Prefer repo-local `review-patterns/` for team-specific coding and review rules.
        - Promote stable cross-project abstractions here only after they have been validated in real work.
        """
    )


def test_init_creates_handle_specific_draft_dir_from_cli_override(
    repo_env: dict[str, Path],
) -> None:
    result = runner.invoke(app, ["init", "--handle", "Lead Reviewer"])
    assert result.exit_code == 0
    assert (repo_env["repo"] / "ai-wiki" / "people" / "lead-reviewer" / "drafts").is_dir()
    assert "Resolved handle: lead-reviewer" in result.output


def test_init_creates_handle_specific_draft_dir_from_env(
    repo_env: dict[str, Path], monkeypatch
) -> None:
    monkeypatch.setenv("AIWIKI_TOOLKIT_HANDLE", "Env User")
    result = runner.invoke(app, ["init"])
    assert result.exit_code == 0
    assert (repo_env["repo"] / "ai-wiki" / "people" / "env-user" / "drafts").is_dir()


def test_init_creates_handle_specific_draft_dir_from_git_config(
    repo_env: dict[str, Path],
) -> None:
    write_git_config(
        repo_env["repo"],
        email="162966873+BochengYin@users.noreply.github.com",
        name="Bocheng Yin",
    )
    result = runner.invoke(app, ["init"])
    assert result.exit_code == 0
    assert (repo_env["repo"] / "ai-wiki" / "people" / "bochengyin" / "drafts").is_dir()


def test_init_does_not_overwrite_existing_user_docs(repo_env: dict[str, Path]) -> None:
    repo_wiki = repo_env["repo"] / "ai-wiki"
    repo_wiki.mkdir()
    (repo_wiki / "index.md").write_text("# Custom index\n", encoding="utf-8")
    (repo_wiki / "constraints.md").write_text("# Custom constraints\n", encoding="utf-8")

    result = runner.invoke(app, ["init", "--handle", "alice"])

    assert result.exit_code == 0
    assert (repo_wiki / "index.md").read_text(encoding="utf-8") == "# Custom index\n"
    assert (repo_wiki / "constraints.md").read_text(encoding="utf-8") == "# Custom constraints\n"


def test_init_does_not_overwrite_existing_user_owned_indexes(repo_env: dict[str, Path]) -> None:
    repo_wiki = repo_env["repo"] / "ai-wiki"
    (repo_wiki / "review-patterns").mkdir(parents=True)
    (repo_wiki / "metrics").mkdir(parents=True)
    (repo_wiki / "people" / "alice").mkdir(parents=True)
    (repo_wiki / "review-patterns" / "index.md").write_text("# Custom review index\n", encoding="utf-8")
    (repo_wiki / "metrics" / "index.md").write_text("# Custom metrics index\n", encoding="utf-8")
    (repo_wiki / "people" / "alice" / "index.md").write_text("# Custom person index\n", encoding="utf-8")

    result = runner.invoke(app, ["init", "--handle", "alice"])

    assert result.exit_code == 0
    assert (repo_wiki / "review-patterns" / "index.md").read_text(encoding="utf-8") == (
        "# Custom review index\n"
    )
    assert (repo_wiki / "metrics" / "index.md").read_text(encoding="utf-8") == (
        "# Custom metrics index\n"
    )
    assert (repo_wiki / "people" / "alice" / "index.md").read_text(encoding="utf-8") == (
        "# Custom person index\n"
    )


def test_init_writes_catalog_and_empty_stats(repo_env: dict[str, Path]) -> None:
    result = runner.invoke(app, ["init", "--handle", "alice"])

    assert result.exit_code == 0
    catalog = (repo_env["repo"] / "ai-wiki" / "_toolkit" / "catalog.json").read_text(encoding="utf-8")
    assert '"schema_version": "reuse-v1"' in catalog
    assert '"doc_id": "review-patterns/index"' in catalog
    assert '"doc_id": "people/alice/index"' in catalog

    document_stats = (
        repo_env["repo"] / "ai-wiki" / "_toolkit" / "metrics" / "document-stats.json"
    ).read_text(encoding="utf-8")
    task_stats = (
        repo_env["repo"] / "ai-wiki" / "_toolkit" / "metrics" / "task-stats.json"
    ).read_text(encoding="utf-8")
    assert '"documents": {}' in document_stats
    assert '"checked_tasks": 0' in task_stats
    assert '"tasks": {}' in task_stats


def test_init_updates_managed_toolkit_files_on_rerun(repo_env: dict[str, Path]) -> None:
    result = runner.invoke(app, ["init", "--handle", "alice"])
    assert result.exit_code == 0

    managed_path = repo_env["repo"] / "ai-wiki" / "_toolkit" / "system.md"
    managed_path.write_text("# stale\n", encoding="utf-8")

    second = runner.invoke(app, ["init", "--handle", "alice"])

    assert second.exit_code == 0
    assert managed_path.read_text(encoding="utf-8").startswith("# Toolkit Managed System Rules")
    assert "Updated managed files: 1" in second.output
