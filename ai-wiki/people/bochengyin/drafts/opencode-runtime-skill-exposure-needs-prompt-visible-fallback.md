---
title: "OpenCode runtime skill exposure needs prompt-visible fallback"
author_handle: "bochengyin"
model: "unknown"
source_kind: "feature_clarification"
status: "draft"
created_at: "2026-04-29T01:18:00+10:00"
updated_at: "2026-04-29T21:04:44+10:00"
promotion_candidate: false
promotion_basis: "none"
---
# Draft

## Context

An OpenCode run in another repository showed that repo-local AI wiki skills under `.agents/skills/` can be discoverable on disk while the active model session still reports no available skills.

## Clarification

This is not primarily a `.gitignore` or skill-on-disk discovery problem. It is a runtime exposure mismatch:

- the repo may contain `.agents/skills/ai-wiki-*`
- OpenCode may be able to discover those skill files on disk
- the active model session may still not expose those skills through the runtime `skill` tool
- when that happens, the model only sees high-level `ai-wiki/_toolkit/system.md` guidance and can miss exact output contracts

## Preferred Upstream Shape

Keep `.agents/skills/` as the source of truth for detailed skill workflows, but ship a managed prompt-visible fallback in `ai-wiki/_toolkit/system.md`.

The fallback should tell agents to manually read:

- `.agents/skills/<skill-name>/SKILL.md`
- `.agents/skills/<skill-name>/references/*.md`

For end-of-task AI wiki behavior, the fallback should point directly to the reuse and update skill output contracts.

`doctor` can also warn or inform when repo-local AI wiki skills exist but the runtime may not expose them. It should avoid pretending it can inspect the active model session unless the runtime provides that signal.

## Implementation Outcome

The upstream fix keeps the short `AGENTS.md`/`CLAUDE.md` prompt block intact and moves the fallback into managed `ai-wiki/_toolkit/system.md`.

The toolkit now also checks this fallback in `doctor`:

- stale managed system docs warn and suggest `aiwiki-toolkit install`
- installed repo-local AI wiki skills produce an informational runtime-exposure note
- the doctor message does not claim to inspect the active model session

## Reuse Assessment

Use this when implementing OpenCode or cross-agent adapter support. Prompt-visible managed docs should provide a fallback path when runtime skill exposure is missing.
