# Impact Eval Notes Index

Use this file as the ordered reading path for impact-eval evidence. Family runbooks describe how to
reproduce a benchmark. Notes describe what a specific run or design iteration found. The report
synthesizes across notes.

## Read Order

1. `evals/impact/README.md`
   Current benchmark framing, workspace layout, and CLI-first execution protocol.
2. `evals/impact/report.md`
   Current synthesis across completed runs, including what can and cannot be claimed.
3. `evals/impact/notes/manual_v2_cli_original_ownership_20260425_findings.md`
   The clean formal CLI-first ownership-boundary run.
4. `evals/impact/notes/manual_v2_original_10_repo_findings.md`
   The earlier 10-repo original-prompt transition run across both benchmark families.
5. `evals/impact/ownership_boundary_runbook.md`
   Reproduction spec and rubric for the ownership-boundary family.
6. `evals/impact/release_distribution_integrity_runbook.md`
   Reproduction spec and rubric for the release-distribution family.
7. `evals/impact/notes/round1_process_lessons.md`
   Historical round1 process lessons and why v2 changed the harness.
8. `evals/impact/notes/ownership_boundary_round1_findings.md`
   Historical ownership-boundary short/medium results.
9. `evals/impact/notes/release_distribution_integrity_round1_findings.md`
   Historical release-distribution short results.
10. `evals/impact/notes/ownership_boundary_v0_failure.md`
   Original failed benchmark design and prompt leakage.

## Run Chronology

| order | note | status | role |
| --- | --- | --- | --- |
| 1 | `ownership_boundary_v0_failure.md` | historical | explains why the first prompt design could not answer the question |
| 2 | `ownership_boundary_round1_findings.md` | historical | first repaired ownership-boundary evidence |
| 3 | `release_distribution_integrity_round1_findings.md` | historical | first release-distribution evidence |
| 4 | `round1_process_lessons.md` | historical/process | captures process failures that v2 addresses |
| 5 | `manual_v2_original_10_repo_findings.md` | transition run | 10-repo original-prompt evidence and remaining confounds |
| 6 | `manual_v2_cli_original_ownership_20260425_findings.md` | current formal run | clean CLI-first ownership-boundary primary comparison |

## Documentation Roles

- Runbooks stay relatively stable and describe family setup, variants, prompts, protocol, and rubric.
- Notes are append-only-ish run records for a concrete batch.
- `report.md` is the human-facing synthesis. It should cite notes rather than restating every diff.
