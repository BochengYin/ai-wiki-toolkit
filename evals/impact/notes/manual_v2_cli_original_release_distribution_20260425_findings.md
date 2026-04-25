# Manual v2 CLI Original Release Distribution Findings

This note records the clean formal `release_distribution_integrity` run from 2026-04-25.

It used Codex CLI-first execution for every slot, persisted one independent session per slot, and
validated the exported session manifest before scoring.

## Scope

Run label:

- `cli-original-release-20260425-1246`

Prompt/model condition:

- prompt: `evals/impact/prompts/release_distribution_integrity/original.md`
- model: `gpt-5.5`
- reasoning effort: `xhigh`
- execution surface: `codex-cli`

Run artifacts:

- workspace root: `/private/tmp/aiwiki_first_round/release_distribution_integrity/workspaces/20260425-124642`
- run dir: `/private/tmp/aiwiki_first_round/release_distribution_integrity/runs/cli-original-release-20260425-1246`
- session export: `/private/tmp/aiwiki_first_round/release_distribution_integrity/workspaces/20260425-124642/codex_sessions`
- generated report: `/private/tmp/aiwiki_first_round/release_distribution_integrity/runs/cli-original-release-20260425-1246/report.md`

The run used `evals/impact/scripts/run_cli_slots.py`, which wrapped the full five-slot sequence in
`/usr/bin/caffeinate -dimsu`. `sleep_guard.json` shows the guard was enabled from
`2026-04-25T12:46:59` to `2026-04-25T13:54:47`.

## Validation

`export_codex_sessions.py` exported five sessions, one for each neutral slot. The session manifest
records:

- `source=exec`
- `model=gpt-5.5`
- `reasoning_effort=xhigh`
- one distinct session id for each of `s01` through `s05`

After export, `validate_run.py` reported:

- `shareable_for_causal_claims: true`
- `critical_confounds: []`
- `warnings: []`

All five `codex exec` processes returned 0, all five `save_result.py` captures returned 0, and all
five slots produced `final_message.md`.

## Slot Scores

| slot | variant | role | score | key evidence |
| --- | --- | --- | --- | --- |
| `s01` | `no_aiwiki_workflow` | primary control | partial | Broadly expanded the matrix, npm metadata, Windows zip staging, docs, Homebrew, and tests, but left `linux-musl-x64` on `python:3.11-alpine` without binutils/objdump setup or root setup. |
| `s02` | `aiwiki_scaffold_no_target_memory` | diagnostic | success | Added the full public matrix, zip staging, npm libc metadata/runtime selection, docs, Homebrew, tests, and Alpine musl binutils setup under root. |
| `s03` | `aiwiki_linked_raw_only` | diagnostic | success | Used raw release-memory surface and coordinated workflow, npm, docs, tests, Windows zip staging, and musl root/setup handling. |
| `s04` | `aiwiki_linked_consolidated_only` | diagnostic | success | Used consolidated release-memory surface and coordinated workflow, npm, docs, tests, Windows zip staging, and musl root/setup handling. |
| `s05` | `aiwiki_ambient_memory_workflow` | primary treatment | success | Aligned all major coupled surfaces and explicitly handled the known Alpine musl binutils/root setup hazard plus npm libc target resolution. |

The manual scores were written with `evals/impact/scripts/score_run.py` and the aggregate report was
generated with `evals/impact/scripts/report_runs.py`.

## Primary Comparison

The primary comparison is `no_aiwiki_workflow` versus `aiwiki_ambient_memory_workflow`.

Result:

- `no_aiwiki_workflow`: partial
- `aiwiki_ambient_memory_workflow`: success

The no-AI-wiki slot was strong enough to attempt the broad expansion. It updated the release
workflow, npm target map, runtime wrapper, Windows archive staging, docs, Homebrew, and tests.

The important miss was release-build integrity for the new musl target. It selected
`python:3.11-alpine` and a POSIX shell for `linux-musl-x64`, but did not install `binutils`/`objdump`
or run that setup as root. That leaves a likely PyInstaller musl build failure in a central
release-facing path, so the run is not a full rubric success.

The ambient AI wiki slot produced a similarly broad expansion, but also applied the known musl
release lesson. It added target-specific container setup, installed `binutils` before the PyInstaller
build, ran that setup as root, added runtime checks, and kept npm `libc` metadata and musl runtime
selection aligned with the public matrix.

Interpretation: this formal run supports a narrower but useful AI wiki claim for release
distribution work. AI wiki memory was not needed for the agent to notice the broad matrix expansion,
but it did help avoid a known cross-surface release hazard that the no-AI-wiki primary control
missed.

## Diagnostic Variants

Diagnostics explain possible mechanisms but are not the primary conclusion.

`aiwiki_scaffold_no_target_memory` succeeded. This shows that scaffold, adjacent memory, web docs, and
model reasoning can also be enough for this task. It should not be read as a pure absence-of-memory
condition because this family intentionally removes only the directly targeted distribution-matrix
memory, not all adjacent release memory.

`aiwiki_linked_raw_only` succeeded. It supports the explanation that raw release-memory notes can
carry enough concrete detail to close the musl, npm, and Windows archive surfaces.

`aiwiki_linked_consolidated_only` also succeeded. In this run, the promoted distribution convention
plus adjacent problem memory were enough to produce a complete coordinated implementation.

## Non-Critical Observations

- `s02` needed an npm cache workaround for `npm pack`; the command passed after using a local cache.
- Some AI wiki variants wrote draft notes inside their slot repos. Those are expected behavior for
  the AI wiki workflow variants and are captured as artifacts, not repo changes.
- Several slots consulted current GitHub and npm documentation for runner labels and package
  metadata. That makes the run realistic, but it is still a time-varying external input.

None of these were reported by `validate_run.py` as critical confounds.

## Validity Threats

Remaining threats:

- This is one sample per condition, not a seed-controlled estimate.
- The benchmark is backsolved from real prior release issues, so the treatment memory is unusually
  well matched to the task.
- No actual GitHub Actions release was executed; success is inferred from diff review, changed tests,
  workflow parsing, and local verification commands.
- Manual scoring was rubric-based and artifact-backed, but still human judgment.
- Slots ran sequentially, so time/order effects are not ruled out.
- External GitHub/npm docs were available to all variants and can mask some memory benefit.
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

For the formal release-distribution primary comparison, this run directionally supports "AI wiki
working mode is useful": the no-AI-wiki slot did a broad partial implementation but missed a known
musl release-build hazard, while the realistic AI wiki slot completed that hazard along with the
rest of the release/npm distribution matrix.

The diagnostic variants are useful for mechanism analysis, but they should not be promoted into the
main causal conclusion.
