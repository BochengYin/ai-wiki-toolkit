---
title: "Distribution target matrices must match published assets"
author_handle: "bochengyin"
model: "gpt-5"
source_kind: "review"
status: "superseded"
created_at: "2026-04-18T23:37:05+10:00"
updated_at: "2026-04-21T21:13:45+1000"
promotion_candidate: false
promotion_basis: "Promoted to ai-wiki/conventions/distribution-target-matrix-must-match-published-assets.md on 2026-04-21 after repeated release and distribution fixes."
---
# Review Draft

## Context

We reviewed the release readiness of `ai-wiki-toolkit`, including the GitHub Release workflow, npm wrapper, and distribution docs.

This issue has now shown up multiple times:

- an earlier review found that wrapper/runtime declarations could drift away from the published release asset matrix
- a later Windows user report showed that `win32` users were still blocked because the public release matrix, npm package metadata, and npm archive download/staging path did not all support `windows-x64`
- a later target expansion added `linux-arm64`, `linux-musl-x64`, and `windows-arm64`, which again required coordinated changes across release workflows, npm target metadata, runtime resolution, archive handling, and docs
- after that expansion, the first `v0.1.12` release attempt still failed because release-facing tests and build helpers carried platform assumptions that were harmless on macOS/Linux but broke on Windows and Alpine-style musl containers

## What Went Wrong

The distribution surface can drift in multiple places at once:

- the public release workflow can omit a target entirely
- the npm meta package can exclude an OS from its own install metadata
- the npm target map can miss a supported platform package
- the npm publish/staging flow can assume only one archive format even when Windows uses `.zip`

Any one of those gaps is enough to turn a supported-looking target into a real install failure.

Even after the target matrix is declared correctly, release verification can still drift if:

- tests assume Unix newline or path-order behavior and fail on Windows
- helper code assumes POSIX-only APIs such as `os.getuid()` or `os.getgid()`
- doctor coverage or similar checks assume `git` exists inside minimal build containers such as Alpine

## Bad Example

- Map `win32-x64` to `windows-x64` in the wrapper runtime.
- Publish the npm package without publishing a matching `windows-x64` GitHub Release asset.
- Document Windows as a supported npm target while the release pipeline excludes it.
- Download only `*.tar.gz` assets in the npm publish workflow even though Windows release assets are `.zip`.

## Fix

Keep the declared distribution matrix aligned across:

- release workflows
- wrapper/runtime target maps
- package metadata and install guards
- archive-format handling in staging/publish scripts
- user-facing docs
- release-facing tests and helper code that validate those targets

If Windows is not part of the public release matrix yet, remove or gate the Windows npm target until matching release assets exist.

If Windows is part of the public matrix, make the downstream npm flow consume the actual published asset set instead of assuming every release archive is `tar.gz`.

Also keep release verification portable:

- write digest fixtures in binary mode when line endings matter
- normalize snapshot assertions by relative path string rather than platform-specific traversal order
- avoid unconditional dependence on POSIX-only APIs or optional tools inside minimal Linux build containers

## Reuse Assessment

This is reusable anywhere a package-manager wrapper downloads prebuilt binaries from a release pipeline. Thin wrappers are especially sensitive because any mismatch between declared targets and published assets becomes an install-time outage rather than a soft documentation bug.

## Promotion Outcome

Promoted on 2026-04-21 to `ai-wiki/conventions/distribution-target-matrix-must-match-published-assets.md`.

That shared convention is now the active rule for future work in this repository.

Keep this draft only as the source record and fuller working history behind that promotion.
