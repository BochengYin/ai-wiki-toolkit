# Postinstall Archive Staging Task

This prompt family tests one concrete npm-wrapper installer failure without leaking the staging
fix directly.

## Task

Debug an `npm install -g ai-wiki-toolkit` failure during the npm wrapper `postinstall` step on a
supported platform.

The release asset exists and returns HTTP 200, but the installer still fails with `ENOENT` for a
path under `npm/vendor/<target>/download.tar.gz`.

The agent should fix the installer and add a regression test that reproduces the failure without
hitting the real GitHub Release service.

## Why this is a real task

This benchmark uses a real historical failure in this repository. The package wrapper downloaded
the release archive into the same target directory that extraction treated as disposable, so the
script could delete its own archive before the unpack step tried to read it.

The repo already has a raw draft about the same failure class:

- `ai-wiki/people/bochengyin/drafts/npm-postinstall-must-not-delete-its-own-download-archive.md`

Without relevant memory, an agent could easily misdiagnose this as a missing release asset,
patch only target names or URLs, remove cleanup entirely, or add a network-dependent test.

## Expected Implementation Shape

A strong solution will usually:

- reproduce the failure with a local fake release source or equivalent test isolation
- fix the wrapper so transient download state is not removed by installation-directory cleanup
- keep the npm wrapper thin and still based on release artifacts
- avoid real GitHub network calls in regression tests

A weak solution often:

- assumes the release asset is missing even though HTTP 200 was observed
- changes only URLs, target names, or asset selection
- disables cleanup instead of separating transient download state from install output
- rebuilds or reimplements the Python CLI inside the npm wrapper
- adds tests that depend on live GitHub Release availability

## What Varies Across Variants

- `no_aiwiki_workflow`: no AI wiki at all
- `aiwiki_ambient_memory_workflow`: realistic current AI wiki memory
- `aiwiki_scaffold_no_target_memory`: AI wiki exists, but not the target postinstall memory
- `aiwiki_linked_raw_only`: the target raw draft exists
- `aiwiki_linked_consolidated_only`: linked consolidated guidance exists if available
- `aiwiki_scaffold_no_adjacent_memory`: AI wiki scaffold exists, but target postinstall memory and
  adjacent distribution memories are removed

## Manual v2 Prompt

Manual v2 uses only:

- `original.md`: the historical failure shape without naming the temp-directory staging fix

## Human Evaluation Questions

- Did the agent identify that the archive could be deleted locally after a successful download?
- Did it add a regression test that reproduces the failure without real GitHub network access?
- Did it keep the wrapper consuming release artifacts instead of rebuilding or bypassing them?
- Did it avoid unrelated package, release, or wiki churn?
- Did the AI wiki workflow help it avoid retrying the same installer-staging mistake?
