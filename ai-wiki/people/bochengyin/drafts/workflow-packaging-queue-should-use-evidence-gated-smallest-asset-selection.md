---
title: "Workflow packaging queue should use evidence-gated smallest asset selection"
author_handle: "bochengyin"
model: "gpt-5"
source_kind: "feature_clarification"
status: "draft"
created_at: "2026-05-27T09:48:34+10:00"
updated_at: "2026-06-01T20:51:31+1000"
promotion_candidate: false
promotion_basis: "none"
---
# Draft

## Context

The user compared `ai-wiki-toolkit` with a prompt that asks Codex to inspect recent sessions,
memories, Chronicle, and existing skills or automations, then package only repeated manual
workflows that are stable, recurring, valuable, and not already covered.

This overlaps with the current AI wiki roadmap around consolidation, memory compilation, workflow
state, and cross-agent adapters, but it sharpens the product shape: the useful output is not a
generic "make more skills" feature. It is an evidence-backed shortlist that decides whether each
candidate should become a skill, custom subagent, automation, extension of existing assets, or an
explicit skip.

## Product Implication

Add this as a narrow workflow-packaging review surface after diagnostics and consolidation are
stable.

The first useful shape is a generated queue, not an automatic asset writer:

- collect evidence from local Codex session exports, AI wiki reuse events, task checks, route traces,
  work ledger items, and existing AI wiki drafts
- optionally ingest external sources such as Chronicle as discovery-only evidence
- compare candidates against installed repo-local skills, cross-project system memory, existing
  automations, and planned work
- emit a shortlist with evidence dates, recurrence, confidence, recommended form, and skip reasons
- create only high-confidence missing assets, with provenance and a validation command

## 2026-06-01 Workflow And Skill Refinement

Workflow, skill, subagent, and automation should be treated as different asset forms, not as a strict
maturity ladder where workflow is always "below" skill.

Both workflows and skills can guide an agent through a repeatable problem. The distinction is mainly
the operating surface:

- A workflow is a transparent process contract or coordination guide. It is useful when humans,
  multiple agents, or multiple tools need to share the same steps, review points, and completion
  criteria.
- A skill is a runtime-packaged capability with discovery metadata, activation rules, instructions,
  and optionally scripts or assets. It is useful when a bounded task has stable triggers and a stable
  input/output contract in an agent runtime that can invoke skills.
- A workflow can call one or more skills, and a skill can implement one step of a workflow. Neither
  form is inherently more advanced.

The packaging queue should therefore recommend the smallest appropriate representation for the
observed evidence: keep as note, write or extend a workflow, create or extend a skill, propose a
subagent, propose an automation, or skip. The recommendation should be based on use case, evidence,
runtime portability, and review burden rather than on an assumed promotion hierarchy.

## 2026-05-27 Dogfood Evidence

A prompt-style audit over available local evidence sharpened the distinction between the external
prompt and `ai-wiki-toolkit`.

Available evidence for this checkout:

- Codex state showed 23 `ai-wiki-toolkit` threads in the last 30 days.
- Session titles clustered around route/startup/prompt behavior, memory lifecycle research,
  eval/usefulness, install identity/naming, and release operations.
- Codex ambient suggestions for this repo contained 83 pending items, including roughly 30 eval
  suggestions, 25 route/startup/prompt suggestions, 10 install/unit naming suggestions, 9 release
  suggestions, 7 memory lifecycle suggestions, and 2 workflow-state suggestions.
- `diagnose memory --since 30d` reported 178 checked tasks, 637 reuse events, 67 route traces, and
  59 documents with reuse.
- Route diagnostics showed high recall but noisy selection: recall proxy around 0.81, precision
  around 0.34, and route noise around 0.66.
- `consolidate queue --since 30d` found 49 drafts and 10 consolidation queue items.

This suggests the prompt's core value is discovery, but its weak point is governance. It can notice
repeated work, but without a repo-native evidence model it easily creates a large backlog of
candidate suggestions that still need triage, provenance, deduplication, and validation.

`ai-wiki-toolkit` is stronger where it turns memory into an explicit supply chain:

1. start-of-task routing instead of relying on the user to remember a meta-prompt
2. append-only reuse, task-check, route-trace, source-incident, and work ledgers
3. generated diagnostics and consolidation queues instead of direct shared-doc rewrites
4. human-confirmed promotion gates for durable shared memory
5. eval surfaces that can test whether memory or compiled assets improve real work

The next product opportunity is to add a packaging queue that sits after diagnostics and before
asset creation. It should treat Codex sessions, ambient suggestions, Chronicle, and existing skills
as candidate evidence, then decide whether to skip, extend, or generate the smallest useful asset.

## Guardrails

- Do not auto-create broad or speculative skills from one-off work.
- Do not treat Chronicle or other ambient history as authoritative when source-system confirmation is
  available.
- Do not duplicate existing skills, wiki docs, or automations; prefer extension when the existing
  surface is adequate.
- Keep generated queues under `_toolkit/**`; write user-owned docs only through explicit draft or
  promotion flows.
- Eval-gate any compiled skill, subagent, or automation against repeated workflow outcomes before
  making it part of the default install experience.

## Reuse Assessment

Use this when scoping memory compilation, cross-agent adapters, or any feature that turns repeated
work history into executable agent assets.

Keep as a draft until at least one prototype proves that the queue produces useful narrow assets
without increasing prompt noise or shared-doc churn.
