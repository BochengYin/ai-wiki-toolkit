# Artifact Manifest Schema

The manifests are intentionally small and portable.

## Run Fields

- `run_id`: stable logical ID, formatted as `<family>/<group>/<chain>`.
- `family`: experiment family.
- `arm`: protocol arm.
- `runner`: agent runner, such as `codex` or `claudecode`.
- `provider`: model provider.
- `model`: model name.
- `effort`: reasoning effort when known.
- `chain`: package/version chain.
- `setup`: `<setup_id>@<setup_version>` from `../setups/`.
- `artifacts`: logical artifact URIs.
- `source_tables`: report tables that cite or derive from the run.

## Artifact Fields

- `artifact_id`: stable logical URI, usually `artifacts://...`.
- `kind`: artifact type, such as `chain_json`, `eval_json`, or `live_log_jsonl`.
- `run_id`: logical run that produced the artifact.
- `public_status`: `external`, `sampled`, `included`, or `local_only`.
- `derived_tables`: source-of-truth tables that depend on the artifact.

## Local Resolution

Local workflows may resolve logical IDs through `local-paths.yaml`. That file is
ignored by git and may contain local absolute paths.
