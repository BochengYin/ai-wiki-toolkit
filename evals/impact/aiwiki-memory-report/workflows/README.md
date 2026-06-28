# Workflows

These workflows keep the report artifact package coherent as upstream
experiment artifacts change.

Files:

- `capture-exploration-setup.md` - record versioned harness, AI Wiki, hook, and
  prompt setup for each exploration family.
- `refresh-source-of-truth.md` - regenerate derived tables from raw artifacts.
- `check-coverage.md` - flag missing, partial, empty, or phase-row-counted cells.
- `check-stale-dependencies.md` - identify downstream tables and report sections
  that must refresh after upstream changes.
- `sanitize-public-release.md` - replace local paths with logical artifact IDs
  before publishing or sharing externally.
- `update-report.md` - checklist for revising `report.md`.
