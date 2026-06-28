# Manifests

Public manifests define logical runs and artifacts without exposing local
absolute paths.

Files:

- `runs.public.yaml` - logical run registry.
- `artifacts.public.yaml` - logical artifact registry.
- `harness-components.public.yaml` - versioned runner, prompt, AI Wiki, and
  hook components used by setup manifests.
- `artifact-schema.md` - schema notes for the manifests.
- `local-paths.example.yaml` - template for ignored local path mapping.

`local-paths.yaml` is intentionally ignored by git. It may contain workstation
paths for local refresh workflows, but it must not be committed.
