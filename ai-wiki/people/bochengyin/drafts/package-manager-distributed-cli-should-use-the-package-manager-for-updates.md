---
title: "Package-manager distributed CLIs should use the package manager for updates"
author_handle: "bochengyin"
model: "gpt-5"
source_kind: "review"
status: "draft"
created_at: "2026-04-19T15:12:31+1000"
updated_at: "2026-04-19T15:12:31+1000"
promotion_candidate: false
promotion_basis: "none"
---
# Review Draft

## Context

We redesigned the npm distribution of `ai-wiki-toolkit` from a `postinstall` downloader to a meta package plus platform-specific binary packages.

During that change, we also decided whether the CLI should grow its own update command.

## What Went Wrong

It is tempting to add a custom self-update function whenever install or upgrade UX feels important.

For package-manager distributed CLIs, that usually duplicates responsibility that already belongs to npm, Homebrew, or another upstream installer and creates a second source of truth for version state, permissions, and rollback behavior.

## Bad Example

- distribute a CLI through npm or Homebrew
- add a custom `tool update` command that mutates the global install out of band
- require users to reason about both package-manager state and tool-managed state

## Fix

Let the package manager own installation and updates.

For npm, document commands like `npm update -g <package>` or `npm install -g <package>@latest` instead of implementing self-update inside the CLI.

Design package topology so the top-level package update naturally refreshes the correct platform-specific binary package.

## Reuse Assessment

This is reusable across binary-distributed CLIs, especially when a meta package delegates to platform packages or prebuilt release assets.

The more packaging layers involved, the more important it is to keep update authority in one place.

## Promotion Decision

Keep as a draft for now. Promote if the same package-manager-versus-self-update decision appears again in another CLI distribution task.
