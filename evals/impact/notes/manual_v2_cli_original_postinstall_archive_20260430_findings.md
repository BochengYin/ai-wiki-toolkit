# Manual v2 CLI Original Postinstall Archive Findings

This note records the formal `postinstall_archive_staging` run from 2026-04-30.

It used Codex CLI-first execution for every slot, persisted one independent session per slot, and
validated the exported session manifest before scoring.

## Scope

Run label:

- `cli-original-postinstall-20260430-0903`

Prompt/model condition:

- prompt: `evals/impact/prompts/postinstall_archive_staging/original.md`
- model: `gpt-5.5`
- reasoning effort: `xhigh`
- execution surface: `codex-cli`

Run artifacts:

- workspace root: `/private/tmp/aiwiki_first_round/postinstall_archive_staging/workspaces/20260430-090327`
- run dir: `/private/tmp/aiwiki_first_round/postinstall_archive_staging/runs/cli-original-postinstall-20260430-0903`
- session export: `/private/tmp/aiwiki_first_round/postinstall_archive_staging/workspaces/20260430-090327/codex_sessions`
- generated report: `/private/tmp/aiwiki_first_round/postinstall_archive_staging/runs/cli-original-postinstall-20260430-0903/report.md`

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
| `s01` | `no_aiwiki_workflow` | primary control | success | Diagnosed that extraction deleted the downloaded archive and staged the archive outside the target dir. |
| `s02` | `aiwiki_scaffold_no_target_memory` | diagnostic | success | Used a sibling `_downloads` staging directory and wrote a new AI wiki draft. |
| `s03` | `aiwiki_linked_raw_only` | diagnostic | success | Used the target raw draft, staged in `os.tmpdir()`, and avoided new user-owned wiki churn. |
| `s04` | `aiwiki_linked_consolidated_only` | diagnostic | success | Fixed the bug but broadened npm wrapper seams and wrote a new AI wiki draft. |
| `s05` | `aiwiki_ambient_memory_workflow` | primary treatment | success | Used ambient target memory, staged in `os.tmpdir()`, and avoided new user-owned wiki churn. |
| `s06` | `aiwiki_scaffold_no_adjacent_memory` | diagnostic | success | Fixed the bug without target or adjacent memory, but produced a new AI wiki draft and catalog churn. |

The manual scores were written with `evals/impact/scripts/score_run.py` and the aggregate report was
generated with `aiwiki-toolkit eval impact report`.

## Primary Comparison

The primary comparison is `no_aiwiki_workflow` versus `aiwiki_ambient_memory_workflow`.

Result:

- `no_aiwiki_workflow`: success
- `aiwiki_ambient_memory_workflow`: success

Both primary slots identified the same root cause: the npm wrapper downloaded
`npm/vendor/<target>/download.tar.gz`, then deleted `npm/vendor/<target>` before the extractor tried
to open that archive.

Interpretation: this run is neutral on first-attempt success and score. The no-AI-wiki control
solved the task cleanly, so this family is not strong evidence that AI wiki memory is necessary for
success.

## Change Profile Signal

The useful product signal is change quality rather than pass/fail.

The generated report now separates changed-file counts into:

- project files outside `ai-wiki/`
- managed AI wiki telemetry under `ai-wiki/_toolkit/` and `ai-wiki/metrics/`
- user-owned AI wiki files such as drafts

For this run:

- primary project-file footprint was tied: `2.00` versus `2.00`
- ambient AI wiki added managed telemetry, but no user-owned wiki files
- `aiwiki_scaffold_no_target_memory`, `aiwiki_linked_consolidated_only`, and
  `aiwiki_scaffold_no_adjacent_memory` each wrote one user-owned draft
- `aiwiki_linked_consolidated_only` also touched one extra project file, `npm/shared.js`

This supports a narrower claim: exact target memory can reduce extra writeback churn and keep the
fix smaller even when the task is easy enough for every condition to pass.

## Validity Threats

Remaining threats:

- This is one sample per condition, not a seed-controlled estimate.
- Manual scoring was artifact-backed but still human judgment.
- The task prompt already localized the failure to `ENOENT` under `npm/vendor/<target>`, making the
  bug easy to infer from code.
- Slots ran sequentially, so time/order effects are not ruled out.
- `s06` exposed stale catalog/reference behavior in the prepared variant; that should be treated as
  a diagnostic finding, not as a core benchmark outcome.

## Bottom Line

For `postinstall_archive_staging`, the result is neutral on "AI wiki improves first-pass success."
The family remains useful for evaluating quality signals: implementation footprint, user-owned wiki
churn, and whether exact memory prevents rewriting an already-known lesson.
