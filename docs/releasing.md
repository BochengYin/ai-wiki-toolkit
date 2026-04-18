# Releasing ai-wiki-toolkit

This document describes the first public release skeleton for `ai-wiki-toolkit`.

## Current Scope

The repository now includes a GitHub Actions workflow at `.github/workflows/release-binaries.yml` that:

1. runs on pushed tags matching `v*`
2. installs the project with the `release` dependency group
3. runs the test suite
4. builds standalone binaries with PyInstaller
5. archives each binary into a release asset
6. renders a Homebrew formula from the release archives
7. creates or updates a GitHub Release for the tag
8. optionally syncs the generated formula into a Homebrew tap repository
9. uploads the built archives and generated formula as release assets

This workflow is the base distribution layer for later package-manager integrations such as Homebrew and npm.

## Supported Release Targets

The workflow currently builds these targets:

- `linux-x64`
- `macos-arm64`
- `macos-x64`

Windows packaging remains implemented in the codebase, but it is currently excluded from the release matrix until the Windows test lane is stabilized.

The target labels map to GitHub-hosted runners and determine the release asset names.

## Asset Naming

Each archive is named like this:

```text
ai-wiki-toolkit-vX.Y.Z-<target>.tar.gz
ai-wiki-toolkit-vX.Y.Z-<target>.zip
```

Examples:

- `ai-wiki-toolkit-v0.1.0-linux-x64.tar.gz`
- `ai-wiki-toolkit-v0.1.0-macos-arm64.tar.gz`

The archive contains a single executable:

- Unix-like targets: `aiwiki-toolkit`

## Release Steps

1. Update the version in:
   - `pyproject.toml`
   - `src/ai_wiki_toolkit/__init__.py`
2. Run the test suite locally:

   ```bash
   uv run pytest
   ```

3. Commit the version bump and any release notes changes.
4. Create and push a semantic tag:

   ```bash
   git tag v0.1.0
   git push origin v0.1.0
   ```

5. Wait for the `Release Binaries` workflow to finish.
6. Verify that the GitHub Release for the tag contains all expected archives and `aiwiki-toolkit.rb`.
7. If tap sync is enabled, verify that the tap repository received the updated `Formula/aiwiki-toolkit.rb`.

## Local Dry Run

You can test the binary build locally before cutting a release:

```bash
python -m pip install ".[release]"
python -m PyInstaller --clean --noconfirm --onefile --name aiwiki-toolkit --paths src --specpath build/pyinstaller src/ai_wiki_toolkit/cli.py
python scripts/build_release_archive.py --binary dist/aiwiki-toolkit --version v0.1.0 --target linux-x64 --output-dir release-assets
```

Windows local dry runs can still be performed manually with `--binary dist/aiwiki-toolkit.exe --target windows-x64`, but that target is not part of the automated public release matrix yet.

## Next Distribution Layers

The intended order of distribution work is:

1. GitHub Releases
2. Homebrew tap
3. npm wrapper

The generated Homebrew formula should consume the versioned GitHub Release assets instead of rebuilding the project independently. The npm wrapper should follow the same rule.

See also:

- [docs/homebrew-tap.md](homebrew-tap.md)
- [docs/npm-wrapper.md](npm-wrapper.md)
- [docs/npm-publish.md](npm-publish.md)
