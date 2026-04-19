# `aiwiki-toolkit doctor` Proposal

This document proposes a future `aiwiki-toolkit doctor` command for diagnosing repo AI wiki health without rewriting user-owned docs.

## Why A Doctor Command

`ai-wiki-toolkit` now has a stronger schema story:

- repo-visible folder indexes such as `review-patterns/index.md`
- machine-readable catalog data under `ai-wiki/_toolkit/catalog.json`
- managed metric aggregates under `ai-wiki/_toolkit/metrics/`
- explicit reuse logging through `aiwiki-toolkit record-reuse`

The installer intentionally does **not** rewrite existing user-owned files under `ai-wiki/**/*.md`.

That compatibility rule is important, but it also means older repositories can drift into a state where:

- `ai-wiki/index.md` still points at raw folders instead of child indexes
- expected child indexes are missing
- `metrics/reuse-events.jsonl` has not been scaffolded yet
- prompt files still reference an older navigation shape
- the repo is valid, but no longer aligned with the latest recommended structure

A `doctor` command would help surface that gap without crossing the boundary into automatic user-doc mutation.

## Goals

- detect common AI wiki structure drift
- explain what is missing, stale, or inconsistent
- suggest safe next actions
- avoid silently editing user-owned docs
- reuse the same compatibility guarantees as `install`

## Non-Goals

- automatically rewrite `ai-wiki/index.md` or other user-owned Markdown
- merge conflicting user content
- infer semantic correctness of arbitrary custom wiki structures
- replace `install`

## Command Shape

Proposed entrypoint:

```bash
aiwiki-toolkit doctor
```

Possible future flags:

```bash
aiwiki-toolkit doctor --format text
aiwiki-toolkit doctor --format json
aiwiki-toolkit doctor --strict
aiwiki-toolkit doctor --write-report ai-wiki/_toolkit/doctor-report.json
```

Recommended v1 scope:

- `--format text` default human-readable output
- `--format json` for machine consumption
- non-zero exit only for `--strict` when actionable warnings exist

## Core Checks

### 1. Repo Initialization

Check that the current directory resolves to a git repo and that `ai-wiki/` exists.

Example findings:

- `ERROR`: no git repository root found
- `ERROR`: `ai-wiki/` missing
- `WARN`: `ai-wiki/_toolkit/system.md` missing

### 2. Top-Level Navigation Shape

Check whether the repo-local index points to the current recommended navigation model.

Suggested checks:

- does `ai-wiki/index.md` exist
- does it mention `review-patterns/index.md`
- does it mention `trails/index.md`
- does it mention `people/<handle>/index.md`
- does it mention `metrics/`

This should remain advisory only.

Example finding:

- `WARN`: `ai-wiki/index.md` exists but does not mention child indexes; repo likely predates the current index-based navigation shape

### 3. Child Index Presence

Check for expected child indexes:

- `ai-wiki/review-patterns/index.md`
- `ai-wiki/trails/index.md`
- `ai-wiki/metrics/index.md`
- `ai-wiki/people/<handle>/index.md` for the resolved handle

Important distinction:

- if the directory exists but the index is missing, suggest creation
- if the directory and index both exist, do not inspect or rewrite user content

Example findings:

- `WARN`: `ai-wiki/review-patterns/` exists but `review-patterns/index.md` is missing
- `INFO`: `ai-wiki/people/alice/index.md` is missing; create one if you want handle-local draft navigation

### 4. Managed Layer Freshness

Check whether managed files expected from the current package exist:

- `ai-wiki/_toolkit/system.md`
- `ai-wiki/_toolkit/catalog.json`
- `ai-wiki/_toolkit/schema/reuse-v1.md`
- `ai-wiki/_toolkit/metrics/document-stats.json`
- `ai-wiki/_toolkit/metrics/task-stats.json`

These are package-managed, so the recommended fix can safely be:

```bash
aiwiki-toolkit install
```

Example finding:

- `WARN`: `ai-wiki/_toolkit/catalog.json` missing; rerun `aiwiki-toolkit install` to refresh managed files

### 5. Reuse Logging Readiness

Check whether the evidence path is usable:

- `ai-wiki/metrics/reuse-events.jsonl`
- package-managed `_toolkit/metrics/*.json`

Example findings:

- `INFO`: `ai-wiki/metrics/reuse-events.jsonl` missing; create it or rerun `install` if the repo has not been initialized with the latest scaffold
- `INFO`: no reuse events recorded yet

### 6. Prompt Block Alignment

Check prompt files in the repo root:

- `AGENT.md`
- `AGENTS.md`
- `CLAUDE.md`

Suggested validations:

- prompt file contains managed block markers
- managed block references `review-patterns/index.md`
- managed block references `people/<handle>/index.md`

This remains safe because the command only diagnoses.

Example finding:

- `WARN`: managed prompt block references older draft-folder navigation instead of person index navigation

### 7. Catalog Coverage

Compare user-owned Markdown files under `ai-wiki/` with entries in `_toolkit/catalog.json`.

Useful checks:

- missing catalog file
- catalog exists but omits a current user-owned document
- catalog includes a path that no longer exists

This helps catch stale managed outputs.

## Output Model

Recommended severity levels:

- `ERROR`: repo cannot safely use toolkit features in the current state
- `WARN`: repo works, but is drifting from the recommended structure
- `INFO`: advisory note or optional improvement
- `OK`: explicit positive confirmation

Text output should stay concise. Example:

```text
Repo: /path/to/repo
Handle: alice

OK   ai-wiki/ exists
OK   ai-wiki/_toolkit/system.md exists
WARN ai-wiki/index.md does not mention review-patterns/index.md
WARN ai-wiki/review-patterns/index.md is missing
INFO no reuse events recorded yet

Suggested next steps:
1. Run `aiwiki-toolkit install` to refresh managed files.
2. Add `ai-wiki/review-patterns/index.md` if you want index-based navigation.
3. Update `ai-wiki/index.md` manually to reference child indexes.
```

JSON output should include structured findings with machine-readable codes, for example:

```json
{
  "repo_root": "/path/to/repo",
  "resolved_handle": "alice",
  "findings": [
    {
      "severity": "warn",
      "code": "missing_review_patterns_index",
      "path": "ai-wiki/review-patterns/index.md",
      "message": "Directory exists but child index is missing.",
      "suggested_fix": "Create the index manually or let install create it if it is absent."
    }
  ]
}
```

## Suggested Fix Strategy

The command should separate suggestions into two classes.

### Safe Automated Follow-Up

These can be fixed by rerunning `install`:

- missing managed `_toolkit/**` files
- stale prompt managed blocks
- missing package-managed metric aggregates

### Manual User-Owned Follow-Up

These should never be auto-written by `doctor` in v1:

- updating `ai-wiki/index.md`
- creating or editing a custom `review-patterns/index.md`
- creating or editing `trails/index.md`
- changing `people/<handle>/index.md` content

The command may suggest patches later, but v1 should stop at diagnosis.

## Optional Future Extensions

### `doctor --suggest-index-upgrade`

This could print a recommended patch for:

- `ai-wiki/index.md`
- missing child indexes

Still do not write automatically; only emit a suggestion.

### `doctor --fix-managed`

This could be a convenience alias for rerunning the managed refresh path, equivalent to:

```bash
aiwiki-toolkit install
```

It should remain limited to package-managed outputs.

### `doctor --strict`

Useful in CI or repo policy checks:

- exit `1` on `ERROR`
- optionally exit `1` on `WARN`

## Recommended v1 Implementation Order

1. Add a pure diagnostic `doctor` command with text output.
2. Add finding codes and JSON output.
3. Add prompt-block and catalog coverage checks.
4. Consider suggestion-mode for manual index migration.

This order keeps compatibility intact while still giving older repos a clear path toward the newer schema.
