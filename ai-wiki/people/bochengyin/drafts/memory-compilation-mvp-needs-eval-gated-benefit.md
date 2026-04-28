---
title: "Memory compilation MVP needs eval-gated benefit"
author_handle: "bochengyin"
model: "gpt-5"
source_kind: "feature_clarification"
status: "draft"
created_at: "2026-04-27T23:03:11+1000"
updated_at: "2026-04-27T23:03:11+1000"
promotion_candidate: false
promotion_basis: "none"
---
# Draft

## Context

While discussing `memory-compilation-mvp`, the user challenged the assumption that compiling stable
Markdown into agent assets is automatically better than reading the original wiki notes.

That challenge is important because prior impact eval work already showed that more polished or
consolidated guidance can underperform a task-specific raw draft when it loses the exact boundary
signal the agent needed.

## Clarification

Treat memory compilation as a product hypothesis, not as an inherently better representation.

The MVP should prove benefit through diagnostic comparisons before claiming improvement:

- baseline AI wiki workflow with normal routing and runtime document reads
- compiled assets only
- raw source notes only when relevant
- raw plus compiled assets when useful for diagnosis

Compiled output is better only when it preserves source provenance and improves at least one
task-relevant outcome without causing a correctness regression.

Useful acceptance signals include:

- fewer repeated implementation-surface mistakes
- fewer missed mandatory workflow or constraint steps
- lower active agent time or lookup overhead after accounting for source incident cost
- lower context noise for simple tasks
- equal or better final task correctness compared with raw source notes
- clear source paths and hashes so compiled guidance can be audited and regenerated

## Implication

The first implementation should keep compiled assets generated, cited, and disposable. Markdown
remains the source of truth. If compiled assets are stale, too abstract, or less task-specific than
the source notes, the route should prefer the source references or report the conflict instead of
silently trusting the compiled form.

## Reuse Assessment

Use this when scoping `memory-compilation-mvp`, designing compile output, or interpreting evals that
compare compiled assets against raw AI wiki notes.
