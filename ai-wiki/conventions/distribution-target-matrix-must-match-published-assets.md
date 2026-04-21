---
title: "Distribution target matrix must match published assets"
status: "active"
scope: "release and package distribution"
source:
  actor: "BochengYin"
  actor_role: "Maintainer"
  context: "Promotion from repeated release and distribution fixes"
  quote: "Every public distribution target must stay aligned across workflows, package metadata, runtime resolution, archive handling, docs, and smoke checks."
  captured_by: "Codex"
  captured_at: "2026-04-21"
  scope: "Release target and package distribution alignment in this repo"
derived_from:
  - "ai-wiki/people/bochengyin/drafts/distribution-target-matrix-must-match-published-assets.md"
---
# Distribution Target Matrix Must Match Published Assets

## Status

Active.

## Scope

Release and package distribution for `ai-wiki-toolkit`.

## Rule

Every public distribution target must be represented consistently across:

- release workflow matrix
- GitHub Release asset names
- npm platform target maps
- package metadata and install guards
- archive-format handling
- Homebrew formula generation
- release docs
- smoke and release-facing verification

## Examples

- If `windows-arm64` is a public target, publish `windows-arm64.zip`, resolve it in the runtime target map, and smoke-test the installed binary on Windows ARM.
- If Linux `musl` is a public target, keep the musl asset name, npm metadata, build setup, and runtime verification aligned.
- Change the matrix in one coordinated PR instead of updating workflows, docs, and downstream packaging in separate follow-ups.

## Applies When

- adding a new OS, CPU, or libc release target
- renaming published release assets
- changing npm platform package names or install guards
- changing archive formats for published artifacts
- expanding smoke coverage for a release target

## Do Not Use When

- building unpublished local-only development binaries
- testing an experimental target that is not yet part of the public release matrix

## Source Pointer

- Actor: BochengYin
- Actor Role: Maintainer
- Context: Promotion from repeated release and distribution fixes
- Quote or Summary: Every public distribution target must stay aligned across workflows, package metadata, runtime resolution, archive handling, docs, and smoke checks.
- Captured By: Codex
- Captured At: 2026-04-21
- Scope: Release target and package distribution alignment in this repo

## History / Supersedes

- 2026-04-18: The draft captured repeated target drift across release workflows, npm metadata, runtime resolution, archive handling, and docs.
- 2026-04-20: Expanded release targets for Linux ARM64, Linux musl x64, and Windows ARM64 reinforced the need for a coordinated matrix update.
- 2026-04-21: Follow-up musl and Windows ARM smoke fixes showed that verification assumptions must stay aligned with the same matrix.
