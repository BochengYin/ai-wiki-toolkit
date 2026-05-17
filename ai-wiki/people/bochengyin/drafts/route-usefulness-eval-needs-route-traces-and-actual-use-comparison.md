---
title: "Route usefulness eval needs route traces and actual-use comparison"
author_handle: "bochengyin"
model: "gpt-5"
source_kind: "feature_clarification"
status: "draft"
created_at: "2026-05-17T18:37:00+10:00"
updated_at: "2026-05-17T18:37:00+10:00"
promotion_candidate: false
promotion_basis: "single route dogfooding signal"
---
# Draft

## Context

When asked how to evaluate whether `route` is useful, the route packet over-weighted dirty worktree path signals and selected local changed-path context. The answer still needed more direct memory about usefulness metrics, feedback diagnosis, and eval product boundaries.

## Lesson

Route usefulness should be evaluated by comparing the route packet against actual downstream use, not by counting selected documents alone.

The key comparison is:

- selected and useful: route helped
- selected but unused or not helpful: route was noisy
- not selected but later used: route missed relevant memory
- selected and changed the plan: high-value route hit

## Metric Gap

The current diagnostics can infer missed, stale, noisy, conflicting, high-ROI, and coverage-gap signals from reuse events and task checks. It cannot yet directly compute route precision or recall because route selection traces are not recorded as first-class evidence.

## Follow-Up

Add route trace evidence so diagnostics can report:

- route-selected docs that were never used
- useful docs that were found outside the route packet
- docs repeatedly selected with `not_helpful` outcomes
- route hits that produced material effects such as `changed_plan`, `avoided_retry`, or `blocked_wrong_path`

## Implementation Shape

Keep route telemetry as a separate append-only evidence stream instead of overloading `record-reuse`.

Suggested first slice:

- add `ai-wiki/metrics/route-traces/<handle>.jsonl`
- add a `route-v1` trace payload with `task_id`, `selected_doc_ids`, `must_load_doc_ids`, `index_card_doc_ids`, `maybe_load_doc_ids`, `skipped_doc_ids`, `changed_paths`, packet word count, selected doc count, and route score metadata
- make `aiwiki-toolkit route` write the trace by default, with `--no-record-trace` for dry runs or tests that need no side effects
- keep `record-reuse` as the downstream actual-use signal, using `retrieval_mode=preloaded` for docs selected by route and `retrieval_mode=lookup` for docs found later
- extend `diagnose memory` to join route traces with reuse events by `task_id`

Derived metrics:

- route precision: useful selected docs divided by selected docs
- route recall proxy: useful selected docs divided by all useful docs for the task
- route noise rate: selected docs with no reuse event or `not_helpful` outcome divided by selected docs
- missed useful docs: useful `lookup` docs that were not in the trace selected set
- context cost: packet word count, selected doc count, index-card count, and lookup count after route
- outcome metrics: reuse effects such as `avoided_retry`, `blocked_wrong_path`, `changed_plan`, and `faster_resolution`

Formal eval metrics should stay in the existing impact-eval artifact layer. Route diagnostics can link to eval run IDs later, but should not infer causal claims from runtime telemetry alone.

## Reuse Assessment

Use this when designing route telemetry, route diagnostics, or route quality metrics.
