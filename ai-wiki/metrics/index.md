# Metrics Index

This folder is user-owned evidence space for measuring whether the AI wiki is helping in real work.

## Evidence Model

- The end-of-task AI wiki footer is the user-facing evidence surface.
- Local telemetry under `metrics/` is the machine-readable record behind that footer.
- Managed `_toolkit/**` docs guide workflow, but they do not count as knowledge-reuse evidence.

## Files

- `reuse-events/<handle>.jsonl` stores per-handle document-level AI wiki reuse observations.
- `task-checks/<handle>.jsonl` stores per-handle task-level AI wiki reuse checks.
- `aiwiki-toolkit record-reuse ...` appends one document-level observation for the current handle and refreshes managed aggregates.
- `aiwiki-toolkit record-reuse-check ...` appends one task-level reuse check for the current handle and refreshes managed aggregates.
- `aiwiki-toolkit refresh-metrics` regenerates package-managed aggregate views when branches drift or merge conflicts need to be resolved.
- Package-managed aggregate views are generated under `_toolkit/metrics/`.
