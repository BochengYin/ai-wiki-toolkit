"""Static starter content for ai-wiki-toolkit."""

from __future__ import annotations

from textwrap import dedent

PROMPT_BLOCK_START = "<!-- aiwiki-toolkit:start -->"
PROMPT_BLOCK_END = "<!-- aiwiki-toolkit:end -->"
GITIGNORE_BLOCK_START = "# <!-- aiwiki-toolkit:start -->"
GITIGNORE_BLOCK_END = "# <!-- aiwiki-toolkit:end -->"
OPENCODE_KEY = "aiwikiToolkit"
TOOLKIT_GITHUB_URL = "https://github.com/BochengYin/ai-wiki-toolkit"
TOOLKIT_SKILLS_DIR = ".agents/skills"
AI_WIKI_UPDATE_SKILL_DIR = ".agents/skills/ai-wiki-update-check"
AI_WIKI_REUSE_SKILL_DIR = ".agents/skills/ai-wiki-reuse-check"
TELEMETRY_IGNORE_PATHS = (
    "ai-wiki/metrics/reuse-events/",
    "ai-wiki/metrics/task-checks/",
    "ai-wiki/_toolkit/metrics/",
    "ai-wiki/_toolkit/catalog.json",
)


def gitignore_block_body() -> str:
    return dedent(
        """
        # Ignore AI wiki telemetry so normal agent use does not dirty git status.
        ai-wiki/metrics/reuse-events/
        ai-wiki/metrics/task-checks/
        ai-wiki/_toolkit/metrics/
        ai-wiki/_toolkit/catalog.json
        """
    ).strip()


def repo_starter_files(handle: str) -> dict[str, str]:
    return {
        "index.md": dedent(
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

            See also `_toolkit/workflows.md` for package-managed baseline workflows that ship with `ai-wiki-toolkit`.
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

            - `reuse-events/<handle>.jsonl` stores per-handle document-level AI wiki reuse observations.
            - `task-checks/<handle>.jsonl` stores per-handle task-level AI wiki reuse checks.
            - `aiwiki-toolkit record-reuse ...` appends one document-level observation for the current handle and refreshes managed aggregates.
            - `aiwiki-toolkit record-reuse-check ...` appends one task-level reuse check for the current handle and refreshes managed aggregates.
            - The installer manages a `.gitignore` block so these telemetry logs and the generated `_toolkit/catalog.json` and `_toolkit/metrics/*.json` files stay local by default.
            - `aiwiki-toolkit refresh-metrics` regenerates package-managed aggregate views if you need a fresh local snapshot.
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
        "index.md": dedent(
            """
            # Toolkit Managed Index

            This directory is managed by ai-wiki-toolkit. Future package versions may update it.

            ## Read Order

            1. Read `system.md` for package-managed collaboration rules.
            2. Read `workflows.md` for package-managed baseline workflows.
            3. Read `schema/reuse-v1.md` only when reuse metrics, logging, or schema questions matter.

            ## Generated Outputs

            - `catalog.json` and `metrics/*.json` are generated outputs, not guidance docs.
            - The installer ignores those generated outputs in `.gitignore` so routine telemetry updates stay local.
            - Regenerate those outputs with `aiwiki-toolkit refresh-metrics` whenever you need a fresh local snapshot.
            """
        ).strip()
        + "\n",
        "system.md": dedent(
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
        ).strip()
        + "\n",
        "workflows.md": dedent(
            """
            # Toolkit Managed Workflows

            This file is managed by ai-wiki-toolkit. Future package versions may update it.

            ## AI Wiki Maintenance

            1. Run one AI wiki reuse check at the end of every completed task, even when no AI wiki docs were used.
            2. If any user-owned repo or system AI wiki docs were consulted, record one `aiwiki-toolkit record-reuse` event per consulted doc.
            3. Do not log managed `_toolkit/**` docs with `record-reuse`; if they changed the plan or behavior, cite their paths in a progress update or the final note instead.
            4. Record one `aiwiki-toolkit record-reuse-check` entry for the task using `wiki_used` or `no_wiki_use`.
            5. The installer manages a `.gitignore` block that ignores `ai-wiki/metrics/reuse-events/`, `ai-wiki/metrics/task-checks/`, `ai-wiki/_toolkit/metrics/`, and `ai-wiki/_toolkit/catalog.json` so telemetry stays local by default.
            6. If those telemetry paths were tracked before you upgraded, run `aiwiki-toolkit doctor` and follow the suggested `git rm --cached` fix once to untrack them.
            7. Run one AI wiki update check at the end of every completed task, even when the result is `None`.
            8. Always end with exactly one status line: `AI Wiki Update Candidate: None`, `Draft`, or `PromotionCandidate`.
            9. If the result is `Draft` or `PromotionCandidate`, also print `AI Wiki Update Path: <path>`.
            10. Put reusable repo-specific lessons in `ai-wiki/review-patterns/`.
            11. Put task-specific chronology and dead ends in `ai-wiki/trails/`.
            12. Put raw personal draft notes in `ai-wiki/people/<handle>/drafts/`.
            13. Promote only stable, reviewable rules into shared patterns.
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

            User-owned reuse observations live in `ai-wiki/metrics/reuse-events/<handle>.jsonl`.

            User-owned reuse checks live in `ai-wiki/metrics/task-checks/<handle>.jsonl`.

            Package-managed aggregate files are regenerated under `ai-wiki/_toolkit/metrics/`.

            The installer ignores the telemetry shards and generated aggregate views in `.gitignore` by default
            so routine reuse logging does not dirty git status.

            The toolkit can append explicit document observations via `aiwiki-toolkit record-reuse`.

            The toolkit can append task-level reuse checks via `aiwiki-toolkit record-reuse-check`.

            Legacy flat files such as `ai-wiki/metrics/reuse-events.jsonl` and `ai-wiki/metrics/task-checks.jsonl`
            are still read for compatibility, but new writes should use the per-handle shard paths.

            ## Reuse Event Fields

            Each JSONL event may include:

            - `schema_version`
            - `event_id`
            - `observed_at`
            - `author_handle`
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

            ## Task Check Fields

            Each task check entry may include:

            - `schema_version`
            - `check_id`
            - `checked_at`
            - `author_handle`
            - `task_id`
            - `check_outcome`
            - `agent_name`
            - `model`
            - `notes`

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

            ## Managed Docs

            Managed control-plane docs under `_toolkit/**` must not be recorded with `aiwiki-toolkit record-reuse`.

            If they materially influence task behavior, cite their path in user-facing progress notes instead.

            ## Aggregate Outputs

            The toolkit currently derives:

            - `_toolkit/catalog.json`
            - `_toolkit/metrics/document-stats.json`
            - `_toolkit/metrics/task-stats.json`

            Those generated views are intended as local snapshots. Regenerate them with
            `aiwiki-toolkit refresh-metrics` whenever you need a fresh local view.
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
        f"{AI_WIKI_REUSE_SKILL_DIR}/SKILL.md": dedent(
            """
            ---
            name: ai-wiki-reuse-check
            description: Run the mandatory end-of-task AI wiki reuse check for ai-wiki-toolkit. Use it to record whether AI wiki docs were consulted during the task, append one reuse event per consulted doc, append one task-level reuse check, and report the outcome.
            ---

            # AI Wiki Reuse Check

            Use this skill at the end of every completed task in this repository.

            This check is mandatory even when the correct outcome is `no_wiki_use`.

            ## Core Workflow

            1. Review whether any repo-local or cross-project AI wiki docs were consulted during the task.
            2. If one or more user-owned AI wiki docs were consulted, append one `aiwiki-toolkit record-reuse` event per consulted doc.
            3. If a managed `_toolkit/**` doc changed the plan or behavior, cite its path in a progress update or final note, but do not log it with `record-reuse`.
            4. When a user-owned AI wiki doc materially changes the plan or behavior, cite its path in a progress update or final note.
            5. Use `reuse_outcome=not_helpful` for consulted user-owned docs that did not help materially but still affected the task flow.
            6. Append one `aiwiki-toolkit record-reuse-check` entry for the task using:
               - `wiki_used` when one or more doc events were recorded
               - `no_wiki_use` when no AI wiki doc events were recorded
            7. Emit the final result using [references/output-contract.md](references/output-contract.md).

            ## Constraints

            - Do not skip the check just because the task was small or the result seems obvious.
            - Record one task-level reuse check for every completed task.
            - If multiple user-owned AI wiki docs were consulted, record them as separate `record-reuse` events.
            - Do not record managed `_toolkit/**` docs with `record-reuse`.
            - If an AI wiki doc changed the task plan or behavior, name the path explicitly in a user-facing update.
            """
        ).strip()
        + "\n",
        f"{AI_WIKI_REUSE_SKILL_DIR}/references/decision-rules.md": dedent(
            """
            # Decision Rules

            ## Outcome Meanings

            - `wiki_used`
              Use when one or more AI wiki document reuse events were recorded for the task.

            - `no_wiki_use`
              Use when the task completed without recording any AI wiki document reuse events.

            ## Recording Rules

            - Record one `aiwiki-toolkit record-reuse` event per consulted user-owned AI wiki document.
            - Do not record managed `_toolkit/**` docs with `record-reuse`; cite those paths in progress updates or final notes instead.
            - Use `reuse_outcome=not_helpful` when a consulted user-owned doc did not help materially but still influenced the search path.
            - Record the task-level `aiwiki-toolkit record-reuse-check` entry after all document-level reuse events for that task are appended.
            """
        ).strip()
        + "\n",
        f"{AI_WIKI_REUSE_SKILL_DIR}/references/output-contract.md": dedent(
            """
            # Output Contract

            Choose exactly one reuse status line:

            - `AI Wiki Reuse Check: wiki_used`
            - `AI Wiki Reuse Check: no_wiki_use`

            If the result is `wiki_used`, also print:

            - `AI Wiki Reuse Docs: <comma-separated doc ids>`

            ## Examples

            No AI wiki docs were used:

            ```text
            AI Wiki Reuse Check: no_wiki_use
            ```

            AI wiki docs were used:

            ```text
            AI Wiki Reuse Check: wiki_used
            AI Wiki Reuse Docs: workflows, review-patterns/shared-prompt-files-must-be-user-agnostic
            ```
            """
        ).strip()
        + "\n",
        f"{AI_WIKI_REUSE_SKILL_DIR}/agents/openai.yaml": dedent(
            """
            interface:
              display_name: "AI Wiki Reuse Check"
              short_description: "Record end-of-task AI wiki reuse"
              default_prompt: "Run the ai-wiki end-of-task reuse check for this completed task."
            """
        ).strip()
        + "\n",
    }


def prompt_block_body() -> str:
    return dedent(
        """
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
        """
    ).strip()


def default_opencode_config() -> dict[str, object]:
    return {
        "schemaVersion": 1,
        "managedBy": "ai-wiki-toolkit",
    }
