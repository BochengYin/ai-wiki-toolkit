# Protocol

This directory defines the experiment protocol in public, portable terms.

Use these files to understand what was tested before reading result tables:

- `arms.md` - arm definitions and memory surfaces.
- `metrics.md` - metric definitions and reader-facing terminology.
- `leakage-boundaries.md` - what information may enter prompts or memory.
- `runner-parity.md` - Codex and Claude Code runner differences.

Protocol docs should avoid local absolute paths. Link to logical run IDs from
`../manifests/runs.public.yaml` when a concrete example is needed.
