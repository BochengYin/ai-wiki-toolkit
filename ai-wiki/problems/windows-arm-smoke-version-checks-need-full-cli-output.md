# Windows Arm Smoke Version Checks Need Full CLI Output

## Symptom

The Windows ARM smoke workflow fails even when the binary is healthy because the assertion compares `--version` output against the bare package version instead of the full CLI output.

## Cause

`aiwiki-toolkit --version` prints `ai-wiki-toolkit <version>`, not only `<version>`. The smoke workflow was checking the wrong expected string in both the release-archive and npm-installed paths.

## Solution

Compare the workflow output against the full CLI version string in both Windows ARM smoke checks and keep the error message explicit about the expected versus actual output.

## Applies When

- editing `.github/workflows/release-smoke-windows-arm.yml`
- changing CLI version output
- adding or updating Windows release smoke checks

## Do Not Use When

- checking package metadata without executing the CLI
- debugging a download or archive extraction failure before `--version` runs

## Related Files

- `.github/workflows/release-smoke-windows-arm.yml`
- `tests/test_release_smoke_workflow.py`
- `src/ai_wiki_toolkit/cli.py`

## Source Pointer

- Commit: `e0d6fa9` `Fix Windows ARM smoke version checks`

## History

- 2026-04-21: Windows ARM smoke checks were updated to compare against the full `ai-wiki-toolkit <version>` output for both release-archive and npm-installed binaries.
