# Toolkit Managed System Rules

This file is managed by ai-wiki-toolkit. Future package versions may update it.

## Start Of Task

1. Read `ai-wiki/_toolkit/index.md`.
2. Read `ai-wiki/index.md`.
3. Read `ai-wiki/conventions/index.md` for shared team conventions that should guide implementation.
4. Read `ai-wiki/decisions.md` for durable project decisions and tradeoffs.
5. Read `ai-wiki/review-patterns/index.md` for reusable review rules and reviewer expectations.
6. Read `ai-wiki/problems/index.md` before implementing or testing similar behavior.
7. Read `ai-wiki/features/index.md` when task-specific requirements, assumptions, or acceptance criteria matter.
8. Read `ai-wiki/workflows.md` for repo-specific workflows that extend the managed baseline.
9. Read `ai-wiki/trails/index.md` when debugging chronology or dead ends may help.
10. Read `ai-wiki/people/<handle>/index.md` when continuing draft work.
11. If repo docs are not enough, read `<home>/ai-wiki/system/_toolkit/system.md` and then `<home>/ai-wiki/system/index.md`.
12. If `ai-wiki-clarify-before-code` is available, use it before implementation when ambiguity materially affects coding.
13. If `ai-wiki-capture-review-learning` is available, use it when reusable review feedback appears.
14. If `ai-wiki-reuse-check` and `ai-wiki-update-check` skills are available, use them for end-of-task AI wiki checks.

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
   - `PromotionCandidate`: you recorded or updated a draft, the two-signal gate is satisfied, and human confirmation is still required before creating `ai-wiki/review-patterns/*.md` or `ai-wiki/conventions/*.md`.
3. Check whether the task produced:
   - a new or refined team convention
   - reusable PR review learning
   - feature requirement clarification
   - a durable decision note
   - a reusable problem-solution memory
   - a conflict, refinement, or supersession with existing memory
   - a person preference that should stay personal for now
4. Prefer small durable memory over long task transcripts or generic summaries.
5. If new memory conflicts with existing conventions, decisions, features, problems, or person preferences, flag it as a conflict, refinement, or supersession instead of silently overwriting.
6. Always print exactly one final status line:
   - `AI Wiki Update Candidate: None`
   - `AI Wiki Update Candidate: Draft`
   - `AI Wiki Update Candidate: PromotionCandidate`
7. If the outcome is `Draft` or `PromotionCandidate`, also print:
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
