---
title: "Adjacent consolidated guidance can underperform task-specific raw drafts in impact evals"
author_handle: "bochengyin"
model: "gpt-5"
source_kind: "problem"
status: "draft"
created_at: "2026-04-23T13:08:00+1000"
updated_at: "2026-04-23T13:08:00+1000"
promotion_candidate: false
promotion_basis: "none"
---
# Problem Draft

## Context

We ran the `ownership_boundary` impact eval with five variants:

- `plain_repo_no_aiwiki`
- `aiwiki_no_relevant_memory`
- `aiwiki_raw_drafts`
- `aiwiki_consolidated`
- `aiwiki_raw_plus_consolidated`

The benchmark asked the agent to add a helper for contributor branch-and-PR workflow behavior
without directly naming the intended implementation surface.

## What Happened

The `aiwiki_raw_drafts` variant produced the cleanest result:

- it added a repo-local helper under `scripts/`
- it added a repo-local test
- it updated repo-local workflow guidance
- it did not also add a package-facing implementation under `src/ai_wiki_toolkit/`

By contrast, the `aiwiki_consolidated` and `aiwiki_raw_plus_consolidated` variants still wrote
new implementation into `src/ai_wiki_toolkit/`, even though those variants had more polished or
more abundant AI wiki memory available.

## Why This Matters

This means “having consolidated memory” is not automatically better than having raw drafts.

If the consolidated memory is only adjacent and abstract, while the raw draft names the exact
boundary mistake that the task is about, the raw draft can be the stronger steer. In this run, the
raw draft about repo-local contributor workflows staying out of the package layer was more useful
than nearby consolidated ownership docs that were valid but less task-specific.

## Fix

When evaluating consolidation value:

1. do not assume consolidated docs should always outperform raw drafts
2. check whether the promoted or shared guidance preserved the task-specific boundary signal
3. if the raw draft keeps winning, that may indicate the repo is missing a better consolidated
   review pattern or convention for that exact mistake cluster
4. judge consolidated quality not only by readability, but by whether it still helps the agent
   choose the correct implementation surface

## Reuse Assessment

Keep as a draft for now.

Promote if the same “adjacent consolidated guidance underperforms a task-specific raw draft”
pattern appears in another benchmark family besides ownership-boundary experiments.
