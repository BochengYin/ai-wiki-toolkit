---
title: "Distribution target matrices must match published assets"
author_handle: "bochengyin"
model: "gpt-5"
source_kind: "review"
status: "draft"
created_at: "2026-04-18T23:37:05+10:00"
updated_at: "2026-04-21T11:45:00+10:00"
promotion_candidate: true
promotion_basis: "Observed repeatedly across Windows support and later arm64/musl expansion work: every released target must stay aligned across workflow matrix, package metadata, target resolution, archive handling, and docs."
---
# Review Draft

## Context

We reviewed the release readiness of `ai-wiki-toolkit`, including the GitHub Release workflow, npm wrapper, and distribution docs.

This issue has now shown up multiple times:

- an earlier review found that wrapper/runtime declarations could drift away from the published release asset matrix
- a later Windows user report showed that `win32` users were still blocked because the public release matrix, npm package metadata, and npm archive download/staging path did not all support `windows-x64`
- a later target expansion added `linux-arm64`, `linux-musl-x64`, and `windows-arm64`, which again required coordinated changes across release workflows, npm target metadata, runtime resolution, archive handling, and docs

## What Went Wrong

The distribution surface can drift in multiple places at once:

- the public release workflow can omit a target entirely
- the npm meta package can exclude an OS from its own install metadata
- the npm target map can miss a supported platform package
- the npm publish/staging flow can assume only one archive format even when Windows uses `.zip`

Any one of those gaps is enough to turn a supported-looking target into a real install failure.

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

If Windows is not part of the public release matrix yet, remove or gate the Windows npm target until matching release assets exist.

If Windows is part of the public matrix, make the downstream npm flow consume the actual published asset set instead of assuming every release archive is `tar.gz`.

## Reuse Assessment

This is reusable anywhere a package-manager wrapper downloads prebuilt binaries from a release pipeline. Thin wrappers are especially sensitive because any mismatch between declared targets and published assets becomes an install-time outage rather than a soft documentation bug.

## Promotion Decision

This now looks like a promotion candidate.

The durable rule is broader than a one-off Windows fix: every public distribution target must be represented consistently across release workflows, package metadata, runtime target maps, libc-aware package resolution where relevant, archive handling, and docs.
