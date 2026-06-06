# Reports

This directory holds synthesized reports across completed impact-eval runs.

- `current.md`: current cross-family synthesis.
- `project_a_diagnostics_2026-06-04.md`: verification pass and optimization backlog for the
  Project A coding-agent eval harness.
- `historical_route_replay_2026-06-04.md`: recovered-prompt replay of the latest 57 historical
  evaluable route traces through the current route scorer, using `--catalog-cutoff trace-routed-at`
  to filter known future docs.
- `route_replay_regression_diagnosis_2026-06-04.md`: root-cause analysis for why the current route
  scorer underperformed the historical selected-doc baseline in replay.
- `route_false_positive_research_2026-06-04.md`: trace-by-trace false-positive research over the
  strict 57-trace route replay, including doc-label versus route-logic hypotheses.
