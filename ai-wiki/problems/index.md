# Problems Index

Use this area for reusable problem-solution memories.

A problem note should help future agents avoid repeating the same debugging loop.

## When to read

Read relevant problem notes before implementing or testing similar behavior.

Examples:
- flaky async notification tests
- import job idempotency issues
- confusing migration failure
- known integration edge cases

## Suggested note shape

Each problem file should include:

- Symptom
- Cause
- Solution
- Applies When
- Do Not Use When
- Related Files
- Source Pointer
- History

## Current Entries

- [Linux musl PyInstaller needs binutils objdump](linux-musl-pyinstaller-needs-binutils-objdump.md): Alpine-based musl release builds need `binutils` available and the setup step must run as root before the build environment is created.
- [Windows ARM smoke version checks need full CLI output](windows-arm-smoke-version-checks-need-full-cli-output.md): Windows ARM release smoke checks should compare against the full `ai-wiki-toolkit <version>` CLI output instead of the bare package version.
