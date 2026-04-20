# Team Memory Schema v1

This schema is lightweight guidance for team coding memory. It is not a strict database schema.

## Common Fields

### Status

Use one of:

- `draft`
- `candidate`
- `active`
- `refined`
- `superseded`

### Scope

Describe where the memory applies.

Examples:

- `repo-wide`
- `Python typing`
- `backend API`
- `tests only`
- `feature: bulk invoice upload`
- `module: app/notifications`

### Source Pointer

Use lightweight source pointers. Do not over-engineer provenance.

Suggested fields:

- `Actor`
- `Actor Role`
- `Context`
- `Quote or Summary`
- `Captured By`
- `Captured At`
- `Scope`

Example:

```yaml
source:
  actor: Carol
  actor_role: Tech Lead
  context: PR #123 review
  quote: "Please don't use object here. We know this returns str or None."
  captured_by: Bob
  captured_at: 2026-04-20
  scope: Python typing in this repo
```

## Memory Types

### Person Preference

A preference tied to a person.

Store under:

- `ai-wiki/people/<handle>/`
- or as a draft under `ai-wiki/people/<handle>/drafts/`

### Team Convention

A shared rule that coding agents should follow.

Store under:

- `ai-wiki/conventions/`

### Review Pattern

A reusable review issue or review expectation.

Store under:

- `ai-wiki/review-patterns/`

### Problem-Solution Memory

A reusable debugging or implementation lesson.

Store under:

- `ai-wiki/problems/`

### Feature Memory

A feature-specific current understanding, requirement, assumption, or acceptance criterion.

Store under:

- `ai-wiki/features/`

### Decision

A durable project decision or tradeoff.

Store in:

- `ai-wiki/decisions.md`
- or a linked decision file if the repo chooses to split decisions

## Conflict and Regression

When adding new memory:

- Check whether it conflicts with existing conventions, decisions, features, or person preferences.
- If it refines an old rule, update the current rule and keep the old item in History.
- If it contradicts an old rule, do not silently overwrite. Mark a conflict or proposed supersession.
- If scope differs, narrow the scope instead of treating it as a global conflict.

## Default Validity

Assume pasted information is active unless the user says it is old, deprecated, historical, or the repo/wiki clearly conflicts with it.
