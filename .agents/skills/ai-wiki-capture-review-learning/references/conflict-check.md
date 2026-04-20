# Conflict Check

Before adding or updating memory, check whether the new learning conflicts with:

- `ai-wiki/conventions/`
- `ai-wiki/review-patterns/`
- `ai-wiki/decisions.md`
- `ai-wiki/features/`
- `ai-wiki/problems/`
- relevant person preferences

## If conflict is found

Do not silently overwrite.

Output:

- Existing memory
- New feedback
- Why they conflict or appear to conflict
- Suggested resolution
- Whether this is a refinement, scope difference, or true contradiction

## Example

Existing convention:
Use `object` for truly opaque external payloads.

New feedback:
Avoid `object`; use `str | None` when possible.

Resolution:
This is not a full contradiction. Refine the convention:
- use the narrowest known type when values are known
- use structured types such as `Mapping[str, Any]` for JSON-like payloads
- reserve `object` for truly opaque Python objects
