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

## Runtime Skill Fallback

1. Repo-local AI wiki skills live under `.agents/skills/<skill-name>/`.
2. Runtime skill discovery can differ from files on disk. If a needed AI wiki skill is not exposed by the active runtime, manually read `.agents/skills/<skill-name>/SKILL.md` and relevant files under `.agents/skills/<skill-name>/references/`.
3. For end-of-task reuse evidence, if `ai-wiki-reuse-check` is unavailable, read `.agents/skills/ai-wiki-reuse-check/SKILL.md` and `.agents/skills/ai-wiki-reuse-check/references/output-contract.md`.
4. For end-of-task write-back, if `ai-wiki-update-check` is unavailable, read `.agents/skills/ai-wiki-update-check/SKILL.md` and `.agents/skills/ai-wiki-update-check/references/output-contract.md`.
5. Do not skip the required AI wiki footer just because the runtime reports no available skills.

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
