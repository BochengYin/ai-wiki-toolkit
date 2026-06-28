# Capture Exploration Setup

Use this workflow whenever a new exploration starts or an existing exploration
changes its harness, AI Wiki setup, hooks, prompt gate, or writeback policy.

1. Create or update component records in
   `manifests/harness-components.public.yaml`.
2. Fingerprint any script-like components, such as launcher scripts or
   `generate/*.py`, with SHA-256.
3. Record AI Wiki install mode, prompt markers, hook config, router policy,
   memory read gate, writeback timing, and leakage boundary.
4. Create a new setup manifest under `setups/` with a new `setup_version`.
5. Link runs in `manifests/runs.public.yaml` to the setup version when the run
   registry is refreshed.
6. Add staleness triggers for any component that would invalidate derived
   source-of-truth tables or report claims.
7. Keep local absolute paths in ignored `manifests/local-paths.yaml`.

Do not silently mutate old setup manifests after a run has been cited. If a
component changed, create a new setup version.
