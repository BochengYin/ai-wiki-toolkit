---
title: "AI wiki usefulness metrics need task-level checks plus document-level events"
author_handle: "bochengyin"
model: "unknown"
source_kind: "review"
status: "draft"
created_at: "2026-04-19T21:33:32+1000"
updated_at: "2026-05-20T23:07:26+1000"
promotion_candidate: true
promotion_basis: "Auto-marked from useful resolved reuse threshold; exact evidence is generated under ai-wiki/_toolkit/reports/promotion-candidates/latest.md."
promotion_report: "ai-wiki/_toolkit/reports/promotion-candidates/latest.md"
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

## Weekly Report Product Refinement

Weekly usefulness reports should not lead with saved-time estimates until those estimates are backed by a separate impact-eval artifact. The safer default report should show:

- how many eligible user-owned Markdown files were referenced in the report period
- how many eligible user-owned Markdown files were not referenced
- which personal drafts have useful resolved reuse and should be suggested for human-approved promotion
- which personal drafts are repeatedly referenced but often partial or not helpful and should be diagnosed or rewritten

Promotion suggestions should remain suggestions. The toolkit can identify candidates, propose a target such as `conventions/`, `problems/`, `features/`, or `review-patterns/`, and provide evidence, but a human should approve the actual shared-memory promotion.

`not_helpful` and missed-memory signals should not be treated as automatically knowable truth. They require an explicit human or agent judgment after the task. Route traces can suggest possible misses, but the report should label those as possible until a user, reviewer, or task outcome confirms the miss.

To make noisy-memory diagnosis useful, future reuse logs should preserve provenance:

- the session or task id that originally generated a personal draft
- the session id for later resolved, partial, or not_helpful reuse
- a structured reason for not_helpful outcomes, such as stale, too generic, wrong scope, missing detail, hard to find, or contradicted by later evidence

This lets the toolkit compare the source memory-generation context against later failed reuse contexts and suggest whether to promote, rewrite, split, merge, archive, or add examples.

## Automated Diagnosis Refinement

The toolkit can infer candidate `not_helpful` and candidate missed-memory signals, but those should be separate from confirmed outcomes.

For example, if an agent reads document A, then continues searching, reads document B, and only B appears to drive the final fix, A can be marked as `candidate_not_helpful` or `superseded_by_later_doc`. That is useful automation, but it is not proof that A had no value; A may have narrowed scope or prevented a wrong path.

A post-task review agent can help, especially when token use is gated by human approval. Prefer a staged workflow:

- collect task prompt, final diff/result, route packet, consulted docs, reuse events, and available session ids
- retrieve a bounded candidate set from the AI wiki index/catalog first
- optionally scan all user-owned AI wiki files only when the user asks, a task failed, a user corrected the agent, or weekly diagnosis flags repeated noisy memory
- emit suggestions such as `possible_missed_doc`, `candidate_not_helpful`, `promotion_candidate`, or `needs_rewrite`
- require human confirmation before writing confirmed missed-memory or not_helpful outcomes

This keeps automation useful without treating a costly retrospective scan as ground truth.

## 2026-05-20 Weekly HTML UX Refinement

The user rejected the weekly HTML report as too dashboard-like and asked for only "self-involving" data.

Refine the product rule:

- the weekly HTML view should be a human review queue, not a full analytics dashboard
- show only items that need human judgment: promotion candidates, personal drafts needing diagnosis, and not_helpful signals
- keep coverage, referenced-file, unreferenced-file, and raw evidence data in JSON or supporting reports instead of the HTML page
- do not display saved-time estimates in the weekly HTML view

This supersedes the earlier HTML-display suggestion that the default weekly page should show referenced and unreferenced file lists. Those counts may still be useful for diagnostics, but they should stay outside the primary human-facing weekly review page unless the user explicitly asks for an audit view.
