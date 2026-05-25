---
title: "Release assets should not be blocked by Homebrew tap sync"
author_handle: "bochengyin"
model: "gpt-5"
source_kind: "release"
status: "draft"
promotion_candidate: true
promotion_basis: "Observed again during v0.1.38: Homebrew tap checkout still returned Bad credentials, but release assets uploaded and npm publishing completed because tap sync is non-blocking."
created_at: "2026-05-20T23:50:00+10:00"
updated_at: "2026-05-25T22:29:46+10:00"
---
# Release Assets Should Not Be Blocked By Homebrew Tap Sync

## Context

During the `v0.1.32` release, all platform build jobs and Linux runtime matrix checks passed, but `Release Binaries` failed in `Publish GitHub Release assets`.

The failure happened after the release was created but before assets were uploaded because the workflow tried to check out `BochengYin/homebrew-tap` with `HOMEBREW_TAP_PAT`, and GitHub returned `Bad credentials`.

During the `v0.1.38` release, the same Homebrew tap credential problem appeared again, but only as a warning after release asset upload. The GitHub Release assets, npm publish workflow, and Windows ARM smoke check all completed successfully.

## Lesson

Homebrew tap sync is optional distribution work. It should not block the core release path:

- GitHub Release archive upload
- generated `aiwiki-toolkit.rb` release asset upload
- npm publish workflow trigger
- Windows ARM release and npm smoke checks

Upload release assets before any optional tap sync. Treat tap checkout, formula sync, and tap push failures as warnings unless the task is specifically to publish the Homebrew tap.

## Recovery Used

For `v0.1.32`, the release was rescued by:

- downloading `release-*` workflow artifacts from the failed `Release Binaries` run
- flattening the archives locally
- regenerating `aiwiki-toolkit.rb`
- uploading all release assets with `gh release upload v0.1.32 ... --clobber`
- manually dispatching `Publish npm Package`
- manually dispatching `Release Smoke Windows ARM` for both binary and npm smoke paths

## Follow-Up

Rotate `HOMEBREW_TAP_PAT` if automatic tap sync should keep working. If tap sync stays optional, keep it non-blocking and rely on the release asset plus npm smoke checks as the release gate.
