---
title: "Feedback diagnosis MVP should start as an explicit generated report"
author_handle: "bochengyin"
model: "unknown"
source_kind: "feature_clarification"
status: "draft"
created_at: "2026-04-28T23:52:00+10:00"
updated_at: "2026-04-28T23:52:00+10:00"
promotion_candidate: false
promotion_basis: "none"
---
# Draft

## Context

The `feedback-diagnosis-report` roadmap item asks the toolkit to diagnose missed, stale, noisy, conflicting, and high-ROI AI wiki memory.

The implementation choice was whether to make diagnosis an explicit user-run tool or run it inside every agent task.

## Clarification

Start with an explicit command:

```bash
aiwiki-toolkit diagnose memory
```

Runtime agent workflow should stay lightweight. It should record evidence such as reuse events, task-level reuse checks, and route traces when those traces exist. The heavier synthesis should happen in a generated report under `ai-wiki/_toolkit/diagnostics/`.

## Reason

Memory diagnosis needs a cross-task view. Running it inside every agent task would add latency and noise, and could encourage shared file churn during normal feature work.

An explicit generated report keeps Markdown as the source of truth, uses per-handle append-only evidence logs, and lets humans inspect maintenance recommendations when they need them.

## Follow-Up

The current MVP reads reuse and task-check evidence. A later version can add route trace evidence so the report can distinguish:

- route selected memory that was never used
- memory that was useful but not selected
- docs that are repeatedly recommended but not helpful

## Reuse Assessment

Use this when extending feedback diagnosis, adding route trace logging, or deciding whether to move a diagnosis behavior into the default agent runtime.
