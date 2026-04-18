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
