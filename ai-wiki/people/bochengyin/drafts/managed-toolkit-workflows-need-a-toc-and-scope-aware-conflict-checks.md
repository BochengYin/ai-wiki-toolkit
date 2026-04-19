---
title: "Managed toolkit workflows need a TOC and scope-aware conflict checks"
author_handle: "bochengyin"
model: "unknown"
source_kind: "review"
status: "draft"
created_at: "2026-04-19T22:30:00+1000"
updated_at: "2026-04-19T22:30:00+1000"
promotion_candidate: false
promotion_basis: "none"
---
# Review Draft

## Context

We wanted package upgrades to ship new baseline workflow guidance without rewriting user-owned repo docs such as `ai-wiki/workflows.md`.

At the same time, once managed workflow docs existed alongside repo-owned workflow docs, the toolkit needed a reliable way to detect same-scope duplication without treating normal repo-vs-home overlap as an error.

## What Went Wrong

The earlier structure had no managed TOC under `ai-wiki/_toolkit/`, so prompt wiring and navigation had to point directly at individual managed files.

That makes future system-level expansion awkward because every new managed document needs prompt and starter changes in multiple places.

The earlier workflow guidance also lived only in user-owned `ai-wiki/workflows.md`, which meant package upgrades could not deliver new baseline workflow rules without violating the no-touch compatibility contract.

## Bad Example

- Put upgradeable baseline workflow rules directly in `ai-wiki/workflows.md`.
- Treat `ai-wiki/_toolkit/system.md` as both the rules doc and the long-term TOC for every managed file.
- Warn on every repo-vs-home duplicate rule even when that overlap is expected and harmless.

## Fix

Create a managed TOC at `ai-wiki/_toolkit/index.md` and route prompt startup through that stable entrypoint.

Move package-managed baseline workflow guidance into `ai-wiki/_toolkit/workflows.md`.

Keep `ai-wiki/workflows.md` user-owned and point it at the managed baseline instead of rewriting it during upgrades.

In `doctor`, treat same-scope duplicates or conflicts as actionable, but ignore cross-scope duplicates and downgrade cross-scope conflicts to informational findings where repo-local guidance wins.

## Reuse Assessment

This looks reusable for any AI wiki setup that mixes package-managed guidance with repo-owned overlays.

The TOC pattern keeps managed navigation extensible, and the scope-aware conflict model avoids turning normal repo-vs-home overlap into noisy failures.

## Promotion Decision

Keep as a draft for now. Promote if the same managed-TOC plus scope-aware-conflict pattern proves useful in another repository or after another round of workflow expansion under `_toolkit/`.
