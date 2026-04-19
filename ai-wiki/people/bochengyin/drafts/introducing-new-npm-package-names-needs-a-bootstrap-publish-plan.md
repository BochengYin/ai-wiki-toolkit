---
title: "Introducing new npm package names needs a bootstrap publish plan"
author_handle: "bochengyin"
model: "gpt-5"
source_kind: "review"
status: "draft"
created_at: "2026-04-19T15:36:49+1000"
updated_at: "2026-04-19T15:36:49+1000"
promotion_candidate: false
promotion_basis: "none"
---
# Review Draft

## Context

We changed the npm distribution of `ai-wiki-toolkit` from a single wrapper package to a meta package plus three platform-specific packages.

The `v0.1.7` GitHub release completed successfully, but the `Publish npm Package` workflow failed at the step that publishes the new platform packages.

## What Went Wrong

We treated the first release of new npm package names as if it were a routine version bump of an existing package.

That assumption is too weak. Even when the root package already has a working publish path, newly introduced package names can require separate bootstrap handling for ownership, authentication, or trusted-publisher configuration.

## Bad Example

- change from one npm package to several package names
- cut a release tag immediately
- rely on the existing publish workflow without validating the bootstrap path for the new package names

## Fix

Before the first public release that introduces new npm package names:

- verify whether each new package name already exists
- decide how the first publish will be authenticated
- confirm whether trusted publishing is already configured for each package or whether an initial manual/token-based publish is required
- test the bootstrap path before relying on the normal release train

After the bootstrap publish succeeds, later releases can usually return to the standard automated path.

## Reuse Assessment

This is reusable for any package ecosystem where distribution topology expands from one package name to several related packages.

The first publish of a new package name is often operationally different from later publishes, even when the code change itself looks like a normal refactor.

## Promotion Decision

Keep as a draft for now. Promote if the same bootstrap-publish issue appears again in another package-manager rollout.
