# Releasing ai-wiki-toolkit

This document describes the first public release skeleton for `ai-wiki-toolkit`.

## Current Scope

The repository now includes a GitHub Actions workflow at `.github/workflows/release-binaries.yml` that:

1. runs on pushed tags matching `v*`
2. installs the project with the `release` dependency group
3. runs the test suite
4. builds standalone binaries with PyInstaller
   - the Linux target is built inside a `python:3.11-bookworm` container so the shipped binary tracks an older glibc baseline
5. archives each binary into a release asset
6. verifies the Linux release archive by running `aiwiki-toolkit --version` in both older and current glibc container baselines
7. renders a Homebrew formula from the release archives
8. creates or updates a GitHub Release for the tag
9. optionally syncs the generated formula into a Homebrew tap repository
10. uploads the built archives and generated formula as release assets

This workflow is the base distribution layer for later package-manager integrations such as Homebrew and npm platform packages.

## Supported Release Targets

The workflow currently builds these targets:

- `linux-arm64`
- `linux-x64`
- `linux-musl-x64`
- `windows-x64`
- `windows-arm64`
- `macos-arm64`
- `macos-x64`

The target labels map to GitHub-hosted runners and determine the release asset names.

## Asset Naming

Each archive is named like this:

```text
ai-wiki-toolkit-vX.Y.Z-<target>.tar.gz
ai-wiki-toolkit-vX.Y.Z-<target>.zip
```

Examples:

- `ai-wiki-toolkit-v0.1.0-linux-arm64.tar.gz`
- `ai-wiki-toolkit-v0.1.0-linux-x64.tar.gz`
- `ai-wiki-toolkit-v0.1.0-linux-musl-x64.tar.gz`
- `ai-wiki-toolkit-v0.1.0-windows-x64.zip`
- `ai-wiki-toolkit-v0.1.0-windows-arm64.zip`
- `ai-wiki-toolkit-v0.1.0-macos-arm64.tar.gz`

The archive contains a single executable:

- Unix-like targets: `aiwiki-toolkit`

## Release Steps

1. Update the version in:
   - `package.json`
   - `pyproject.toml`
   - `src/ai_wiki_toolkit/__init__.py`
2. Run the test suite locally:

   ```bash
   uv run pytest
   ```

3. Commit the version bump and any release notes changes.
4. Create and push a semantic tag:

   ```bash
   uv run python scripts/pr_flow.py tag-release 0.1.0
   ```

   This helper syncs `main`, verifies the package metadata against the release version,
   creates the tag, and pushes it to `origin`.

5. Wait for the `Release Binaries` workflow to finish.
6. Confirm that the Linux runtime checks passed for the published glibc and musl targets.
7. Verify that the GitHub Release for the tag contains all expected archives and `aiwiki-toolkit.rb`.
8. Wait for the npm publish workflow to stage and publish the platform packages plus the meta package.
9. Watch the `Release Smoke Windows ARM` workflow:
   - after `Release Binaries`, it downloads `windows-arm64.zip` on `windows-11-arm` and runs `aiwiki-toolkit.exe --version`
   - after `Publish npm Package`, it installs `ai-wiki-toolkit@<version>` on `windows-11-arm` and runs `aiwiki-toolkit --version`
   - you can also run it manually with `workflow_dispatch` for any existing release tag
10. If tap sync is enabled, verify that the tap repository received the updated `Formula/aiwiki-toolkit.rb`.

## Local Dry Run

You can test the Linux binary build locally before cutting a release:

```bash
PYTHONPATH=src python scripts/build_linux_release_in_container.py --version v0.1.0 --target linux-x64
PYTHONPATH=src python scripts/check_linux_runtime_matrix.py --asset release-assets/ai-wiki-toolkit-v0.1.0-linux-x64.tar.gz
```

This path expects Docker locally. The build itself happens inside `python:3.11-bookworm`, so the host Python environment does not need the release extras installed.

Windows local dry runs can still be performed manually with `--binary dist/aiwiki-toolkit.exe --target windows-x64` or `--target windows-arm64` when you need to validate packaging outside GitHub Actions.

## Next Distribution Layers

The intended order of distribution work is:

1. GitHub Releases
2. Homebrew tap
3. npm meta package plus platform packages

The generated Homebrew formula should consume the versioned GitHub Release assets instead of rebuilding the project independently. The npm platform packages should follow the same rule.

See also:

- [docs/homebrew-tap.md](homebrew-tap.md)
- [docs/npm-wrapper.md](npm-wrapper.md)
- [docs/npm-publish.md](npm-publish.md)
