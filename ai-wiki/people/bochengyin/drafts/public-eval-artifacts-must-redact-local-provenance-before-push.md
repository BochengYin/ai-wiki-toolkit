---
title: "Public eval artifacts must redact local provenance before push"
author_handle: "bochengyin"
model: "gpt-5"
source_kind: "problem_solution"
status: "draft"
created_at: "2026-06-06T13:07:34+1000"
updated_at: "2026-06-06T13:07:34+1000"
promotion_candidate: false
promotion_basis: "Observed while preparing route precision and Project A eval artifacts for a public GitHub PR."
---
# Problem Draft

## Context

Generated eval reports can mix reusable research summaries with local provenance details such as
absolute checkout paths, local Codex session IDs, rollout paths, and task prompts that were not meant
for public artifacts.

## What Went Wrong

The route precision cleanup found several commit candidates that looked like normal reports but
contained local paths, source session UUIDs, and a historical external-form prompt. The public-facing
research reports needed to be separated from local replay JSON and sanitized before pushing.

## Preferred Pattern

Before pushing eval/public or eval/report artifacts:

- keep raw replay JSON, local session paths, and full provenance logs ignored or local-only
- redact absolute paths and local session identifiers in committed summaries
- remove job-targeted or external-form context from public research writeups
- make experiment scripts emit redacted provenance references for committed label artifacts
- commit only lightweight manifests, labels, rubrics, summaries, and public reports that are safe to
  read in a public repository

## Reuse Assessment

This should be reused for future eval-as-product and route-quality reports, especially when reports
are generated from local Codex sessions or include recovered historical prompts.
