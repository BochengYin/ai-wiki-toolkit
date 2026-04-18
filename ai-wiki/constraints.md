# Project Constraints

These are repo-specific constraints that should be treated as hard boundaries.

## Compatibility Guarantees

1. User-owned Markdown under `ai-wiki/` is `Strict no-touch` by default.
2. Package-managed writes are limited to `ai-wiki/_toolkit/**`, `<home>/ai-wiki/system/_toolkit/**`, managed prompt blocks, and the namespaced `aiwikiToolkit` key in `opencode.json`.
3. Uninstall must preserve shared home wiki content by default.
4. Purge behavior must not delete user-owned cross-project content under `<home>/ai-wiki/system/`.

## Shared Prompt File Rules

1. `AGENTS.md`, `AGENT.md`, and `CLAUDE.md` are repo-shared files, not user-private files.
2. Managed prompt instructions must remain user-agnostic.
3. Never write concrete local identities such as `alice` or `bob` into a repo-shared managed block.
4. Use placeholders such as `<handle>` when a per-user path needs to be referenced.

## Distribution Rules

1. GitHub Release binaries are the source of truth for downstream distribution.
2. Homebrew and npm distribution layers must consume those release assets, not fork business logic.
3. Release tags must point at commits where the relevant workflow fixes are already merged to `main`.

## Test Expectations

1. Filesystem behavior changes require before/after state-transition tests.
2. Release-facing tests must avoid platform-specific assumptions about newlines, path separators, or shell behavior.
