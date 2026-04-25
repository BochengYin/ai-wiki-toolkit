# Manual v2 CLI Original Ownership Findings

This note records the clean formal `ownership_boundary` run from 2026-04-25, plus the
supplemental `s06` diagnostic added later the same day.

Unlike the earlier transition batch, this run used Codex CLI-first execution for every slot,
persisted one independent session per slot, and validated the exported session manifest before
scoring.

## Scope

Run label:

- `cli-original-ownership-20260425-1158`

Prompt/model condition:

- prompt: `evals/impact/prompts/ownership_boundary/original.md`
- model: `gpt-5.5`
- reasoning effort: `xhigh`
- execution surface: `codex-cli`

Run artifacts:

- workspace root: `/private/tmp/aiwiki_first_round/ownership_boundary/workspaces/20260425-115832`
- run dir: `/private/tmp/aiwiki_first_round/ownership_boundary/runs/cli-original-ownership-20260425-1158`
- session export: `/private/tmp/aiwiki_first_round/ownership_boundary/workspaces/20260425-115832/codex_sessions`
- generated report: `/private/tmp/aiwiki_first_round/ownership_boundary/runs/cli-original-ownership-20260425-1158/report.md`

The run used `evals/impact/scripts/run_cli_slots.py`, which wrapped the full five-slot sequence in
`/usr/bin/caffeinate -dimsu`. `sleep_guard.json` shows the guard was enabled from
`2026-04-25T11:58:43` to `2026-04-25T12:37:58`.

After the original five-slot run had already been scored, a supplemental `s06`
`aiwiki_scaffold_no_adjacent_memory` repo was added inside the same workspace/run folder and executed
with the same original prompt, model, reasoning effort, and Codex CLI-first path. The original
`s01` through `s05` results were not rerun.

## Validation

`export_codex_sessions.py` now exports six sessions, one for each neutral slot. The session manifest
records:

- `source=exec`
- `model=gpt-5.5`
- `reasoning_effort=xhigh`
- one distinct session id for each of `s01` through `s06`

After the export completed, `validate_run.py` reported:

- `shareable_for_causal_claims: true`
- `critical_confounds: []`
- `warnings: []`

A first validator call was accidentally started in parallel with the session export and briefly
reported missing session exports. That was a sequencing false positive, not a run confound. The
post-export validator output is the authoritative validation artifact.

## Slot Scores

| slot | variant | role | score | key evidence |
| --- | --- | --- | --- | --- |
| `s01` | `no_aiwiki_workflow` | primary control | fail | Added `src/ai_wiki_toolkit/contributor_workflow.py` and package CLI wiring in `src/ai_wiki_toolkit/cli.py`. |
| `s02` | `aiwiki_scaffold_no_target_memory` | diagnostic | success | Added repo-local `scripts/pr_flow.py`, tests, and `CONTRIBUTING.md`; no package code. |
| `s03` | `aiwiki_linked_raw_only` | diagnostic | success | Used raw placement draft, added repo-local helper/tests, and updated `ai-wiki/workflows.md`. |
| `s04` | `aiwiki_linked_consolidated_only` | diagnostic | fail | Added a wrapper under `scripts/`, but core implementation went into `src/ai_wiki_toolkit/pr_flow.py`. |
| `s05` | `aiwiki_ambient_memory_workflow` | primary treatment | success | Added repo-local `scripts/pr_flow.py`, tests, `CONTRIBUTING.md`, and `ai-wiki/workflows.md`; no package code. |
| `s06` | `aiwiki_scaffold_no_adjacent_memory` | diagnostic | fail | Added a repo-local script and tests, but also put core implementation under `src/ai_wiki_toolkit/contributor_workflow.py`, which is a hard rubric failure. |

All six slots produced `final_message.md`, first-pass capture artifacts, and changed-test evidence.
All `codex exec` and `save_result.py` commands returned 0.

## Primary Comparison

The primary comparison is `no_aiwiki_workflow` versus `aiwiki_ambient_memory_workflow`.

Result:

- `no_aiwiki_workflow`: fail
- `aiwiki_ambient_memory_workflow`: success

The no-AI-wiki slot repeated the historical ownership-boundary mistake: it treated a
contributor-only repository workflow as package functionality by adding implementation under
`src/ai_wiki_toolkit/` and wiring a package CLI command.

The ambient AI wiki slot found and used the repo-local workflow memory. It explicitly cited the
draft about keeping contributor workflows out of the package layer, implemented the helper under
`scripts/`, added tests, and avoided package CLI or package-module changes.

Interpretation: this formal run supports the claim that the AI wiki working mode was useful for the
ownership-boundary task. The useful behavior was not just extra context; it changed the implementation
surface the agent selected.

## Diagnostic Variants

Diagnostics explain possible mechanisms but are not the primary conclusion.

`aiwiki_scaffold_no_target_memory` also succeeded, but it is not a clean no-target diagnostic. Its
visible transcript and reuse footer show that it consulted `ai-wiki/workflows.md` plus impact-eval
meta drafts, including a note saying no-target slots must exclude task-specific workflow memory. This
slot should be read as evidence that scaffold/workflow routing can already be strong, not as a pure
absence-of-memory condition.

`aiwiki_linked_raw_only` succeeded and used the raw draft
`repo-local-contributor-workflows-should-stay-out-of-the-package-layer.md`. This supports the
mechanistic explanation that direct raw memory can route the implementation away from package code.

`aiwiki_linked_consolidated_only` failed the hard ownership rule. It had adjacent ownership guidance,
but still put the core helper in `src/ai_wiki_toolkit/pr_flow.py`. That suggests adjacent consolidated
docs alone did not carry enough task-specific placement force in this run.

`aiwiki_scaffold_no_adjacent_memory` also failed. This is the strictest scaffold diagnostic: it kept
the AI wiki scaffold path but removed the adjacent workflow memory that contaminated `s02`. The slot
still built a working helper and tests, but placed core logic in package code. That strengthens the
mechanism story that the successful ambient run depended on reachable workflow/placement memory, not
just the existence of an AI wiki scaffold.

## Validity Threats

Remaining threats:

- This is still one sample per condition, not a seed-controlled estimate.
- The benchmark is backsolved from a real prior mistake, so the treatment memory is unusually well
  matched to the task.
- The diagnostic no-target slot was contaminated by remaining workflow and meta-eval memory, so it
  should not be used as a pure mechanism control.
- The `s06` strict no-adjacent diagnostic was added after the original five slots rather than as part
  of the initial sequential batch, so it is explanatory rather than part of the primary comparison.
- Slots ran sequentially, so time/order effects are not ruled out.
- Manual scoring was rubric-based and artifact-backed, but still human judgment.
- `temperature` and seed are not captured.

Controls that improved over the transition run:

- neutral slot paths
- one independent persisted CLI session per slot
- original prompt only
- no VS Code UI or Computer Use formal execution path
- run-level `caffeinate` protection
- complete exported session manifest with observed source/model/effort
- clean validator output after export

## Bottom Line

For the formal ownership-boundary primary comparison, this run supports "AI wiki working mode is
useful": the no-AI-wiki slot failed by entering the package surface, while the realistic AI wiki
slot succeeded by keeping the workflow repo-local.

The diagnostic variants are useful for explanation, especially the raw-draft success,
consolidated-only failure, and strict `s06` scaffold failure, but they should not be promoted into
the main causal conclusion.
