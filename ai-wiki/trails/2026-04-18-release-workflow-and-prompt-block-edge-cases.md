# Release Workflow And Prompt Block Edge Cases

## Problem

The first release and prompt-management rollout exposed a few toolchain edge cases that were easy to miss locally but broke real workflow usage.

## Symptoms

- `Release Binaries` produced zero-job failures on GitHub Actions.
- The `v0.1.0` release build failed on `windows-x64` while local tests were green.
- Running `install` against this repo inserted the managed block into the middle of `AGENTS.md` instead of appending it cleanly.

## Trial And Error

1. Verified that the tag itself had reached `origin` and that GitHub had created a tag-based run.
2. Compared `main` branch failures with the `v0.1.0` run to separate trigger issues from job-level issues.
3. Inspected the workflow definition and found that optional Homebrew sync steps were gated directly with `secrets.HOMEBREW_TAP_PAT` inside step-level `if:` conditions.
4. Queried the run job list and narrowed the remaining release failure to `Build windows-x64 -> Run test suite`.
5. Audited tests for platform-sensitive assumptions and found an exact newline assertion in the CLI version test.
6. Re-ran `install` against a repo containing inline marker strings and confirmed that the managed-block regex was matching documentation text, not just standalone block markers.

## Root Cause

- GitHub Actions workflow parsing was brittle when optional Homebrew sync gating depended directly on a secret inside step-level `if:` expressions.
- The CLI version test assumed Unix newlines and failed on Windows runners.
- The prompt managed-block matcher treated any occurrence of the marker strings as a real block, including inline documentation inside `AGENTS.md`.

## Correct Path

- Move optional Homebrew sync gating to a job-level environment variable and test `env.HOMEBREW_TAP_PAT != ''` in the relevant steps.
- Make CLI output assertions newline-agnostic by asserting on `splitlines()` rather than exact `\n`.
- Match prompt managed blocks only when the start and end markers appear on their own lines.
- Re-run `install` after fixing the regex so the managed block is appended cleanly to the end of `AGENTS.md`.

## Canonical Updates

- Keep `release-binaries.yml` tag-triggered release flow aligned with real GitHub Actions parsing behavior, not just local YAML expectations.
- Treat Windows newline behavior as part of the standard release matrix when writing CLI tests.
- Treat managed prompt markers as line-scoped delimiters, never as freeform substrings.
