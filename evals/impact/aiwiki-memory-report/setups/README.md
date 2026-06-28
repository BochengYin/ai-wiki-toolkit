# Setups

This directory records versioned setup manifests for experiment explorations.

Each setup manifest answers:

- Which harness component versions ran the exploration?
- Which agent runner, model, effort, and session policy were used?
- How was AI Wiki installed or disabled?
- Which prompts, hooks, writeback mechanisms, and memory selection rules were
  active?
- Which source-of-truth tables depend on the setup?

Do not mutate a setup manifest when the underlying runner or AI Wiki mechanism
changes. Add a new `setup_version` and update the relevant run registry entries.

Public setup manifests must not contain local absolute paths. Use component IDs
from `../manifests/harness-components.public.yaml` and artifact IDs from
`../manifests/artifacts.public.yaml`.
