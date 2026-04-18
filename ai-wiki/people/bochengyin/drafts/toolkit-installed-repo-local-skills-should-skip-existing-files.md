---
title: "Toolkit-installed repo-local skills should skip existing files"
author_handle: "bochengyin"
model: "unknown"
source_kind: "review"
status: "draft"
created_at: "2026-04-18T13:45:00Z"
updated_at: "2026-04-18T13:45:00Z"
promotion_candidate: false
promotion_basis: "none"
---
# Review Draft

## Context

We wanted `aiwiki-toolkit install` to set up a repo-local Codex skill for the AI wiki update check, but without breaking user-owned skill files or other repo-local skill customizations.

## What Went Wrong

Treating repo-local skill files like managed files would violate the same no-touch boundary we already enforce for user-owned wiki documents.

## Bad Example

- Install a toolkit-owned skill by overwriting an existing `.agents/skills/ai-wiki-update-check/SKILL.md`.
- Replace user-customized decision rules or output contract files during install.

## Fix

Treat the repo-local skill as starter scaffolding:

- create missing files under `.agents/skills/ai-wiki-update-check/`
- skip existing files instead of overwriting them
- tell the user which files were skipped
- print a manual merge URL back to the toolkit repository

## Reuse Assessment

This should generalize to other agent-harness packages that want to seed repo-local skills without taking ownership of user-customized skill contents.

## Promotion Decision

Keep as a draft until we validate the same rule with at least one more repo-installed skill.
