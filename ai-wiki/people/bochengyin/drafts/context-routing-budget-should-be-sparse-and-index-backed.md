---
title: "Context routing budget should be sparse and index-backed"
author_handle: "bochengyin"
model: "gpt-5"
source_kind: "design"
status: "draft"
created_at: "2026-04-27T21:05:00+10:00"
updated_at: "2026-04-27T21:18:00+10:00"
promotion_candidate: false
promotion_basis: "none"
---
# Review Draft

## Context

While discussing `context-routing-v2`, we clarified that the route packet budget should not mean "fill the packet up to 900 words every time."

The budget is a cap and allocation policy for task-relevant memory, not a target to exhaust. It may not need to be a prominent user-facing concept at all; if kept, `budget_words` should behave more like a high safety threshold than a normal tuning knob.

## Design Clarification

Routing should prefer sparse, high-signal packets:

- include only memory likely to affect the current task
- leave unused budget unused when the task is simple
- provide links and load reasons for lower-confidence or deep reference files
- avoid turning every route packet into a large memory dump

For large AI wiki collections, routing should use an index/card layer before loading full documents. The shape is similar to skills:

- stable name or title
- short description
- doc kind and scope
- applies-when or routing hints
- link to the full reference document

The index/card layer may be generated or checked by the toolkit so user-owned indexes do not become package upgrade surfaces.

The preferred retrieval shape is:

1. present all relevant index cards with short descriptions and reference links
2. let the acting agent open the referenced document at runtime when the card is clearly relevant
3. keep the packet focused on required workflow or constraint material plus pointers

For simple operational tasks, such as pushing or finishing an already-decided PR, route should choose a low-effort path and point to the specific workflow rather than loading broad memory.

## Runtime Concern

As AI wiki file counts grow, route runtime matters, but this should not become a complex product-visible "hot path" concept. Mandatory behavior belongs in `workflows.md`, `constraints.md`, or other authoritative docs. Everything else can be handled by AI over lightweight index/card metadata first, with full references loaded only on demand.

## Implication

`context-routing-v2` should treat budgeted memory selection as:

1. choose candidate memory from lightweight index/card metadata first
2. include required workflow or constraint material directly when it is mandatory
3. provide short descriptions and reference links for the rest
4. let the agent load full documents at runtime when needed
5. avoid making `budget_words` drive packet filling

This keeps route packets useful for small tasks while still supporting large-document tasks through staged retrieval.
