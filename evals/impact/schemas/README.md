# Manual v2 Artifact Schemas

The v2 harness uses lightweight JSON contracts instead of a database.

## Workspace Assignment

`assignment.json` lives beside `slots/` in a prepared workspace root. It records:

- `schema_version`
- `experiment`
- `baseline_ref`
- `workspace_layout`
- `primary_comparison`
- `diagnostic_variants`
- `slots`: neutral slot id, semantic variant, and workspace path

Variant names must stay out of workspace paths.

## Result Capture

`save_result.py --phase first_pass` writes under:

```text
<run-dir>/<slot>/<prompt-level>/first_pass/
```

Manual v2 uses `original` as the default and intended prompt level. Legacy round1 levels such as
`short`, `medium`, and `full` remain readable for old artifacts only.

`--phase final` writes under the sibling `final/` directory. Capture artifacts record workspace
facts only; they do not assign a manual score.

## Score

`score_run.py` writes:

```text
<run-dir>/<slot>/<prompt-level>/score.json
```

Allowed labels are `success`, `partial`, and `fail`.

## Confounds

`validate_run.py` writes `<run-dir>/confounds.json`.

Critical confounds include missing session exports, prompt mismatches, session reuse, and semantic
variant-name leaks through paths or visible transcripts.

Formal CLI-first runs also require a complete `codex_sessions/manifest.json`. The validator treats
missing manifests, incomplete manifests, non-CLI session sources, model mismatches, and reasoning
effort mismatches as critical confounds.
