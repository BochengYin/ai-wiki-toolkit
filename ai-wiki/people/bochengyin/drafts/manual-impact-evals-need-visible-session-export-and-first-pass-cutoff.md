---
title: "Manual impact evals need visible session export and first-pass cutoff"
author_handle: "bochengyin"
model: "unknown"
source_kind: "task"
status: "draft"
created_at: "2026-04-24T21:35:00+10:00"
updated_at: "2026-04-24T21:35:00+10:00"
promotion_candidate: false
promotion_basis: "none"
---
# Draft Note

## Context

While documenting the first manual impact-eval round for `ownership_boundary` and
`release_distribution_integrity`, we reviewed both the saved run artifacts and the exported visible
Codex sessions.

That review showed a recurring evaluation-process gap:

- the task prompt itself could be clean and match the benchmark guide
- but the full visible prompt surface could still differ through `AGENTS.md`, workspace paths,
  `cwd`, and skill availability
- and a later user follow-up such as `code` could overwrite what looked like a final-message
  artifact even though the real first substantive closeout happened earlier

## What Went Wrong

Diff capture alone was not enough to judge fairness or correctness.

The saved `final_message.md` also turned out to be weaker than expected for manual UI-based runs,
because it could reflect a later follow-up rather than the original closeout.

That means a manual impact eval can look cleaner than it really is if it only preserves:

- the final diff
- the changed-file list
- a final-message snapshot

## Fix

For manual subscription-session impact evals:

- always export visible session traces for the workspace set
- compare the benchmark task prompt against the full visible prompt surface
- treat `final_message.md` as optional convenience output, not as the source of truth
- freeze a first-pass cutoff artifact before any later follow-up such as `code`
- grade the run from diff plus visible transcript plus changed tests, not from `report.md` or
  final-message text alone

## Reuse Assessment

This should generalize to future manual agent evals in this repo and likely to other UI-driven
benchmark workflows where the operator does not control the session transcript as tightly as an API
request log.

## Promotion Decision

Keep as a draft for now.

Promote if the same first-pass cutoff/session-export rule is needed in another benchmark family or
if the eval harness formalizes it into shared process guidance.
