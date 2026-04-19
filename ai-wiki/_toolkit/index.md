# Toolkit Managed Index

This directory is managed by ai-wiki-toolkit. Future package versions may update it.

## Read Order

1. Read `system.md` for package-managed collaboration rules.
2. Read `workflows.md` for package-managed baseline workflows.
3. Read `schema/reuse-v1.md` only when reuse metrics, logging, or schema questions matter.

## Generated Outputs

- `catalog.json` and `metrics/*.json` are generated outputs, not guidance docs.
- The installer ignores those generated outputs in `.gitignore` so routine telemetry updates stay local.
- Regenerate those outputs with `aiwiki-toolkit refresh-metrics` whenever you need a fresh local snapshot.
