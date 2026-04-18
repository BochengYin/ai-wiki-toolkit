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
        "ai-wiki/_toolkit/system.md",
        "ai-wiki/constraints.md",
        "ai-wiki/decisions.md",
        "ai-wiki/index.md",
        "ai-wiki/people/",
        "ai-wiki/people/by/",
        "ai-wiki/people/by/drafts/",
        "ai-wiki/review-patterns/",
        "ai-wiki/trails/",
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
        2. Read `ai-wiki/index.md`.
        3. Read `ai-wiki/review-patterns/` before implementation or review work.
        4. Read your own folder under `ai-wiki/people/<handle>/drafts/` when continuing draft notes.
        5. If repo docs are not enough, read `<home>/ai-wiki/system/_toolkit/system.md` and then `<home>/ai-wiki/system/index.md`.
        6. Keep project-specific notes in `ai-wiki/`.
        7. Keep cross-project reusable notes in `<home>/ai-wiki/system/`.
        8. Only suggest promotion from a draft to a shared pattern when the two-signal gate is satisfied.
        9. Agents may suggest promotion candidates, but humans confirm shared patterns.
        10. If an `ai-wiki-update-check` skill is available, use it for the end-of-task AI wiki update check.

        ## End Of Task

        1. Run one AI wiki update check for every completed task, even if the result is `None`.
        2. Choose exactly one result: `None`, `Draft`, or `PromotionCandidate`.
        3. If the result is `Draft`, record the lesson under `ai-wiki/people/<handle>/drafts/` and print `AI Wiki Update Path: <path>`.
        4. If the result is `PromotionCandidate`, mark or update the draft as a promotion candidate, print `AI Wiki Update Path: <path>`, and ask for human confirmation before creating `ai-wiki/review-patterns/*.md`.
        5. Always print exactly one final status line:
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

        1. Read `_toolkit/system.md` for package-managed collaboration rules.
        2. Read `constraints.md` for hard constraints and non-negotiables.
        3. Read `workflows.md` for preferred ways of working in this repo.
        4. Read `decisions.md` for durable project decisions and tradeoffs.
        5. Read `review-patterns/` before implementation and review tasks.
        6. Read files in `trails/` only when they match the current task.
        7. Read `people/<handle>/drafts/` when continuing or recording personal draft notes.

        ## Areas

        - `review-patterns/` contains shared, reusable review rules.
        - `people/<handle>/drafts/` contains raw personal notes that may later be promoted.
        - `_toolkit/system.md` contains package-managed collaboration protocol and note schemas.
        """
    )


def test_init_writes_expected_toolkit_managed_files(repo_env: dict[str, Path]) -> None:
    result = runner.invoke(app, ["init", "--handle", "alice"])

    assert result.exit_code == 0
    assert (
        repo_env["repo"] / "ai-wiki" / "_toolkit" / "system.md"
    ).read_text(encoding="utf-8") == strip_margin(
        """
        # Toolkit Managed System Rules

        This file is managed by ai-wiki-toolkit. Future package versions may update it.

        ## Start Of Task

        1. Read `ai-wiki/index.md`.
        2. Read `ai-wiki/review-patterns/` before implementation or review work.
        3. Read `ai-wiki/people/<handle>/drafts/` when continuing draft work.
        4. If repo docs are not enough, read `<home>/ai-wiki/system/_toolkit/system.md` and then `<home>/ai-wiki/system/index.md`.
        5. If an `ai-wiki-update-check` skill is available, use it for end-of-task AI wiki checks.

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


def test_init_updates_managed_toolkit_files_on_rerun(repo_env: dict[str, Path]) -> None:
    result = runner.invoke(app, ["init", "--handle", "alice"])
    assert result.exit_code == 0

    managed_path = repo_env["repo"] / "ai-wiki" / "_toolkit" / "system.md"
    managed_path.write_text("# stale\n", encoding="utf-8")

    second = runner.invoke(app, ["init", "--handle", "alice"])

    assert second.exit_code == 0
    assert managed_path.read_text(encoding="utf-8").startswith("# Toolkit Managed System Rules")
    assert "Updated managed files: 1" in second.output
