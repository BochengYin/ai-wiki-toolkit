# Impact Eval Families

Each family directory contains a `spec.toml` file that defines the historical baseline and the
memory docs used by the workflow-primary v2 harness.

The spec separates:

- `raw_docs`: source drafts tied to the historical problem family
- `raw_overlays`: family-local fixture files copied into raw-memory destinations
- `consolidated_docs`: linked shared docs for diagnostic consolidation checks
- `consolidated_overlays`: family-local fixture files copied into consolidated-memory destinations
- `ambient_exclude_paths`: eval-process notes that should not leak into realistic treatment repos

Prompt files currently remain under `evals/impact/prompts/<family>/` for round1 compatibility.
Future families can move prompts under their family directory once the runbooks are updated.
