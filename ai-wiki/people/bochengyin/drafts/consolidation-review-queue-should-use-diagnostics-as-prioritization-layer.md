---
title: "Consolidation review queue should use diagnostics as its prioritization layer"
author_handle: "bochengyin"
model: "unknown"
source_kind: "feature_clarification"
status: "draft"
created_at: "2026-04-29T00:24:00+10:00"
updated_at: "2026-04-29T00:24:00+10:00"
promotion_candidate: false
promotion_basis: "none"
---
# Draft

## Context

After implementing `aiwiki-toolkit diagnose memory`, the next roadmap item is `consolidation-review-queue`.

The user clarified that the queue should combine with the draft and memory diagnostics work instead of becoming a separate inventory command.

## Clarification

Use diagnostics as the prioritization layer for consolidation.

The consolidation queue should take signals such as high-ROI memory, stale memory, noisy memory, conflicts, missed-memory notes, and coverage gaps, then turn them into human-reviewable actions:

- keep draft
- refine draft
- promotion candidate
- conflict
- supersession

The queue should not automatically rewrite shared docs. It should generate review items under `_toolkit/` and require human confirmation before writing to `conventions/`, `review-patterns/`, `problems/`, `features/`, or `decisions.md`.

## Implication

The next MVP should extend the explicit generated-report pattern:

```bash
aiwiki-toolkit consolidate queue
```

or a similar command that reads diagnostics plus drafts and emits a generated review queue.

Runtime agents should keep recording evidence. The heavier cluster-and-action synthesis should remain explicit and generated.

## Reuse Assessment

Use this when implementing the consolidation review queue or deciding how diagnostics output should feed memory governance.
