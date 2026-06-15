# Memory Index

This folder contains bounded, public/local trial-error memory for future coding agents.

## Read Rule

Read this index first, then open at most one linked memory file before acting.

Open a memory file only when it strongly matches the current source file, API, command,
behavior, or repeated public/local failure surface.

Do not use hidden evaluator failures, hidden test names, private benchmark answers, or
prior hidden-derived fixes as memory.

## Entries

- [SWE-Chain 015 Agent Writeback PRD Rules](swe-chain-015-agent-writeback-prd-rules.md):
  read when running, reviewing, or modifying the `swe-chain-015-flask-agent-skill-writeback` experiment,
  especially runner normal-end hook protocol and quarantine/audit rules.

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
