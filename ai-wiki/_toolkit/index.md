# Toolkit Managed Index

This directory is managed by ai-wiki-toolkit. Future package versions may update it.

## Read Order

1. Read `system.md` for package-managed collaboration rules.
2. Read `workflows.md` for package-managed baseline workflows.
3. Read `schema/route-v1.md` when task-aware context packets or routing trust boundaries matter.
4. Read `schema/work-v1.md` when work-ledger events, task lifecycle state, or generated work reports matter.
5. Read `schema/team-memory-v1.md` when note shapes, memory types, or source pointers matter.
6. Read `schema/reuse-v1.md` only when reuse metrics, logging, or schema questions matter.

## Generated Outputs

- `catalog.json`, `metrics/*.json`, and `work/*` are generated outputs, not guidance docs.
- `aiwiki-toolkit route` emits transient context packets to stdout; packets are derived from source docs and should be regenerated rather than treated as canonical memory.
- The installer ignores those generated outputs in `.gitignore` so routine telemetry updates stay local.
- Regenerate catalog, metrics, and work views with `aiwiki-toolkit refresh-metrics` whenever you need a fresh local snapshot.
