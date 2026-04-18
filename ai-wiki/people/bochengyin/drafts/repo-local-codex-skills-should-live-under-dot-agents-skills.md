---
title: "Repo-local Codex skills should live under .agents/skills"
author_handle: "bochengyin"
model: "unknown"
source_kind: "review"
status: "draft"
created_at: "2026-04-18T13:28:00Z"
updated_at: "2026-04-18T13:28:00Z"
promotion_candidate: false
promotion_basis: "none"
---
# Review Draft

## Context

We initially added a repo-local `ai-wiki-update-check` skill under `.codex/skills/`, then compared it against the Codex skill documentation and the built-in `skill-creator` guidance.

## What Went Wrong

The first implementation had the right idea but used the wrong repo-local discovery path and packed too much detail into a single `SKILL.md`.

## Bad Example

- Put a repo-local skill under `.codex/skills/`.
- Use one large `SKILL.md` for trigger metadata, workflow, decision rules, and examples.

## Fix

For repo-local Codex skills:

- place the skill under `.agents/skills/<skill-name>/`
- keep `SKILL.md` focused on trigger description and core workflow
- move detailed rules and examples into `references/`
- optionally add `agents/openai.yaml` for UI metadata

## Reuse Assessment

This looks reusable anywhere we want repo-scoped Codex workflows to be checked into source control and discovered consistently by other contributors.

## Promotion Decision

Keep as a draft until we validate the same structure in at least one more repo-local skill.
