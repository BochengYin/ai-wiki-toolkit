---
title: Packaged eval runners need real Python script launchers
author_handle: bochengyin
model: gpt-5
source_kind: release_e2e
status: draft
created_at: 2026-05-24
updated_at: 2026-05-24
promotion_candidate: false
promotion_basis: "Observed during the v0.1.36 npm release E2E after v0.1.35 published successfully but failed local eval runner orchestration from the standalone npm binary."
---

# Packaged eval runners need real Python script launchers

When validating the released npm-installed CLI, do not assume `sys.executable` is a Python interpreter. In a PyInstaller or standalone npm binary, `sys.executable` can point at the `aiwiki-toolkit` executable itself.

That breaks helper-script orchestration because a command like:

```text
<sys.executable> evals/impact/scripts/prepare_variants.py ...
```

can become:

```text
aiwiki-toolkit evals/impact/scripts/prepare_variants.py ...
```

Typer then treats the script path as a CLI subcommand and the released binary fails even though source-mode tests pass.

For eval/product release checks, include a dogfood step that runs the npm-installed binary path, not only `uv run` or editable source installs. Helper-script launchers should choose a real Python interpreter from `sys.executable` only when it is Python-like, otherwise fall back to `python3` or `python` from `PATH`.
