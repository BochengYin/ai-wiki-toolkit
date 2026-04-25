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
        ".agents/skills/ai-wiki-capture-review-learning/",
        ".agents/skills/ai-wiki-capture-review-learning/SKILL.md",
        ".agents/skills/ai-wiki-capture-review-learning/agents/",
        ".agents/skills/ai-wiki-capture-review-learning/agents/openai.yaml",
        ".agents/skills/ai-wiki-capture-review-learning/references/",
        ".agents/skills/ai-wiki-capture-review-learning/references/classification.md",
        ".agents/skills/ai-wiki-capture-review-learning/references/conflict-check.md",
        ".agents/skills/ai-wiki-capture-review-learning/references/output-contract.md",
        ".agents/skills/ai-wiki-capture-review-learning/references/promotion-rules.md",
        ".agents/skills/ai-wiki-clarify-before-code/",
        ".agents/skills/ai-wiki-clarify-before-code/SKILL.md",
        ".agents/skills/ai-wiki-clarify-before-code/agents/",
        ".agents/skills/ai-wiki-clarify-before-code/agents/openai.yaml",
        ".agents/skills/ai-wiki-clarify-before-code/references/",
        ".agents/skills/ai-wiki-clarify-before-code/references/ambiguity-categories.md",
        ".agents/skills/ai-wiki-clarify-before-code/references/output-contract.md",
        ".agents/skills/ai-wiki-clarify-before-code/references/wiki-update-rules.md",
        ".agents/skills/ai-wiki-consolidate-drafts/",
        ".agents/skills/ai-wiki-consolidate-drafts/SKILL.md",
        ".agents/skills/ai-wiki-consolidate-drafts/agents/",
        ".agents/skills/ai-wiki-consolidate-drafts/agents/openai.yaml",
        ".agents/skills/ai-wiki-consolidate-drafts/references/",
        ".agents/skills/ai-wiki-consolidate-drafts/references/candidate-types.md",
        ".agents/skills/ai-wiki-consolidate-drafts/references/conflict-and-supersession.md",
        ".agents/skills/ai-wiki-consolidate-drafts/references/output-contract.md",
        ".agents/skills/ai-wiki-consolidate-drafts/references/promotion-targets.md",
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
        ".gitignore",
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
        "ai-wiki/_toolkit/schema/team-memory-v1.md",
        "ai-wiki/_toolkit/system.md",
        "ai-wiki/_toolkit/workflows.md",
        "ai-wiki/constraints.md",
        "ai-wiki/conventions/",
        "ai-wiki/conventions/index.md",
        "ai-wiki/decisions.md",
        "ai-wiki/features/",
        "ai-wiki/features/index.md",
        "ai-wiki/index.md",
        "ai-wiki/metrics/",
        "ai-wiki/metrics/index.md",
        "ai-wiki/metrics/reuse-events/",
        "ai-wiki/metrics/task-checks/",
        "ai-wiki/people/",
        "ai-wiki/people/by/",
        "ai-wiki/people/by/drafts/",
        "ai-wiki/people/by/index.md",
        "ai-wiki/problems/",
        "ai-wiki/problems/index.md",
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

        1. Read `ai-wiki/_toolkit/system.md`.
        2. Use `ai-wiki/index.md` as a repo-owned map when you need a quick overview of local AI wiki areas.
        3. If repo docs are not enough, read `<home>/ai-wiki/system/_toolkit/system.md` and then `<home>/ai-wiki/system/index.md`.
        4. Keep project-specific notes in `ai-wiki/`.
        5. Keep cross-project reusable notes in `<home>/ai-wiki/system/`.
        6. Only suggest promotion from a draft to a shared pattern or convention when the two-signal gate is satisfied.
        7. Agents may suggest promotion candidates, but humans confirm shared patterns and team conventions.
        8. If `ai-wiki-clarify-before-code` is available, use it before implementation when ambiguity materially affects coding.
        9. If `ai-wiki-capture-review-learning` is available, use it when reusable review feedback appears.
        10. If `ai-wiki-reuse-check` and `ai-wiki-update-check` skills are available, use them to produce the end-of-task AI wiki evidence footer and write-back outcome.

        ## End Of Task

        1. Produce one AI wiki reuse footer for every completed task.
        2. First classify the task as `relevant`, `optional`, or `not_relevant` for AI wiki use; pure operational tasks such as pushing a PR or running an already-decided command are `not_relevant`.
        3. If any user-owned AI wiki docs were consulted, record one `aiwiki-toolkit record-reuse` event per consulted doc.
        4. If a managed `_toolkit/**` doc materially changed the plan or behavior, cite its path in a progress update or final note, but do not log it with `record-reuse`.
        5. If a user-owned AI wiki doc materially changed the plan or behavior, cite its path in a progress update or final note.
        6. Record one `aiwiki-toolkit record-reuse-check` entry for the task using `wiki_used` or `no_wiki_use`.
        7. Produce one AI wiki write-back outcome for every completed task, even if the result is `None`.
        8. Before returning `None`, check for convention candidates, reusable PR review learning, feature clarification memory, durable decisions, problem-solution memory, missed relevant memory, conflict or supersession, or a person preference that should stay personal for now.
        9. Choose exactly one result: `None`, `Draft`, or `PromotionCandidate`.
        10. If the result is `Draft`, record the lesson under `ai-wiki/people/<handle>/drafts/` and print `AI Wiki Write-Back Path: <path>`.
        11. If the result is `PromotionCandidate`, mark or update the draft as a promotion candidate, print `AI Wiki Write-Back Path: <path>`, and ask for human confirmation before creating `ai-wiki/review-patterns/*.md` or `ai-wiki/conventions/*.md`.
        12. Always print exactly one final status line:
           - `AI Wiki Write-Back: none`
           - `AI Wiki Write-Back: draft recorded`
           - `AI Wiki Write-Back: promotion candidate`
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

        Use this file as a repo-owned map and overview.

        Package-managed start-of-task routing lives in `_toolkit/system.md` and may evolve without requiring this file to change.

        ## Areas

        - `_toolkit/system.md` carries the managed start-of-task workflow and evolving read order.
        - `_toolkit/index.md` maps package-managed collaboration rules, baseline workflows, and schemas.
        - `constraints.md` maps hard constraints and non-negotiables.
        - `conventions/index.md` maps shared team conventions that coding agents should follow.
        - `decisions.md` maps durable project decisions and tradeoffs.
        - `review-patterns/index.md` maps reusable review rules and reviewer expectations.
        - `problems/index.md` maps reusable problem-solution memories.
        - `features/index.md` maps feature-specific working memory, clarified requirements, and accepted assumptions.
        - `workflows.md` maps repo-specific workflows that extend the managed baseline.
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
    assert (repo_env["repo"] / "ai-wiki" / "constraints.md").read_text(encoding="utf-8") == strip_margin(
        """
        # Project Constraints

        This file is intentionally project-specific.

        Record hard repo boundaries and non-negotiable requirements here. If no constraints are
        listed yet, the team has not recorded any project-specific hard constraints.

        Good entries include security requirements, compatibility promises, release boundaries,
        data handling rules, or areas agents must not modify without approval.
        """
    )
    assert (repo_env["repo"] / "ai-wiki" / "decisions.md").read_text(encoding="utf-8") == strip_margin(
        """
        # Project Decisions

        This file is intentionally project-specific.

        Record durable architecture or process decisions here after the team has made them. If no
        decisions are listed yet, the team has not recorded any project-specific decisions.

        Good entries explain what was decided, why, what alternatives were rejected, and when the
        decision was made.
        """
    )


def test_init_writes_expected_gitignore_snapshot(repo_env: dict[str, Path]) -> None:
    result = runner.invoke(app, ["init", "--handle", "alice"])

    assert result.exit_code == 0
    assert (repo_env["repo"] / ".gitignore").read_text(encoding="utf-8") == strip_margin(
        """
        # <!-- aiwiki-toolkit:start -->
        # Ignore AI wiki telemetry so normal agent use does not dirty git status.
        ai-wiki/metrics/reuse-events/
        ai-wiki/metrics/task-checks/
        ai-wiki/_toolkit/metrics/
        ai-wiki/_toolkit/catalog.json
        # <!-- aiwiki-toolkit:end -->
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
        3. Read `schema/team-memory-v1.md` when note shapes, memory types, or source pointers matter.
        4. Read `schema/reuse-v1.md` only when reuse metrics, logging, or schema questions matter.

        ## Generated Outputs

        - `catalog.json` and `metrics/*.json` are generated outputs, not guidance docs.
        - The installer ignores those generated outputs in `.gitignore` so routine telemetry updates stay local.
        - Regenerate those outputs with `aiwiki-toolkit refresh-metrics` whenever you need a fresh local snapshot.
        """
    )
    assert (
        repo_env["repo"] / "ai-wiki" / "_toolkit" / "system.md"
    ).read_text(encoding="utf-8") == strip_margin(
        """
        # Toolkit Managed System Rules

        This file is managed by ai-wiki-toolkit. Future package versions may update it.

        ## Start Of Task

        1. Read `ai-wiki/constraints.md` for hard constraints and non-negotiables.
        2. Read `ai-wiki/conventions/index.md` for shared team conventions that should guide implementation.
        3. Read `ai-wiki/decisions.md` for durable project decisions and tradeoffs.
        4. Read `ai-wiki/review-patterns/index.md` for reusable review rules and reviewer expectations.
        5. Read `ai-wiki/problems/index.md` before implementing or testing similar behavior.
        6. Read `ai-wiki/features/index.md` when task-specific requirements, assumptions, or acceptance criteria matter.
        7. Read `ai-wiki/workflows.md` for repo-specific workflows that extend the managed baseline.
        8. Read `ai-wiki/trails/index.md` when debugging chronology or dead ends may help.
        9. Read `ai-wiki/people/<handle>/index.md` when continuing draft work.
        10. Read `ai-wiki/_toolkit/index.md` when you need package-managed schema, metrics, or directory guidance beyond this workflow.
        11. Use `ai-wiki/index.md` as a repo-owned map when you need a quick overview of local AI wiki areas.
        12. If repo docs are not enough, read `<home>/ai-wiki/system/_toolkit/system.md` and then `<home>/ai-wiki/system/index.md`.
        13. If `ai-wiki-clarify-before-code` is available, use it before implementation when ambiguity materially affects coding.
        14. If `ai-wiki-capture-review-learning` is available, use it when reusable review feedback appears.
        15. If `ai-wiki-reuse-check` and `ai-wiki-update-check` skills are available, use them to produce end-of-task AI wiki evidence and write-back outcomes.

        ## AI Wiki Reuse Evidence

        1. Produce one AI wiki reuse evidence footer at the end of every completed task.
        2. First classify the task as `relevant`, `optional`, or `not_relevant` for AI wiki use.
        3. Treat pure operational tasks such as pushing a PR, renaming a branch, or running an already-decided command as `not_relevant`; do not force unrelated wiki reads just to improve coverage metrics.
        4. If any user-owned repo or system AI wiki docs were consulted, record one `aiwiki-toolkit record-reuse` event per consulted document.
        5. If a managed `_toolkit/**` doc changed the plan or behavior, cite its path in a progress update or final note, but do not record it with `record-reuse`.
        6. When a user-owned AI wiki doc materially changes the plan or behavior, cite its path in a progress update or final note.
        7. Use `reuse_outcome=not_helpful` when a consulted user-owned AI wiki document did not help materially but still influenced the search path.
        8. Record one `aiwiki-toolkit record-reuse-check` entry for the task with:
           - `wiki_used` when one or more AI wiki document events were recorded
           - `no_wiki_use` when no AI wiki document events were needed for the task

        ## AI Wiki Write-Back Outcome

        1. Produce one AI wiki write-back outcome at the end of every completed task, even when you expect the result to be `None`.
        2. Before returning `None`, run memory candidate detection for:
           - a new or refined team convention
           - reusable PR review learning
           - feature clarification memory
           - a durable decision note
           - a reusable problem-solution memory
           - missed relevant memory
           - a conflict, refinement, or supersession with existing memory
           - a person preference that should stay personal for now
        3. Use concrete task signals before returning `None`, especially:
           - repeated release, CI, or platform failure
           - workflow, packaging, or environment assumption mismatch
           - tooling fixes future agents may need again
           - multi-turn requirement clarification or accepted implementation assumptions
           - acceptance criteria or unresolved feature questions that emerged during the task
        4. Choose exactly one outcome:
           - `None`: you checked and found no durable lesson worth recording.
           - `Draft`: you found a durable lesson, recorded it under `ai-wiki/people/<handle>/drafts/`, and it is not yet ready for shared promotion.
           - `PromotionCandidate`: you recorded or updated a draft, the two-signal gate is satisfied, and human confirmation is still required before creating `ai-wiki/review-patterns/*.md` or `ai-wiki/conventions/*.md`.
        5. Prefer small durable memory over long task transcripts or generic summaries.
        6. If new memory conflicts with existing conventions, decisions, features, problems, or person preferences, flag it as a conflict, refinement, or supersession instead of silently overwriting.
        7. If a relevant existing AI wiki doc should have been used but was missed, treat that as missed relevant memory instead of silently returning `None`.
        8. Always print exactly one final status line:
           - `AI Wiki Write-Back: none`
           - `AI Wiki Write-Back: draft recorded`
           - `AI Wiki Write-Back: promotion candidate`
        9. If the outcome is `Draft` or `PromotionCandidate`, also print:
           - `AI Wiki Write-Back Path: <path>`

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

        ## Team Memory Placement

        1. Put shared team rules in `ai-wiki/conventions/`.
        2. Put reusable problem-solution memories in `ai-wiki/problems/`.
        3. Put feature-specific clarifications in `ai-wiki/features/`.
        4. Keep reviewer-specific or person-specific preferences under `ai-wiki/people/<handle>/` until they are clearly team-wide.

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

        1. Produce one AI wiki reuse evidence footer at the end of every completed task.
        2. First classify the task as `relevant`, `optional`, or `not_relevant` for AI wiki use.
        3. Record one `aiwiki-toolkit record-reuse` event per consulted user-owned AI wiki doc.
        4. Do not log managed `_toolkit/**` docs with `record-reuse`; if they changed the plan or behavior, cite their paths in a progress update or the final note instead.
        5. Record one `aiwiki-toolkit record-reuse-check` entry for the task using `wiki_used` or `no_wiki_use`.
        6. Treat the footer as the user-facing evidence surface; telemetry and generated aggregates are the local machine-readable record behind it.
        7. The installer manages a `.gitignore` block that ignores `ai-wiki/metrics/reuse-events/`, `ai-wiki/metrics/task-checks/`, `ai-wiki/_toolkit/metrics/`, and `ai-wiki/_toolkit/catalog.json` so telemetry stays local by default.
        8. If those telemetry paths were tracked before you upgraded, run `aiwiki-toolkit doctor` and follow the suggested `git rm --cached` fix once to untrack them.
        9. Produce one AI wiki write-back outcome at the end of every completed task, even when the result is `None`.
        10. Before returning `None`, run memory candidate detection for problem-solution memory, feature clarification memory, convention candidates, missed relevant memory, and conflict or supersession.
        11. Always end with exactly one status line: `AI Wiki Write-Back: none`, `draft recorded`, or `promotion candidate`.
        12. If the result is `Draft` or `PromotionCandidate`, also print `AI Wiki Write-Back Path: <path>`.
        13. Do not write every task summary into the wiki; capture only durable memory.
        14. Put shared team conventions in `ai-wiki/conventions/`.
        15. Put reusable repo-specific review lessons in `ai-wiki/review-patterns/`.
        16. Put reusable problem-solution memories in `ai-wiki/problems/`.
        17. Put feature clarifications in `ai-wiki/features/`.
        18. Put task-specific chronology and dead ends in `ai-wiki/trails/`.
        19. Put raw personal draft notes in `ai-wiki/people/<handle>/drafts/`.
        20. Promote only stable, reviewable rules into shared patterns or conventions.
        """
    )
    assert (
        repo_env["repo"] / "ai-wiki" / "_toolkit" / "schema" / "team-memory-v1.md"
    ).read_text(encoding="utf-8").startswith("# Team Memory Schema v1")
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
    (repo_wiki / "conventions").mkdir(parents=True)
    (repo_wiki / "features").mkdir(parents=True)
    (repo_wiki / "problems").mkdir(parents=True)
    (repo_wiki / "review-patterns").mkdir(parents=True)
    (repo_wiki / "metrics").mkdir(parents=True)
    (repo_wiki / "people" / "alice").mkdir(parents=True)
    (repo_wiki / "conventions" / "index.md").write_text("# Custom conventions index\n", encoding="utf-8")
    (repo_wiki / "features" / "index.md").write_text("# Custom features index\n", encoding="utf-8")
    (repo_wiki / "problems" / "index.md").write_text("# Custom problems index\n", encoding="utf-8")
    (repo_wiki / "review-patterns" / "index.md").write_text("# Custom review index\n", encoding="utf-8")
    (repo_wiki / "metrics" / "index.md").write_text("# Custom metrics index\n", encoding="utf-8")
    (repo_wiki / "people" / "alice" / "index.md").write_text("# Custom person index\n", encoding="utf-8")

    result = runner.invoke(app, ["init", "--handle", "alice"])

    assert result.exit_code == 0
    assert (repo_wiki / "conventions" / "index.md").read_text(encoding="utf-8") == (
        "# Custom conventions index\n"
    )
    assert (repo_wiki / "features" / "index.md").read_text(encoding="utf-8") == (
        "# Custom features index\n"
    )
    assert (repo_wiki / "problems" / "index.md").read_text(encoding="utf-8") == (
        "# Custom problems index\n"
    )
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
    assert '"doc_id": "conventions/index"' in catalog
    assert '"doc_id": "problems/index"' in catalog
    assert '"doc_id": "features/index"' in catalog
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
