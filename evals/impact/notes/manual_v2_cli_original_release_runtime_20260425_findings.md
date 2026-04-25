# Manual v2 CLI Original Release Runtime Findings

This note records the clean formal `release_runtime_compatibility` run from 2026-04-25.

It used Codex CLI-first execution for every slot, persisted one independent session per slot, and
validated the exported session manifest before scoring.

## Scope

Run label:

- `cli-original-runtime-20260425-1618`

Prompt/model condition:

- prompt: `evals/impact/prompts/release_runtime_compatibility/original.md`
- model: `gpt-5.5`
- reasoning effort: `xhigh`
- execution surface: `codex-cli`

Run artifacts:

- workspace root: `/private/tmp/aiwiki_first_round/release_runtime_compatibility/workspaces/20260425-160315`
- run dir: `/private/tmp/aiwiki_first_round/release_runtime_compatibility/runs/cli-original-runtime-20260425-1618`
- session export: `/private/tmp/aiwiki_first_round/release_runtime_compatibility/workspaces/20260425-160315/codex_sessions`
- generated report: `/private/tmp/aiwiki_first_round/release_runtime_compatibility/runs/cli-original-runtime-20260425-1618/report.md`

## Validation

`export_codex_sessions.py` exported six sessions, one for each neutral slot. After export,
`validate_run.py` reported:

- `shareable_for_causal_claims: true`
- `critical_confounds: []`
- `warnings: []`

All six `codex exec` processes returned 0, all six captures returned 0, and all six slots produced
`final_message.md`.

## Slot Scores

| slot | variant | role | score | key evidence |
| --- | --- | --- | --- | --- |
| `s01` | `no_aiwiki_workflow` | primary control | partial | Added release and npm runtime smoke checks in `node:24-bookworm`, but left `linux-x64` building on `ubuntu-24.04`. |
| `s02` | `aiwiki_scaffold_no_target_memory` | diagnostic | success | Built `linux-x64` in `python:3.11-bookworm`, smoked the archive and staged npm install in `node:24-bookworm`, and updated docs/tests. |
| `s03` | `aiwiki_linked_raw_only` | diagnostic | success | Added a dedicated Bookworm Linux build, `node:24-bookworm`/`node:24-trixie` release smoke, staged npm smoke, docs, and tests. |
| `s04` | `aiwiki_linked_consolidated_only` | diagnostic | success | Built on `python:3.11-bullseye`, smoked in Bullseye and Bookworm runtimes, added npm smoke, scripts, docs, and tests. |
| `s05` | `aiwiki_ambient_memory_workflow` | primary treatment | success | Moved Linux build to `ubuntu-22.04`, added release runtime smoke and staged npm smoke in Bookworm, and updated docs/tests. |
| `s06` | `aiwiki_scaffold_no_adjacent_memory` | diagnostic | success | Also moved Linux build to `ubuntu-22.04` and added Bookworm release/npm runtime smoke before publishing. |

The manual scores were written with `evals/impact/scripts/score_run.py` and the aggregate report was
generated with `evals/impact/scripts/report_runs.py`.

## Primary Comparison

The primary comparison is `no_aiwiki_workflow` versus `aiwiki_ambient_memory_workflow`.

Result:

- `no_aiwiki_workflow`: partial
- `aiwiki_ambient_memory_workflow`: success

The no-AI-wiki slot added meaningful gates: it would catch the runtime failure before GitHub Release
asset upload and before npm publish. The miss is that it continued to build the Linux binary on the
newer `ubuntu-24.04` runner, so the release process still produces a binary from the newer glibc
baseline and relies on the smoke test to fail.

The ambient AI wiki slot both lowered the Linux build baseline to `ubuntu-22.04` and added runtime
checks before release and npm publishing. That more directly addresses the historical class of
failure: build success and install success are not enough; the actual binary must run on the target
runtime before anything is published.

Interpretation: this run supports a narrow AI wiki usefulness claim for release-runtime work. The
target working mode improved the quality of the release-process fix, not merely the amount of code
changed.

## Diagnostic Variants

Diagnostics explain possible mechanisms but are not the primary conclusion.

`aiwiki_linked_raw_only` succeeded and explicitly used the raw Linux runtime draft. `aiwiki_linked`
`_consolidated_only` also succeeded with a promoted problem note. Both support the mechanism that
task-specific runtime memory helps agents choose a better build baseline and add true runtime
verification.

`aiwiki_scaffold_no_target_memory` succeeded, which means adjacent release/distribution memory plus
model reasoning can also be enough. `aiwiki_scaffold_no_adjacent_memory` succeeded too, so this
family should not be interpreted as showing that target memory is necessary. The stronger claim is
that the realistic AI wiki workflow improved the primary treatment relative to the no-AI-wiki
control in this one run.

## Validity Threats

Remaining threats:

- This is one sample per condition, not a seed-controlled estimate.
- No actual GitHub Actions release or npm publish was executed; success is inferred from workflow
  diffs, tests, scripts, and local verification.
- Some implementations rely on Docker-based CI steps that were not all run locally.
- Manual scoring was artifact-backed but still human judgment.
- Slots ran sequentially, so time/order effects are not ruled out.
- The diagnostic `s06` success narrows the claim because the task can be solved without adjacent
  target memory.

## Bottom Line

For `release_runtime_compatibility`, the primary comparison directionally supports "AI wiki working
mode is useful": the no-AI-wiki slot added smoke checks but missed the older build baseline, while
the ambient AI wiki slot added both the older baseline and pre-publish runtime verification.

The diagnostic successes keep the conclusion narrow. AI wiki memory improved one primary comparison;
it was not necessary for every successful solution in this family.
