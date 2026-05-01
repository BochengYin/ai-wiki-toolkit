# Manual v2 CLI Original AI Wiki Evidence Findings

This note records the first formal `aiwiki_evidence_integrity` run from 2026-05-01.

It used Codex CLI-first execution for every neutral slot, persisted one independent session per
slot, exported the visible sessions, validated the run, manually scored the captures, and generated
both the script-level and product-level reports.

## Scope

Run label:

- `cli-original-aiwiki-evidence-20260501-1725`

Prompt/model condition:

- prompt: `evals/impact/prompts/aiwiki_evidence_integrity/original.md`
- model: `gpt-5.5`
- reasoning effort: `xhigh`
- execution surface: `codex-cli`

Run artifacts:

- workspace root: `/private/tmp/aiwiki_first_round/aiwiki_evidence_integrity/workspaces/20260501-1725-formal`
- run dir: `/private/tmp/aiwiki_first_round/aiwiki_evidence_integrity/runs/cli-original-aiwiki-evidence-20260501-1725`
- session export: `/private/tmp/aiwiki_first_round/aiwiki_evidence_integrity/workspaces/20260501-1725-formal/codex_sessions`
- generated report: `/private/tmp/aiwiki_first_round/aiwiki_evidence_integrity/runs/cli-original-aiwiki-evidence-20260501-1725/report.md`
- product report: `/private/tmp/aiwiki_first_round/aiwiki_evidence_integrity/runs/cli-original-aiwiki-evidence-20260501-1725/product_report.md`

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
| `s01` | `no_aiwiki_workflow` | primary control | partial | Added task-level coverage, document stats, managed-doc exclusion, docs, and tests, but used flat shared evidence files and a `record-check` command rather than the expected per-handle reuse-check shape. |
| `s02` | `aiwiki_scaffold_no_target_memory` | diagnostic | success | Added `record-reuse-check`, `refresh-metrics`, per-handle reuse/task-check shards, managed-doc filtering, separate coverage aggregation, explicit write-back guidance, scaffold/docs, and tests. |
| `s03` | `aiwiki_linked_raw_only` | diagnostic | success | Used the raw target drafts and implemented per-handle shards, task-check coverage, managed-doc exclusion, explicit write-back wording, docs, scaffold updates, and tests. |
| `s04` | `aiwiki_linked_consolidated_only` | diagnostic | success | Used consolidated metrics/ownership guidance and implemented task checks, per-handle logs, managed-doc filtering, coverage/audit stats, `refresh-metrics`, docs, and tests. |
| `s05` | `aiwiki_ambient_memory_workflow` | primary treatment | success | Used ambient memory to implement the complete evidence flow: per-handle document/task-check shards, `record-reuse-check`, `refresh-metrics`, managed-doc exclusion, explicit write-back workflow, README/docs/scaffold updates, and tests. |
| `s06` | `aiwiki_scaffold_no_adjacent_memory` | diagnostic | partial | Added task-level reuse/write-back checks, managed-doc exclusion, separate document-vs-coverage stats, docs, and tests, but kept flat shared reuse/task-check logs and recorded several `not_helpful` document events, weakening the evidence-integrity target. |

The manual scores were written with `evals/impact/scripts/score_run.py`. The script report was
generated with `evals/impact/scripts/report_runs.py`, and the product report was generated with
`aiwiki-toolkit eval impact report`.

## Primary Comparison

The primary comparison is `no_aiwiki_workflow` versus `aiwiki_ambient_memory_workflow`.

Result:

- `no_aiwiki_workflow`: partial
- `aiwiki_ambient_memory_workflow`: success

The product report classifies this as a `positive_signal`: ambient AI wiki improved the first-pass
outcome versus no AI wiki under the manual score mapping.

The narrower interpretation is more useful than the binary label. The no-AI-wiki control found the
main idea and implemented a task-level denominator, but missed important evidence-integrity details:
per-handle sharding and the target `record-reuse-check` style audit flow. The ambient AI wiki slot
completed those details and kept the task-level check, document reuse events, managed-doc exclusion,
and explicit write-back decision aligned.

## Diagnostic Signals

The diagnostic slots explain the mechanism:

- `aiwiki_linked_raw_only` and `aiwiki_linked_consolidated_only` both succeeded, so both raw drafts
  and consolidated metric/ownership guidance were sufficient for the intended design.
- `aiwiki_scaffold_no_target_memory` also succeeded, which suggests the managed scaffold/workflow
  context already carried enough of the desired evidence model to solve this task.
- `aiwiki_scaffold_no_adjacent_memory` was partial: it understood the task-check separation but
  missed per-handle evidence sharding and blurred document reuse evidence by logging several
  `not_helpful` observations.

## Change Profile Signal

The product report splits changed files into project files, managed AI wiki files, and user-owned
AI wiki files.

For the primary slots:

- `no_aiwiki_workflow`: `11.00` project files, `0.00` managed AI wiki files, `0.00` user-owned AI
  wiki files
- `aiwiki_ambient_memory_workflow`: `14.00` project files, `4.00` managed AI wiki files, `0.00`
  user-owned AI wiki files

This family is not a small-patch benchmark. Strong solutions naturally touch CLI, schema,
scaffolded workflow text, README/docs, and focused tests. The more meaningful quality signal is
whether the added evidence surfaces preserve audit semantics.

## Validity Threats

Remaining threats:

- This is one sample per condition, not a seed-controlled estimate.
- Manual scoring was artifact-backed but still human judgment.
- The prompt already described the evidence gap in detail, so a strong model could infer much of
  the intended design without task-specific memory.
- Slots ran sequentially, so time/order effects are not ruled out.
- `report_runs.py` still displays `first_pass_success` as `pending` because the capture artifact
  does not encode that field; the product report derives first-attempt success from manual scores.
- Some successful slots recorded local AI wiki telemetry inside the slot worktree. That is expected
  dogfooding evidence, but it increases changed-file counts.

## Bottom Line

For `aiwiki_evidence_integrity`, the first formal result is a positive quality signal for AI wiki
memory, not proof that memory was necessary for the task. The no-AI-wiki control solved the core
idea partially, while the ambient/raw/consolidated AI wiki variants more reliably preserved the
full evidence-integrity contract: document reuse stays separate from task coverage, managed docs do
not inflate knowledge reuse, evidence is sharded by handle, and write-back decisions remain visible.
