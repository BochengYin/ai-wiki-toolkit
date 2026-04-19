---
title: "Linux release binaries need runtime checks against an older glibc baseline"
author_handle: "bochengyin"
model: "gpt-5"
source_kind: "review"
status: "draft"
created_at: "2026-04-19T17:21:00+1000"
updated_at: "2026-04-19T18:22:00+1000"
promotion_candidate: false
promotion_basis: "none"
---
# Review Draft

## Context

On April 19, 2026, we tested the newly published npm platform packages for `ai-wiki-toolkit` in isolated environments.

The new package topology worked as intended at the install layer:

- `ai-wiki-toolkit-darwin-arm64` installed and ran on a macOS arm64 host
- `ai-wiki-toolkit-darwin-x64` installed and ran under Rosetta on the same host
- `ai-wiki-toolkit-linux-x64` installed and ran in a `node:24-trixie` linux/amd64 container

We also tested the user-facing meta package `ai-wiki-toolkit` in Linux containers.

## What Went Wrong

In a `node:24-bookworm` linux/amd64 container, `npm install -g ai-wiki-toolkit@0.1.7` completed successfully, but `aiwiki-toolkit --version` failed at runtime.

The binary exited with:

`Failed to load Python shared library ... libm.so.6: version 'GLIBC_2.38' not found`

So the publish path and npm install path were both green, but the shipped Linux binary still had a runtime compatibility gap for older glibc environments.

## Bad Example

- verify that release assets upload successfully
- verify that npm packages publish successfully
- verify that `npm install` succeeds in one Linux environment
- stop before running the built binary on an older but still common distro baseline

## Fix

For Linux binary releases, build the binary on an intentionally older glibc baseline and test both:

- runtime compatibility of the build environment itself
- install success
- runtime success on at least one older glibc baseline and one current baseline

That means the release check should include an actual command such as `aiwiki-toolkit --version`, not just `npm install`, and the container matrix should include a distro old enough to expose glibc assumptions.

In practice, the durable fix here was:

- move the `linux-x64` build lane from the host runner to a `python:3.11-bookworm` container
- keep the separate runtime matrix that executes the built binary on both `bookworm` and `trixie`

## Reuse Assessment

This is reusable for any Python-packaged or native binary distributed through npm platform packages.

A green npm publish does not prove the binary is broadly runnable on Linux. Runtime compatibility needs its own test matrix.

## Promotion Decision

Keep as a draft for now. Promote if another release hits the same gap or if we formalize a release test matrix for binary compatibility.
