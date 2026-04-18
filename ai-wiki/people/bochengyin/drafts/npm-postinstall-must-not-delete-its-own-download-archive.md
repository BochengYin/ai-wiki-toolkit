---
title: "npm postinstall must not delete its own download archive"
author_handle: "bochengyin"
model: "gpt-5"
source_kind: "review"
status: "draft"
created_at: "2026-04-19T00:28:58+1000"
updated_at: "2026-04-19T00:28:58+1000"
promotion_candidate: false
promotion_basis: "none"
---
# Review Draft

## Context

We investigated a real `npm install` failure for the published `ai-wiki-toolkit` wrapper on `darwin-arm64`.

The GitHub Release asset existed and returned HTTP 200, but npm `postinstall` still failed with `ENOENT` for `npm/vendor/macos-arm64/download.tar.gz`.

## What Went Wrong

The installer downloaded the release archive into the same per-target directory that `extractArchive()` deletes before unpacking.

That meant the script successfully downloaded the asset and then removed the file itself before `tar.x()` tried to read it.

## Bad Example

- Download `download.tar.gz` into `npm/vendor/<target>/`.
- Start extraction by recursively deleting `npm/vendor/<target>/`.
- Attempt to open the archive path that was just deleted.

## Fix

Keep transient download state outside the directory that gets cleaned for installation.

For this wrapper, the practical fix was to download into a temporary directory under `os.tmpdir()`, extract into `npm/vendor/<target>/`, and clean up the temporary directory afterward.

## Reuse Assessment

This pattern is reusable for thin package-manager wrappers and self-updating installers.

Any installer that stages artifacts into a directory it later treats as disposable can create a misleading `ENOENT` that looks like a missing release asset even when the remote download succeeded.

## Promotion Decision

Keep as a draft for now. Promote if the same self-deleting staging pattern appears again in another distribution path or installer.
