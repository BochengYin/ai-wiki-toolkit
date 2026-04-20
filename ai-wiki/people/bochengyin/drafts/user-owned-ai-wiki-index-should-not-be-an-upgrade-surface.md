# User-Owned AI Wiki Index Should Not Be An Upgrade Surface

## Summary

`ai-wiki/index.md` should stay user-owned and stable. Package evolution should not require users to run `doctor --suggest-index-upgrade` and manually refresh that file just to pick up new navigation guidance.

## Problem

Right now the toolkit duplicates changing navigation rules across:

- the managed prompt block in `AGENTS.md`
- managed `_toolkit/system.md`
- user-owned `ai-wiki/index.md`
- doctor checks that compare `ai-wiki/index.md` against the latest starter shape

That makes `ai-wiki/index.md` feel package-managed even though the compatibility contract says it is user-owned.

## Recommendation

Treat `ai-wiki/index.md` as a repo-owned map, not as a package upgrade surface.

- Keep creating it with `write-if-missing`.
- Stop expecting existing copies to match the latest starter navigation.
- Put evolving package read order in managed `_toolkit/system.md`.
- Keep the managed prompt block pointing to managed routing first.
- Only read `ai-wiki/index.md` as optional repo-specific context.

## Why `_toolkit/system.md`

`_toolkit/system.md` already holds start-of-task and end-of-task managed workflow rules. It is a better home for package-versioned routing than `_toolkit/index.md`, which is more naturally a directory map.

## Follow-Up Shape

Possible implementation direction:

- simplify the managed prompt block so it reads `_toolkit/system.md` first
- make `ai-wiki/index.md` a minimal evergreen starter
- relax doctor so it warns only about missing user-owned starter docs, not starter drift in existing ones
- keep managed docs as the only auto-refresh surface for evolving navigation rules
