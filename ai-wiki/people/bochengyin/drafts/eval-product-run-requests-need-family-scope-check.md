---
title: "Eval product run requests need evidence scope check"
author_handle: "bochengyin"
model: "gpt-5.5"
source_kind: "task"
status: "draft"
created_at: "2026-04-29T23:03:45+1000"
updated_at: "2026-04-29T23:21:16+1000"
promotion_candidate: false
promotion_basis: "none"
---
# Draft

## Context

After running `eval-as-product-mvp` locally, the report used the existing five captured impact-eval
families. The follow-up clarified that a product theme such as trial-and-error reduction should
first be grounded in existing AI wiki evidence, not automatically turned into a new benchmark family.

## Lesson

When asked to "run the eval product MVP," separate four scopes before reporting results:

- evidence inventory from existing AI wiki drafts, reuse events, diagnostics, and other toolkit
  reports
- report smoke over existing captured `run/` artifacts
- formal rerun of already-defined families
- design and execution of a new family, only after the evidence inventory shows a concrete repeated
  task shape worth replaying

If the user names a product theme such as trial-and-error, first search existing evidence surfaces:

- `ai-wiki/metrics/reuse-events/<handle>.jsonl` for effects such as `avoided_retry`
- `ai-wiki/_toolkit/diagnostics/memory-report.md` for high-ROI, missed, noisy, stale, or conflicting
  memory
- relevant drafts such as `efficiency-eval-should-include-source-incident-cost`
- public/report docs that already summarize repeated mistakes and source incident cost

Only then check whether a corresponding family exists under `evals/impact/families/`, whether
captured runs exist under the artifact directories, or whether a new family should be proposed.

## Reuse Assessment

Use this when interpreting future eval-product requests so the answer does not imply that generating
a report over old artifacts is the same as evaluating a product theme, and does not imply that a
product theme must start as a new family instead of an evidence-backed report over existing AI wiki
signals.
