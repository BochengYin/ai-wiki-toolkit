---
title: "AI wiki reuse metrics should exclude managed docs and shard logs by handle"
author_handle: "bochengyin"
model: "unknown"
source_kind: "review"
status: "draft"
created_at: "2026-04-19T21:48:57+1000"
updated_at: "2026-05-20T23:31:05+1000"
promotion_candidate: true
promotion_basis: "Auto-marked from useful resolved reuse threshold; exact evidence is generated under ai-wiki/_toolkit/reports/promotion-candidates/latest.md."
promotion_report: "ai-wiki/_toolkit/reports/promotion-candidates/latest.md"
---
# Review Draft

## Context

We tightened the new AI wiki reuse metrics workflow after noticing two distortions.

First, managed `_toolkit/**` docs were being counted as successful reuse events even though they mostly represent control-plane instructions rather than reusable project knowledge.

Second, all evidence was still flowing into shared top-level JSONL files, which would create avoidable merge conflicts when multiple teammates or agents append metrics on separate branches.

## What Went Wrong

The first version treated every consulted AI wiki path as equally valid for usefulness metrics.

That inflated the signal because almost every compliant task will touch `_toolkit/system.md`, even when no user-owned project knowledge actually helped.

It also used shared append-only logs as a single write target, which makes collaboration noisy and fragile.

## Bad Example

- Log `_toolkit/system` as a successful reuse event.
- Use the same append-only `reuse-events.jsonl` file for the entire team.
- Merge generated aggregate JSON files by hand instead of regenerating them from source logs.

## Fix

Treat managed `_toolkit/**` docs as workflow controls, not knowledge-reuse evidence.

When those docs affect behavior, cite their paths in progress notes or final notes, but do not record them with `record-reuse`.

Write user-owned reuse evidence to per-handle shards such as:

- `ai-wiki/metrics/reuse-events/<handle>.jsonl`
- `ai-wiki/metrics/task-checks/<handle>.jsonl`

Then regenerate package-managed aggregate views from those shards when branches drift or conflict.

## Reuse Assessment

This pattern should apply to any repo that wants trustworthy AI memory metrics in a collaborative git workflow.

It preserves a cleaner usefulness signal while also reducing conflicts on append-only evidence files.

## 2026-05-20 Generated View Refinement

The same conflict-avoidance rule should apply to generated `_toolkit/**` views when those views depend on a user or agent handle.

Team-facing split:

- shared source-of-truth: repo-owned Markdown, package-managed `_toolkit` control docs, and explicit per-handle source logs such as `ai-wiki/metrics/reuse-events/<handle>.jsonl`, `ai-wiki/metrics/task-checks/<handle>.jsonl`, and `ai-wiki/work/events/<handle>.jsonl`
- local generated views: reports, diagnostics, promotion evidence, usefulness reports, weekly reports, and handle-filtered metrics

Generated views that depend on a handle should write under handle-scoped paths such as:

- `ai-wiki/_toolkit/metrics/by-handle/<handle>/`
- `ai-wiki/_toolkit/diagnostics/<handle-or-all>/`
- `ai-wiki/_toolkit/consolidation/<handle>/`
- `ai-wiki/_toolkit/reports/promotion-candidates/<handle>/`
- `ai-wiki/_toolkit/reports/usefulness/<handle-or-all>/`
- `ai-wiki/_toolkit/reports/weekly/<handle>/`

Global generated aggregates can still exist for explicit local refreshes, but frequent per-task writes should prefer handle-scoped outputs so multiple teammates do not churn the same generated files.

## Promotion Decision

Keep as a draft for now. Promote if the same distinction between control-plane docs and reusable knowledge proves useful in another repository or if sharded metrics logs clearly reduce merge friction across multiple teams.
