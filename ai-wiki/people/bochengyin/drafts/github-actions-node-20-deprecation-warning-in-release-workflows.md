---
title: "GitHub Actions Node 20 deprecation warnings need release workflow follow-up"
author_handle: "bochengyin"
model: "unknown"
source_kind: "release"
status: "draft"
created_at: "2026-04-28T21:08:00+10:00"
updated_at: "2026-04-28T21:08:00+10:00"
promotion_candidate: false
promotion_basis: "none"
---
# Release Draft

## Context

During the `v0.1.24` release, GitHub Actions emitted Node.js 20 deprecation warnings across release-related workflows.

The warnings named common actions such as `actions/checkout@v4`, `actions/setup-python@v5`, `actions/setup-node@v4`, `actions/upload-artifact@v4`, and `actions/download-artifact@v4`.

## Signal

GitHub said JavaScript actions will be forced to Node.js 24 by default starting 2026-06-02, and Node.js 20 will be removed from the runner on 2026-09-16.

This did not block `v0.1.24`, but it is a release workflow maintenance item because future release runs may change behavior when GitHub flips the runtime default.

## Follow-Up

Before the 2026-06-02 default switch, audit the release, npm publish, smoke, and CI workflows for action versions that explicitly support Node.js 24.

If an action cannot be upgraded before the switch, decide whether the temporary opt-out is acceptable for this repository. Prefer upgrading action versions over relying on temporary environment toggles.

## Reuse Assessment

This is a repo-local release maintenance warning for now. Keep it as a draft until a future workflow update confirms the exact action upgrades or the warning becomes a recurring release failure.
