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
AI_WIKI_CAPTURE_REVIEW_LEARNING_SKILL_DIR = ".agents/skills/ai-wiki-capture-review-learning"
AI_WIKI_CLARIFY_BEFORE_CODE_SKILL_DIR = ".agents/skills/ai-wiki-clarify-before-code"
AI_WIKI_CONSOLIDATE_DRAFTS_SKILL_DIR = ".agents/skills/ai-wiki-consolidate-drafts"
AI_WIKI_UPDATE_SKILL_DIR = ".agents/skills/ai-wiki-update-check"
AI_WIKI_REUSE_SKILL_DIR = ".agents/skills/ai-wiki-reuse-check"
TELEMETRY_IGNORE_PATHS = (
    ".env.aiwiki",
    "ai-wiki/metrics/reuse-events/",
    "ai-wiki/metrics/task-checks/",
    "ai-wiki/_toolkit/consolidation/",
    "ai-wiki/_toolkit/diagnostics/",
    "ai-wiki/_toolkit/metrics/",
    "ai-wiki/_toolkit/work/",
    "ai-wiki/_toolkit/catalog.json",
)


def gitignore_block_body() -> str:
    return dedent(
        """
        # Ignore AI wiki local state so normal agent use does not dirty git status.
        .env.aiwiki
        ai-wiki/metrics/reuse-events/
        ai-wiki/metrics/task-checks/
        ai-wiki/_toolkit/consolidation/
        ai-wiki/_toolkit/diagnostics/
        ai-wiki/_toolkit/metrics/
        ai-wiki/_toolkit/work/
        ai-wiki/_toolkit/catalog.json
        """
    ).strip()


def repo_starter_files(handle: str) -> dict[str, str]:
    return {
        "index.md": dedent(
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
            - `work/index.md` maps the append-only work ledger for todos, active tasks, and epics.
            - `people/<handle>/index.md` maps handle-local draft notes and working history.
            - `metrics/` contains user-owned evidence logs such as `reuse-events/<handle>.jsonl` and `task-checks/<handle>.jsonl`.
            """
        ).strip()
        + "\n",
        "constraints.md": dedent(
            """
            # Project Constraints

            This file is intentionally project-specific.

            Record hard repo boundaries and non-negotiable requirements here. If no constraints are
            listed yet, the team has not recorded any project-specific hard constraints.

            Good entries include security requirements, compatibility promises, release boundaries,
            data handling rules, or areas agents must not modify without approval.
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

            This file is intentionally project-specific.

            Record durable architecture or process decisions here after the team has made them. If no
            decisions are listed yet, the team has not recorded any project-specific decisions.

            Good entries explain what was decided, why, what alternatives were rejected, and when the
            decision was made.
            """
        ).strip()
        + "\n",
        "conventions/index.md": dedent(
            """
            # Conventions Index

            Use this area for shared team conventions that coding agents should read before implementation.

            Conventions are stronger than personal preferences and more stable than one-off review comments.

            ## When to read

            Read relevant convention files before changing code in their scope.

            Examples:
            - Python typing conventions
            - testing conventions
            - API design conventions
            - error handling conventions
            - logging conventions

            ## Promotion rule

            Do not promote a single review comment into a team convention automatically unless one of these is true:

            - the reviewer is an owner or tech lead for that area
            - the same preference appears repeatedly
            - the user explicitly says to remember it as a team rule
            - an existing convention is being refined
            - the PR discussion clearly accepts it as a reusable rule

            ## Suggested note shape

            Each convention file should include:

            - Status
            - Scope
            - Rule
            - Examples
            - Applies When
            - Do Not Use When
            - Source Pointer
            - History / Supersedes
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
        "problems/index.md": dedent(
            """
            # Problems Index

            Use this area for reusable problem-solution memories.

            A problem note should help future agents avoid repeating the same debugging loop.

            ## When to read

            Read relevant problem notes before implementing or testing similar behavior.

            Examples:
            - flaky async notification tests
            - import job idempotency issues
            - confusing migration failure
            - known integration edge cases

            ## Suggested note shape

            Each problem file should include:

            - Symptom
            - Cause
            - Solution
            - Applies When
            - Do Not Use When
            - Related Files
            - Source Pointer
            - History
            """
        ).strip()
        + "\n",
        "features/index.md": dedent(
            """
            # Features Index

            Use this area for feature-specific working memory.

            Feature notes are useful when requirements are clarified across multiple agent sessions, PR reviews, or conversations.

            ## When to read

            Read a feature note when the current task is implementing, modifying, testing, or reviewing that feature.

            ## Suggested note shape

            Each feature file should include:

            - Current Understanding
            - Confirmed Requirements
            - Blocking Unknowns
            - Non-Blocking Assumptions
            - Acceptance Criteria
            - Related Decisions
            - Related Conventions
            - Related Problems
            - Source Pointers
            - History / Supersedes
            """
        ).strip()
        + "\n",
        "work/index.md": dedent(
            """
            # Work Ledger Index

            Use this area for repo-native work state that agents should be able to reference across conversations.

            The default machine-readable event log lives under `work/events/<handle>.jsonl`.

            Keep canonical work items in this central ledger, not inside `people/<handle>/`.
            Link work to people with `author_handle`, `reporter_handle`, and `assignee_handles`.

            ## Statuses

            Work items may move through:

            - `inbox`
            - `proposed`
            - `todo`
            - `planned`
            - `active`
            - `processing`
            - `blocked`
            - `review`
            - `done`
            - `archived`
            - `dropped`

            ## Usage

            - Resolve current local actor identity from `.env.aiwiki` when no explicit handle is supplied.
            - Capture conversation todos with `aiwiki-toolkit work capture`.
            - Update status with `aiwiki-toolkit work status`.
            - Use `aiwiki-toolkit work mine` to inspect open work assigned to the current local actor.
            - Use `aiwiki-toolkit work list --assignee <handle>` or `--reporter <handle>` for team views.
            - Regenerate local managed views with `aiwiki-toolkit work report`.
            - Treat generated files under `_toolkit/work/` as views, not canonical work memory.
            - Route packets should treat work assigned to the current actor as actionable by default. Work assigned to other handles should appear only when directly matched by the user's request.
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

            ## Evidence Model

            - The end-of-task AI wiki footer is the user-facing evidence surface.
            - Local telemetry under `metrics/` is the machine-readable record behind that footer.
            - Managed `_toolkit/**` docs guide workflow, but they do not count as knowledge-reuse evidence.

            ## Files

            - `reuse-events/<handle>.jsonl` stores per-handle document-level AI wiki reuse observations.
            - `task-checks/<handle>.jsonl` stores per-handle task-level AI wiki reuse checks.
            - `aiwiki-toolkit record-reuse ...` appends one document-level observation for the current handle and refreshes managed aggregates.
            - `aiwiki-toolkit record-reuse-check ...` appends one task-level reuse check for the current handle and refreshes managed aggregates.
            - The installer manages a `.gitignore` block so `.env.aiwiki`, telemetry logs, and generated `_toolkit/catalog.json`, `_toolkit/metrics/*.json`, `_toolkit/diagnostics/*`, and `_toolkit/consolidation/*` files stay local by default.
            - `aiwiki-toolkit refresh-metrics` regenerates package-managed aggregate views if you need a fresh local snapshot.
            - `aiwiki-toolkit diagnose memory` generates local memory quality diagnostics under `_toolkit/diagnostics/`.
            - `aiwiki-toolkit consolidate queue` generates a local human-review queue for draft consolidation and promotion candidates under `_toolkit/consolidation/`.
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
            3. Read `schema/route-v1.md` when task-aware context packets or routing trust boundaries matter.
            4. Read `schema/work-v1.md` when work-ledger events, task lifecycle state, or generated work reports matter.
            5. Read `schema/team-memory-v1.md` when note shapes, memory types, or source pointers matter.
            6. Read `schema/reuse-v1.md` only when reuse metrics, logging, or schema questions matter.

            ## Generated Outputs

            - `catalog.json`, `consolidation/*`, `diagnostics/*`, `metrics/*.json`, and `work/*` are generated outputs, not guidance docs.
            - `aiwiki-toolkit route` emits transient context packets to stdout; packets are derived from source docs and should be regenerated rather than treated as canonical memory.
            - The installer ignores local identity and generated outputs in `.gitignore` so routine agent use stays local.
            - Regenerate catalog, metrics, and work views with `aiwiki-toolkit refresh-metrics` whenever you need a fresh local snapshot.
            - Generate local memory quality diagnostics with `aiwiki-toolkit diagnose memory` when you need to inspect missed, stale, noisy, conflicting, or high-ROI memory.
            - Generate a local draft consolidation and promotion review queue with `aiwiki-toolkit consolidate queue`.
            """
        ).strip()
        + "\n",
        "system.md": dedent(
            """
            # Toolkit Managed System Rules

            This file is managed by ai-wiki-toolkit. Future package versions may update it.

            ## Start Of Task

            1. Run `aiwiki-toolkit route --task "<current user request>"` when available to generate a task-aware AI Wiki Context Packet.
            2. Use the packet's `must_load`, `must_follow`, `context_notes`, and `skip` sections as the first-pass routing layer for the task.
            3. Treat the packet as a generated view with cited sources, not as canonical memory; the Markdown files under `ai-wiki/` remain the source of truth.
            4. If routing is unavailable, fails, or looks insufficient, continue with the baseline read order below.
            5. Read `ai-wiki/constraints.md` for hard constraints and non-negotiables.
            6. Read `ai-wiki/conventions/index.md` for shared team conventions that should guide implementation.
            7. Read `ai-wiki/decisions.md` for durable project decisions and tradeoffs.
            8. Read `ai-wiki/review-patterns/index.md` for reusable review rules and reviewer expectations.
            9. Read `ai-wiki/problems/index.md` before implementing or testing similar behavior.
            10. Read `ai-wiki/features/index.md` when task-specific requirements, assumptions, or acceptance criteria matter.
            11. Read `ai-wiki/workflows.md` for repo-specific workflows that extend the managed baseline.
            12. Read `ai-wiki/trails/index.md` when debugging chronology or dead ends may help.
            13. Read `ai-wiki/_toolkit/work/report.md` when the route packet reports relevant active, processing, blocked, or planned work.
            14. Read `ai-wiki/people/<handle>/index.md` when continuing draft work.
            15. Read `ai-wiki/_toolkit/index.md` when you need package-managed schema, metrics, work views, or directory guidance beyond this workflow.
            16. Use `ai-wiki/index.md` as a repo-owned map when you need a quick overview of local AI wiki areas.
            17. If repo docs are not enough, read `<home>/ai-wiki/system/_toolkit/system.md` and then `<home>/ai-wiki/system/index.md`.
            18. If `ai-wiki-clarify-before-code` is available, use it before implementation when ambiguity materially affects coding.
            19. If `ai-wiki-capture-review-learning` is available, use it when reusable review feedback appears.
            20. If `ai-wiki-reuse-check` and `ai-wiki-update-check` skills are available, use them to produce end-of-task AI wiki evidence and write-back outcomes.

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
        ).strip()
        + "\n",
        "workflows.md": dedent(
            """
            # Toolkit Managed Workflows

            This file is managed by ai-wiki-toolkit. Future package versions may update it.

            ## AI Wiki Maintenance

            1. Start each non-trivial task by running `aiwiki-toolkit route --task "<current user request>"` when available.
            2. Use the route packet to decide which user-owned docs to consult first, but record reuse only for docs actually consulted or materially used.
            3. Produce one AI wiki reuse evidence footer at the end of every completed task.
            4. First classify the task as `relevant`, `optional`, or `not_relevant` for AI wiki use.
            5. Record one `aiwiki-toolkit record-reuse` event per consulted user-owned AI wiki doc.
            6. Do not log managed `_toolkit/**` docs with `record-reuse`; if they changed the plan or behavior, cite their paths in a progress update or the final note instead.
            7. Record one `aiwiki-toolkit record-reuse-check` entry for the task using `wiki_used` or `no_wiki_use`.
            8. Treat the footer as the user-facing evidence surface; telemetry and generated aggregates are the local machine-readable record behind it.
            9. The installer manages a `.gitignore` block that ignores `.env.aiwiki`, `ai-wiki/metrics/reuse-events/`, `ai-wiki/metrics/task-checks/`, `ai-wiki/_toolkit/consolidation/`, `ai-wiki/_toolkit/diagnostics/`, `ai-wiki/_toolkit/metrics/`, `ai-wiki/_toolkit/work/`, and `ai-wiki/_toolkit/catalog.json` so local identity, telemetry, and generated views stay local by default.
            10. If those local-state paths were tracked before you upgraded, run `aiwiki-toolkit doctor` and follow the suggested `git rm --cached` fix once to untrack them.
            11. Produce one AI wiki write-back outcome at the end of every completed task, even when the result is `None`.
            12. Before returning `None`, run memory candidate detection for problem-solution memory, feature clarification memory, convention candidates, missed relevant memory, and conflict or supersession.
            13. Always end with exactly one status line: `AI Wiki Write-Back: none`, `draft recorded`, or `promotion candidate`.
            14. If the result is `Draft` or `PromotionCandidate`, also print `AI Wiki Write-Back Path: <path>`.
            15. Do not write every task summary into the wiki; capture only durable memory.
            16. Put shared team conventions in `ai-wiki/conventions/`.
            17. Put reusable repo-specific review lessons in `ai-wiki/review-patterns/`.
            18. Put reusable problem-solution memories in `ai-wiki/problems/`.
            19. Put feature clarifications in `ai-wiki/features/`.
            20. Put task-specific chronology and dead ends in `ai-wiki/trails/`.
            21. Put todo, active, processing, blocked, review, done, and archived work state in `ai-wiki/work/events/<handle>.jsonl` via `aiwiki-toolkit work`.
            22. Put raw personal draft notes in `ai-wiki/people/<handle>/drafts/`.
            23. Promote only stable, reviewable rules into shared patterns or conventions.
            """
        ).strip()
        + "\n",
        "schema/route-v1.md": dedent(
            """
            # Route Schema v1

            `aiwiki-toolkit route` generates a transient AI Wiki Context Packet for the current task.

            The packet is a derived view, not canonical memory. Markdown files under `ai-wiki/`
            remain the source of truth.

            ## Packet Fields

            - `schema_version`: currently `route-v1`.
            - `task_id`: stable task id, either supplied by the caller or derived from the task text.
            - `task`: current user request text, when supplied by the agent.
            - `route.task_type`: coarse task class such as `scaffold_prompt_workflow`, `release_distribution`, `memory_governance`, `workflow_state`, `eval_workflow`, or `general`.
            - `route.risk_tags`: task risks such as `user_owned_docs`, `managed_prompt_block`, `release_distribution`, `ci_workflow`, `memory_governance`, `workflow_state`, or `task_evaluation`.
            - `route.changed_paths`: path signals supplied by the caller or inferred from `git status --short`.
            - `actor`: resolved local actor handle from CLI/environment, `.env.aiwiki`, git config, or fallback.
            - `route.effort`: coarse effort level such as `low`, `normal`, or `deep`.
            - `context_budget`: safety cap and document limits for the packet. The word value is not a fill target; route may use less.
            - `routing_strategy`: how the packet expects agents to use direct context versus runtime references.
            - `work_context`: actor-scoped matching work-ledger items from `ai-wiki/_toolkit/work/state.json`, when available.
              Work items include `actor_relation` so agents can distinguish assigned, reported, unassigned, and other matched work.
            - `index_cards`: short name/description/reference cards for selected docs and runtime references.
            - `must_load`: authoritative user-owned AI wiki docs the agent should consult directly when required.
            - `maybe_load`: lower-confidence docs that may help if the task needs more context.
            - `must_follow`: source-cited rules extracted from authoritative user-owned docs.
            - `context_notes`: source-cited notes from exploratory docs such as drafts.
            - `skip`: docs intentionally not loaded because the route found no strong signal.
            - `trust_model`: reminders about provenance and source-of-truth boundaries.

            ## Trust Rules

            1. Every `must_follow` rule must cite a user-owned source path.
            2. Drafts and trails may provide `context_notes`, but they should not become authoritative rules unless promoted by the existing human-confirmed workflow.
            3. Managed `_toolkit/**` docs can guide routing behavior, but they should not be recorded as user-owned reuse events.
            4. If the packet looks wrong or incomplete, agents should fall back to the baseline read order in `ai-wiki/_toolkit/system.md`.
            5. Record reuse only for user-owned docs actually consulted or materially used, not for every packet candidate.
            6. Treat `work_context` items with `actor_relation=assignee` as actionable for the current actor. Treat other matched work as context unless the user explicitly asks to work on it.
            7. Prefer index cards and runtime references over loading broad full documents. Simple operational tasks should follow the specific workflow they need instead of pulling in broad memory.
            """
        ).strip()
        + "\n",
        "schema/team-memory-v1.md": dedent(
            """
            # Team Memory Schema v1

            This schema is lightweight guidance for team coding memory. It is not a strict database schema.

            ## Common Fields

            ### Status

            Use one of:

            - `draft`
            - `candidate`
            - `active`
            - `refined`
            - `superseded`

            ### Scope

            Describe where the memory applies.

            Examples:

            - `repo-wide`
            - `Python typing`
            - `backend API`
            - `tests only`
            - `feature: bulk invoice upload`
            - `module: app/notifications`

            ### Source Pointer

            Use lightweight source pointers. Do not over-engineer provenance.

            Suggested fields:

            - `Actor`
            - `Actor Role`
            - `Context`
            - `Quote or Summary`
            - `Captured By`
            - `Captured At`
            - `Scope`

            Example:

            ```yaml
            source:
              actor: Carol
              actor_role: Tech Lead
              context: PR #123 review
              quote: "Please don't use object here. We know this returns str or None."
              captured_by: Bob
              captured_at: 2026-04-20
              scope: Python typing in this repo
            ```

            ## Memory Types

            ### Person Preference

            A preference tied to a person.

            Store under:

            - `ai-wiki/people/<handle>/`
            - or as a draft under `ai-wiki/people/<handle>/drafts/`

            ### Team Convention

            A shared rule that coding agents should follow.

            Store under:

            - `ai-wiki/conventions/`

            ### Review Pattern

            A reusable review issue or review expectation.

            Store under:

            - `ai-wiki/review-patterns/`

            ### Problem-Solution Memory

            A reusable debugging or implementation lesson.

            Store under:

            - `ai-wiki/problems/`

            ### Feature Memory

            A feature-specific current understanding, requirement, assumption, or acceptance criterion.

            Store under:

            - `ai-wiki/features/`

            ### Decision

            A durable project decision or tradeoff.

            Store in:

            - `ai-wiki/decisions.md`
            - or a linked decision file if the repo chooses to split decisions

            ## Conflict and Regression

            When adding new memory:

            - Check whether it conflicts with existing conventions, decisions, features, or person preferences.
            - If it refines an old rule, update the current rule and keep the old item in History.
            - If it contradicts an old rule, do not silently overwrite. Mark a conflict or proposed supersession.
            - If scope differs, narrow the scope instead of treating it as a global conflict.

            ## Default Validity

            Assume pasted information is active unless the user says it is old, deprecated, historical, or the repo/wiki clearly conflicts with it.
            """
        ).strip()
        + "\n",
        "schema/work-v1.md": dedent(
            """
            # Work Ledger Schema v1

            The work ledger records todos, active or processing work, blocked items, review items, completed work, and epics as append-only events.

            ## Source Of Truth

            Local actor identity lives in the gitignored `.env.aiwiki` file at the repository root.

            User-owned work events live in `ai-wiki/work/events/<handle>.jsonl`.

            Package-managed generated views live under `ai-wiki/_toolkit/work/`:

            - `state.json`
            - `report.md`
            - `by-assignee/<handle>.md`
            - `by-reporter/<handle>.md`

            Generated views are local snapshots. Regenerate them with `aiwiki-toolkit work report` or `aiwiki-toolkit refresh-metrics`.

            Keep canonical work state in `ai-wiki/work/events/<handle>.jsonl`, not in `ai-wiki/people/<handle>/`.
            The people namespace is for personal drafts and preferences. Work links to people through event fields.

            ## Event Fields

            Each JSONL event may include:

            - `schema_version`: currently `work-v1`
            - `event_id`
            - `event_type`: `captured` or `status_changed`
            - `occurred_at`
            - `author_handle`
            - `reporter_handle`
            - `assignee_handles`
            - `item_type`: `task` or `epic`
            - `work_id`
            - `title`
            - `status`
            - `epic_id`
            - `source`
            - `links`
            - `agent_name`
            - `model`
            - `notes`

            ## Statuses

            Use:

            - `inbox`
            - `proposed`
            - `todo`
            - `planned`
            - `active`
            - `processing`
            - `blocked`
            - `review`
            - `done`
            - `archived`
            - `dropped`

            ## Lifecycle Rules

            1. Capture conversation todos with `aiwiki-toolkit work capture`.
            2. Move work through lifecycle states with `aiwiki-toolkit work status`.
            3. Resolve the current actor from explicit CLI input, environment, `.env.aiwiki`, git config, then fallback.
            4. Default `author_handle`, `reporter_handle`, and `assignee_handles` to the current actor when capturing new work.
            5. Prefer append-only events over rewriting shared work files.
            6. Treat `_toolkit/work/*` as generated views, not canonical memory.
            7. Do not automatically archive or drop a large epic without human confirmation.
            8. Route packets may use work assigned to the current actor as actionable context by default.
            9. Route packets may show work assigned to other handles only when the current task directly matches that work.
            10. Work events are not knowledge-reuse evidence by themselves.
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
            description: Produce the mandatory end-of-task AI wiki write-back outcome for ai-wiki-toolkit. Use it to detect durable memory candidates, decide whether the result is None, Draft, or PromotionCandidate, and emit the required final status line.
            ---

            # AI Wiki Write-Back Check

            Use this skill at the end of every completed task in this repository.

            This outcome is mandatory even when the correct result is `None`.

            ## Core Workflow

            1. Review the task outcome, changes made, and lessons learned.
            2. Before returning `None`, run memory candidate detection for:
               - a team convention
               - reusable PR review learning
               - feature clarification memory
               - a durable decision note
               - a reusable problem-solution memory
               - missed relevant memory
               - a conflict, refinement, or supersession with existing memory
               - a person preference that should stay personal for now
            3. Check concrete task signals before returning `None`, especially repeated release, CI, or platform failures; workflow or packaging assumption mismatches; environment or tooling fixes future agents may need; multi-turn clarification; accepted assumptions; emerging acceptance criteria; and unresolved feature questions.
            4. Choose exactly one outcome: `None`, `Draft`, or `PromotionCandidate`.
            5. If the outcome is `Draft` or `PromotionCandidate`, create or update a note under `ai-wiki/people/<handle>/drafts/`.
            6. Emit the final result using the exact output contract in [references/output-contract.md](references/output-contract.md).
            7. Use [references/decision-rules.md](references/decision-rules.md) for the decision gate, promotion rules, memory candidate detection, conflict handling, and note placement rules.

            ## Constraints

            - Do not skip the write-back outcome just because no durable lesson is expected.
            - Do not write every task summary into the wiki.
            - Do not create or update `ai-wiki/review-patterns/*.md` without human confirmation.
            - Do not promote a reviewer preference into a team convention unless the promotion rules are met.
            - Do not treat "no wiki docs were opened" as proof that no durable memory was produced.
            - If new memory conflicts with existing memory, flag it as a conflict, refinement, or supersession.
            - Prefer small durable memory over long transcripts.
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
              Use when a draft exists or was updated and the lesson satisfies the promotion gate, but human confirmation is still required before creating or updating `ai-wiki/review-patterns/*.md` or `ai-wiki/conventions/*.md`.

            ## Promotion Gate

            Only choose `PromotionCandidate` when at least one of these is true:

            - the same issue has been observed at least twice
            - a reviewer judges it reusable and can express it as a stable rule

            ## What To Check

            At task end, check whether the task produced:

            - a new or refined team convention
            - reusable PR review learning
            - feature clarification memory
            - a durable decision note
            - a reusable problem-solution memory
            - missed relevant memory
            - a conflict, refinement, or supersession with existing memory
            - a person preference that should stay personal for now

            ## Memory Candidate Detection

            Before returning `None`, check whether the task produced any of these signals.

            ### Problem-Solution Candidate Signals

            - repeated failure across release, CI, or platform work
            - workflow, packaging, or environment assumption mismatch
            - user correction of an agent mistake that could recur
            - tooling or environment fix that future agents may need again
            - workaround discovered after debugging

            ### Feature Memory Candidate Signals

            - multi-turn clarification
            - accepted implementation assumption
            - acceptance criteria that emerged during the task
            - feature behavior that changed from the initial understanding
            - unresolved question that still matters for the feature

            ### Convention, Conflict, And Missed-Memory Signals

            - a reusable rule now spans code, tests, docs, or release workflow changes
            - the task revealed conflict, refinement, or supersession with existing memory
            - a relevant AI wiki doc should have been used but the agent only found it after user correction, review, or later failure
            - the task repeated work that existing team memory should have prevented

            ## Writing Targets

            - Put raw personal notes in `ai-wiki/people/<handle>/drafts/`.
            - Put shared team conventions in `ai-wiki/conventions/` only after human confirmation or explicit team confirmation.
            - Put shared, reusable repo review rules in `ai-wiki/review-patterns/` only after human confirmation.
            - Put reusable problem-solution memories in `ai-wiki/problems/`.
            - Put feature clarifications in `ai-wiki/features/`.
            - Put durable project decisions in `ai-wiki/decisions.md` or a linked decision note if the repo splits decisions.
            - Put missed-relevant-memory follow-ups in `ai-wiki/people/<handle>/drafts/` until the repo chooses a dedicated incident format.
            - Keep project-specific lessons in `ai-wiki/`.
            - Keep cross-project lessons in `<home>/ai-wiki/system/`.

            ## Conflict Handling

            - If new memory conflicts with existing conventions, decisions, features, problems, or person preferences, flag it as a conflict, refinement, or supersession.
            - Narrow scope when the new memory only applies to one feature, module, or reviewer.
            """
        ).strip()
        + "\n",
        f"{AI_WIKI_UPDATE_SKILL_DIR}/references/output-contract.md": dedent(
            """
            # Output Contract

            Choose exactly one user-facing write-back status line:

            - `AI Wiki Write-Back: none`
            - `AI Wiki Write-Back: draft recorded`
            - `AI Wiki Write-Back: promotion candidate`

            If the outcome is `Draft` or `PromotionCandidate`, also print:

            - `AI Wiki Write-Back Path: <path>`

            ## Examples

            No durable lesson:

            ```text
            AI Wiki Write-Back: none
            ```

            Durable lesson, not yet ready for promotion:

            ```text
            AI Wiki Write-Back: draft recorded
            AI Wiki Write-Back Path: ai-wiki/people/<handle>/drafts/<file>.md
            ```

            Ready to ask for promotion:

            ```text
            AI Wiki Write-Back: promotion candidate
            AI Wiki Write-Back Path: ai-wiki/people/<handle>/drafts/<file>.md
            ```
            """
        ).strip()
        + "\n",
        f"{AI_WIKI_UPDATE_SKILL_DIR}/agents/openai.yaml": dedent(
            """
            interface:
              display_name: "AI Wiki Write-Back Evidence"
              short_description: "Detect durable memory from completed tasks"
              default_prompt: "Use $ai-wiki-update-check to produce the end-of-task AI wiki write-back outcome for this completed task."
            """
        ).strip()
        + "\n",
        f"{AI_WIKI_REUSE_SKILL_DIR}/SKILL.md": dedent(
            """
            ---
            name: ai-wiki-reuse-check
            description: Produce the mandatory end-of-task AI wiki reuse evidence for ai-wiki-toolkit. Use it to classify task relevance, record consulted user-owned docs, append local telemetry, and emit the user-facing footer.
            ---

            # AI Wiki Reuse Evidence

            Use this skill at the end of every completed task in this repository.

            This evidence footer is mandatory even when the correct outcome is `no_wiki_use`.

            ## Core Workflow

            1. Classify the task as `relevant`, `optional`, or `not_relevant` for AI wiki use before judging whether the absence of wiki reads is a problem.
            2. Use the final AI wiki footer as the user-facing evidence surface; local telemetry is the machine-readable record behind it.
            3. Review whether any repo-local or cross-project AI wiki docs were consulted during the task.
            4. Before or during the task, check whether relevant memory existed in:
               - `conventions/`
               - `decisions.md`
               - `review-patterns/`
               - `problems/`
               - `features/`
               - `trails/`
               - `people/<handle>/`
            5. If one or more user-owned AI wiki docs were consulted, append one `aiwiki-toolkit record-reuse` event per consulted doc.
            6. If a managed `_toolkit/**` doc changed the plan or behavior, cite its path in a progress update or final note, but do not log it with `record-reuse`.
            7. When a user-owned AI wiki doc materially changes the plan or behavior, cite its path in a progress update or final note.
            8. Use `reuse_outcome=not_helpful` for consulted user-owned docs that did not help materially but still affected the task flow.
            9. Prefer specific doc ids such as `conventions/python-typing`, `problems/async-notification-tests-flaky`, or `features/bulk-invoice-upload`.
            10. Append one `aiwiki-toolkit record-reuse-check` entry for the task using:
               - `wiki_used` when one or more doc events were recorded
               - `no_wiki_use` when no AI wiki doc events were recorded
            11. Emit the final result using [references/output-contract.md](references/output-contract.md).

            ## Constraints

            - Do not skip the footer just because the task was small or the result seems obvious.
            - Record one task-level reuse check for every completed task.
            - `no_wiki_use` is correct for `not_relevant` operational tasks.
            - Do not force unrelated wiki reads just to improve coverage metrics.
            - If multiple user-owned AI wiki docs were consulted, record them as separate `record-reuse` events.
            - Do not record managed `_toolkit/**` docs with `record-reuse`.
            - Listing used docs is evidence of touch, not proof of material reuse.
            - If a relevant user-owned AI wiki doc should have been used but was not, note the miss in the footer even if telemetry still records `no_wiki_use`.
            - If an AI wiki doc changed the task plan or behavior, name the path explicitly in a user-facing update.
            """
        ).strip()
        + "\n",
        f"{AI_WIKI_REUSE_SKILL_DIR}/references/decision-rules.md": dedent(
            """
            # Decision Rules

            ## Task Relevance

            Classify the task before judging whether `no_wiki_use` is acceptable.

            - `not_relevant`
              Pure operational work such as pushing a PR, renaming a branch, or running an already-decided command.

            - `optional`
              Low-risk work where repo memory may help, but the task can often complete correctly without it.

            - `relevant`
              Coding, debugging, release, review, clarification, or conflict-heavy work where existing team memory could materially change the plan.

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
            - Prefer specific doc ids such as `conventions/python-typing`, `problems/async-notification-tests-flaky`, `features/bulk-invoice-upload`, or `review-patterns/shared-prompt-files-must-be-user-agnostic`.
            - `no_wiki_use` is correct for `not_relevant` tasks; do not force unrelated wiki reads just to improve coverage metrics.

            ## Material Reuse Hints

            Listing used docs is not enough to prove usefulness. When relevant, note whether the wiki:

            - changed the plan
            - avoided a retry
            - blocked a wrong path
            - resolved a conflict
            - reused an existing convention
            - captured durable memory

            ## Missed Relevant Memory

            If a relevant user-owned AI wiki doc should have been used but was only discovered after user correction, review, or later failure, note the miss in the footer even when telemetry still records `no_wiki_use`.
            """
        ).strip()
        + "\n",
        f"{AI_WIKI_REUSE_SKILL_DIR}/references/output-contract.md": dedent(
            """
            # Output Contract

            Use the AI wiki footer as the user-facing evidence surface.

            Choose exactly one user-facing reuse status line:

            - `AI Wiki Reuse: user-owned memory used`
            - `AI Wiki Reuse: no user-owned memory used`

            Also print:

            - `AI Wiki Task Relevance: relevant | optional | not_relevant`

            If user-owned memory was used, also print:

            - `AI Wiki Docs Used: <comma-separated doc ids>`

            When relevant, also print:

            - `AI Wiki Impact: <short user-facing impacts or none>`
            - `AI Wiki Missed Memory: none known | <short note>`

            ## Examples

            No AI wiki docs were needed for an operational task:

            ```text
            AI Wiki Reuse: no user-owned memory used
            AI Wiki Task Relevance: not_relevant
            AI Wiki Missed Memory: none known
            ```

            AI wiki docs were used in a relevant task:

            ```text
            AI Wiki Reuse: user-owned memory used
            AI Wiki Task Relevance: relevant
            AI Wiki Docs Used: conventions/python-typing, review-patterns/shared-prompt-files-must-be-user-agnostic
            AI Wiki Impact: changed the plan, reused an existing convention
            AI Wiki Missed Memory: none known
            ```
            """
        ).strip()
        + "\n",
        f"{AI_WIKI_REUSE_SKILL_DIR}/agents/openai.yaml": dedent(
            """
            interface:
              display_name: "AI Wiki Reuse Evidence"
              short_description: "Produce end-of-task AI wiki evidence"
              default_prompt: "Use $ai-wiki-reuse-check to produce the end-of-task AI wiki reuse footer for this completed task."
            """
        ).strip()
        + "\n",
        f"{AI_WIKI_CONSOLIDATE_DRAFTS_SKILL_DIR}/SKILL.md": dedent(
            """
            ---
            name: ai-wiki-consolidate-drafts
            description: Use when handle-local AI wiki drafts have grown into a noisy backlog and related notes should be clustered, refined, or promoted without directly rewriting shared docs by default.
            ---

            # AI Wiki Consolidate Drafts

            Use this skill when `ai-wiki/people/*/drafts/` has accumulated related notes and the next step is to consolidate them into clearer draft clusters, promotion candidates, or explicit conflicts and supersessions.

            ## Workflow

            1. Read the relevant draft set, usually under one handle in `ai-wiki/people/*/drafts/`.
            2. Read nearby context that may confirm or narrow the consolidation target:
               - `ai-wiki/conventions/index.md`
               - `ai-wiki/decisions.md`
               - `ai-wiki/review-patterns/index.md`
               - `ai-wiki/problems/index.md`
               - `ai-wiki/features/index.md`
               - relevant files under `ai-wiki/trails/` when chronology matters
               - `ai-wiki/metrics/` and `_toolkit/metrics/*.json` only as weak signals
            3. Cluster drafts by durable topic, repeated failure mode, or repeated rule, not by filename alone.
            4. For each cluster, choose one next action using [references/candidate-types.md](references/candidate-types.md).
            5. Use [references/promotion-targets.md](references/promotion-targets.md) to propose the best destination when a cluster is mature enough for shared or repo-level memory.
            6. Use [references/conflict-and-supersession.md](references/conflict-and-supersession.md) to flag conflicts, refinements, or supersession instead of silently merging away differences.
            7. Default to refining handle-local drafts first. Do not directly rewrite `ai-wiki/conventions/*.md`, `ai-wiki/review-patterns/*.md`, `ai-wiki/problems/*.md`, or `ai-wiki/features/*.md` unless the user explicitly asks for promotion or doc creation.
            8. Emit the result using [references/output-contract.md](references/output-contract.md).

            ## Rules

            - Cluster first, judge second.
            - Do not promote every repeated draft.
            - Metrics may support prioritization, but they are weak signals and must not be the sole basis for promotion.
            - Make the suggested target path explicit whenever the action is `Refine draft` or `Promotion candidate`.
            - If a cluster is still unstable, keep it local and explain what evidence is still missing.
            - Shared conventions and review patterns still require human confirmation before writing shared docs.
            """
        ).strip()
        + "\n",
        f"{AI_WIKI_CONSOLIDATE_DRAFTS_SKILL_DIR}/references/candidate-types.md": dedent(
            """
            # Candidate Types

            Use exactly one primary action per cluster.

            - `Keep draft`
              Use when the note is still too raw, too narrow, or only observed once.

            - `Refine draft`
              Use when the lesson looks durable but the current draft is fragmented, duplicated, or needs a clearer problem statement before promotion.

            - `Promotion candidate`
              Use when the lesson is stable enough for a shared convention, review pattern, problem note, feature note, or decision update, but still needs human confirmation before shared docs are written.

            - `Conflict`
              Use when a cluster contradicts active conventions, decisions, features, problems, or existing person-local guidance and the mismatch still needs human review.

            - `Supersession`
              Use when a newer cluster clearly replaces an older draft or stale shared memory item and the result should point to the replacement path.
            """
        ).strip()
        + "\n",
        f"{AI_WIKI_CONSOLIDATE_DRAFTS_SKILL_DIR}/references/promotion-targets.md": dedent(
            """
            # Promotion Targets

            Choose the narrowest durable target that matches the lesson.

            - `ai-wiki/conventions/<name>.md`
              Use for shared team rules that should guide future implementation before code is written.

            - `ai-wiki/review-patterns/<name>.md`
              Use for reusable PR review findings or review checklists that describe how the same mistake shows up in code review.

            - `ai-wiki/problems/<name>.md`
              Use for reusable problem-solution memories that help future agents avoid repeating the same debugging loop.

            - `ai-wiki/features/<name>.md`
              Use for feature-specific requirements, accepted assumptions, or clarified acceptance criteria.

            - `ai-wiki/decisions.md`
              Use for durable project tradeoffs or decisions that should live alongside other explicit repo decisions.

            - `ai-wiki/people/<handle>/drafts/<name>.md`
              Keep or move the note here when the lesson is still personal, exploratory, or not yet ready for shared memory.

            Do not suggest a shared target just because multiple drafts mention the same area. The target must match the memory type, not only the topic.
            """
        ).strip()
        + "\n",
        f"{AI_WIKI_CONSOLIDATE_DRAFTS_SKILL_DIR}/references/conflict-and-supersession.md": dedent(
            """
            # Conflict And Supersession

            Compare each cluster against existing conventions, decisions, review patterns, problems, features, and nearby drafts.

            ## Mark `Conflict` when

            - two active rules overlap in scope but recommend different behavior
            - a proposed promotion would contradict an existing decision
            - the cluster is broad enough that narrowing scope no longer resolves the mismatch

            ## Mark `Supersession` when

            - a newer draft clearly replaces an older draft with better scope or better evidence
            - a promotion candidate would replace stale shared memory rather than coexist with it
            - the old note should remain in history, but future reads should prefer the new note

            ## Mark `Refine draft` instead when

            - the notes mostly agree but need a tighter title, narrower scope, or merged source pointers
            - the evidence is promising but still too rough for a stable shared rule
            - different drafts describe the same lesson at different levels of detail
            """
        ).strip()
        + "\n",
        f"{AI_WIKI_CONSOLIDATE_DRAFTS_SKILL_DIR}/references/output-contract.md": dedent(
            """
            # Output Contract

            Use this structure:

            ```markdown
            # AI Wiki Draft Consolidation

            ## Draft Clusters

            ### Cluster 1: <short title>

            Source drafts:
            - ai-wiki/people/<handle>/drafts/<file>.md

            Existing memory checked:
            - ai-wiki/conventions/<file>.md

            Suggested action:
            - Keep draft | Refine draft | Promotion candidate | Conflict | Supersession

            Suggested target:
            - <path or n/a>

            Why:
            - <short reason>

            Weak signals considered:
            - <metrics or trail signal, or `None`>

            Human confirmation:
            - Required | Not required
            ```

            Keep each cluster short and actionable. Prefer a few strong clusters over a long inventory of nearly identical notes.
            """
        ).strip()
        + "\n",
        f"{AI_WIKI_CONSOLIDATE_DRAFTS_SKILL_DIR}/agents/openai.yaml": dedent(
            """
            interface:
              display_name: "AI Wiki Consolidate Drafts"
              short_description: "Cluster draft notes into next actions"
              default_prompt: "Use $ai-wiki-consolidate-drafts to cluster related AI wiki drafts and propose the next refinement, promotion, conflict, or supersession actions."
            """
        ).strip()
        + "\n",
        f"{AI_WIKI_CLARIFY_BEFORE_CODE_SKILL_DIR}/SKILL.md": dedent(
            """
            ---
            name: ai-wiki-clarify-before-code
            description: Use before implementation when a request is ambiguous enough that coding directly may create wrong behavior, wrong tests, wrong API shape, wrong data model, wrong permission behavior, or wrong long-term team memory.
            ---

            # AI Wiki Clarify Before Code

            Use this skill before implementation when a request is ambiguous enough that coding directly may create wrong behavior, wrong tests, wrong API shape, wrong data model, wrong permission behavior, or wrong long-term team memory.

            Do not ask generic questions just to be safe. Ask only questions that materially affect implementation.

            ## Workflow

            1. Read the task.
            2. Read relevant AI wiki context:
               - `ai-wiki/conventions/index.md`
               - `ai-wiki/decisions.md`
               - `ai-wiki/review-patterns/index.md`
               - `ai-wiki/problems/index.md`
               - `ai-wiki/features/index.md` when feature context matters
            3. Identify known constraints.
            4. Identify blocking unknowns.
            5. Identify non-blocking assumptions.
            6. Decide whether the agent is ready to code.
            7. Propose wiki updates only for durable learnings.

            ## Output Contract

            Use the output format in [references/output-contract.md](references/output-contract.md).

            ## Rules

            - Do not treat inferred assumptions as confirmed requirements.
            - Do not block coding on unknowns that do not affect implementation.
            - Prefer 3-5 high-impact questions over a long generic questionnaire.
            - If new information conflicts with existing AI wiki memory, flag it in the workflow.
            - If a clarification becomes durable, propose a feature note, decision, convention, or problem-solution memory.
            """
        ).strip()
        + "\n",
        f"{AI_WIKI_CLARIFY_BEFORE_CODE_SKILL_DIR}/references/ambiguity-categories.md": dedent(
            """
            # Ambiguity Categories

            Use these categories to decide whether a coding task needs clarification.

            ## Behavior

            What should the feature actually do? What are edge cases?

            ## Data Model

            Are new fields, tables, states, enums, or migrations required?

            ## API Contract

            What are inputs, outputs, error codes, compatibility rules?

            ## Permissions

            Who can do this? Who cannot? What data can they see?

            ## Failure Modes

            What happens on failure, retry, partial success, invalid input, external dependency failure?

            ## Existing Conventions

            Does the repo already have a pattern, convention, or decision that should be reused?

            ## UX / User-Facing Text

            Does exact copy or user-visible behavior matter?

            ## Performance / Scale

            Does data volume, latency, async processing, pagination, batching, or streaming change implementation?

            ## Testing Expectation

            Which behavior must be tested? Are there known flaky patterns to avoid?

            ## Rollout / Migration

            Does this affect existing data, old users, old APIs, or migration behavior?

            ## Important

            Do not ask all categories every time. Ask only the questions that block safe implementation.
            """
        ).strip()
        + "\n",
        f"{AI_WIKI_CLARIFY_BEFORE_CODE_SKILL_DIR}/references/output-contract.md": dedent(
            """
            # Clarify Before Code Output Contract

            ## Current Understanding

            Briefly state what the agent thinks the task is.

            ## Known Constraints

            List confirmed constraints that can guide implementation.

            ## Blocking Unknowns

            List only unknowns that affect implementation structure, behavior, data model, permissions, API, tests, rollout, or long-term memory.

            ## Non-Blocking Assumptions

            List assumptions that can be used temporarily if the user accepts them.

            For each assumption:

            - Assumption:
            - Impact if wrong:

            ## Ready To Code?

            Answer one of:

            - Yes
            - No
            - Yes, if these assumptions are accepted

            Explain why.

            ## Suggested Questions

            Ask the minimum useful questions.

            ## Proposed AI Wiki Updates

            Only include durable updates.

            Possible types:

            - feature requirement candidate
            - decision candidate
            - convention candidate
            - review pattern candidate
            - problem-solution memory
            - person preference
            - open question
            """
        ).strip()
        + "\n",
        f"{AI_WIKI_CLARIFY_BEFORE_CODE_SKILL_DIR}/references/wiki-update-rules.md": dedent(
            """
            # Wiki Update Rules

            A clarification should become AI wiki memory only if it is likely to help future coding tasks.

            ## Store as feature memory when

            - it clarifies behavior or acceptance criteria for a specific feature
            - it records a blocking unknown
            - it records a non-obvious assumption accepted for implementation

            ## Store as decision when

            - it changes architecture, product behavior, data model, API contract, or durable process

            ## Store as convention when

            - it is a reusable team rule

            ## Store as person preference when

            - it reflects a specific person's preference and is not yet clearly team-wide

            ## Store as problem-solution memory when

            - it prevents repeating a debugging or implementation mistake

            ## Do not store when

            - it is one-off implementation detail
            - it is obvious from the code
            - it is temporary scratch
            - it cannot plausibly help a future agent
            """
        ).strip()
        + "\n",
        f"{AI_WIKI_CLARIFY_BEFORE_CODE_SKILL_DIR}/agents/openai.yaml": dedent(
            """
            interface:
              display_name: "AI Wiki Clarify Before Code"
              short_description: "Clarify ambiguous coding tasks before implementation"
              default_prompt: "Run the clarify-before-code workflow for this task and decide whether it is ready to code."
            """
        ).strip()
        + "\n",
        f"{AI_WIKI_CAPTURE_REVIEW_LEARNING_SKILL_DIR}/SKILL.md": dedent(
            """
            ---
            name: ai-wiki-capture-review-learning
            description: Use when the user provides PR review feedback, code review comments, or reviewer preferences that may be reusable.
            ---

            # AI Wiki Capture PR Review Learning

            Use this skill when the user provides PR review feedback, code review comments, or reviewer preferences that may be reusable.

            The goal is not to save every comment. The goal is to preserve feedback that can help future agents avoid repeated review issues.

            ## Workflow

            1. Read the review comment.
            2. Identify reviewer, reviewer role, and scope if available.
            3. Classify the feedback.
            4. Decide whether it is reusable.
            5. Check existing AI wiki memory for related conventions, review patterns, decisions, problems, and person preferences.
            6. Propose the smallest useful wiki update.
            7. If the feedback conflicts with existing memory, flag the conflict instead of silently overwriting.
            8. Prefer draft or person preference first unless promotion criteria are met.

            ## Important Rules

            - A single review comment should not automatically become a team convention.
            - If the reviewer is an owner or tech lead for that area, it may be a stronger convention candidate.
            - If the same feedback appears repeatedly, suggest promotion.
            - If it refines an existing convention, update the convention with history.
            - If it only applies to the current code, mark it as one-off and do not store.
            """
        ).strip()
        + "\n",
        f"{AI_WIKI_CAPTURE_REVIEW_LEARNING_SKILL_DIR}/references/classification.md": dedent(
            """
            # PR Review Learning Classification

            ## One-Off Fix

            Applies only to the current diff.

            Example:
            "Rename this variable to match the API response."

            ## Person Preference

            Reflects a reviewer's preference but is not yet a team-wide rule.

            Example:
            "Carol prefers precise Python type hints and dislikes casual `object`."

            ## Team Convention Candidate

            A reusable rule that may apply broadly.

            Example:
            "Prefer `str | None` over `object` when the possible return values are known."

            ## Review Pattern Candidate

            A repeated review issue.

            Example:
            "Do not update generated prompt blocks manually."

            ## Decision Candidate

            A durable tradeoff or product or architecture choice.

            Example:
            "We will make imports partial-success instead of all-or-nothing."

            ## Problem-Solution Memory

            A reusable debugging or implementation lesson.

            Example:
            "Async notification tests are flaky unless using the fake queue."

            ## Not Reusable

            Too local, obvious, or unlikely to help future tasks.
            """
        ).strip()
        + "\n",
        f"{AI_WIKI_CAPTURE_REVIEW_LEARNING_SKILL_DIR}/references/output-contract.md": dedent(
            """
            # PR Review Learning Output Contract

            ## Review Comment

            Quote or summarize the feedback.

            ## Classification

            - Type:
            - Reusable:
            - Scope:
            - Suggested target:

            ## Proposed Memory

            ### Person Preference

            If applicable.

            ### Team Convention Candidate

            If applicable.

            ### Review Pattern Candidate

            If applicable.

            ### Decision Candidate

            If applicable.

            ### Problem-Solution Memory

            If applicable.

            ## Conflict Check

            - No conflict found

            or

            - Potential conflict:
            - Suggested resolution:

            ## Source Pointer

            - Actor:
            - Actor Role:
            - Context:
            - Quote:
            - Captured By:
            - Captured At:
            - Scope:

            ## Next Action

            Choose one:

            - Do not store
            - Store as personal draft
            - Propose promotion candidate
            - Update existing convention
            - Ask user for confirmation
            """
        ).strip()
        + "\n",
        f"{AI_WIKI_CAPTURE_REVIEW_LEARNING_SKILL_DIR}/references/promotion-rules.md": dedent(
            """
            # Promotion Rules

            Review feedback can move through these levels:

            ## Level 1: Person Preference

            A reviewer preference tied to one person.

            Store under:

            - `ai-wiki/people/<handle>/drafts/`
            - or update that person's page if the repo uses person pages directly

            ## Level 2: Team Convention Candidate

            A possible shared rule.

            Store as a draft or candidate under:

            - `ai-wiki/conventions/`
            - or mention it in a draft until human confirmation

            ## Level 3: Active Team Convention

            A confirmed team-wide rule.

            Promote only when at least one is true:

            - the reviewer is the relevant owner or tech lead
            - the same preference appears repeatedly
            - the user explicitly says "remember this as a team rule"
            - the feedback refines an existing convention
            - the PR discussion clearly accepts it as reusable guidance

            ## Avoid Over-Promotion

            - Do not turn every review comment into a repo-wide rule.
            - Always preserve scope.
            """
        ).strip()
        + "\n",
        f"{AI_WIKI_CAPTURE_REVIEW_LEARNING_SKILL_DIR}/references/conflict-check.md": dedent(
            """
            # Conflict Check

            Before adding or updating memory, check whether the new learning conflicts with:

            - `ai-wiki/conventions/`
            - `ai-wiki/review-patterns/`
            - `ai-wiki/decisions.md`
            - `ai-wiki/features/`
            - `ai-wiki/problems/`
            - relevant person preferences

            ## If conflict is found

            Do not silently overwrite.

            Output:

            - Existing memory
            - New feedback
            - Why they conflict or appear to conflict
            - Suggested resolution
            - Whether this is a refinement, scope difference, or true contradiction

            ## Example

            Existing convention:
            Use `object` for truly opaque external payloads.

            New feedback:
            Avoid `object`; use `str | None` when possible.

            Resolution:
            This is not a full contradiction. Refine the convention:
            - use the narrowest known type when values are known
            - use structured types such as `Mapping[str, Any]` for JSON-like payloads
            - reserve `object` for truly opaque Python objects
            """
        ).strip()
        + "\n",
        f"{AI_WIKI_CAPTURE_REVIEW_LEARNING_SKILL_DIR}/agents/openai.yaml": dedent(
            """
            interface:
              display_name: "AI Wiki Capture PR Review Learning"
              short_description: "Classify and store reusable PR review feedback"
              default_prompt: "Run the capture-review-learning workflow for this review feedback and propose the smallest useful AI wiki update."
            """
        ).strip()
        + "\n",
    }


def prompt_block_body() -> str:
    return dedent(
        """
        ## AI Wiki Toolkit

        If this repository contains `ai-wiki/`, read `ai-wiki/_toolkit/system.md` before starting work and follow its end-of-task workflow. Use `ai-wiki/index.md` as the repo-owned map when you need navigation.
        """
    ).strip()


def default_opencode_config() -> dict[str, object]:
    return {
        "schemaVersion": 1,
        "managedBy": "ai-wiki-toolkit",
    }
