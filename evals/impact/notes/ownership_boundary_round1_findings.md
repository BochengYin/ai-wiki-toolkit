# Ownership Boundary Round 1 Findings

This note summarizes the first valid `ownership_boundary` runs after the v0 leakage issue was
fixed.

These findings are now the repo-recorded result summary for this benchmark family.

## Runs

### Short

- report: `/private/tmp/aiwiki_first_round/ownership_boundary/runs/20260423-115153/report.md`

### Medium

- report: `/private/tmp/aiwiki_first_round/ownership_boundary/runs/20260423-170541/report.md`

## Execution Conditions

The saved runs were executed manually under these intended conditions:

- execution surface: Codex subscription sessions, not direct API requests
- model: `gpt-5.4`
- reasoning effort: `xhigh` / extra high

Because these runs were executed through subscription sessions, not the API, temperature and seed
were not operator-exposed controls in this experiment.

Not captured by the current harness:

- exact exported Codex session metadata

So the runs are comparable manual trials, not fully instrumented deterministic samples.

## Manual Scorecard For The 10 Recorded Runs

The following labels are a manual grading pass over the 10 recorded runs:

- 5 `short` variants
- 5 `medium` variants

These labels use the rubric in `evals/impact/ownership_boundary_runbook.md`.

### Short

| variant | manual grade | rationale |
| --- | --- | --- |
| `plain_repo_no_aiwiki` | `fail` | added both `scripts/contributor_workflow.py` and `src/ai_wiki_toolkit/contributor_workflow.py`, so the contributor-only workflow also became package code |
| `aiwiki_no_relevant_memory` | `fail` | added `src/ai_wiki_toolkit/contributor_workflow.py` and `src/ai_wiki_toolkit/cli.py`, turning the workflow into package CLI behavior |
| `aiwiki_raw_drafts` | `success` | stayed in repo-local surfaces, added helper plus tests, and updated local workflow guidance without new `src/` implementation |
| `aiwiki_consolidated` | `fail` | added a repo-local script but still created `src/ai_wiki_toolkit/contributor_workflow.py`, so the main boundary was not preserved |
| `aiwiki_raw_plus_consolidated` | `fail` | again created package-surface implementation and CLI wiring, so the contributor workflow became product behavior |

### Medium

| variant | manual grade | rationale |
| --- | --- | --- |
| `plain_repo_no_aiwiki` | `success` | stayed in repo-local surfaces and added helper plus tests; `CONTRIBUTING.md` is the best available local guidance in the no-AI-wiki variant |
| `aiwiki_no_relevant_memory` | `success` | stayed in repo-local surfaces, added helper plus tests, and updated `ai-wiki/workflows.md` |
| `aiwiki_raw_drafts` | `success` | stayed in repo-local surfaces, added helper plus tests, and updated `ai-wiki/workflows.md` |
| `aiwiki_consolidated` | `partial` | stayed out of `src/`, but the run updated `README.md` rather than the more obviously local contributor docs, so the surface choice was improved but not fully clean |
| `aiwiki_raw_plus_consolidated` | `success` | stayed in repo-local surfaces, added helper plus tests, and updated `ai-wiki/workflows.md` |

## Short Findings

The `short` prompt was the more discriminating run.

### Strongest result

- `aiwiki_raw_drafts`

Observed changed surfaces:

- `README.md`
- `ai-wiki/workflows.md`
- `scripts/contributor_pr_workflow.py`
- `tests/test_contributor_pr_workflow.py`

Key property:

- no new implementation under `src/ai_wiki_toolkit/`

### Boundary failures

`plain_repo_no_aiwiki`

- added both a repo-local script and a package implementation
- changed:
  - `scripts/contributor_workflow.py`
  - `src/ai_wiki_toolkit/contributor_workflow.py`
  - `tests/test_contributor_workflow.py`

`aiwiki_no_relevant_memory`

- drifted into package CLI behavior
- changed:
  - `src/ai_wiki_toolkit/cli.py`
  - `src/ai_wiki_toolkit/contributor_workflow.py`
  - `tests/test_contributor_workflow.py`

`aiwiki_consolidated`

- partially improved, but still wrote package code
- changed:
  - `scripts/contributor_branch_pr.py`
  - `src/ai_wiki_toolkit/contributor_workflow.py`
  - `tests/test_contributor_workflow.py`

`aiwiki_raw_plus_consolidated`

- behaved like the package-feature path again
- changed:
  - `src/ai_wiki_toolkit/cli.py`
  - `src/ai_wiki_toolkit/contributor_workflow.py`
  - `tests/test_contributor_workflow.py`

### Short-run interpretation

The strongest supported statement is:

- in this single `short` run, the raw-drafts-only variant outperformed the plain no-AI-wiki
  baseline and the adjacent-consolidated variants on implementation surface choice

The weaker but still reasonable hypothesis is:

- adjacent consolidated guidance may dilute or interfere with a task-specific raw draft when the
  consolidated docs are not direct promotions of the same failure pattern

Important qualifier:

- the current consolidated variant does not contain a direct promotion of the PR-workflow placement
  lesson
- it contains adjacent shared docs about ownership boundaries and shared prompt stability
- so the current result is about adjacent consolidation, not about a true one-to-one consolidation
  of the raw PR-workflow draft

## Medium Findings

The `medium` prompt added one explicit boundary sentence:

- contributor workflow behavior for this repository
- not a distributed `ai-wiki-toolkit` product feature

That sentence changed the outcome more than the memory variants did.

### Observed effect

All five variants stayed in repo-local surfaces:

- `scripts/...`
- `tests/...`
- optional `ai-wiki/workflows.md`

No variant added new implementation under:

- `src/ai_wiki_toolkit/`

### Medium-run interpretation

The strongest supported statement is:

- in this benchmark, one explicit boundary sentence was enough to suppress the package-surface
  failure mode across all five variants

The medium run therefore says more about prompt scope control than about raw vs consolidated memory.

That means the medium run should not be over-read as evidence that all five memory states are
equally good. It mainly shows that one explicit scope boundary can dominate the task.

## What We Can Defend

1. We can defend that the original leaked benchmark was invalid and was correctly repaired by:
   - switching to baseline `34cd5a3^`
   - removing prompts that named an existing repo-local helper

2. We can defend that, for the repaired `short` run:
   - `aiwiki_raw_drafts` performed materially better than `plain_repo_no_aiwiki`
   - `aiwiki_raw_drafts` also outperformed the current adjacent-consolidated variants on the main
     surface-choice criterion

3. We can defend that, for the repaired `medium` run:
   - the extra boundary sentence dominated the result
   - memory variants were much less distinguishable
   - no variant wrote new implementation under `src/ai_wiki_toolkit/`

## What We Cannot Defend Yet

- We cannot claim a general property of all consolidation.
- We cannot claim that raw-plus-consolidated is universally worse than raw-only.
- We cannot claim stable model-level effects from one run per condition.
- We cannot claim model consistency was automatically enforced by the harness.
- We cannot yet claim that the current consolidated docs are "wrong" in general. The narrower claim
  is that they were not sufficiently task-specific for this benchmark.

## Recommended Next Documentation

- keep this note as the benchmark result summary
- keep `ownership_boundary_runbook.md` as the reproduction guide
- if this pattern repeats in another benchmark family, promote the lesson about adjacent
  consolidated guidance into a stronger shared evaluation pattern
