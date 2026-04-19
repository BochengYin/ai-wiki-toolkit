---
title: "AI wiki reuse metrics should exclude managed docs and shard logs by handle"
author_handle: "bochengyin"
model: "unknown"
source_kind: "review"
status: "draft"
created_at: "2026-04-19T21:48:57+1000"
updated_at: "2026-04-19T21:48:57+1000"
promotion_candidate: false
promotion_basis: "none"
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

## Promotion Decision

Keep as a draft for now. Promote if the same distinction between control-plane docs and reusable knowledge proves useful in another repository or if sharded metrics logs clearly reduce merge friction across multiple teams.
