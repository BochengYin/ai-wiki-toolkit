---
title: "Impact eval result capture must include untracked files"
author_handle: "bochengyin"
model: "gpt-5"
source_kind: "problem"
status: "draft"
created_at: "2026-04-23T12:56:00+1000"
updated_at: "2026-04-23T12:56:00+1000"
promotion_candidate: false
promotion_basis: "none"
---
# Problem Draft

## Context

While reviewing saved artifacts for the `ownership_boundary` impact experiment, we noticed that
`save_result.py` had captured only tracked modifications. The saved `workspace_status.txt` showed
new files such as `scripts/contributor_pr_workflow.py`, but `workspace_diff.patch`,
`workspace_diff_stat.txt`, and `result.json` did not include them.

That made the stored run artifacts incomplete and understated what the agent had actually changed.

## What Went Wrong

The capture logic relied on:

- `git diff --binary`
- `git diff --stat`
- `git diff --name-only`

Those commands ignore untracked files by default. As a result:

- new files were visible in `git status --short`
- but their contents were missing from the saved patch
- and `changed_files` undercounted the actual workspace delta

For impact-eval analysis, that is a real problem because many agent runs create new helper scripts
or new tests instead of only editing tracked files.

## Fix

When capturing eval artifacts:

1. keep the tracked diff from `git diff`
2. separately enumerate untracked files with `git ls-files --others --exclude-standard`
3. append a `git diff --no-index /dev/null <path>` patch for each untracked file
4. append corresponding `--stat` output
5. include untracked paths in `changed_files`
6. record them explicitly under a dedicated `untracked_files` field in `result.json`

After this change, saved artifacts reflect the full workspace state that the agent produced, not
just tracked edits.

## Reuse Assessment

Keep this as a draft for now.

Promote if we hit the same issue again in another eval family or if we standardize artifact capture
rules across multiple manual benchmark runners.
