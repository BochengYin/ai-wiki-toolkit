---
title: "Trial-error reduction should extend memory diagnostics"
author_handle: "bochengyin"
model: "gpt-5.5"
source_kind: "feature_clarification"
status: "draft"
created_at: "2026-04-29T23:26:10+1000"
updated_at: "2026-04-29T23:26:10+1000"
promotion_candidate: false
promotion_basis: "none"
---
# Draft

## Context

While discussing `eval-as-product-mvp`, we clarified that `trial_and_error_reduction` is not
primarily a new benchmark family name. It is a product/evaluation dimension that should first be
derived from existing AI wiki evidence.

## Clarification

The next product slice should extend the explicit diagnosis surface, likely under
`aiwiki-toolkit diagnose memory`, rather than start with a new formal replay family.

The report should inventory existing signals such as:

- reuse events with effects like `avoided_retry`, `blocked_wrong_path`, `changed_plan`, and
  `faster_resolution`
- task-level checks that show whether AI wiki was used for relevant work
- missed-memory incidents where a known doc existed but was not used
- high-ROI memories from `ai-wiki/_toolkit/diagnostics/memory-report.*`
- source incident or rework-cost notes that explain what trial-and-error was avoided

Only after that evidence points to a concrete repeated task shape should the project consider a new
impact-eval family.

## Reuse Assessment

Use this when designing trial/error usefulness reporting, extending feedback diagnosis, or deciding
whether an eval product request should produce a generated evidence report versus a new benchmark
family.
