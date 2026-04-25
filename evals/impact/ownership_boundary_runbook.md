# Ownership Boundary Runbook

This document describes how to reproduce the current `ownership_boundary` manual impact eval and
how the generated repos differ before any prompt is run.

For result chronology and synthesis, read:

- `evals/impact/notes/index.md`
- `evals/impact/notes/manual_v2_original_10_repo_findings.md`
- `evals/impact/report.md`

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

## Active Prompt

Prompt family:

- `evals/impact/prompts/ownership_boundary/`

Task description:

- `evals/impact/prompts/ownership_boundary/TASK.md`

Formal v2 runs use one active prompt level:

- `original.md`

`original.md` recreates the historical user request without directly saying that the helper must
stay out of the distributed package. That makes the run test memory/workflow reuse instead of
prompt saturation.

Legacy round1 prompts remain only for old-run interpretation:

- `short.md`
- `medium.md`
- `full.md`

Do not use `medium.md` for workflow-primary claims; it names the core ownership boundary too
directly.

## Codex CLI-First Protocol

For each neutral slot:

1. Prefer `run_cli_slots.py` so the whole slot set runs under one `caffeinate -dimsu` sleep guard.
2. Run `original.md` with `codex exec` from a fresh persisted CLI session.
3. Use the same `gpt-5.5` / `xhigh` condition across all slots.
4. Capture the first pass with:
   - `evals/impact/scripts/save_result.py`
5. Export session traces with:
   - `evals/impact/scripts/export_codex_sessions.py`
6. Validate the run with:
   - `evals/impact/scripts/validate_run.py`
7. Score the run manually with:
   - `evals/impact/scripts/score_run.py`
8. After all slots are scored, aggregate with:
   - `evals/impact/scripts/report_runs.py`

Important controls:

- one fresh session per slot
- same selected model and reasoning effort across variants
- same prompt text within a comparison set
- save artifacts outside the experiment repos
- require a complete `codex_sessions/manifest.json` before making shareable claims
- require exported session metadata to show `source=exec`, `model=gpt-5.5`, and
  `reasoning_effort=xhigh`

Computer Use or the VS Code Codex extension can still be used for smoke checks, but UI automation
is not the formal execution path.

Whole-run command:

```bash
uv run python evals/impact/scripts/run_cli_slots.py \
  --run-dir <run-dir> \
  --prompt-level original
```

If the sleep guard is unavailable or a `codex exec` process hangs before writing
`final_message.md`, treat that run as an infrastructure confound and restart from a new workspace
for formal claims.

## Model And Sampling Notes

The formal v2 condition is:

- execution surface: `codex-cli`
- model family: `gpt-5.5`
- reasoning effort: `xhigh`

`init_run.py` records those expected fields in `metadata.json`. `export_codex_sessions.py` exports
the observed session `source`, model, and reasoning effort into each session `metadata.json` and
the workspace-level `manifest.json`. `validate_run.py` treats mismatches as critical confounds.

The legacy saved `short` and `medium` runs were executed manually with GPT-5.4 at extra-high
reasoning through subscription sessions. Use them as historical qualitative evidence, not as the
formal v2 condition.

No temperature or seed is captured here.

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

### Manual v2 original transition run

- workspace root:
  - `/private/tmp/aiwiki_first_round/ownership_boundary/workspaces/20260425-005106`
- run dir:
  - `/private/tmp/aiwiki_first_round/ownership_boundary/runs/ui-original-five-slots-20260425-0139`
- exported sessions:
  - `/private/tmp/aiwiki_first_round/ownership_boundary/workspaces/20260425-005106/codex_sessions_ui_original_ownership/manifest.json`
- findings note:
  - `evals/impact/notes/manual_v2_original_10_repo_findings.md`

Important: this was a transition run before the formal CLI-first validator was fully in place.
Use it as qualitative evidence, not a clean formal causal run.

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
- The harness records observed source/model/effort through exported sessions, but it still relies on
  the local Codex session history being available at export time.
- No temperature or seed is captured here.
- Current evidence is from one task family and one run per variant/prompt level.

## Interpretation Guardrails

- Treat formal v2 `original` runs as the workflow-primary evidence.
- Treat legacy `short` and `medium` runs as historical controls only.
- Treat `medium` as a prompt-strength control, not memory-reuse evidence.
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
