---
title: "Route precision experiments should separate forward routing from historical metrics"
author_handle: bochengyin
model: codex
source_kind: implementation_note
status: draft
created_at: 2026-06-04
updated_at: 2026-06-04
promotion_candidate: false
promotion_basis: "Single implementation pass; useful as local working memory before promoting."
---

# Route Precision Experiments Should Separate Forward Routing From Historical Metrics

## Problem

`aiwiki-toolkit eval impact route-noise report` summarizes historical route traces and downstream reuse events. A scorer change will not retroactively improve the reported precision or noise rate until new routes are recorded and later paired with reuse evidence.

Route experiments can also pollute the metric they are trying to inspect if exploratory route commands are run without `--no-record-trace`.

## Preferred Pattern

Use `aiwiki-toolkit route --task "<task>" --format json --no-record-trace` for scorer smoke tests. Inspect `task_type`, `risk_tags`, selected cards, and `route_quality_adjustment` before claiming an improvement.

Use the historical route-noise report to identify noisy doc patterns and missed-useful hotspots, but treat precision/noise changes as forward-looking until new post-change tasks have reuse events.

When a dirty worktree is present, do not let implicit `git status` paths drive routing for a specific task. Pass explicit `--changed-path` only when the path should influence task classification, risk tags, and document scoring.
