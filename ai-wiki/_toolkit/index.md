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

- `catalog.json`, `consolidation/*`, `diagnostics/*`, `metrics/*.json`, and `work/*` are generated outputs, not guidance docs.
- `aiwiki-toolkit route` emits transient context packets to stdout; packets are derived from source docs and should be regenerated rather than treated as canonical memory.
- The installer ignores local identity and generated outputs in `.gitignore` so routine agent use stays local.
- Regenerate catalog, metrics, and work views with `aiwiki-toolkit refresh-metrics` whenever you need a fresh local snapshot.
- Generate local memory quality diagnostics with `aiwiki-toolkit diagnose memory` when you need to inspect missed, stale, noisy, conflicting, or high-ROI memory.
- Generate a local draft consolidation and promotion review queue with `aiwiki-toolkit consolidate queue`.
