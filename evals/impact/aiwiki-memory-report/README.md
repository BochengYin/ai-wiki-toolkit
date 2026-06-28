# AI Wiki Memory SWE-Chain Report Artifact Package

This directory is the public-facing artifact package and local writing workspace
for the AI Wiki memory report. It keeps report materials, source-of-truth
tables, harness documentation, and sanitized artifact manifests inside this
repository without committing large SWE-Chain raw run artifacts or local
absolute paths.

## Layout

- `protocol/` - experiment definitions: arms, metrics, leakage boundaries, and
  runner-parity caveats.
- `harness/` - how the SWE-Chain experiment harness runs: entrypoints, step
  lifecycle, artifact contracts, and reliability model.
- `setups/` - versioned setup manifests for each exploration family, including
  harness component versions, AI Wiki install surfaces, prompts, hooks, and
  writeback policy.
- `manifests/` - public logical run/artifact registries plus an ignored local
  path mapping example.
- `artifacts/` - small sanitized examples and notes about optional external
  artifact archives.
- `workflows/` - maintenance workflows for refreshing source-of-truth tables and
  flagging stale dependencies.
- `audits/codex-data-audit-20260627.md` - audit notes after checking imported
  packet data against raw `eval.json` and selected `chain.json` artifacts.
- `source-of-truth/` - report-level canonical tables to cite first while
  reporting.
- `report.md` - current report.
- `raw-artifacts/` - ignored local scratch area for optional copied raw
  artifacts.
- `materials/` - ignored local-only working notes. Do not commit this directory.

## Artifact Boundary

Public files use logical artifact IDs such as
`artifacts://swe-chain-019/raw-codex/flask_2.0.0_to_2.3.3/eval.json`.
Local absolute paths belong only in `manifests/local-paths.yaml`, which is
ignored by git. Do not expose workstation paths in public report text or public
manifests. Run `workflows/sanitize-public-release.md` before treating this
package as public-ready.

Local notes and imported Markdown tables are convenient local writing material,
not the original measurement source. Numeric source of truth remains the raw
SWE-Chain `eval.json` files named by the logical manifests and audits. Do not
copy local notes, full `chain.json`, `live_log.jsonl`, or
`live_results.jsonl` trees into git; they are large and should stay in local
experiment roots or an external artifact archive.

## Working Rules

Before writing or revising the report:

1. Read `audits/codex-data-audit-20260627.md`.
2. Use `source-of-truth/cross-model-net-improvement.md` as the main
   cross-repo comparison table.
3. Use `source-of-truth/020-flask-hook-ablation.md` for the 020 hook sweep.
4. Mark partial evals explicitly.
5. Keep 020 Flask hook-ablation numbers separate from 020 cross-repo stop-only
   numbers.
6. Refresh status prose from current `eval.json` before publishing.
7. Use software-testing terminology in reader-facing prose: fixed target
   behavior, missed target behavior, introduced unrelated regression, and
   preserved unrelated behavior. Avoid leading with SWE-Chain's raw
   `TP`/`FN`/`FP`/`TN` labels because AI Wiki memory here is not ML model
   training.
8. When raw artifacts or audit overrides change, follow
   `workflows/check-stale-dependencies.md` and refresh dependent
   source-of-truth tables or mark report sections stale.
9. When an exploration setup changes, create a new setup version under
   `setups/` and update `manifests/harness-components.public.yaml` rather than
   mutating old setup records in place.
