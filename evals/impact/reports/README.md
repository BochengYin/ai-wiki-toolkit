# Reports

This directory holds synthesized impact-eval reports. Generated reports are grouped by run family so
the root stays readable.

## Entry Points

- `synthesis/current.md`: current cross-family synthesis.
- `2026-06-08-layered-refactor/local_layered_experiment_report_2026-06-08.md`: local decision report
  for the 2026-06-08 layered route refactor experiments.
- `2026-06-08-layered-refactor/aiwiki_toolkit_layered_architecture_2026-06-08.md`: architecture
  write-up for the layered route design.

## Report Groups

- `project-a-2026-06-04/`: Project A diagnostics and optimization backlog.
- `route-research-2026-06-04/`: strict route replay, false-positive research, precision cohort, and
  regression diagnosis.
- `route-method-2026-06-05/`: route precision handoff after the 57-trace research pass.
- `phase-plan-2026-06-06/`: phase-plan replay, behavior harness, Codex runtime capability smoke, and
  activation decision.
- `layered-route-2026-06-07/`: layered replay, activation, and eval-stage ablation reports for the
  57-trace cohorts.
- `2026-06-08-layered-refactor/`: all-58 local replay, ablation, behavior, taxonomy, clean pre/post,
  trace-signal, and fresh VS Code forward artifacts.
- `synthesis/`: cross-family synthesis reports.

## Notes

- Raw or temporary local run data belongs under `evals/impact/local_experiment/`.
- Some generated replay rows preserve original user prompts. Those rows may contain historical paths
  that were valid when the prompt was written; treat them as evidence text, not current file links.
