---
title: "Post-turn hooks should be opt-in"
author_handle: "bochengyin"
model: "gpt-5"
source_kind: "feature_clarification"
status: "draft"
created_at: "2026-05-25T20:00:00+1000"
updated_at: "2026-05-25T20:04:00+1000"
promotion_candidate: false
promotion_basis: "single product design signal"
---
# Draft

## Context

While discussing automatic trial/error capture, we clarified that `ai-wiki-toolkit` should not
silently install agent post-turn hooks during package-manager installation.

## Clarification

Package install should only make the `aiwiki-toolkit` binary available. It should not mutate user
agent configuration, add lifecycle scripts, or start background behavior.

Repo setup through `aiwiki-toolkit install` may refresh managed prompt blocks, managed `_toolkit/**`
files, repo-local skills, `.gitignore`, and the namespaced `aiwikiToolkit` key where supported.

Post-turn capture should be an explicit opt-in step, such as a future `aiwiki-toolkit hooks install`
or `aiwiki-toolkit install --enable-post-turn-hook`, with a dry-run preview, idempotent managed
config block, uninstall support, and a clear per-agent target like Codex, Claude Code, or OpenCode.

The hook itself should call:

```bash
aiwiki-toolkit source-incident capture-post-turn --apply
```

Default installation should recommend this step. `doctor` should report whether post-turn capture
evidence has been recorded for the current handle, without failing strict mode when no hook is
configured yet.

Until the project has stable runtime-specific hook installers, this recommendation should stay as an
explicit command suggestion rather than a real `--enable-post-turn-hook` implementation.

## Reuse Assessment

Use this when designing installation, hook setup, package-manager behavior, or cross-agent adapter
support for source incident capture.
