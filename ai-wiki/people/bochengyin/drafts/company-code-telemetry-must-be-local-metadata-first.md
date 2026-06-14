---
title: "Company code telemetry must be local metadata first"
author_handle: "bochengyin"
model: "gpt-5"
source_kind: "feature_clarification"
status: "draft"
created_at: "2026-06-03T08:44:30+1000"
updated_at: "2026-06-03T09:01:00+1000"
promotion_candidate: false
promotion_basis: "none"
---
# Draft

## Context

The user raised a concern that the externally dogfooded `ai-wiki-toolkit` use is happening on a
company computer and company codebase. Future CLI feedback or evaluation features may be useful, but
they must not accidentally collect or expose company source code.

## Lesson

For company-code use, feedback and evaluation collection should default to local-only,
metadata-first evidence:

- task ids, timestamps, route-selected doc ids, reuse outcomes, and failure taxonomy labels
- command names, exit codes, test pass/fail summaries, and diffstats
- generated reports under gitignored `ai-wiki/_toolkit/**`
- per-handle local telemetry under gitignored `ai-wiki/metrics/**`

Do not collect source text, full patches, raw terminal logs, raw agent transcripts, customer data, or
repository-specific business details by default.

Any feature that exports artifacts, runs an external LLM over evidence, publishes a benchmark, or
captures raw diffs/transcripts should require explicit opt-in and should support redaction or
company-approved endpoints.

## 2026-06-03 Refinement

The user's company already allows large-model usage through approved interfaces. The boundary is
therefore not "never use an LLM on company work." The safer product rule is:

- collect metadata-first local evidence by default
- feed generated reports or sanitized evidence summaries to a configured, company-approved model
  endpoint when the user opts in
- keep raw code, full diffs, raw transcripts, and business data out of the default diagnostic bundle
- make the LLM layer an interpretation step over local evidence, not the source of truth

## 2026-06-03 VS Code Agent Refinement

The user's company workflow runs inside VS Code, where the approved agent/model can already read
repository files directly. In that environment, `ai-wiki-toolkit` does not need to call an LLM API
itself for advisor features.

Prefer an agent-native advisor shape:

- deterministic CLI commands generate local evidence reports
- the VS Code agent reads those reports and relevant AI wiki docs from the repository
- the agent synthesizes recommendations in the normal approved IDE/model workflow
- package code stays model-provider-agnostic

An in-tool LLM provider is only useful for terminal-only or scheduled automation where no IDE agent
is orchestrating the analysis.

## Reuse Assessment

Use this when designing CLI feedback collection, repo evaluation exports, impact-eval artifact
publishing, or any feature that might run on private company code.
