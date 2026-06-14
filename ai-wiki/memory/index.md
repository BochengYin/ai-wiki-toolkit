# Memory Index

This folder contains bounded, public/local trial-error memory for future coding agents.

## Read Rule

Read this index first, then open at most one linked memory file before acting.

Open a memory file only when it strongly matches the current source file, API, command,
behavior, or repeated public/local failure surface.

Do not use hidden evaluator failures, hidden test names, private benchmark answers, or
prior hidden-derived fixes as memory.

## Entries

- [Run scaffold previews from the seed repo cwd](scaffold-previews-use-seed-repo-cwd.md):
  when previewing toolkit scaffold/install output into a synthetic repo or
  harness fixture, set cwd to the intended seed repo and verify the source
  checkout remains clean.

## Suggested Entry Shape

Each memory file should include:

- Trigger
- Public/Local Signal
- Failed Attempt
- Fix Or Rule
- Applies When
- Do Not Use When
- Related Files
- Source Pointer
