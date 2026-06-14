# Decision Rules

## Outcome Meanings

- `None`
  Use when you completed the check and found no durable lesson worth recording.

- `MemoryRecorded`
  Use when there is a durable public/local trial-error lesson or reusable clarification worth keeping for future tasks.

## What To Check

At task end, check only whether the task produced:

- a public/local trial-error lesson
- a reusable clarification from the user
- a missed-memory note about a relevant memory that should have been used
- a conflict with existing memory that future agents must not miss

## Memory Candidate Detection

Before returning `None`, check whether the task produced any of these signals.

### Trial-Error Candidate Signals

- a failed local command, public test, build, lint, typecheck, package check, or documented public workflow changed the fix
- repeated failed attempts on the same source file, API, command, or behavior changed the approach
- a public/local environment, packaging, or tooling assumption was wrong and the correction is reusable

### Clarification Candidate Signals

- the user clarified behavior, acceptance criteria, or a repo rule that should guide future tasks
- the clarification is not obvious from code or existing docs
- the clarification can be applied without hidden/private benchmark knowledge

### Missed-Memory And Conflict Signals

- the task revealed conflict with existing memory
- a relevant AI wiki doc should have been used but the agent only found it after user correction, review, or later failure
- the task repeated work that existing team memory should have prevented

## Writing Targets

- Put public/local trial-error memories in `ai-wiki/memory/<slug>.md`.
- Keep `ai-wiki/memory/index.md` as the bounded read entrypoint.
- Add one short index entry with trigger, related files, and source pointer.
- Do not write broad conventions, review patterns, feature docs, decisions, or person preferences from this default write-back path.

## Memory Shape

Each memory file should be short and include:

- Trigger
- Public/Local Signal
- Failed Attempt
- Fix Or Rule
- Applies When
- Do Not Use When
- Related Files
- Source Pointer

## Conflict Handling

- If new memory conflicts with existing memory, flag the conflict in the memory file and index entry.
- Narrow scope when the new memory only applies to one feature, module, file, API, command, or public/local failure surface.
