# `aiwiki-toolkit doctor` Proposal

This document proposes a future `aiwiki-toolkit doctor` command for diagnosing AI wiki structure drift, with v1 focused mainly on outdated or missing index files.

## Why Narrow The Scope

`ai-wiki-toolkit` now has a clearer navigation shape:

- `ai-wiki/index.md`
- `ai-wiki/review-patterns/index.md`
- `ai-wiki/trails/index.md`
- `ai-wiki/people/<handle>/index.md`
- `ai-wiki/metrics/index.md`

The package intentionally does **not** rewrite user-owned files under `ai-wiki/**/*.md` after they have been created.

That compatibility rule is correct, but it creates a practical problem:

- older repos may still have a legacy `ai-wiki/index.md`
- child indexes may be missing
- prompt files may already point at the newer index-based read path
- the repo is still valid, but the navigation model is out of date

The simplest high-value `doctor` pass is therefore:

1. detect index drift
2. explain it clearly
3. suggest a safe upgrade path

## V1 Goal

Focus `doctor` on one narrow question:

> Is this repo still using the current recommended AI wiki index structure?

This keeps the first implementation small and directly addresses the most likely upgrade gap.

## V1 Non-Goals

- rewriting user-owned indexes automatically
- merging custom prose into an upgraded index
- diagnosing every possible AI wiki health issue
- replacing `install`

## Proposed Command Shape

Base command:

```bash
aiwiki-toolkit doctor
```

Likely flags:

```bash
aiwiki-toolkit doctor --format text
aiwiki-toolkit doctor --format json
aiwiki-toolkit doctor --strict
aiwiki-toolkit doctor --suggest-index-upgrade
```

Recommended v1 behavior:

- default output is human-readable text
- JSON output is optional
- `--strict` exits non-zero on actionable warnings
- `--suggest-index-upgrade` prints upgrade guidance without writing user-owned files

## Core V1 Checks

### 1. Repo Initialization

Check:

- does the current directory resolve to a git repo
- does `ai-wiki/` exist
- does `ai-wiki/index.md` exist

Example findings:

- `ERROR`: no git repository root found
- `ERROR`: `ai-wiki/` missing
- `WARN`: `ai-wiki/index.md` missing

### 2. Top-Level Index Shape

Check whether `ai-wiki/index.md` reflects the current navigation model.

Suggested signals:

- mentions `review-patterns/index.md`
- mentions `trails/index.md`
- mentions `people/<handle>/index.md`
- mentions `metrics/`

Example finding:

- `WARN`: `ai-wiki/index.md` exists but still points at raw folders instead of child indexes

### 3. Child Index Presence

Check for:

- `ai-wiki/review-patterns/index.md`
- `ai-wiki/trails/index.md`
- `ai-wiki/metrics/index.md`
- `ai-wiki/people/<handle>/index.md` for the resolved handle

Example findings:

- `WARN`: `ai-wiki/review-patterns/index.md` missing
- `INFO`: `ai-wiki/people/alice/index.md` missing for the current handle

### 4. Prompt Block Alignment

Check root prompt files:

- `AGENT.md`
- `AGENTS.md`
- `CLAUDE.md`

Suggested checks:

- managed block exists
- managed block references `review-patterns/index.md`
- managed block references `people/<handle>/index.md`

This is useful because a repo can end up in a partially upgraded state where prompt wiring expects indexes but the indexes themselves are missing.

### 5. Managed Refresh Availability

Check whether `_toolkit/**` exists and is fresh enough to support the newer structure:

- `ai-wiki/_toolkit/system.md`
- `ai-wiki/_toolkit/catalog.json`
- `ai-wiki/_toolkit/schema/reuse-v1.md`

These are package-managed and can safely be refreshed by rerunning:

```bash
aiwiki-toolkit install
```

## Output Model

Recommended severity levels:

- `ERROR`: repo cannot safely use the toolkit in its current state
- `WARN`: repo works, but index navigation is not aligned with the recommended structure
- `INFO`: optional improvement
- `OK`: explicit confirmation

Example text output:

```text
Repo: /path/to/repo
Handle: alice

OK   ai-wiki/ exists
OK   ai-wiki/_toolkit/system.md exists
WARN ai-wiki/index.md still uses legacy folder navigation
WARN ai-wiki/review-patterns/index.md is missing
INFO ai-wiki/people/alice/index.md is missing

Suggested next steps:
1. Run `aiwiki-toolkit install` to refresh managed files.
2. Add missing child indexes manually.
3. Update `ai-wiki/index.md` manually or use `doctor --suggest-index-upgrade`.
```

## Suggested Upgrade Strategy

V1 should separate fixes into two buckets.

### Safe Automatic Follow-Up

These are package-managed and can be refreshed safely:

- `_toolkit/system.md`
- `_toolkit/catalog.json`
- `_toolkit/schema/reuse-v1.md`

Recommended action:

```bash
aiwiki-toolkit install
```

### Manual User-Owned Follow-Up

These should remain manual in v1:

- `ai-wiki/index.md`
- `ai-wiki/review-patterns/index.md`
- `ai-wiki/trails/index.md`
- `ai-wiki/people/<handle>/index.md`
- `ai-wiki/metrics/index.md`

The repo owner may have custom content in those files, so `doctor` should not overwrite them silently.

## `--suggest-index-upgrade`

This is the most useful next step after bare diagnosis.

Instead of writing user-owned files directly, the command should print:

- which indexes are missing
- which links in `ai-wiki/index.md` look outdated
- the latest recommended starter text or patch for each missing/outdated index

Possible output shape:

```text
Suggested index upgrades:

- ai-wiki/index.md
  Replace legacy folder references with:
  - review-patterns/index.md
  - trails/index.md
  - people/<handle>/index.md
  - metrics/

- ai-wiki/review-patterns/index.md
  File is missing. Suggested starter content:
  ...
```

This gives the user or an agent enough structure to apply a patch consciously.

## Agent-Assisted Upgrade Flow

If the user wants help upgrading indexes, the cleanest workflow is:

1. run `aiwiki-toolkit doctor`
2. see the warnings
3. run `aiwiki-toolkit doctor --suggest-index-upgrade`
4. let the agent apply the suggested patch in the target repo

This keeps the decision visible and avoids hidden mutation of user-owned docs.

## Should The Agent Fetch A Webpage?

Not by default.

Fetching a rendered GitHub webpage is the wrong source for index upgrades because:

- HTML is presentation-layer output, not source content
- headings, code fences, and list structure can be distorted
- links may be rewritten into absolute UI URLs
- extracting clean Markdown from the page is brittle

## Better Source Priority

If an agent needs the latest recommended index content, use this order:

1. local installed toolkit template content
2. raw source content from the upstream repository
3. rendered web pages only as a fallback of last resort

For `ai-wiki-toolkit`, the most stable source is the package's own template content in `src/ai_wiki_toolkit/content.py`.

If the target repo is on an older installed version and the user explicitly wants the newest upstream recommendation, the agent can fetch the raw source file from GitHub and extract the relevant starter content.

It should still propose a patch, not silently overwrite the repo's user-owned index.

## Future Extension: Prompt Emission Instead Of Direct Patches

If you want a lighter-weight v1.5, `doctor --suggest-index-upgrade` could emit a ready-to-use agent prompt like:

```text
Your repo AI wiki index is using a legacy structure.
Compare the current `ai-wiki/index.md` with the recommended index starter below.
Preserve repo-specific notes, but update the navigation to reference:
- review-patterns/index.md
- trails/index.md
- people/<handle>/index.md
- metrics/
Also create any missing child indexes using the suggested starter content.
```

That is safer than automatic writing and easier to implement than a structural Markdown merge engine.

## Recommended Implementation Order

1. Add `doctor` with text warnings for index drift and missing child indexes.
2. Add `--suggest-index-upgrade` that prints suggested starter content or a patch.
3. Add JSON output and machine-readable finding codes.
4. Later, consider broader health checks beyond indexes.

This keeps the first `doctor` implementation tightly aligned with the real migration problem: older repos that still have non-latest index files.
