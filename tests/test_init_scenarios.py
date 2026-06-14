from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from ai_wiki_toolkit.cli import app
from ai_wiki_toolkit.content import (
    managed_repo_toolkit_files,
    PROMPT_BLOCK_END,
    PROMPT_BLOCK_START,
    prompt_block_body,
)
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
        ".env.aiwiki",
        ".git/",
        ".git/config",
        ".gitignore",
        "AGENTS.md",
        "ai-wiki/",
        "ai-wiki/_toolkit/",
        "ai-wiki/_toolkit/catalog.json",
        "ai-wiki/_toolkit/index.md",
        "ai-wiki/_toolkit/metrics/",
        "ai-wiki/_toolkit/metrics/by-handle/",
        "ai-wiki/_toolkit/metrics/by-handle/by/",
        "ai-wiki/_toolkit/metrics/by-handle/by/document-stats.json",
        "ai-wiki/_toolkit/metrics/by-handle/by/task-stats.json",
        "ai-wiki/_toolkit/metrics/document-stats.json",
        "ai-wiki/_toolkit/metrics/task-stats.json",
        "ai-wiki/_toolkit/schema/",
        "ai-wiki/_toolkit/schema/reuse-v1.md",
        "ai-wiki/_toolkit/schema/route-v1.md",
        "ai-wiki/_toolkit/schema/team-memory-v1.md",
        "ai-wiki/_toolkit/schema/work-v1.md",
        "ai-wiki/_toolkit/system.md",
        "ai-wiki/_toolkit/work/",
        "ai-wiki/_toolkit/work/report.md",
        "ai-wiki/_toolkit/work/state.json",
        "ai-wiki/_toolkit/workflows.md",
        "ai-wiki/constraints.md",
        "ai-wiki/conventions/",
        "ai-wiki/conventions/index.md",
        "ai-wiki/decisions.md",
        "ai-wiki/features/",
        "ai-wiki/features/index.md",
        "ai-wiki/index.md",
        "ai-wiki/memory/",
        "ai-wiki/memory/index.md",
        "ai-wiki/metrics/",
        "ai-wiki/metrics/index.md",
        "ai-wiki/metrics/reuse-events/",
        "ai-wiki/metrics/route-traces/",
        "ai-wiki/metrics/source-incidents/",
        "ai-wiki/metrics/task-checks/",
        "ai-wiki/metrics/taxonomy-evidence/",
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
        "ai-wiki/work/",
        "ai-wiki/work/events/",
        "ai-wiki/work/index.md",
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


def test_init_writes_expected_agents_snapshot(repo_env: dict[str, Path]) -> None:
    result = runner.invoke(app, ["init", "--handle", "alice"])

    assert result.exit_code == 0
    assert (repo_env["repo"] / "AGENTS.md").read_text(encoding="utf-8") == (
        f"{PROMPT_BLOCK_START}\n{prompt_block_body()}\n{PROMPT_BLOCK_END}\n"
    )


def test_init_writes_expected_repo_index_snapshot(repo_env: dict[str, Path]) -> None:
    result = runner.invoke(app, ["init", "--handle", "alice"])

    assert result.exit_code == 0
    assert (repo_env["repo"] / "ai-wiki" / "index.md").read_text(encoding="utf-8") == strip_margin(
        """
        # Project AI Wiki Index

        This is the user-owned entrypoint for project-specific AI wiki content.

        Use this file as a repo-owned map and overview.

        Package-managed start-of-task workflow guidance lives in `_toolkit/system.md` and may evolve without requiring this file to change.

        ## Areas

        - `_toolkit/system.md` carries the managed start-of-task workflow and bounded read rules.
        - `_toolkit/index.md` maps package-managed collaboration rules, baseline workflows, and schemas.
        - `constraints.md` maps hard constraints and non-negotiables.
        - `conventions/index.md` maps shared team conventions that coding agents should follow.
        - `decisions.md` maps durable project decisions and tradeoffs.
        - `review-patterns/index.md` maps reusable review rules and reviewer expectations.
        - `problems/index.md` maps reusable problem-solution memories.
        - `features/index.md` maps feature-specific working memory, clarified requirements, and accepted assumptions.
        - `memory/index.md` maps bounded public/local trial-error memories.
        - `workflows.md` maps repo-specific workflows that extend the managed baseline.
        - `trails/index.md` maps task-specific chronology, dead ends, and release trails.
        - `work/index.md` maps the append-only work ledger for todos, active tasks, and epics.
        - `people/<handle>/index.md` maps handle-local draft notes and working history.
        - `metrics/` contains user-owned evidence logs such as `reuse-events/<handle>.jsonl`, `route-traces/<handle>.jsonl`, `source-incidents/<handle>.jsonl`, `taxonomy-evidence/<handle>.jsonl`, and `task-checks/<handle>.jsonl`.
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
    assert (repo_env["repo"] / "ai-wiki" / "memory" / "index.md").read_text(encoding="utf-8") == strip_margin(
        """
        # Memory Index

        This folder contains bounded, public/local trial-error memory for future coding agents.

        ## Read Rule

        Read this index first, then open at most one linked memory file before acting.

        Open a memory file only when it strongly matches the current source file, API, command,
        behavior, or repeated public/local failure surface.

        Do not use hidden evaluator failures, hidden test names, private benchmark answers, or
        prior hidden-derived fixes as memory.

        ## Entries

        No public/local trial-error memory has been recorded yet.

        ## Suggested Entry Shape

        Each memory file should include:

        - Trigger
        - Public/Local Signal
        - Failed Attempt
        - Fix Or Rule
        - Applies When
        - Do Not Use When
        - Related Files
        - Source Pointer
        """
    )


def test_init_writes_expected_gitignore_snapshot(repo_env: dict[str, Path]) -> None:
    result = runner.invoke(app, ["init", "--handle", "alice"])

    assert result.exit_code == 0
    assert (repo_env["repo"] / ".gitignore").read_text(encoding="utf-8") == strip_margin(
        """
        # <!-- aiwiki-toolkit:start -->
        # Ignore AI wiki local state so normal agent use does not dirty git status.
        .env.aiwiki
        ai-wiki/metrics/reuse-events/
        ai-wiki/metrics/route-traces/
        ai-wiki/metrics/source-incidents/
        ai-wiki/metrics/taxonomy-evidence/
        ai-wiki/metrics/task-checks/
        ai-wiki/_toolkit/consolidation/
        ai-wiki/_toolkit/diagnostics/
        ai-wiki/_toolkit/metrics/
        ai-wiki/_toolkit/reports/
        ai-wiki/_toolkit/work/
        ai-wiki/_toolkit/catalog.json
        # <!-- aiwiki-toolkit:end -->
        """
    )
    assert (repo_env["repo"] / ".env.aiwiki").read_text(encoding="utf-8") == strip_margin(
        """
        # <!-- aiwiki-toolkit:start -->
        # Local aiwiki-toolkit identity. This file is ignored by git.
        AIWIKI_TOOLKIT_LOCAL_IDENTITY_VERSION=1
        AIWIKI_TOOLKIT_ACTOR_HANDLE=alice
        AIWIKI_TOOLKIT_IDENTITY_SOURCE=explicit-handle
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
        3. Read `schema/route-v1.md` when task-aware context packets or routing trust boundaries matter.
        4. Read `schema/work-v1.md` when work-ledger events, task lifecycle state, or generated work reports matter.
        5. Read `schema/team-memory-v1.md` when note shapes, memory types, or source pointers matter.
        6. Read `schema/reuse-v1.md` only when reuse metrics, logging, or schema questions matter.

        ## Generated Outputs

        - `catalog.json`, `consolidation/*`, `diagnostics/*`, `metrics/*`, `reports/*`, and `work/*` are generated outputs, not guidance docs.
        - `aiwiki-toolkit route` emits transient context packets to stdout; packets are derived from source docs and should be regenerated rather than treated as canonical memory.
        - The installer ignores local identity and generated outputs in `.gitignore` so routine agent use stays local.
        - Regenerate catalog, metrics, and work views with `aiwiki-toolkit refresh-metrics` whenever you need a fresh local snapshot.
        - Generate local memory quality diagnostics with `aiwiki-toolkit diagnose memory` when you need to inspect missed, stale, noisy, conflicting, or high-ROI memory.
        - Generate a local draft consolidation and promotion review queue with `aiwiki-toolkit consolidate queue`.
        - Keep generated diagnostics, reports, and per-handle metric views handle-scoped when they depend on a handle.
        - Mark useful reused drafts as handle-local promotion candidates with `aiwiki-toolkit promote candidates --apply`; exact reuse counts stay in `_toolkit/reports/promotion-candidates/<handle>/`, not in user-owned indexes.
        - Generate referenced-file and time-impact reports with `aiwiki-toolkit report usefulness`.
        - Generate weekly local HTML review queues with `aiwiki-toolkit report weekly --if-due`.
        """
    )
    managed_files = managed_repo_toolkit_files()
    assert (
        repo_env["repo"] / "ai-wiki" / "_toolkit" / "system.md"
    ).read_text(encoding="utf-8") == managed_files["system.md"]
    assert (
        repo_env["repo"] / "ai-wiki" / "_toolkit" / "workflows.md"
    ).read_text(encoding="utf-8") == managed_files["workflows.md"]
    assert (
        repo_env["repo"] / "ai-wiki" / "_toolkit" / "schema" / "route-v1.md"
    ).read_text(encoding="utf-8").startswith("# Route Schema v1")
    assert (
        repo_env["repo"] / "ai-wiki" / "_toolkit" / "schema" / "team-memory-v1.md"
    ).read_text(encoding="utf-8").startswith("# Team Memory Schema v1")
    assert (
        repo_env["repo"] / "ai-wiki" / "_toolkit" / "schema" / "work-v1.md"
    ).read_text(encoding="utf-8").startswith("# Work Ledger Schema v1")
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
    (repo_wiki / "work").mkdir(parents=True)
    (repo_wiki / "people" / "alice").mkdir(parents=True)
    (repo_wiki / "conventions" / "index.md").write_text("# Custom conventions index\n", encoding="utf-8")
    (repo_wiki / "features" / "index.md").write_text("# Custom features index\n", encoding="utf-8")
    (repo_wiki / "problems" / "index.md").write_text("# Custom problems index\n", encoding="utf-8")
    (repo_wiki / "review-patterns" / "index.md").write_text("# Custom review index\n", encoding="utf-8")
    (repo_wiki / "metrics" / "index.md").write_text("# Custom metrics index\n", encoding="utf-8")
    (repo_wiki / "work" / "index.md").write_text("# Custom work index\n", encoding="utf-8")
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
    assert (repo_wiki / "work" / "index.md").read_text(encoding="utf-8") == (
        "# Custom work index\n"
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
    assert '"doc_id": "work/index"' in catalog
    assert '"doc_id": "people/alice/index"' in catalog

    document_stats = (
        repo_env["repo"] / "ai-wiki" / "_toolkit" / "metrics" / "document-stats.json"
    ).read_text(encoding="utf-8")
    task_stats = (
        repo_env["repo"] / "ai-wiki" / "_toolkit" / "metrics" / "task-stats.json"
    ).read_text(encoding="utf-8")
    handle_document_stats = (
        repo_env["repo"]
        / "ai-wiki"
        / "_toolkit"
        / "metrics"
        / "by-handle"
        / "alice"
        / "document-stats.json"
    ).read_text(encoding="utf-8")
    handle_task_stats = (
        repo_env["repo"]
        / "ai-wiki"
        / "_toolkit"
        / "metrics"
        / "by-handle"
        / "alice"
        / "task-stats.json"
    ).read_text(encoding="utf-8")
    assert '"documents": {}' in document_stats
    assert '"checked_tasks": 0' in task_stats
    assert '"tasks": {}' in task_stats
    assert '"handle": "alice"' in handle_document_stats
    assert '"handle": "alice"' in handle_task_stats


def test_init_updates_managed_toolkit_files_on_rerun(repo_env: dict[str, Path]) -> None:
    result = runner.invoke(app, ["init", "--handle", "alice"])
    assert result.exit_code == 0

    managed_path = repo_env["repo"] / "ai-wiki" / "_toolkit" / "system.md"
    managed_path.write_text("# stale\n", encoding="utf-8")

    second = runner.invoke(app, ["init", "--handle", "alice"])

    assert second.exit_code == 0
    assert managed_path.read_text(encoding="utf-8").startswith("# Toolkit Managed System Rules")
    assert "Updated managed files: 1" in second.output
