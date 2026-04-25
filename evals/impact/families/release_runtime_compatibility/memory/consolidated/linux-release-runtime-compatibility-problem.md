# Linux Release Binaries Need Runtime Checks Against An Older Glibc Baseline

## Symptom

`npm install -g ai-wiki-toolkit@0.1.7` can succeed in a Linux container while `aiwiki-toolkit --version` fails at runtime with a Python shared library / GLIBC version error.

## Cause

Publishing and installing the npm package does not prove the bundled Linux binary is compatible with older still-supported glibc environments.

## Solution

Build Linux release binaries on an intentionally older glibc baseline and verify the actual executable in both older and current runtime containers.

The check should run a real command such as `aiwiki-toolkit --version`; a successful package install alone is not enough.

## Applies When

- changing Linux release binary build jobs
- changing npm platform package publishing
- adding or updating release smoke tests

## Do Not Use When

- validating package metadata without executing the binary
- debugging a platform package resolution failure before the binary starts

## Related Files

- `.github/workflows/release-binaries.yml`
- `scripts/check_linux_runtime_matrix.py`
- `scripts/build_linux_release_in_container.py`
