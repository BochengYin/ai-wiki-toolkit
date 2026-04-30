---
title: "Neutral impact eval runs need change-profile quality metrics"
author_handle: "bochengyin"
model: "gpt-5.5"
source_kind: "task"
status: "draft"
created_at: "2026-04-30T20:08:00+10:00"
updated_at: "2026-04-30T20:08:00+10:00"
promotion_candidate: false
promotion_basis: "none"
---
# Draft

## Context

The `postinstall_archive_staging` impact eval produced a neutral first-attempt result: all six
slots fixed the npm postinstall bug successfully.

The useful difference was not success rate. It was quality and churn:

- exact target memory kept the implementation to the same project-file footprint as the no-AI-wiki
  control
- no-target and no-adjacent variants rewrote the known lesson as new user-owned drafts
- one diagnostic variant broadened the project surface by touching an extra npm wrapper file
- AI wiki workflow naturally produced managed telemetry, which should not be confused with
  user-owned wiki churn

## Lesson

Impact eval product reports should not stop at `success`, `partial`, and `fail`.

When a run is neutral on success rate, report change-profile metrics that distinguish:

- project files outside `ai-wiki/`
- managed AI wiki telemetry under `ai-wiki/_toolkit/` and `ai-wiki/metrics/`
- user-owned AI wiki files such as drafts, conventions, problems, features, trails, and personal notes

This lets the report say whether AI wiki memory helped reduce extra implementation surface or
repeat writeback churn even when every variant passed.

## Reuse Assessment

Use this when interpreting future eval product reports, especially narrow bug-replay families where
the prompt and code are direct enough for every condition to succeed.

The change-profile signal should support a narrower claim than success-rate uplift: memory may help
with fix quality, repeated-lesson avoidance, or less user-owned wiki churn.
