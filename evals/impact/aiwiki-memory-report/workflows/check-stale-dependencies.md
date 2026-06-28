# Check Stale Dependencies

Treat report drift as dependency invalidation.

Dependency graph:

```text
raw eval.json + audit overrides
  -> source-of-truth tables
  -> report sections
  -> imported narrative summaries, if reused
```

When an upstream artifact changes:

1. Identify the logical artifact ID in `manifests/artifacts.public.yaml`.
2. Find `derived_tables` for that artifact.
3. Refresh or mark those source-of-truth tables stale.
4. Search `report.md` for sections that cite those tables.
5. Mark dependent prose stale until reviewed.
6. Do not let imported narrative material override refreshed source-of-truth
   tables.

This workflow should eventually become a small report-maintenance skill.
