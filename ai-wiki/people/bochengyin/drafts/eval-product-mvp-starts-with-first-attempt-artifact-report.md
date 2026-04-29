---
title: "Eval product MVP starts with first-attempt artifact report"
author_handle: "bochengyin"
model: "gpt-5.5"
source_kind: "task"
status: "draft"
created_at: "2026-04-29T21:47:41+1000"
updated_at: "2026-04-29T22:09:31+1000"
promotion_candidate: false
promotion_basis: "none"
---
# Draft

## Context

While turning `eval-as-product-mvp` into code, the product question was whether AI wiki should
evaluate by explicitly comparing no-AI-wiki and AI-wiki first attempts, or by running diagnosis in
the agent runtime.

## Lesson

The first product slice should be an artifact-driven report over existing captured runs:

- read `metadata.json`, `result.json`, `score.json`, and `confounds.json` from a run directory
- compare the primary variants, normally `no_aiwiki_workflow` and
  `aiwiki_ambient_memory_workflow`
- grade only `first_pass` captures as the first-attempt product signal
- keep `final` repair captures diagnostic
- report success rate, score, attempts, human nudges, changed files, untracked files, and causal
  claim readiness
- avoid auto-running agents or making saved-time claims before the capture artifacts contain the
  required duration/source-incident fields

This keeps the MVP product surface useful without hiding eval assumptions inside runtime behavior.

## Implementation Follow-Up

After adding the package command, the release path should also smoke-test the installed package
manager binary against a real captured run. A repo-local helper can verify that the shipped
`aiwiki-toolkit` exposes `eval impact report`, can emit the JSON schema, and can write markdown/json
reports outside the run directory.

That post-release check belongs in the eval harness, not inside the package runtime.

## Reuse Assessment

Use this when extending the eval product beyond report generation. Add automation for preparing or
running eval families only after the artifact report remains stable enough to make the measured
signal explicit.

## Promotion Decision

Keep as a draft for now. Promote only if another eval product feature repeats the same
artifact-first boundary.
