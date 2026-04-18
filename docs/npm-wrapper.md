# npm Wrapper Plan

The npm package for `ai-wiki-toolkit` is intended to be a thin wrapper around the GitHub Release binaries.

## Current Design

The wrapper lives in this repository as:

- `package.json`
- `npm/install.js`
- `npm/bin/aiwiki-toolkit.js`
- `npm/shared.js`

Its job is:

1. detect the current platform and architecture
2. resolve the matching GitHub Release asset
3. download and extract the archive during `postinstall`
4. expose the `aiwiki-toolkit` command through npm’s `bin` field

## Supported npm Targets

The wrapper currently maps:

- `darwin-arm64` -> `macos-arm64`
- `darwin-x64` -> `macos-x64`
- `linux-x64` -> `linux-x64`
- `win32-x64` -> `windows-x64`

Unsupported platforms fail fast during installation.

## Why Keep It Thin

The npm package should not reimplement the CLI in JavaScript and should not rebuild the Python project.

Instead, it should always consume the GitHub Release artifacts produced by the main release workflow. This keeps:

- one implementation
- one binary build pipeline
- one source of truth for versioned assets

## Publish Flow

The intended npm flow is:

1. build and upload GitHub Release binaries
2. publish the npm package with the same version
3. npm `postinstall` downloads the matching release asset

The publishing workflow is documented in [docs/npm-publish.md](npm-publish.md).

## Open Work

The repository now contains both the wrapper skeleton and an npm publishing workflow skeleton. Before publishing to npm, verify:

- the GitHub Releases are public and stable
- the asset naming is frozen
- the npm package version always matches the Python package version
- npm trusted publishing is configured for the package
