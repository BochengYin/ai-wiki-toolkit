---
name: ai-wiki-update-check
description: Produce the mandatory end-of-task AI wiki update outcome for ai-wiki-toolkit. Use it to detect durable memory candidates, decide whether the result is None, Draft, or PromotionCandidate, and emit the required final status line.
---

# AI Wiki Update Check

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

- Do not skip the update outcome just because no durable lesson is expected.
- Do not treat "no wiki docs were opened" as proof that no durable memory was produced.
- Do not create or update `ai-wiki/review-patterns/*.md` without human confirmation.
- Keep project-specific knowledge in `ai-wiki/`.
- Keep cross-project knowledge in `<home>/ai-wiki/system/`.
