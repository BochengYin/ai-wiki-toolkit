# Ownership Boundary Runbook

This document describes how to reproduce the current `ownership_boundary` manual impact eval and
how the generated repos differ before any prompt is run.

## Goal

Measure whether AI wiki memory changes where an agent places a contributor-only branch-and-PR
helper.

The intended good outcome is:

- repo-local helper under `scripts/`
- matching tests under `tests/`
- optional update to `ai-wiki/workflows.md`
- no new implementation under `src/ai_wiki_toolkit/`

## Historical Trigger

This benchmark is backsolved from the repo's real branch-and-merge workflow discussion. The user
request that motivated the original workflow said, in effect:

- contributors should not merge from `main`
- the repo should require starting from a feature branch
- after merge, local state should return to `main`
- AI wiki is the right place to record and reinforce that workflow

This benchmark intentionally reuses that original problem shape instead of inventing a synthetic
"ownership boundary" toy task.

The task-specific raw draft for the placement mistake is:

- `ai-wiki/people/bochengyin/drafts/repo-local-contributor-workflows-should-stay-out-of-the-package-layer.md`

## Baseline

All variants are generated from the historical git ref:

- `34cd5a3^`

That baseline predates the later repo-local helper work such as:

- `scripts/pr_flow.py`
- `tests/test_pr_flow_script.py`

Using this baseline avoids leaking the intended implementation surface into every variant.

## Generation Script

Workspace generation is defined in:

- `evals/impact/scripts/prepare_variants.py`

Important defaults:

- source mode: committed git snapshot, not the current working tree
- experiment family: `ownership_boundary`
- baseline ref: `34cd5a3^`

This means local uncommitted eval scaffolding and scratch notes do not leak into the generated
experiment repos.

## Variant Setup

All variants start from the same historical baseline. The only intended differences are the AI wiki
surface and which memory files are present.

### plain_repo_no_aiwiki

Removed:

- `ai-wiki/`
- repo-shared managed AI wiki block from `AGENTS.md`
- `.agents/skills/ai-wiki-*`

Meaning:

- no AI wiki scaffold
- no AI wiki prompts
- no AI wiki skills

### aiwiki_no_relevant_memory

Keeps the AI wiki scaffold, but removes the memory files relevant to this benchmark.

Removed raw drafts:

- `ai-wiki/people/bochengyin/drafts/user-owned-ai-wiki-index-should-not-be-an-upgrade-surface.md`
- `ai-wiki/people/bochengyin/drafts/repo-local-contributor-workflows-should-stay-out-of-the-package-layer.md`
- `ai-wiki/people/bochengyin/drafts/managed-toolkit-workflows-need-a-toc-and-scope-aware-conflict-checks.md`

Removed consolidated docs:

- `ai-wiki/conventions/package-managed-vs-user-owned-docs.md`
- `ai-wiki/review-patterns/shared-prompt-files-must-be-user-agnostic.md`

Removed index entries:

- `ai-wiki/conventions/index.md` entry for `package-managed-vs-user-owned-docs.md`
- `ai-wiki/review-patterns/index.md` entry for `shared-prompt-files-must-be-user-agnostic.md`

### aiwiki_raw_drafts

Starts from `aiwiki_no_relevant_memory`, then adds back only the raw drafts:

- `ai-wiki/people/bochengyin/drafts/user-owned-ai-wiki-index-should-not-be-an-upgrade-surface.md`
- `ai-wiki/people/bochengyin/drafts/repo-local-contributor-workflows-should-stay-out-of-the-package-layer.md`
- `ai-wiki/people/bochengyin/drafts/managed-toolkit-workflows-need-a-toc-and-scope-aware-conflict-checks.md`

No consolidated shared docs are added back.

### aiwiki_consolidated

Starts from `aiwiki_no_relevant_memory`, then adds back only the adjacent consolidated docs:

- `ai-wiki/conventions/package-managed-vs-user-owned-docs.md`
- `ai-wiki/review-patterns/shared-prompt-files-must-be-user-agnostic.md`

And re-adds their index entries:

- `ai-wiki/conventions/index.md`
- `ai-wiki/review-patterns/index.md`

Important: these are adjacent ownership/prompt-stability docs, not direct promotions of the
repo-local PR workflow placement draft.

### aiwiki_raw_plus_consolidated

Includes both:

- the three raw drafts
- the two consolidated shared docs
- the two index entries

## Active Prompts

Prompt family:

- `evals/impact/prompts/ownership_boundary/`

Task description:

- `evals/impact/prompts/ownership_boundary/TASK.md`

Active prompt levels:

- `short.md`
- `medium.md`

Retired:

- `full.md`

### short

Contains only the task requirement:

- add a helper for the contributor branch-and-PR workflow
- require branch-first work instead of direct work on `main`
- require return to `main` after merge
- require branch names:
  - `feature/YYYY_MM_DD_description`
  - `chore/YYYY_MM_DD_description`
  - `fix/YYYY_MM_DD_description`

### medium

Adds exactly one extra scope boundary:

- this is contributor workflow behavior for this repository
- it is not a distributed `ai-wiki-toolkit` product feature

## Manual Protocol

For each variant:

1. Open the workspace in a fresh Codex session.
2. Paste `short.md` or `medium.md`.
3. Let the agent work normally.
4. Save the result with:
   - `evals/impact/scripts/save_result.py`
5. After all runs, aggregate with:
   - `evals/impact/scripts/report_runs.py`

Important controls:

- one fresh session per variant
- same selected model across variants if possible
- same prompt text within a comparison set
- save artifacts outside the experiment repos

## Model And Sampling Notes For The Current Runs

The currently saved `short` and `medium` runs were executed manually with:

- execution surface: Codex subscription sessions, not direct API calls
- model family: `gpt-5.4`
- reasoning effort: `xhigh` / extra high

These settings were manually held constant by the operator. They are not yet captured as verified
fields inside `result.json`.

Because these runs were done through subscription sessions rather than direct API requests, the
operator did not have exposed request knobs for parameters such as temperature or seed.

What is not currently recorded by the harness:

- exact session metadata exported from the Codex UI

So current conclusions should be treated as manually controlled comparisons, not as fully
instrumented deterministic replays.

## Manual Scoring Rubric

Use this rubric when assigning a post-run label.

### Success

All of the following are true:

- the implementation stays out of `src/ai_wiki_toolkit/`
- the run adds a repo-local helper under `scripts/`
- the run adds matching helper tests under `tests/`
- the run documents the workflow in an appropriate local surface for that variant
- the run does not add obvious unrelated product-surface churn

### Partial

The run gets the main boundary partly right but still has notable issues, for example:

- it stays out of `src/ai_wiki_toolkit/` but updates a less appropriate doc surface
- it adds the helper and tests correctly but introduces avoidable doc churn
- it mixes strong repo-local behavior with weaker secondary choices that would likely need review

### Fail

Any of the following is enough for failure:

- new implementation under `src/ai_wiki_toolkit/`
- new package CLI wiring for this contributor-only workflow
- no repo-local helper added
- no matching tests added
- the change clearly treats the workflow as distributed product behavior

## Current Saved Runs

### Short run

- workspace root:
  - `/private/tmp/aiwiki_first_round/ownership_boundary/workspaces/20260423-115153`
- run dir:
  - `/private/tmp/aiwiki_first_round/ownership_boundary/runs/20260423-115153`
- report:
  - `/private/tmp/aiwiki_first_round/ownership_boundary/runs/20260423-115153/report.md`

### Medium run

- workspace root:
  - `/private/tmp/aiwiki_first_round/ownership_boundary/workspaces/20260423-170541`
- run dir:
  - `/private/tmp/aiwiki_first_round/ownership_boundary/runs/20260423-170541`
- report:
  - `/private/tmp/aiwiki_first_round/ownership_boundary/runs/20260423-170541/report.md`

## What The Diffs Actually Contained

Across the current runs, the changed files fall into a small set of surfaces:

- repo-local helper scripts under `scripts/`
- helper tests under `tests/`
- local workflow docs under `ai-wiki/workflows.md`
- extra repo docs churn such as `CONTRIBUTING.md`, `README.md`, or `CHANGELOG.md`
- in the problematic `short` cases, package code under `src/ai_wiki_toolkit/`

The helper implementations consistently included some form of:

- branch-name validation with a regex for `feature|chore|fix/YYYY_MM_DD_description`
- commands for start / push / finish or after-merge
- safety checks around current branch and clean worktree

The package-surface failures usually looked like:

- `src/ai_wiki_toolkit/contributor_workflow.py`
- optional CLI wiring in `src/ai_wiki_toolkit/cli.py`

The repo-local successes usually looked like:

- `scripts/contributor_pr_workflow.py`
- `scripts/contributor_pr.py`
- matching `tests/test_*.py`
- optional update to `ai-wiki/workflows.md`

## Threats To Validity

- This is still a manual experiment, not an automated benchmark.
- The harness does not currently record the actual selected model or reasoning effort inside the
  saved run artifacts.
- The observed runs were executed with GPT-5.4 at extra-high reasoning, but that is currently a
  user-controlled condition rather than an automatically verified field in `result.json`.
- No temperature or seed is captured here.
- Current evidence is from one task family and one run per variant/prompt level.

## Interpretation Guardrails

- Treat `short` as the more informative memory-sensitivity run.
- Treat `medium` as the stronger test of whether one explicit boundary sentence can suppress the
  package-surface failure mode.
- Do not claim that the current consolidated docs are generally harmful. The strongest justified
  claim is narrower:
  adjacent consolidated guidance can underperform, or interfere with, a task-specific raw draft in
  this benchmark.
- Do not describe the current consolidated variant as a direct consolidation of the PR-workflow
  placement lesson. In this experiment it contains adjacent shared docs:
  - `ai-wiki/conventions/package-managed-vs-user-owned-docs.md`
  - `ai-wiki/review-patterns/shared-prompt-files-must-be-user-agnostic.md`
  Those are related boundary docs, but they are not direct promotions of
  `ai-wiki/people/bochengyin/drafts/repo-local-contributor-workflows-should-stay-out-of-the-package-layer.md`.
