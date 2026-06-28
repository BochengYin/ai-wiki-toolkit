# Setup Manifest Schema

Required fields:

- `setup_id`: stable logical setup ID.
- `setup_version`: semantic or date-based setup version.
- `exploration`: human-readable exploration family.
- `protocol_arms`: arms covered by the setup.
- `harness_components`: versioned components from
  `../manifests/harness-components.public.yaml`.
- `agent_policy`: runner, model, effort, execution location, and session policy.
- `aiwiki_surface`: whether AI Wiki is disabled, prompt-only, native, hook-based,
  exact-gated, or writeback-enabled.
- `hooks`: lifecycle hook configuration summary.
- `memory_policy`: memory read/write rules and leakage boundaries.
- `artifact_outputs`: expected output artifacts.
- `source_tables`: tables that cite runs produced by this setup.
- `known_caveats`: interpretation limits.

Recommended fields:

- `created_for_report_date`
- `supersedes`
- `staleness_triggers`
- `public_redaction`

Use logical IDs and fingerprints, not local absolute paths.
