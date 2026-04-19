---
title: "AI wiki usefulness metrics need task-level checks plus document-level events"
author_handle: "bochengyin"
model: "unknown"
source_kind: "review"
status: "draft"
created_at: "2026-04-19T21:33:32+1000"
updated_at: "2026-04-19T21:33:32+1000"
promotion_candidate: false
promotion_basis: "none"
---
# Review Draft

## Context

We wanted to productize AI wiki usefulness tracking instead of relying on ad hoc commentary or optional manual logging.

The existing `record-reuse` flow could append per-document reuse events, but it still left a critical blind spot: there was no task-level record showing whether a completed task had been checked for AI wiki reuse at all.

## What Went Wrong

Document-level events alone provide only a numerator.

They can show which docs were reused, but they cannot distinguish between:

- a task that used no AI wiki docs after a real check
- a task that never performed the check

That makes adoption and usefulness hard to measure honestly.

## Bad Example

- Only append `reuse-events.jsonl` entries when a reused doc is obvious.
- Treat the absence of reuse events as evidence that the AI wiki was not useful.
- Omit any task-level confirmation that the reuse check actually happened.

## Fix

Use two layers of evidence:

- one document-level reuse event per consulted AI wiki doc
- one task-level reuse check for every completed task, even when no wiki docs were used

This creates both provenance and coverage. The document events show what was reused, while the task checks provide the denominator needed to judge whether the AI wiki is actually helping in practice.

## Reuse Assessment

This looks reusable for any repo that wants to measure AI wiki usefulness rather than just accumulate anecdotes.

The same pattern should apply anywhere agents are expected to consult durable repo memory but the team also wants auditable evidence that the workflow was followed.

## Promotion Decision

Keep as a draft for now. Promote if the same measurement gap appears again in another repo or if task-level reuse checks prove consistently useful across multiple agent workflows.
