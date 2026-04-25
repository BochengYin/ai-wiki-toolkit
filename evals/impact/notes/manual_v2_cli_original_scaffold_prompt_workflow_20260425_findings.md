# Manual v2 CLI Original Scaffold Prompt Workflow Findings

This note records the clean formal `scaffold_prompt_workflow_compliance` run from 2026-04-25.

It used Codex CLI-first execution for every slot, persisted one independent session per slot, and
validated the exported session manifest before scoring.

## Scope

Run label:

- `cli-original-scaffold-20260425-1618`

Prompt/model condition:

- prompt: `evals/impact/prompts/scaffold_prompt_workflow_compliance/original.md`
- model: `gpt-5.5`
- reasoning effort: `xhigh`
- execution surface: `codex-cli`

Run artifacts:

- workspace root: `/private/tmp/aiwiki_first_round/scaffold_prompt_workflow_compliance/workspaces/20260425-160315`
- run dir: `/private/tmp/aiwiki_first_round/scaffold_prompt_workflow_compliance/runs/cli-original-scaffold-20260425-1618`
- session export: `/private/tmp/aiwiki_first_round/scaffold_prompt_workflow_compliance/workspaces/20260425-160315/codex_sessions`
- generated report: `/private/tmp/aiwiki_first_round/scaffold_prompt_workflow_compliance/runs/cli-original-scaffold-20260425-1618/report.md`

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
| `s01` | `no_aiwiki_workflow` | primary control | partial | Added most scaffold surfaces, but drifted into `problem-solutions/`, `ai-wiki-clarify-coding-task`, `ai-wiki-pr-review-learning`, and older `_toolkit/index.md` prompt routing. |
| `s02` | `aiwiki_scaffold_no_target_memory` | diagnostic | success | Added `conventions/`, `problems/`, `features/`, correct skill names, managed schema, prompt guidance, doctor/catalog updates, README, and tests. |
| `s03` | `aiwiki_linked_raw_only` | diagnostic | success | Same complete scaffold expansion with correct areas, skills, managed schema, docs, doctor/catalog updates, and tests. |
| `s04` | `aiwiki_linked_consolidated_only` | diagnostic | success | Same complete scaffold expansion while preserving create-if-missing user-owned docs and skip-if-existing skills. |
| `s05` | `aiwiki_ambient_memory_workflow` | primary treatment | success | Implemented the requested starter areas, skill templates, schema/workflow guidance, doctor checks, README, and tests; minor caveat is less catalog-kind coverage than other successes. |
| `s06` | `aiwiki_scaffold_no_adjacent_memory` | diagnostic | success | Implemented correct areas, skills, managed schema, prompt/system/workflow guidance, doctor/catalog/docs/tests, and passed pytest/diff check. |

The manual scores were written with `evals/impact/scripts/score_run.py` and the aggregate report was
generated with `evals/impact/scripts/report_runs.py`.

## Primary Comparison

The primary comparison is `no_aiwiki_workflow` versus `aiwiki_ambient_memory_workflow`.

Result:

- `no_aiwiki_workflow`: partial
- `aiwiki_ambient_memory_workflow`: success

The no-AI-wiki slot understood the broad task and implemented many correct surfaces. Its miss was
workflow/naming consistency: it invented `problem-solutions/`, `ai-wiki-clarify-coding-task`, and
`ai-wiki-pr-review-learning`, and kept prompt guidance routed through the older `_toolkit/index.md`
shape.

The ambient AI wiki slot stayed aligned with the existing memory structure: `conventions/`,
`problems/`, `features/`, `ai-wiki-clarify-before-code`, `ai-wiki-capture-review-learning`, managed
schema guidance, prompt/system workflow updates, doctor checks, README, and tests.

Interpretation: this run supports a workflow-discipline version of the AI wiki usefulness claim. The
benefit is not simply completing the task; it is using the same names, routing, and compatibility
boundaries that the repo had been converging on.

## Diagnostic Variants

Diagnostics explain possible mechanisms but are not the primary conclusion.

`aiwiki_scaffold_no_target_memory`, `aiwiki_linked_raw_only`, and `aiwiki_linked_consolidated_only`
all succeeded. This suggests that the scaffold and adjacent repo memory were already enough to
stabilize the intended naming and prompt-routing conventions.

`aiwiki_scaffold_no_adjacent_memory` also succeeded. That narrows the mechanism claim: the task
itself plus generic scaffold/workflow memory can be enough for a strong implementation. The primary
comparison still shows an AI wiki workflow advantage over no AI wiki, but this family should be read
as workflow-compliance evidence rather than proof that target memory is necessary.

## Validity Threats

Remaining threats:

- This is one sample per condition, not a seed-controlled estimate.
- Manual scoring was artifact-backed but still human judgment.
- The prompt itself explicitly names the broad scaffold surfaces, so the benchmark primarily tests
  naming/routing discipline and compatibility coverage.
- No downstream package release was performed; success is inferred from diffs and test runs.
- Slots ran sequentially, so time/order effects are not ruled out.
- `s05` scored success despite less catalog-kind coverage than several other slots; that caveat
  should be considered in any later replication.

## Bottom Line

For `scaffold_prompt_workflow_compliance`, the primary comparison directionally supports "AI wiki
working mode is useful": the no-AI-wiki slot was a broad partial implementation with naming/routing
drift, while the ambient AI wiki slot stayed aligned with the repo's established scaffold and prompt
workflow.

The diagnostic successes keep the claim narrow. AI wiki workflow improved discipline in the primary
comparison; target memory was not necessary for all successful diagnostic slots.
