---
title: "Intentionally empty starter docs need empty-state guidance"
author_handle: "bochengyin"
model: "gpt-5.5"
source_kind: "user_feedback"
status: "draft"
created_at: "2026-04-25T13:00:00Z"
updated_at: "2026-04-25T13:00:00Z"
promotion_candidate: false
promotion_basis: "none"
---
# Review Draft

## Context

A user asked why `ai-wiki/constraints.md` and `ai-wiki/decisions.md` looked empty after install.

Those files are intentionally project-specific and user-owned. The package should not fill them with
generic active rules or fake decisions, because agents may treat that content as real team memory.

## What Went Wrong

The starter files were semantically correct but too terse. A nearly empty user-owned doc can look
like a broken install or missing setup step if it does not explain why it is blank.

## Bad Example

```md
# Project Decisions

Capture durable architectural and process decisions here.
```

## Fix

When a starter doc is intentionally empty or project-specific, include an empty-state explanation:

- state that the file is intentionally project-specific
- explain that no entries means the team has not recorded that kind of memory yet
- give examples of appropriate entries without turning them into active defaults
- keep package-managed evolving guidance in `_toolkit/**`

## Reuse Assessment

This should apply to future starter files that are meant to be filled by the user, especially files
that agents may read as authoritative project memory.

## Promotion Decision

Keep as a draft until this pattern appears in another starter or install-feedback issue.
