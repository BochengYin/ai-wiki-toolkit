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
