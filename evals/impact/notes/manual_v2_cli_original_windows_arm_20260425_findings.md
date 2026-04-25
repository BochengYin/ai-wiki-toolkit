# Manual v2 CLI Original Windows ARM Smoke Findings

This note records the clean formal `windows_arm_smoke_cli_output` run from 2026-04-25.

It used Codex CLI-first execution for every slot, persisted one independent session per slot, and
validated the exported session manifest before scoring.

## Scope

Run label:

- `cli-original-windows-arm-20260425-1618`

Prompt/model condition:

- prompt: `evals/impact/prompts/windows_arm_smoke_cli_output/original.md`
- model: `gpt-5.5`
- reasoning effort: `xhigh`
- execution surface: `codex-cli`

Run artifacts:

- workspace root: `/private/tmp/aiwiki_first_round/windows_arm_smoke_cli_output/workspaces/20260425-160315`
- run dir: `/private/tmp/aiwiki_first_round/windows_arm_smoke_cli_output/runs/cli-original-windows-arm-20260425-1618`
- session export: `/private/tmp/aiwiki_first_round/windows_arm_smoke_cli_output/workspaces/20260425-160315/codex_sessions`
- generated report: `/private/tmp/aiwiki_first_round/windows_arm_smoke_cli_output/runs/cli-original-windows-arm-20260425-1618/report.md`

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
| `s01` | `no_aiwiki_workflow` | primary control | success | Changed both Windows ARM smoke paths to compare against `ai-wiki-toolkit <version>` and updated workflow tests. |
| `s02` | `aiwiki_scaffold_no_target_memory` | diagnostic | success | Same workflow/test fix; also wrote an AI wiki draft. |
| `s03` | `aiwiki_linked_raw_only` | diagnostic | success | Same workflow/test fix, including a guard against the old bare-version comparison. |
| `s04` | `aiwiki_linked_consolidated_only` | diagnostic | success | Used the consolidated Windows ARM problem note and fixed both smoke paths. |
| `s05` | `aiwiki_ambient_memory_workflow` | primary treatment | success | Used the target problem memory and fixed both smoke paths with tests. |
| `s06` | `aiwiki_scaffold_no_adjacent_memory` | diagnostic | success | Fixed both smoke paths and tests without adjacent release memories. |

The manual scores were written with `evals/impact/scripts/score_run.py` and the aggregate report was
generated with `evals/impact/scripts/report_runs.py`.

## Primary Comparison

The primary comparison is `no_aiwiki_workflow` versus `aiwiki_ambient_memory_workflow`.

Result:

- `no_aiwiki_workflow`: success
- `aiwiki_ambient_memory_workflow`: success

Both primary slots identified the same root cause: the workflow compared `aiwiki-toolkit --version`
output with the bare package version even though the CLI prints `ai-wiki-toolkit <version>`.

Interpretation: this run does not support a strong AI wiki usefulness claim. The no-AI-wiki control
solved the task cleanly, so the target memory was not necessary for success. The family is still a
useful narrow smoke benchmark because it is deterministic and checks whether agents update both
release-archive and npm-installed paths plus regression tests.

## Diagnostic Variants

Diagnostics explain possible mechanisms but are not the primary conclusion.

All four diagnostic variants also succeeded. The target raw and consolidated memories helped explain
the failure quickly, but the task prompt and code surface were already sufficiently direct for every
condition to solve it.

`aiwiki_scaffold_no_adjacent_memory` succeeded as well, which reinforces that this family is not a
good discriminator for whether AI wiki memory is necessary. It is better used as a small
regression-style benchmark for CLI-first harness reliability and first-pass artifact capture.

## Validity Threats

Remaining threats:

- This is one sample per condition, not a seed-controlled estimate.
- No actual GitHub Actions Windows ARM run was executed; success is inferred from workflow diff,
  tests, and local verification.
- Manual scoring was artifact-backed but still human judgment.
- The task prompt itself strongly localized the failure to version verification.
- Slots ran sequentially, so time/order effects are not ruled out.

## Bottom Line

For `windows_arm_smoke_cli_output`, the result is neutral on "AI wiki working mode is useful": both
the no-AI-wiki control and ambient AI wiki treatment succeeded.

This family should be kept as a narrow, deterministic follow-up benchmark, but not used as primary
evidence that AI wiki memory improves success rates.
