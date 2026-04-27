---
title: "Npm publish recovery needs explicit auth mode and per-package trusted publisher"
author_handle: "bochengyin"
model: "gpt-5"
source_kind: "release"
status: "draft"
created_at: "2026-04-27T14:57:15+1000"
updated_at: "2026-04-27T16:05:21+1000"
promotion_candidate: false
promotion_basis: "none"
---
# Review Draft

## Context

During the `v0.1.22` release, GitHub Release binaries and Homebrew tap sync succeeded, but the `Publish npm Package` workflow failed while publishing `ai-wiki-toolkit-darwin-arm64@0.1.22`.

The same workflow had successfully published `0.1.21` two days earlier. The repository still had `NPM_PUBLISH_TOKEN` configured, so the workflow chose token-based npm publish.

## What Went Wrong

The npm registry returned `E404` for an existing package name, with the message that the package did not exist or the token did not have permission. A rerun produced the same failure, which made a transient npm outage unlikely.

Adding a manual recovery path that forced trusted publishing confirmed the second half of the auth problem: once the workflow ignored the token and removed setup-node auth config, npm returned `ENEEDAUTH`. That means trusted publishing was not configured for at least the first platform package.

## Fix

Release workflows that support both token and trusted npm publishing should provide an explicit manual auth-mode override:

- `auto`: normal behavior
- `token`: require a valid `NPM_PUBLISH_TOKEN`
- `trusted`: ignore `NPM_PUBLISH_TOKEN`, remove npm auth config, and publish with provenance

For packages split into a meta package plus platform packages, npm trusted publishing must be configured for every package name, not only the root package.

Recovery publish workflows should also be idempotent. Before publishing each platform package or the meta package, check whether `name@version` already exists in the registry and skip it if present. This keeps recovery safe when a run publishes some platform packages and then stops on the first package with missing npm-side trust configuration.

After the missing npm-side trusted publishers were configured for the remaining platform packages, rerunning the same `v0.1.22` workflow succeeded. The idempotent checks skipped the already-published platform packages, published the remaining platform packages, published the root meta package, and triggered a successful Windows ARM npm smoke check.

## Reuse Assessment

This is reusable for release triage when npm publish fails after all build artifacts have succeeded. A prior successful npm release does not prove the current token is still valid, and a trusted publishing fallback only works after npm-side trusted publishers are configured per package.

## Promotion Decision

Keep as a draft for now. Promote if another release is blocked by registry auth state rather than build artifacts.
