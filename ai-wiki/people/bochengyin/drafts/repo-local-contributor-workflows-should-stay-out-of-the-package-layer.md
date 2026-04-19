---
title: "Repo-local contributor workflows should stay out of the package layer"
author_handle: "bochengyin"
model: "unknown"
source_kind: "review"
status: "draft"
created_at: "2026-04-19T13:58:00Z"
updated_at: "2026-04-19T13:58:00Z"
promotion_candidate: false
promotion_basis: "none"
---
# Review Draft

## Context

We wanted a helper for this repository's PR flow: create a PR, rebase-merge it, delete the branch, and switch back to `main` locally.

The first implementation started to add a new module under `src/ai_wiki_toolkit/`, which would have turned a repository-specific contributor workflow into a distributed package feature.

## What Went Wrong

The workflow belonged to this repository's collaboration rules, not to `ai-wiki-toolkit` as an end-user product feature.

Putting it in `src/ai_wiki_toolkit/` would have made the package own behavior that only this repository needs.

## Bad Example

- Add a new `src/ai_wiki_toolkit/*.py` module for a workflow that only contributors to this repository use.
- Document that workflow in package-facing README or scaffold behavior.
- Treat repo-specific merge habits as if they should be shipped to downstream users.

## Fix

For contributor workflows that are only needed in this repository:

- keep the helper under `scripts/`
- document the flow in `ai-wiki/workflows.md`
- optionally reference it from `AGENTS.md` or repo-local skills if agents should follow it
- keep `src/ai_wiki_toolkit/` reserved for actual toolkit functionality that downstream users should install

## Reuse Assessment

This should generalize to other tool repositories that mix a distributed package with their own contributor workflow automation.

## Promotion Decision

Keep as a draft until we reuse the same boundary in at least one more repo-specific workflow helper.
