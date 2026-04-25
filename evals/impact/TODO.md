# Impact Eval TODO

This file tracks benchmark families that still need to be designed or run.

Use this as the first entrypoint when opening a new session to continue impact-eval work.

## Reusable Benchmark Recipe

Unless a family clearly needs a different harness, reuse the Manual v2 workflow-primary harness:

1. choose a real historical problem, not a synthetic toy task
2. pick a baseline commit from before the fix landed
3. define the primary workflow comparison:
   - `no_aiwiki_workflow`
   - `aiwiki_ambient_memory_workflow`
4. define the diagnostic variants:
   - `aiwiki_scaffold_no_target_memory`
   - `aiwiki_linked_raw_only`
   - `aiwiki_linked_consolidated_only`
5. define one `original` prompt that recreates the historical request without adding the answer
6. run each neutral slot in a fresh persisted Codex CLI session
7. save artifacts with:
   - `prepare_variants.py`
   - `init_run.py`
   - `save_result.py`
   - `export_codex_sessions.py`
   - `validate_run.py`
   - `score_run.py`
   - `report_runs.py`
8. require `codex_sessions/manifest.json` before making shareable workflow or causal claims
9. grade the results with the manual rubric:
   - `success`
   - `partial`
   - `fail`

Reference implementation:

- `evals/impact/notes/index.md`
- `evals/impact/report.md`
- `evals/impact/ownership_boundary_runbook.md`
- `evals/impact/notes/manual_v2_original_10_repo_findings.md`
- `evals/impact/notes/ownership_boundary_round1_findings.md`

## Publication Prep

Current public-writeup draft:

- `evals/impact/public_writeup_draft.md`

Published artifact repository:

- https://github.com/BochengYin/ai-wiki-toolkit-impact-eval-artifacts

The public note itself should stay focused on the experiment, results, limitations, and artifact
links. Keep publication logistics in this TODO or release-prep notes rather than in the public note.

Recommended publishing layout:

- keep stable benchmark materials in this repository under `evals/impact/`
- do not commit large or sensitive raw session exports directly into the source tree
- publish redacted per-run artifacts as a GitHub Release artifact bundle, Git LFS artifact repo, or
  separate `eval-artifacts` repository
- use Gist, a blog post, or a social post only as a short narrative pointer back to the repo and
  artifact bundle

Before publishing an artifact bundle:

1. collect each run's `assignment.json`, `confounds.json`, `scores.json`, generated `report.md`, slot
   `workspace_diff.patch`, `visible_transcript.md`, `visible_session.jsonl`,
   `first_pass/final_message.md`, and `codex_sessions/manifest.json`
2. decide whether full raw session exports can be public
3. redact or withhold any logs containing API keys, tokens, cookies, credentials, private URLs,
   personal identifiers, unrelated filesystem details, unpublished product context, or private chat
   content
4. if raw logs are withheld, publish visible logs plus SHA-256 hashes of the raw logs and state why
   the raw files are withheld
5. update `evals/impact/public_writeup_draft.md` with final artifact links
6. run `git diff --check`

Initial 2026-04-25 scan notes:

- focused scan over the five formal run dirs plus exported `codex_sessions/` found no obvious
  token-shaped secrets such as OpenAI keys, GitHub PATs, npm tokens, PyPI tokens, Slack tokens, AWS
  access keys, Google API keys, or private keys
- raw session exports still contain local filesystem paths, sandbox paths, and skill/plugin
  inventory; treat those as redaction candidates before publishing raw logs
- email-like matches were public GitHub noreply or test/example fixture addresses; still re-check
  before publishing a final bundle
- published `ai-wiki-toolkit-impact-eval-artifacts` with visible artifacts only; raw
  `session_without_reasoning.jsonl` files are omitted and represented by SHA-256 hashes

## Status Legend

- `done`: benchmark family has already been run and documented
- `next`: high-priority next family to design
- `planned`: likely future family, but task/prompt design still needs work
- `needs-more-signals`: promising family, but current raw/consolidated evidence is still too thin

## Family Backlog

| family | status | type | core question | likely source memory |
| --- | --- | --- | --- | --- |
| `ownership_boundary` | `done` | repeated-problem / surface-choice | does AI wiki memory keep a contributor-only helper out of package code? | `repo-local-contributor-workflows-should-stay-out-of-the-package-layer`, adjacent ownership/prompt docs |
| `release_distribution_integrity` | `done` | repeated-problem / coordinated multi-surface change | when a public distribution target changes, does memory help the agent keep workflows, asset names, npm metadata, archive handling, docs, and smoke checks aligned? | `ai-wiki/conventions/distribution-target-matrix-must-match-published-assets.md`, source draft, related release-fix drafts |
| `windows_arm_smoke_cli_output` | `done` | narrow repeated-problem benchmark | does memory help the agent fix the exact Windows ARM smoke assertion by comparing against full CLI output instead of the bare version? | `ai-wiki/problems/windows-arm-smoke-version-checks-need-full-cli-output.md` |
| `release_runtime_compatibility` | `done` | repeated-problem / release-runtime verification | does memory help the agent choose an older glibc baseline and add runtime verification instead of stopping at build or install success? | `linux-release-binaries-need-runtime-checks-against-an-older-glibc-baseline.md` |
| `postinstall_archive_staging` | `planned` | repeated-problem / packaging | does memory help the agent avoid self-deleting npm postinstall staging paths? | `npm-postinstall-must-not-delete-its-own-download-archive.md` |
| `scaffold_prompt_workflow_compliance` | `done` | workflow-compliance | when changing scaffold or prompt behavior, does memory help the agent update tests, rerun install, and avoid prompt churn? | `ai-wiki/workflows.md`, `shared-prompt-files-must-be-user-agnostic.md`, prompt-churn drafts |
| `aiwiki_evidence_integrity` | `planned` | telemetry / end-of-task workflow | does memory help the agent preserve the distinction between document-level reuse events and task-level checks, and always run update checks? | `ai-wiki-usefulness-metrics-need-task-level-checks-plus-doc-events.md`, `end-of-task-ai-wiki-update-check-must-always-run.md`, `ai-wiki-reuse-metrics-should-exclude-managed-docs-and-shard-by-handle.md` |
| `capture_vs_consolidation` | `needs-more-signals` | consolidation-design benchmark | when consolidation exists, does it improve reuse without creating shared-doc churn or overwriting end-of-task capture? | `consolidation-should-layer-over-end-of-task-capture-and-avoid-shared-doc-churn.md` |

## Notes Per Family

### ownership_boundary

Already run.

Artifacts:

- `evals/impact/ownership_boundary_runbook.md`
- `evals/impact/notes/ownership_boundary_round1_findings.md`

### release_distribution_integrity

Already run and documented.

Artifacts:

- `evals/impact/release_distribution_integrity_runbook.md`
- `evals/impact/notes/release_distribution_integrity_round1_findings.md`
- `evals/impact/notes/round1_process_lessons.md`

Current defended takeaway:

- this family is useful for coordinated multi-surface completeness
- it is less discriminating than `ownership_boundary short` for basic success/failure
- full prompt surface still needs tighter control before stronger causal claims

Why this family was still a strong candidate:

- a promoted shared convention
- a detailed source draft
- repeated multi-surface failures across workflows, npm, docs, and smoke verification

### windows_arm_smoke_cli_output

Run and documented.

Artifacts:

- `evals/impact/notes/manual_v2_cli_original_windows_arm_20260425_findings.md`
- `/private/tmp/aiwiki_first_round/windows_arm_smoke_cli_output/runs/cli-original-windows-arm-20260425-1618/report.md`

Current defended takeaway:

- all six slots succeeded
- the family is deterministic and useful for harness smoke coverage
- it is not strong evidence that AI wiki memory is necessary because the no-AI-wiki primary control also succeeded

### release_runtime_compatibility

Run and documented.

Artifacts:

- `evals/impact/notes/manual_v2_cli_original_release_runtime_20260425_findings.md`
- `/private/tmp/aiwiki_first_round/release_runtime_compatibility/runs/cli-original-runtime-20260425-1618/report.md`

Current defended takeaway:

- the no-AI-wiki primary control was partial because it added smoke gates but left `linux-x64` on the newer `ubuntu-24.04` build baseline
- the ambient AI wiki primary treatment succeeded by adding an older build baseline plus release/npm runtime verification
- diagnostics also succeeded, so the claim is usefulness in the primary comparison, not necessity

### postinstall_archive_staging

This is another good narrow repeated-problem family.

The benchmark would likely test whether the agent:

- keeps transient downloads outside disposable target directories
- fixes the staging layout rather than misdiagnosing the remote asset

### scaffold_prompt_workflow_compliance

Run and documented.

Artifacts:

- `evals/impact/notes/manual_v2_cli_original_scaffold_prompt_workflow_20260425_findings.md`
- `/private/tmp/aiwiki_first_round/scaffold_prompt_workflow_compliance/runs/cli-original-scaffold-20260425-1618/report.md`

Current defended takeaway:

- the no-AI-wiki primary control was partial because it implemented broad scaffold changes but drifted on naming/routing
- the ambient AI wiki primary treatment succeeded and stayed aligned with repo memory for areas, skills, managed routing, docs, and tests
- diagnostics also succeeded, so the family is workflow-compliance evidence rather than proof that target memory is necessary

### aiwiki_evidence_integrity

This family is less about code placement and more about end-of-task workflow correctness.

It would likely test whether the agent:

- records task-level checks
- separates document events from denominator coverage
- avoids counting managed `_toolkit/**` docs as reuse evidence
- always emits an update outcome

This family may need a slightly different scoring rubric from `ownership_boundary`.

### capture_vs_consolidation

This is not the best next family yet.

It is still more of a design hypothesis than a benchmark with a clean direct task.

Promote it later if more concrete consolidation tasks appear.

## Suggested Next Session Starts

If you want the closest follow-on to the current release family:

1. `postinstall_archive_staging`

If you want the next broader release/verification benchmark:

1. `aiwiki_evidence_integrity`

If you want the next workflow-style benchmark:

1. `capture_vs_consolidation` after more concrete signals exist
