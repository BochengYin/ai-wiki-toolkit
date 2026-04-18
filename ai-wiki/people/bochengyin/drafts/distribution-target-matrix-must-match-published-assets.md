---
title: "Distribution target matrices must match published assets"
author_handle: "bochengyin"
model: "gpt-5"
source_kind: "review"
status: "draft"
created_at: "2026-04-18T23:37:05+10:00"
updated_at: "2026-04-18T23:37:05+10:00"
promotion_candidate: false
promotion_basis: "none"
---
# Review Draft

## Context

We reviewed the release readiness of `ai-wiki-toolkit`, including the GitHub Release workflow, npm wrapper, and distribution docs.

## What Went Wrong

The npm wrapper and wrapper docs advertised `win32-x64` support, but the release workflow only built and published `linux-x64`, `macos-arm64`, and `macos-x64` assets.

That creates a hard failure mode: `npm install -g` on Windows resolves a release asset URL that does not exist and fails during `postinstall`.

## Bad Example

- Map `win32-x64` to `windows-x64` in the wrapper runtime.
- Publish the npm package without publishing a matching `windows-x64` GitHub Release asset.
- Document Windows as a supported npm target while the release pipeline excludes it.

## Fix

Keep the declared distribution matrix aligned across:

- release workflows
- wrapper/runtime target maps
- package metadata and install guards
- user-facing docs

If Windows is not part of the public release matrix yet, remove or gate the Windows npm target until matching release assets exist.

## Reuse Assessment

This is reusable anywhere a package-manager wrapper downloads prebuilt binaries from a release pipeline. Thin wrappers are especially sensitive because any mismatch between declared targets and published assets becomes an install-time outage rather than a soft documentation bug.

## Promotion Decision

Keep as a draft for now. Promote if the same matrix-drift issue shows up again in another wrapper, tap, or binary-distribution flow.
