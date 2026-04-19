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
