# Impact Eval Notes Index

Use this file as the ordered reading path for impact-eval evidence. Family runbooks describe how to
reproduce a benchmark. Notes describe what a specific run or design iteration found. The report
synthesizes across notes.

## Read Order

1. `evals/impact/README.md`
   Current benchmark framing, workspace layout, and CLI-first execution protocol.
2. `evals/impact/reports/current.md`
   Current synthesis across completed runs, including what can and cannot be claimed.
3. `evals/impact/notes/manual_v2_cli_original_ownership_20260425_findings.md`
   The clean formal CLI-first ownership-boundary run, extended with supplemental `s06`.
4. `evals/impact/notes/manual_v2_cli_original_release_distribution_20260425_findings.md`
   The clean formal CLI-first release-distribution run, extended with supplemental `s06`.
5. `evals/impact/notes/manual_v2_cli_original_release_runtime_20260425_findings.md`
   The clean formal CLI-first release-runtime compatibility run.
6. `evals/impact/notes/manual_v2_cli_original_scaffold_prompt_workflow_20260425_findings.md`
   The clean formal CLI-first scaffold/prompt workflow-compliance run.
7. `evals/impact/notes/manual_v2_cli_original_windows_arm_20260425_findings.md`
   The clean formal CLI-first Windows ARM smoke-output run.
8. `evals/impact/notes/manual_v2_cli_original_postinstall_archive_20260430_findings.md`
   The clean formal CLI-first postinstall archive-staging run.
9. `evals/impact/notes/manual_v2_cli_original_aiwiki_evidence_20260501_findings.md`
   The clean formal CLI-first AI wiki evidence-integrity run.
10. `evals/impact/notes/manual_v2_original_10_repo_findings.md`
   The earlier 10-repo original-prompt transition run across both benchmark families.
11. `evals/impact/runbooks/ownership_boundary.md`
   Reproduction spec and rubric for the ownership-boundary family.
12. `evals/impact/runbooks/release_distribution_integrity.md`
   Reproduction spec and rubric for the release-distribution family.
13. `evals/impact/notes/round1_process_lessons.md`
   Historical round1 process lessons and why v2 changed the harness.
14. `evals/impact/notes/ownership_boundary_round1_findings.md`
   Historical ownership-boundary short/medium results.
15. `evals/impact/notes/release_distribution_integrity_round1_findings.md`
   Historical release-distribution short results.
16. `evals/impact/notes/ownership_boundary_v0_failure.md`
   Original failed benchmark design and prompt leakage.

## Run Chronology

| order | note | status | role |
| --- | --- | --- | --- |
| 1 | `ownership_boundary_v0_failure.md` | historical | explains why the first prompt design could not answer the question |
| 2 | `ownership_boundary_round1_findings.md` | historical | first repaired ownership-boundary evidence |
| 3 | `release_distribution_integrity_round1_findings.md` | historical | first release-distribution evidence |
| 4 | `round1_process_lessons.md` | historical/process | captures process failures that v2 addresses |
| 5 | `manual_v2_original_10_repo_findings.md` | transition run | 10-repo original-prompt evidence and remaining confounds |
| 6 | `manual_v2_cli_original_ownership_20260425_findings.md` | current formal run + supplemental diagnostic | clean CLI-first ownership-boundary primary comparison plus `s06` no-adjacent mechanism check |
| 7 | `manual_v2_cli_original_release_distribution_20260425_findings.md` | current formal run + supplemental diagnostic | clean CLI-first release-distribution primary comparison plus `s06` no-adjacent mechanism check |
| 8 | `manual_v2_cli_original_windows_arm_20260425_findings.md` | current formal run | narrow Windows ARM smoke-output benchmark |
| 9 | `manual_v2_cli_original_release_runtime_20260425_findings.md` | current formal run | release-runtime compatibility primary comparison and diagnostics |
| 10 | `manual_v2_cli_original_scaffold_prompt_workflow_20260425_findings.md` | current formal run | scaffold/prompt workflow-compliance primary comparison and diagnostics |
| 11 | `manual_v2_cli_original_postinstall_archive_20260430_findings.md` | current formal run | postinstall archive-staging primary comparison and diagnostics |
| 12 | `manual_v2_cli_original_aiwiki_evidence_20260501_findings.md` | current formal run | AI wiki evidence-integrity primary comparison and diagnostics |

## Documentation Roles

- Runbooks stay relatively stable and describe family setup, variants, prompts, protocol, and rubric.
- Notes are append-only-ish run records for a concrete batch.
- `reports/current.md` is the human-facing synthesis. It should cite notes rather than restating
  every diff.
