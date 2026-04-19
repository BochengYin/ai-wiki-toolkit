"""Static starter content for ai-wiki-toolkit."""

from __future__ import annotations

from textwrap import dedent

PROMPT_BLOCK_START = "<!-- aiwiki-toolkit:start -->"
PROMPT_BLOCK_END = "<!-- aiwiki-toolkit:end -->"
OPENCODE_KEY = "aiwikiToolkit"
TOOLKIT_GITHUB_URL = "https://github.com/BochengYin/ai-wiki-toolkit"
AI_WIKI_UPDATE_SKILL_DIR = ".agents/skills/ai-wiki-update-check"


def repo_starter_files(handle: str) -> dict[str, str]:
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
            5. Read `review-patterns/index.md` before individual review patterns.
            6. Read `trails/index.md` when task-specific chronology or dead ends may help.
            7. Read `people/<handle>/index.md` when continuing or recording personal draft notes.

            ## Areas

            - `review-patterns/index.md` maps shared, reusable review rules.
            - `trails/index.md` maps task-specific chronology, dead ends, and release trails.
            - `people/<handle>/index.md` maps handle-local draft notes and working history.
            - `metrics/` contains user-owned evidence logs such as `reuse-events.jsonl`.
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
        "review-patterns/index.md": dedent(
            """
            # Review Patterns Index

            Use this file to map reusable repo-specific review rules.

            Keep each promoted rule as its own file under `review-patterns/`, then update this index with a short description and when to read it.
            """
        ).strip()
        + "\n",
        "trails/index.md": dedent(
            """
            # Trails Index

            Use this file to map task-specific chronology, release investigations, and dead ends.

            Trail files are useful when an agent needs previous debugging context, but they should not replace stable rules in `review-patterns/`.
            """
        ).strip()
        + "\n",
        f"people/{handle}/index.md": dedent(
            """
            # Personal Draft Index

            This folder contains handle-local draft notes and working memory.

            ## Areas

            - `drafts/` contains raw notes that may later be promoted into shared review patterns.
            - Add short links here when draft volume grows and navigation becomes harder.
            """
        ).strip()
        + "\n",
        "metrics/index.md": dedent(
            """
            # Metrics Index

            This folder is user-owned evidence space for measuring whether the AI wiki is helping in real work.

            ## Files

            - `reuse-events.jsonl` is an append-only event log for knowledge reuse observations.
            - `aiwiki-toolkit record-reuse ...` appends one explicit observation and refreshes managed aggregates.
            - Package-managed aggregate views are generated under `_toolkit/metrics/`.
            """
        ).strip()
        + "\n",
        "metrics/reuse-events.jsonl": "",
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
            2. Read `ai-wiki/review-patterns/index.md` before implementation or review work.
            3. Read `ai-wiki/people/<handle>/index.md` when continuing draft work.
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
        ).strip()
        + "\n",
        "schema/reuse-v1.md": dedent(
            """
            # Reuse Schema v1

            This document describes the first machine-readable schema for measuring whether AI wiki knowledge was reused during real work.

            ## Goals

            - keep user-owned Markdown knowledge stable
            - add machine-readable evidence without rewriting user docs
            - distinguish preloaded knowledge reuse from lookup-based reuse
            - support lightweight efficiency estimates without pretending token measurements are exact

            ## Source Of Truth

            User-owned reuse observations live in `ai-wiki/metrics/reuse-events.jsonl`.

            Package-managed aggregate files are regenerated under `ai-wiki/_toolkit/metrics/`.

            The toolkit can append explicit observations via `aiwiki-toolkit record-reuse`.

            ## Event Fields

            Each JSONL event may include:

            - `schema_version`
            - `event_id`
            - `observed_at`
            - `task_id`
            - `doc_id`
            - `doc_kind`
            - `retrieval_mode`
            - `evidence_mode`
            - `reuse_outcome`
            - `reuse_effects`
            - `agent_name`
            - `model`
            - `notes`
            - `estimated_savings`

            ## Retrieval Mode

            - `preloaded`: the document was already loaded in the normal read path
            - `lookup`: the document was consulted after extra searching or backtracking

            ## Evidence Mode

            - `explicit`: the run clearly stated that the document was used
            - `inferred`: the reuse is inferred from behavior or chronology rather than an explicit statement

            ## Reuse Outcome

            - `resolved`: the wiki materially helped resolve the task
            - `partial`: the wiki helped, but did not fully resolve the task
            - `not_helpful`: the wiki was consulted, but did not help materially

            ## Aggregate Outputs

            The toolkit currently derives:

            - `_toolkit/catalog.json`
            - `_toolkit/metrics/document-stats.json`
            - `_toolkit/metrics/task-stats.json`
            """
        ).strip()
        + "\n",
    }


def managed_home_toolkit_files() -> dict[str, str]:
    return {
        "system.md": dedent(
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
        ).strip()
        + "\n"
    }


def repo_skill_starter_files() -> dict[str, str]:
    return {
        f"{AI_WIKI_UPDATE_SKILL_DIR}/SKILL.md": dedent(
            """
            ---
            name: ai-wiki-update-check
            description: Run the mandatory end-of-task AI wiki update check for ai-wiki-toolkit. Use at the end of every completed task in this repository to decide whether the result is None, Draft, or PromotionCandidate, update ai-wiki notes when needed, and emit the required final status line.
            ---

            # AI Wiki Update Check

            Use this skill at the end of every completed task in this repository.

            This check is mandatory even when the correct outcome is `None`.

            ## Core Workflow

            1. Review the task outcome, changes made, and lessons learned.
            2. Choose exactly one outcome: `None`, `Draft`, or `PromotionCandidate`.
            3. If the outcome is `Draft` or `PromotionCandidate`, create or update a note under `ai-wiki/people/<handle>/drafts/`.
            4. Emit the final result using the exact output contract in [references/output-contract.md](references/output-contract.md).
            5. Use [references/decision-rules.md](references/decision-rules.md) for the decision gate, promotion rules, and note placement rules.

            ## Constraints

            - Do not skip the check just because no durable lesson is expected.
            - Do not create or update `ai-wiki/review-patterns/*.md` without human confirmation.
            - Keep project-specific knowledge in `ai-wiki/`.
            - Keep cross-project knowledge in `<home>/ai-wiki/system/`.
            """
        ).strip()
        + "\n",
        f"{AI_WIKI_UPDATE_SKILL_DIR}/references/decision-rules.md": dedent(
            """
            # Decision Rules

            ## Outcome Meanings

            - `None`
              Use when you completed the check and found no durable lesson worth recording.

            - `Draft`
              Use when there is a durable lesson worth keeping, but it is still raw, task-specific, or not yet validated as a shared rule.

            - `PromotionCandidate`
              Use when a draft exists or was updated and the lesson satisfies the promotion gate, but human confirmation is still required before creating or updating `ai-wiki/review-patterns/*.md`.

            ## Promotion Gate

            Only choose `PromotionCandidate` when at least one of these is true:

            - the same issue has been observed at least twice
            - a reviewer judges it reusable and can express it as a stable rule

            ## Writing Targets

            - Put raw personal notes in `ai-wiki/people/<handle>/drafts/`.
            - Put shared, reusable repo rules in `ai-wiki/review-patterns/` only after human confirmation.
            - Keep project-specific lessons in `ai-wiki/`.
            - Keep cross-project lessons in `<home>/ai-wiki/system/`.
            """
        ).strip()
        + "\n",
        f"{AI_WIKI_UPDATE_SKILL_DIR}/references/output-contract.md": dedent(
            """
            # Output Contract

            Choose exactly one final status line:

            - `AI Wiki Update Candidate: None`
            - `AI Wiki Update Candidate: Draft`
            - `AI Wiki Update Candidate: PromotionCandidate`

            If the outcome is `Draft` or `PromotionCandidate`, also print:

            - `AI Wiki Update Path: <path>`

            ## Examples

            No durable lesson:

            ```text
            AI Wiki Update Candidate: None
            ```

            Durable lesson, not yet ready for promotion:

            ```text
            AI Wiki Update Candidate: Draft
            AI Wiki Update Path: ai-wiki/people/<handle>/drafts/<file>.md
            ```

            Ready to ask for promotion:

            ```text
            AI Wiki Update Candidate: PromotionCandidate
            AI Wiki Update Path: ai-wiki/people/<handle>/drafts/<file>.md
            ```
            """
        ).strip()
        + "\n",
        f"{AI_WIKI_UPDATE_SKILL_DIR}/agents/openai.yaml": dedent(
            """
            interface:
              display_name: "AI Wiki Update Check"
              short_description: "Run the mandatory end-of-task AI wiki check"
              default_prompt: "Run the ai-wiki end-of-task update check for this completed task."
            """
        ).strip()
        + "\n",
    }


def prompt_block_body() -> str:
    return dedent(
        """
        ## AI Wiki Toolkit

        Before starting work:

        1. Read `ai-wiki/_toolkit/system.md`.
        2. Read `ai-wiki/index.md`.
        3. Read `ai-wiki/review-patterns/index.md` before implementation or review work.
        4. Read your own folder index under `ai-wiki/people/<handle>/index.md` when continuing draft notes.
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
        """
    ).strip()


def default_opencode_config() -> dict[str, object]:
    return {
        "schemaVersion": 1,
        "managedBy": "ai-wiki-toolkit",
    }
