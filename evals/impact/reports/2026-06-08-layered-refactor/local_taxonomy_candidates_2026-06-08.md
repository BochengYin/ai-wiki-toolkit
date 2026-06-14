# Taxonomy Candidate Induction

Generated at: `2026-06-08T13:46:16+10:00`

## Filters

- Handle: `bochengyin`
- Minimum evidence: 2

## Summary

- Evidence events scanned: 3
- Clusters considered: 2
- Candidates: 1
- Shadow candidates: 0
- Rejected clusters: 1
- Active taxonomy changed: false

## Candidates

### Candidate 1: tax_route-phase-planning

- Kind: `agent_runtime_taxonomy`
- Status: `proposed`
- Active: `false`
- Gate 1: `passed` with 2 evidence events
- Gate 2: `not_run`

When:
- Use when repeated route evidence matches `route_phase_planning` language, for example: Planning/research prompts about why router misclassified planning-only prompts can be routed as code/bug_fix or wrong fixed workflow.

Do:
- Classify this as `route-phase-planning` in shadow mode, route against that category, and compare selected docs plus downstream behavior before activation.

Excluding:
- Do not activate from this candidate until Gate 2 proves improvement without regression; do not use it when the task only mentions this label as an example.

Source evidence:
- `txe_a6d9c6285907`
- `txe_f52a3a6314c5`

## Rejected Clusters

- `code-phase-for-upgrade-task` rejected: insufficient_evidence (1/2 evidence).

## Notes

- This report induces TaxonomyCandidate records only; it never activates taxonomy.
- Gate 1 is repeated coherent local evidence.
- Gate 2 requires a supplied shadow replay or behavior test result that improves routing without regression.
- Candidates stay proposed when Gate 2 is missing or fails.
