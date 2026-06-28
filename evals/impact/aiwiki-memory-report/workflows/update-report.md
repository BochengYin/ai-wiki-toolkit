# Update Report

Use this workflow when revising `report.md`.

1. Read `source-of-truth/README.md`.
2. Check `source-of-truth/coverage-status.md`.
3. Use `source-of-truth/buildfix-absolute-metrics.md` for valid absolute
   build+fix counts and rates.
4. Use `source-of-truth/cross-model-net-improvement.md` for cross-repo delta
   claims.
5. Use `source-of-truth/020-flask-hook-ablation.md` only for the single-repo
   Flask hook ablation.
6. Check `protocol/runner-parity.md` before making cross-runner claims.
7. Check `protocol/leakage-boundaries.md` before writing memory-causality or
   writeback claims.
8. If any upstream source changed, run `check-stale-dependencies.md` first.
