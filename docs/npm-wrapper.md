# npm Distribution

The npm distribution for `ai-wiki-toolkit` uses a thin meta package plus platform-specific binary packages.

## Install

```bash
npm install -g ai-wiki-toolkit
```

The global command is:

```bash
aiwiki-toolkit
```

## Current Design

The meta package lives in this repository as:

- `package.json`
- `npm/bin/aiwiki-toolkit.js`
- `npm/shared.js`
- `npm/platform-targets.json`

Its job is:

1. declare optional dependencies on supported platform packages
2. let npm install the matching platform package for the current machine
3. expose the `aiwiki-toolkit` command through the meta package `bin` field
4. resolve the installed platform binary at runtime

## Supported npm Targets

The platform package map currently supports:

- `darwin-arm64` -> `macos-arm64`
- `darwin-x64` -> `macos-x64`
- `linux-x64` -> `linux-x64`

Unsupported platforms fail fast during installation.

Windows is intentionally excluded from the public npm target map until the main release workflow publishes matching `windows-x64` assets.

## Why Keep It Thin

The npm distribution should not reimplement the CLI in JavaScript and should not rebuild the Python project.

Instead, it should always consume the GitHub Release artifacts produced by the main release workflow. This keeps:

- one implementation
- one binary build pipeline
- one source of truth for versioned assets

## Publish Flow

The intended npm flow is:

1. build and upload GitHub Release binaries
2. stage one npm platform package per published release target
3. publish the platform packages with the same version
4. publish the `ai-wiki-toolkit` meta package with the same version

The publishing workflow is documented in [docs/npm-publish.md](npm-publish.md).

## Updates

Users should update through npm, not through a custom CLI self-update command:

```bash
npm update -g ai-wiki-toolkit
```

The meta package pins the platform-specific optional dependency to the same version, so updating the top-level package updates the matching platform binary as well.

## Release Expectations

The published npm package should continue to satisfy these constraints:

- the GitHub Releases are public and stable
- the asset naming is frozen
- the npm platform target map matches the current public release asset matrix
- the npm package version always matches the Python package version
- npm trusted publishing is configured for the package
