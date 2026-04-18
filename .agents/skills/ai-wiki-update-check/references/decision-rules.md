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
