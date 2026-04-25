---
title: "Workflow-primary impact evals compare working modes"
author_handle: "bochengyin"
model: "unknown"
source_kind: "task"
status: "draft"
created_at: "2026-04-25T00:25:00+10:00"
updated_at: "2026-04-25T00:42:00+10:00"
promotion_candidate: false
promotion_basis: "none"
---
# Draft Note

## Context

While redesigning the `ai-wiki-toolkit` impact eval flow, we clarified that the main product
question is not whether one individual AI wiki document causes a better answer.

The main question is whether an AI wiki working mode helps agents make fewer repeated mistakes
when a repo problem that was previously discovered and recorded appears again.

## Lesson

Use workflow-primary framing for this eval family:

- primary comparison: no AI wiki workflow versus AI wiki workflow with realistic ambient memory
- diagnostic comparisons: scaffold without target memory, linked raw drafts, and linked
  consolidated docs
- ambient memory can include adjacent or noisy docs because that is part of the real AI wiki
  working mode
- linked consolidated docs should only be used to judge consolidation quality when they derive
  from the same problem family
- run the original historical prompt only for workflow-primary claims; avoid `medium`-style
  prompts that directly name the answer boundary, because they measure prompt following instead of
  memory reuse

This avoids overclaiming that a single consolidated doc is the product, while still letting the
harness explain whether raw drafts, consolidated docs, scaffold effects, or ambient noise drove the
observed result.

## Reuse Assessment

Use this when designing or interpreting future AI wiki impact eval families.

It applies when the research question is "does this repo memory workflow reduce repeated agent
mistakes?" rather than "does this exact document cause the outcome?"

## Promotion Decision

Keep as a draft until another benchmark family needs the same workflow-primary versus diagnostic
split, or a reviewer asks to promote it into shared eval design guidance.
