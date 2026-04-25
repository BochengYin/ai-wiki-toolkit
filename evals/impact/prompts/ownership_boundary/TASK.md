# Ownership Boundary Task

This prompt family tests one concrete, repo-realistic implementation task without leaking the
intended implementation surface.

## Task

Add a helper for the contributor branch-and-PR workflow in this repository.

The workflow should require starting from a new branch instead of working on `main`, pushing
changes from that branch, and switching back to `main` after the pull request is merged.

Document the branch naming rule in the correct local workflow guidance if needed.

The intended branch naming rule is:

- `feature/YYYY_MM_DD_description`
- `chore/YYYY_MM_DD_description`
- `fix/YYYY_MM_DD_description`

The agent should treat this as contributor workflow behavior for this repository, not as a
distributed `ai-wiki-toolkit` product feature.

## Why this is a real task

This benchmark uses the original problem class that actually appeared in this repo's history,
rather than a synthetic placeholder task.

The repo already has:

- repo-local workflow guidance in `ai-wiki/workflows.md`
- a raw draft about the same boundary mistake:
  - `ai-wiki/people/bochengyin/drafts/repo-local-contributor-workflows-should-stay-out-of-the-package-layer.md`
- adjacent consolidated ownership guidance:
  - `ai-wiki/conventions/package-managed-vs-user-owned-docs.md`
  - `ai-wiki/review-patterns/shared-prompt-files-must-be-user-agnostic.md`

Without relevant memory, an agent could easily put this helper in `src/ai_wiki_toolkit/`, invent
a package CLI feature, or update the wrong docs. The benchmark measures whether different memory
states help the agent keep the change out of distributed package surfaces without directly naming
the intended file location in the prompt.

The historical user request behind this task was essentially:

- contributors should not work from `main`
- the repo should make branch-first PR flow explicit
- after merge, the local workflow should return to `main`
- AI wiki is the right place to record and reinforce that behavior

## Expected implementation shape

A strong solution will usually:

- add a repo-local helper under `scripts/`
- add or update tests for the helper behavior
- update `ai-wiki/workflows.md` if the workflow guidance should mention the branch naming rule

A weak solution often:

- adds new code under `src/ai_wiki_toolkit/`
- turns the rule into package-managed behavior
- updates unrelated AI wiki docs instead of the repo-local workflow guidance

## What varies across variants

- `no_aiwiki_workflow`: no AI wiki at all
- `aiwiki_ambient_memory_workflow`: realistic current AI wiki memory
- `aiwiki_scaffold_no_target_memory`: AI wiki exists, but not the target ownership memory
- `aiwiki_linked_raw_only`: target raw drafts exist
- `aiwiki_linked_consolidated_only`: linked consolidated docs exist

## Manual v2 prompt

Manual v2 uses only:

- `original.md`: the historical task shape without the direct product-scope boundary sentence

The old `short.md`, `medium.md`, and `full.md` files are retained only for round1 interpretation.
`medium.md` should not be used for workflow-primary claims because it tells the agent the core
boundary answer.

## Human evaluation questions

- Did the agent keep the change in repo-local surfaces instead of `src/ai_wiki_toolkit/`?
- Did it add the helper in `scripts/` rather than inventing a package feature?
- Did it update the most appropriate workflow guidance?
- Did it avoid unrelated wiki churn?
- Did the AI wiki workflow help it avoid the repeated boundary mistake without extra prompt detail?
