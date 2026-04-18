"""Static starter content for ai-wiki-toolkit."""

from __future__ import annotations

from textwrap import dedent

PROMPT_BLOCK_START = "<!-- aiwiki-toolkit:start -->"
PROMPT_BLOCK_END = "<!-- aiwiki-toolkit:end -->"
OPENCODE_KEY = "aiwikiToolkit"


def repo_starter_files() -> dict[str, str]:
    return {
        "index.md": dedent(
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
        ).strip()
        + "\n",
        "constraints.md": dedent(
            """
            # Project Constraints

            Capture stable project rules, boundaries, and non-negotiable requirements here.
            """
        ).strip()
        + "\n",
        "workflows.md": dedent(
            """
            # Project Workflows

            Capture repeatable repo-specific workflows here.
            """
        ).strip()
        + "\n",
        "decisions.md": dedent(
            """
            # Project Decisions

            Capture durable architectural and process decisions here.
            """
        ).strip()
        + "\n",
    }


def system_starter_files() -> dict[str, str]:
    return {
        "index.md": dedent(
            """
            # System AI Wiki Index

            This is the user-owned entrypoint for cross-project AI wiki content.

            ## Read Order

            1. Read `_toolkit/system.md` for package-managed cross-project collaboration rules.
            2. Read `preferences.md` for default working preferences.
            3. Read files in `playbooks/` when a reusable procedure is needed.
            4. Read files in `templates/` when creating new durable guidance.
            """
        ).strip()
        + "\n",
        "preferences.md": dedent(
            """
            # Preferences

            Capture cross-project defaults, habits, and reusable guidance here.
            """
        ).strip()
        + "\n",
    }


def managed_repo_toolkit_files() -> dict[str, str]:
    return {
        "system.md": dedent(
            """
            # Toolkit Managed System Rules

            This file is managed by ai-wiki-toolkit. Future package versions may update it.

            ## Start Of Task

            1. Read `ai-wiki/index.md`.
            2. Read `ai-wiki/review-patterns/` before implementation or review work.
            3. Read `ai-wiki/people/<handle>/drafts/` when continuing draft work.
            4. If repo docs are not enough, read `~/ai-wiki/system/_toolkit/system.md` and then `~/ai-wiki/system/index.md`.

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
        ).strip()
        + "\n"
    }


def managed_home_toolkit_files() -> dict[str, str]:
    return {
        "system.md": dedent(
            """
            # Toolkit Managed Cross-Project Rules

            This file is managed by ai-wiki-toolkit. Future package versions may update it.

            ## Cross-Project Usage

            1. Keep reusable debugging, review, and workflow guidance under `~/ai-wiki/system/`.
            2. Keep package-managed rules under `~/ai-wiki/system/_toolkit/`.
            3. Keep user-owned preferences, playbooks, and templates outside `_toolkit/`.

            ## Review Pattern Reuse

            - Only move knowledge here when it is clearly reusable beyond a single repository.
            - Prefer repo-local `review-patterns/` for team-specific coding and review rules.
            - Promote stable cross-project abstractions here only after they have been validated in real work.
            """
        ).strip()
        + "\n"
    }


def prompt_block_body(handle: str) -> str:
    return dedent(
        f"""
        ## AI Wiki Toolkit

        Before starting work:

        1. Read `ai-wiki/_toolkit/system.md`.
        2. Read `ai-wiki/index.md`.
        3. Read `ai-wiki/review-patterns/` before implementation or review work.
        4. Read `ai-wiki/people/{handle}/drafts/` when continuing your own draft notes.
        5. If repo docs are not enough, read `~/ai-wiki/system/_toolkit/system.md` and then `~/ai-wiki/system/index.md`.
        6. Keep project-specific notes in `ai-wiki/`.
        7. Keep cross-project reusable notes in `~/ai-wiki/system/`.
        8. Only suggest promotion from a draft to a shared pattern when the two-signal gate is satisfied.
        9. Agents may suggest promotion candidates, but humans confirm shared patterns.

        ## End Of Task

        1. If you discovered a new review or implementation lesson, record it in `ai-wiki/people/{handle}/drafts/`.
        2. If it meets the promotion gate, mark it as a promotion candidate and ask for human confirmation before creating `ai-wiki/review-patterns/*.md`.
        3. If no durable pattern was found, explicitly say `AI Wiki Update Candidate: none`.
        """
    ).strip()


def default_opencode_config() -> dict[str, object]:
    return {
        "schemaVersion": 1,
        "managedBy": "ai-wiki-toolkit",
    }
