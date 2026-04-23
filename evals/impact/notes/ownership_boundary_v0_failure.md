# Ownership Boundary v0 Failure

## Summary

The first `ownership_boundary` benchmark design failed as an experiment about implementation
surface choice.

The run did produce diffs, but the setup leaked too much of the intended answer. As a result, the
results could not answer the original question:

> Does AI wiki memory help an agent choose the correct repo-local surface instead of turning a
> contributor workflow into package code?

## What Leaked

### 1. The repo baseline already contained the helper surface

All variants were generated from a repo state that already included:

- `scripts/pr_flow.py`
- `tests/test_pr_flow_script.py`

That meant the agent did not need to discover the correct surface. The repo already advertised it.

### 2. The prompt leaked the intended surface

The original prompt asked the agent to:

> extend the existing repo-local PR flow

That wording directly hinted that:

- a repo-local PR flow already existed
- the change should extend it

So even variants without relevant AI wiki memory still had a strong path toward the intended
surface.

## Observed Symptoms

- All variants changed repo-local surfaces instead of `src/ai_wiki_toolkit/`.
- The experiment therefore did **not** separate surface choice behavior by memory state.
- The main visible differences were only:
  - extra doc churn such as `CONTRIBUTING.md` or `CHANGELOG.md`
  - whether `ai-wiki/workflows.md` was updated

Those signals may still be interesting, but they are not the primary question this benchmark was
meant to answer.

## Why The Result Was Invalid

The benchmark was supposed to measure whether different AI wiki memory states change where an agent
implements a contributor-only workflow.

Because both the repo and the prompt already pointed at the repo-local helper surface, the
experiment mostly measured:

- how much extra churn the agent introduced
- how much local guidance it edited

It did **not** cleanly measure:

- `scripts/` vs `src/ai_wiki_toolkit/`
- repo-local workflow vs distributed product feature

## Repair Strategy

The corrected design uses:

1. a historical baseline from before the PR helper was added
2. controlled injection of raw and consolidated AI wiki memory into the generated variants
3. prompt wording that does not say `existing repo-local PR flow`

For this benchmark family, the chosen historical baseline is:

- `34cd5a3^`

That baseline predates the addition of:

- `scripts/pr_flow.py`
- `tests/test_pr_flow_script.py`
- the helper references later added to repo-local workflow guidance

## Follow-Up Rule

Before treating a benchmark result as evidence of memory impact, verify both:

1. the target implementation surface is not already present in every variant
2. the prompt does not directly name the intended target surface unless the benchmark is explicitly
   about behavior *within* that surface
