---
title: "Shared prompt files must be user-agnostic"
author_handle: "bochengyin"
model: "unknown"
source_kind: "review"
status: "active"
created_at: "2026-04-18T22:15:00+10:00"
updated_at: "2026-04-18T22:15:00+10:00"
derived_from: "ai-wiki/trails/2026-04-18-release-workflow-and-prompt-block-edge-cases.md"
promotion_basis: "reviewer_judgment"
---

# Shared Prompt Files Must Be User-Agnostic

## Problem Pattern

Managed prompt content writes concrete local user identities into repo-shared files such as `AGENTS.md`, `AGENT.md`, or `CLAUDE.md`.

## Why It Happens

The tool needs to reference per-user paths like `ai-wiki/people/<handle>/drafts/`, and it is tempting to render the resolved local handle directly into the shared file.

That works for one person, but it creates meaningless diffs as soon as multiple teammates run the installer with different handles.

## Bad Example

```md
Read `ai-wiki/people/alice/drafts/` when continuing draft notes.
```

A second user running the installer may rewrite the same file to:

```md
Read `ai-wiki/people/bob/drafts/` when continuing draft notes.
```

## Preferred Pattern

Keep repo-shared prompt instructions generic and use placeholders:

```md
Read your own folder under `ai-wiki/people/<handle>/drafts/` when continuing draft notes.
```

Resolve the real handle at runtime in the agent's behavior, not in the committed shared prompt file.

## Review Checklist

- Does this prompt file live in the repo and therefore affect all contributors?
- Would two different users running `install` produce different file content?
- Can a placeholder such as `<handle>` express the rule clearly enough?
- Is the per-user value only needed for runtime behavior rather than committed documentation?
