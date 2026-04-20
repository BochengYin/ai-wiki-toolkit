# Changelog

All notable changes to `ai-wiki-toolkit` are documented in this file.

## Unreleased

### Added

- Added small-team coding memory scaffolds for `conventions/`, `problems/`, and `features/`.
- Added repo-local `ai-wiki-clarify-before-code` and `ai-wiki-capture-review-learning` skill scaffolds.
- Added managed `team-memory-v1` schema guidance for lightweight team coding memory.
- Added TeamCodingBench roadmap documentation for future baseline-vs-treatment evaluation planning.

### Changed

- Extended AI wiki read order, doctor checks, and prompt guidance to include team conventions, reusable problems, and feature memory.
- Extended doc-kind inference, catalog coverage, and reuse logging paths for convention, problem, and feature docs.
- Expanded the end-of-task AI wiki update and reuse guidance to cover PR review learning, feature clarification, and conflict-aware team memory capture.

## v0.1.10

### Added

- Added managed `.gitignore` telemetry ignores plus `doctor` guidance for untracking legacy AI wiki metrics files.
- Added a repo-local `scripts/pr_flow.py` helper for creating and finishing pull requests in this repository.

### Changed

- Updated repo-local workflow guidance to keep contributor-only PR flow automation out of the distributed package layer.
- Clarified that commit and push steps in this repository must run sequentially, with remote state verified after push.

## v0.1.9

### Added

- Added repo starter indexes for `review-patterns/`, `trails/`, `people/<handle>/`, and `metrics/`.
- Added a machine-readable AI wiki catalog and first reuse schema scaffold under `ai-wiki/_toolkit/`.
- Added `aiwiki-toolkit record-reuse` for appending reuse events and refreshing managed metric aggregates.
- Added `aiwiki-toolkit doctor --suggest-index-upgrade` for diagnosing non-latest AI wiki indexes and printing copy-paste starter content for the affected paths.

### Changed

- Updated the default AI wiki read path to point at folder indexes instead of raw directories.

## v0.1.8

### Added

- Added a manual bootstrap publish path for npm package recovery and first-time platform package publishes.
- Added token-based npm publish fallback support for bootstrap and recovery workflows.
- Added a Linux runtime compatibility check that runs release binaries against older and current glibc container baselines before publish.

### Changed

- Changed the Linux release build lane to build inside a `python:3.11-bookworm` container instead of the host runner so the binary targets an older glibc baseline.
- Normalized manually entered npm release tags in the publish workflow so `0.1.7` and `v0.1.7` resolve consistently.

## v0.1.7

### Changed

- Switched npm distribution from a `postinstall` downloader to a meta package plus platform-specific binary packages.
- Clarified install flow, handle detection, and coding-agent integration in the README.
- Documented that package-manager installs and scaffold initialization are separate steps.

## v0.1.6

### Fixed

- Fixed npm wrapper archive staging so `postinstall` no longer deleted its own downloaded archive before extraction.

## v0.1.3

### Changed

- Aligned distribution metadata and installation docs for public release targets.
- Added explicit license and repository metadata for public package distribution.
- Tightened checks to keep advertised distribution targets aligned with published release assets.

## v0.1.2

### Added

- Added repo-local `.agents/skills/ai-wiki-update-check/` scaffolding.
- Added release version guards across `package.json`, `pyproject.toml`, and `src/ai_wiki_toolkit/__init__.py`.

### Changed

- Expanded install and uninstall behavior to support repo-local skill scaffolding without overwriting existing files.

## v0.1.1

### Changed

- Scoped the public release matrix to macOS and Linux while Windows packaging remained out of the published matrix.
- Tagged the same code snapshot as `v0.1.0` while keeping the early public release line on the supported target set.

## v0.1.0

### Added

- Initial public release skeleton for repo-local and home-level AI wiki scaffolding.
- Base GitHub Release workflow, Homebrew distribution artifacts, and npm wrapper distribution layer.
- Managed prompt-block integration for `AGENT.md`, `AGENTS.md`, and `CLAUDE.md`.
