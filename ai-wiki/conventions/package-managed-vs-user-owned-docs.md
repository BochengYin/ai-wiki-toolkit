---
title: "Package-managed vs user-owned AI wiki docs"
status: "active"
scope: "repo-wide package design"
source:
  actor: "BochengYin"
  actor_role: "Maintainer"
  context: "PR #13 and promotion from personal draft"
  quote: "Move managed routing to _toolkit system doc"
  captured_by: "Codex"
  captured_at: "2026-04-21"
  scope: "AI wiki ownership boundaries in this repo"
derived_from:
  - "ai-wiki/people/bochengyin/drafts/user-owned-ai-wiki-index-should-not-be-an-upgrade-surface.md"
---
# Package-Managed Vs User-Owned AI Wiki Docs

## Status

Active.

## Scope

Repo-wide package design for AI wiki ownership boundaries.

## Rule

Put evolving package-controlled guidance in `ai-wiki/_toolkit/**`.

Keep user-owned docs such as `ai-wiki/index.md`, `ai-wiki/workflows.md`, `ai-wiki/conventions/**`, `ai-wiki/problems/**`, and `ai-wiki/features/**` stable unless a repo contributor intentionally edits them.

## Examples

- Put package-managed start-of-task routing in `ai-wiki/_toolkit/system.md`.
- Keep `ai-wiki/index.md` as a repo-owned map instead of comparing it against the latest starter text.
- Refresh managed prompt blocks and managed `_toolkit/**` docs when package read order changes.

## Applies When

- adding new package-managed routing
- updating prompt read order
- changing `doctor` checks for starter drift
- deciding whether a file should be refreshed automatically on `install`

## Do Not Use When

- editing repo-specific knowledge manually
- recording team-specific coding knowledge that belongs in user-owned conventions, problems, or features
- promoting a personal draft into shared memory outside package design boundaries

## Source Pointer

- Actor: BochengYin
- Actor Role: Maintainer
- Context: PR #13 and promotion from a personal design draft
- Quote or Summary: Move managed routing to `_toolkit/system.md` and keep `ai-wiki/index.md` repo-owned
- Captured By: Codex
- Captured At: 2026-04-21
- Scope: AI wiki ownership boundaries in this repo

## History / Supersedes

- 2026-04-20: PR #13 moved package-managed routing to `ai-wiki/_toolkit/system.md`.
- Supersedes the earlier expectation that `doctor --suggest-index-upgrade` should compare existing `ai-wiki/index.md` files against the latest starter navigation.
