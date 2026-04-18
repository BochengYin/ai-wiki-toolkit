# Toolkit Managed System Rules

This file is managed by ai-wiki-toolkit. Future package versions may update it.

## Start Of Task

1. Read `ai-wiki/index.md`.
2. Read `ai-wiki/review-patterns/` before implementation or review work.
3. Read `ai-wiki/people/<handle>/drafts/` when continuing draft work.
4. If repo docs are not enough, read `<home>/ai-wiki/system/_toolkit/system.md` and then `<home>/ai-wiki/system/index.md`.

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
