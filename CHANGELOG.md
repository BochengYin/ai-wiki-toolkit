# Changelog

All notable changes to `ai-wiki-toolkit` are documented in this file.

## Unreleased

## v0.1.21

### Added

- Added a public AI wiki impact-eval pilot write-up with protocol details, artifact links, and
  non-statistical claim boundaries.

### Changed

- Clarified the `ai-wiki/constraints.md` and `ai-wiki/decisions.md` starter files so new installs
  explain that mostly empty project-specific docs are intentional placeholders, not missing package
  defaults.

## v0.1.20

### Added

- Added completed CLI-first impact-eval documentation for Windows ARM smoke output, release runtime compatibility, and scaffold prompt workflow compliance.

### Changed

- Reworded the user-facing AI wiki footer around task relevance, impact, and write-back outcomes instead of internal eligibility and update-candidate labels.
- Changed `aiwiki-toolkit install` to refresh package-owned repo-local `.agents/skills/ai-wiki-*` files so existing repos receive updated workflow and footer contracts after package upgrades.

## v0.1.19

### Fixed

- Fixed the `linux-musl-x64` release lane to install `git` alongside `binutils` inside the Alpine build container, so release-time tests that shell out to Git keep passing during packaging.

## v0.1.18

### Fixed

- Fixed `aiwiki-toolkit install` so duplicate options in unrelated `.git/config` sections no longer crash handle resolution; the installer now falls back to Git's own config parser when Python's `configparser` rejects the file.

## v0.1.17

### Added

- Added runtime AI wiki memory candidate detection guidance for problem-solution memory, feature clarification memory, missed relevant memory, and conflict-aware update decisions.
- Added `docs/ai-wiki-usefulness-metrics-v2.md` to define eligibility-aware coverage, material reuse, and missed-memory metrics for AI wiki evaluation.

### Changed

- Reframed end-of-task AI wiki reuse guidance around a user-facing evidence footer, task eligibility, and material-reuse hints instead of an extra visible check step.
- Updated generated prompt blocks, managed workflow docs, and repo-local skill scaffolds to emit AI wiki evidence and update outcomes with clearer routing rules.
- Updated the Python package description to position `ai-wiki-toolkit` as a repository-native AI wiki memory harness for coding agents.

### Fixed

- Fixed Windows ARM smoke workflow version assertions to compare against the CLI's full `ai-wiki-toolkit <version>` output.

## v0.1.16

### Fixed

- Fixed the `linux-musl-x64` release lane so Alpine package setup can run as root before switching back to the normal containerized build flow, allowing `binutils` and `objdump` to be installed during release packaging.

## v0.1.15

### Fixed

- Fixed the `linux-musl-x64` release container to install `binutils` before running PyInstaller, so Alpine-based musl builds provide the required `objdump` tool during binary packaging.

## v0.1.14

### Fixed

- Fixed the `linux-musl-x64` release lane by importing `pytest` in `tests/test_doctor.py`, so the tracked-telemetry skip path works inside minimal musl build containers.

## v0.1.13

### Added

- Added a repo-local `ai-wiki-release-tag` skill plus `scripts/pr_flow.py tag-release` helper so release tags can be created from synced `main` with version verification.

### Fixed

- Fixed release-facing tests and build helpers that still carried cross-platform assumptions after the target-matrix expansion.
- Normalized digest fixtures and tree snapshot assertions so Windows newline and traversal-order differences no longer break release CI.
- Stopped requiring POSIX-only uid/gid APIs in Docker build arguments and skipped tracked-telemetry git coverage when `git` is unavailable in minimal musl build containers.

## v0.1.12

### Added

- Added public release targets for `linux-arm64`, `linux-musl-x64`, and `windows-arm64`.
- Added a dedicated `Release Smoke Windows ARM` workflow that verifies the published `windows-arm64.zip` asset and npm install path on `windows-11-arm`.

### Changed

- Extended the npm platform target map and package metadata to cover Linux `glibc` versus `musl`, Linux ARM64, and Windows ARM64.
- Extended Linux build and runtime verification helpers so release workflows can validate the new Linux ARM64 and musl targets.
- Extended the generated Homebrew formula and release documentation to reflect the expanded public target matrix.

## v0.1.11

### Added

- Added small-team coding memory scaffolds for `conventions/`, `problems/`, and `features/`.
- Added repo-local `ai-wiki-clarify-before-code` and `ai-wiki-capture-review-learning` skill scaffolds.
- Added managed `team-memory-v1` schema guidance for lightweight team coding memory.
- Added TeamCodingBench roadmap documentation for future baseline-vs-treatment evaluation planning.

### Changed

- Extended AI wiki read order, doctor checks, and prompt guidance to include team conventions, reusable problems, and feature memory.
- Extended doc-kind inference, catalog coverage, and reuse logging paths for convention, problem, and feature docs.
- Expanded the end-of-task AI wiki update and reuse guidance to cover PR review learning, feature clarification, and conflict-aware team memory capture.
- Moved the evolving repo read-order entrypoint to managed `ai-wiki/_toolkit/system.md` so `ai-wiki/index.md` can remain a repo-owned map instead of a package upgrade surface.

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
