---
title: "End-of-task AI wiki update checks should always run"
author_handle: "bochengyin"
model: "unknown"
source_kind: "review"
status: "draft"
created_at: "2026-04-18T13:18:00Z"
updated_at: "2026-04-18T13:18:00Z"
promotion_candidate: false
promotion_basis: "none"
---
# Review Draft

## Context

We noticed that `AI Wiki Update Candidate: None` was useful precisely because it proved the workflow had been checked, not because it indicated the absence of work. Treating `None` as optional made the whole end-of-task workflow lossy and inconsistent across tasks and agents.

## What Went Wrong

The older prompt wording only described what to do when a lesson existed, and then separately said to print `AI Wiki Update Candidate: None` when no durable pattern was found. That made the check feel optional instead of mandatory.

## Bad Example

- End a task without explicitly deciding whether the outcome is `None`, `Draft`, or `PromotionCandidate`.
- Only mention AI wiki updates when a new draft was written.

## Fix

Make the end-of-task AI wiki update check mandatory for every completed task. Always emit one final status line. If the result is `Draft` or `PromotionCandidate`, also emit the path to the affected note.

## Reuse Assessment

This looks reusable for any repo that wants AI wiki maintenance to behave like an explicit workflow rather than an ad hoc reminder. A repo-level prompt contract should enforce the check; an optional skill can standardize how the check is performed.

## Promotion Decision

Keep as a draft for now. This should be promoted only after the same enforcement pattern proves useful in at least one more repository or review cycle.
