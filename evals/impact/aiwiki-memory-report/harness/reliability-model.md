# Reliability Model

Current round guardrails:

- Runs can resume from `chain.json`.
- Long queues can be monitored through live logs.
- Step coverage is counted by unique `(prev_version, next_version)` pairs.
- Empty `0/0/0` shells are quarantined in `coverage-status.md`.
- Current source-of-truth tables exclude empty shells from result tables.
- Imported narrative materials are treated as context, not numeric source of truth.

Still-needed automation:

- Standard detached queue runner and watcher.
- Coverage generation from raw `eval.json`.
- Flags for missing, partial, empty, or phase-row-counted cells before publication.
- Dependency-aware report refresh workflow.
- Memory root, prompt marker, hook config, and cross-group contamination checks.
- Runner parity schema for execution location, conversation policy, effort,
  token, cost, latency, and timeout data.
