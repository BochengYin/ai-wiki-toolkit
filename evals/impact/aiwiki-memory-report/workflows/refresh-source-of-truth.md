# Refresh Source Of Truth

Use this workflow when raw `eval.json`, an audit override, or an artifact
manifest changes.

1. Resolve logical artifact IDs through the ignored `manifests/local-paths.yaml`
   mapping or an external artifact archive.
2. Recompute coverage by unique `(prev_version, next_version)` pairs.
3. Refresh `source-of-truth/coverage-status.md`.
4. Refresh `source-of-truth/buildfix-absolute-metrics.md` for valid build+fix
   cells.
5. Refresh `source-of-truth/cross-model-net-improvement.md` for comparable
   cross-repo delta rows.
6. Keep `source-of-truth/020-flask-hook-ablation.md` separate from cross-repo
   stop-only cells.
7. Record which raw logical artifacts and audit overrides changed.
8. Mark dependent report sections stale until reviewed.
