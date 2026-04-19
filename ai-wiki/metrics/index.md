# Metrics Index

This folder is user-owned evidence space for measuring whether the AI wiki is helping in real work.

## Files

- `reuse-events/<handle>.jsonl` stores per-handle document-level AI wiki reuse observations.
- `task-checks/<handle>.jsonl` stores per-handle task-level AI wiki reuse checks.
- `aiwiki-toolkit record-reuse ...` appends one document-level observation for the current handle and refreshes managed aggregates.
- `aiwiki-toolkit record-reuse-check ...` appends one task-level reuse check for the current handle and refreshes managed aggregates.
- `aiwiki-toolkit refresh-metrics` regenerates package-managed aggregate views when branches drift or merge conflicts need to be resolved.
- Package-managed aggregate views are generated under `_toolkit/metrics/`.
