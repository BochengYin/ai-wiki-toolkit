# Release Distribution Integrity Runbook

This document describes how to reproduce the current `release_distribution_integrity` manual
impact eval and how the generated repos differ before any prompt is run.

## Goal

Measure whether AI wiki memory changes how reliably an agent keeps a public release/distribution
matrix aligned across the relevant code, workflow, packaging, documentation, and verification
surfaces.

The intended good outcome is:

- public release targets added in the main workflow
- npm target resolution and package metadata kept in sync with those targets
- Windows archive-format differences handled correctly
- release and install docs updated to match the public matrix
- release-facing checks extended enough to catch obvious target drift

## Historical Trigger

This benchmark is backsolved from repeated real release/distribution failures in this repo, not a
synthetic "matrix coordination" toy task.

The combined historical problem shape was:

- Windows npm support looked partly declared but was not fully real end to end
- later target expansion added `linux-arm64`, `linux-musl-x64`, and `windows-arm64`
- release workflow, npm metadata, archive handling, docs, and verification could drift apart

The benchmark-targeted memory cluster is:

- raw draft:
  - `ai-wiki/people/bochengyin/drafts/distribution-target-matrix-must-match-published-assets.md`
- promoted convention:
  - `ai-wiki/conventions/distribution-target-matrix-must-match-published-assets.md`

## Baseline

All variants are generated from the historical git ref:

- `06a47cd^`

That baseline predates the later coordinated expansion work, so the experiment does not start from
repos that already advertise the full intended target matrix.

## Generation Script

Workspace generation is defined in:

- `evals/impact/scripts/prepare_variants.py`

Important defaults:

- source mode: committed git snapshot, not the current working tree
- experiment family: `release_distribution_integrity`
- baseline ref: `06a47cd^`

This keeps local uncommitted notes, eval scaffolding, and scratch work out of the generated
experiment repos.

## Variant Setup

All variants start from the same historical baseline. The intended differences are the AI wiki
surface and which benchmark-targeted memory files are present.

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

Keeps the AI wiki scaffold, but removes the benchmark-targeted distribution-matrix memory.

Removed raw draft:

- `ai-wiki/people/bochengyin/drafts/distribution-target-matrix-must-match-published-assets.md`

Removed consolidated doc:

- `ai-wiki/conventions/distribution-target-matrix-must-match-published-assets.md`

Removed index entry:

- `ai-wiki/conventions/index.md` entry for `distribution-target-matrix-must-match-published-assets.md`

Important:

- this family removes the directly targeted matrix-memory files only
- other adjacent release docs still remain in the repo
- so `aiwiki_no_relevant_memory` is "targeted-memory removed", not "memory-free release repo"

### aiwiki_raw_drafts

Starts from `aiwiki_no_relevant_memory`, then adds back only the raw draft:

- `ai-wiki/people/bochengyin/drafts/distribution-target-matrix-must-match-published-assets.md`

No promoted shared convention is added back.

### aiwiki_consolidated

Starts from `aiwiki_no_relevant_memory`, then adds back only the promoted shared convention:

- `ai-wiki/conventions/distribution-target-matrix-must-match-published-assets.md`

And re-adds its index entry:

- `ai-wiki/conventions/index.md`

### aiwiki_raw_plus_consolidated

Includes both:

- the raw draft
- the promoted shared convention
- the restored convention index entry

## Active Prompts

Prompt family:

- `evals/impact/prompts/release_distribution_integrity/`

Task description:

- `evals/impact/prompts/release_distribution_integrity/TASK.md`

Active prompt levels:

- `short.md`
- `medium.md`

### short

Contains only the task requirement:

- expand public release and npm distribution support
- add end-to-end Windows npm support
- expand the public matrix to:
  - `linux-arm64`
  - `linux-musl-x64`
  - `windows-arm64`
- keep docs and tests up to date

### medium

Adds exactly one extra coordination sentence:

- treat this as one coordinated public distribution change
- keep release assets, npm target resolution/package metadata, archive handling, docs, and
  release-facing verification aligned

## Manual Protocol

For each variant:

1. Open the workspace in a fresh Codex session.
2. Paste `short.md` or `medium.md`.
3. Let the agent work normally.
4. Capture the workspace with:
   - `evals/impact/scripts/save_result.py`
5. Export the visible Codex session with:
   - `evals/impact/scripts/export_codex_sessions.py`
6. Grade the run from:
   - `workspace_diff.patch`
   - `workspace_diff_stat.txt`
   - `visible_transcript.md`
   - `visible_session.jsonl`
   - the changed tests

Important controls:

- one fresh session per variant
- same selected model across variants if possible
- same prompt text within a comparison set
- save artifacts outside the experiment repos
- do not grade from `report.md` or `final_message.md` alone

## Artifact Interpretation Rules

The current harness captures useful artifacts, but the analysis should follow these rules:

1. Treat `prompt.md` as the task prompt only.
2. Treat `visible_transcript.md` and `visible_session.jsonl` as the visible full prompt surface.
3. Use `workspace_diff.patch` plus the session trace to judge whether the implementation really hit
   the task.
4. Treat `final_message.md` as optional convenience output, not the source of truth.
5. If a session continued after the first substantive closeout, use the first closeout block in
   `visible_transcript.md` rather than a later `final_message.md` snapshot.

## Model And Sampling Notes For The Current Runs

The currently saved release run was executed manually with:

- execution surface: Codex subscription sessions, not direct API calls
- model family: `gpt-5.4`
- reasoning effort: `xhigh` / extra high

These settings were manually held constant by the operator. They are not yet stored as verified
fields in `result.json`.

Because these runs were done through subscription sessions rather than direct API requests, the
operator did not have exposed request knobs for parameters such as temperature or seed.

What is not currently recorded by the harness:

- exact model and effort fields in result capture
- an explicit first-pass cutoff timestamp
- a frozen saved first-pass final message

So current conclusions should be treated as manually controlled qualitative comparisons, not as
fully instrumented deterministic replays.

## Manual Scoring Rubric

Use this rubric when assigning a post-run label.

### Success

All of the following are true:

- the run makes Windows npm support real end to end
- the public release workflow matrix and npm target/package metadata are aligned
- Windows archive handling is updated where needed
- the main release/install docs are updated
- the run adds or updates enough release-facing checks to cover the widened matrix
- no obvious target drift remains in a major coupled surface

### Partial

The run gets the main expansion mostly right but still leaves a notable coupled-surface gap, for
example:

- the main workflow and npm path are aligned, but another relevant public distribution surface is
  left behind
- docs are updated, but release-facing verification remains thinner than the change warrants
- the implementation broadly works, but one important coupled layer would likely need review before
  treating the matrix as fully aligned

### Fail

Any of the following is enough for failure:

- only one layer is updated
- Windows npm support is still not real end to end
- the public matrix still obviously drifts across workflow, packaging, docs, or verification
- the run advertises support that the repo still does not actually publish or stage correctly

## Current Saved Runs

### Short run

- workspace root:
  - `/private/tmp/aiwiki_first_round/release_distribution_integrity/workspaces/20260424-182219`
- run dir:
  - `/private/tmp/aiwiki_first_round/release_distribution_integrity/runs/short-five-way`
- report:
  - `/private/tmp/aiwiki_first_round/release_distribution_integrity/runs/short-five-way/report.md`
- exported sessions:
  - `/private/tmp/aiwiki_first_round/release_distribution_integrity/workspaces/20260424-182219/codex_sessions/manifest.json`
