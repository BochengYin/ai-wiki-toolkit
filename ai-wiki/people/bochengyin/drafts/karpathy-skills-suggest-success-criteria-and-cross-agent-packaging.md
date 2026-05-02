---
title: "Karpathy skills suggest success criteria and cross-agent packaging"
author_handle: "bochengyin"
model: "gpt-5"
source_kind: "external_reference"
status: "draft"
created_at: "2026-05-02T22:07:03+1000"
updated_at: "2026-05-02T22:17:32+1000"
promotion_candidate: false
promotion_basis: "none"
---
# Draft

## Context

The `forrestchang/andrej-karpathy-skills` repo packages a small set of coding-agent behavioral guardrails as multiple runtime surfaces:

- a Claude Code plugin manifest
- a reusable `SKILL.md`
- a root `CLAUDE.md`
- a Cursor rule
- examples that contrast common agent failure modes with preferred behavior

The content is not a memory system. Its useful signal for `ai-wiki-toolkit` is packaging and product shape: small operational guidance can be made portable across agent runtimes when the same source idea is exposed through adapter-specific artifacts.

## Product Implication

Two ideas are worth testing for `ai-wiki-toolkit`:

1. Route packets and workflow-state surfaces should make success criteria and verification plans explicit for non-trivial tasks. The current route packet selects relevant memory; it does not yet help the agent turn the task into a verifiable goal.
2. Memory compilation should target small, provenance-backed runtime assets such as skill templates, Cursor rules, or Claude-style plugin bundles, not only larger context summaries.

## Implementation Outcome

The first concrete step was a conservative route-packet MVP:

- `aiwiki-toolkit route` now emits generated `success_criteria` alongside memory routing fields.
- Text output renders a `Success Criteria` section before index cards.
- Managed route schema docs identify the criteria as generated planning guidance, not canonical memory.
- Cross-agent generated assets remain future work and should still be eval-gated before becoming a broader `memory-compilation-mvp` feature.

## Guardrails

Do not copy the external repo's content wholesale into user-owned AI wiki docs.

Do not treat compiled agent assets as canonical memory. Stable Markdown remains the source of truth, and generated runtime assets should be disposable, cited, and eval-gated.

Do not add every generic coding principle to the package layer by default. Keep optional cross-agent assets focused on reducing repeated AI wiki workflow mistakes or repo-specific failure modes.

## Reuse Assessment

Use this when scoping:

- `memory-compilation-mvp`
- cross-agent adapters
- route packet success criteria
- generated agent assets under managed or disposable paths

Keep as a draft until a concrete prototype proves that generated success criteria or cross-agent packaged assets improve task outcomes without adding prompt noise.
