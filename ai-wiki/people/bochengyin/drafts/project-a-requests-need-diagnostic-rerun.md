---
title: "Project A requests need a diagnostic rerun"
author_handle: "bochengyin"
model: "gpt-5"
source_kind: "user_correction"
status: "draft"
created_at: "2026-06-03T21:21:50+1000"
updated_at: "2026-06-04T07:02:00+1000"
promotion_candidate: false
promotion_basis: "single user correction"
---
# Draft

## Context

After asking to "do Project A" for the coding-agent eval harness, the user clarified that a docs-only
portfolio artifact was not enough. They expected the agent to rerun the relevant local tests and
diagnostics, then explain concrete optimization opportunities.

## Lesson

When the user asks to do or strengthen Project A, treat the request as an evidence-refresh task, not
only a documentation task.

Default to running:

- `uv run pytest`
- `npm pack --dry-run --ignore-scripts` from the repo root
- `aiwiki-toolkit eval impact families --format json`
- `aiwiki-toolkit eval impact schedule report --format json`
- `aiwiki-toolkit evaluate repo --since 30d --format json --no-write`
- relevant memory diagnostics such as `diagnose memory --focus route`
- `git diff --check`

Then report the current bottlenecks and claim boundaries. If a full Codex slot benchmark rerun is
not performed, say that explicitly and distinguish it from normal local automated tests.

## 2026-06-04 Refinement

After rubrics and run index coverage are fixed, Project A diagnostics should inspect recent
successful `score_policy=rubric` runs before recommending another benchmark rerun. If every runnable
family already has a recent successful rubric run, the next optimization should shift to:

- route precision/noise before adding more memory
- neutral benchmark families that show no treatment lift
- runner observability, especially per-slot elapsed time, timeout, and heartbeat artifacts for long
  Codex slots

## Reuse Assessment

Use this when responding to future Project A or coding-agent-eval-harness requests in this repo.
The expected output is a test-backed diagnostic and optimization view, not just a nicer portfolio
write-up.
