---
title: "PR flow finish needs rebase sync after local main was ahead"
author_handle: "bochengyin"
model: "gpt-5"
source_kind: "problem"
status: "draft"
created_at: "2026-05-02T00:17:27+1000"
updated_at: "2026-05-02T00:17:27+1000"
promotion_candidate: false
promotion_basis: "none"
---
# Problem Draft

## Context

A publish-and-merge task started while local `main` was already ahead of `origin/main`.

The topic branch was created from that local `main`, pushed, opened as a pull request, and merged
through GitHub with rebase merge.

## What Happened

`scripts/pr_flow.py finish` successfully merged the pull request and deleted the remote topic branch,
but its final `git pull --ff-only origin main` step failed.

After GitHub rebase merge, remote `main` contained patch-equivalent commits with different SHAs.
Local `main` still had the original local commits, so Git reported `main...origin/main` as ahead and
behind even though `git log --left-right --cherry-pick main...origin/main` showed no unique patches.

Running `git pull --rebase origin main` skipped the already-applied local commits and aligned local
`main` with `origin/main`.

## Why This Matters

This is an easy edge case to hit when an agent inherits commits already made on local `main` and then
correctly moves them onto a topic branch for PR review.

The helper's normal fast-forward sync assumes local `main` does not also contain the pre-merge commit
SHAs. That assumption breaks after GitHub rebase merge rewrites or recreates equivalent commits on the
remote base branch.

## Fix

When `scripts/pr_flow.py finish` fails at `git pull --ff-only origin main` after a successful rebase
merge, check whether the divergence is patch-equivalent:

```bash
git log --left-right --cherry-pick --oneline main...origin/main
```

If there are no unique patches and the worktree is clean, use:

```bash
git pull --rebase origin main
```

This preserves the intended remote history and drops the duplicate local patch-equivalent commits.

## Reuse Assessment

Keep as a draft until this exact local-main-ahead PR handoff happens again or the helper is updated to
handle it automatically.
