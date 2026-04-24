# Release Distribution Integrity Task

This prompt family tests one concrete, repo-realistic release and distribution update task without
leaking the exact file list.

## Task

Expand public release and npm distribution support in this repository.

Add end-to-end Windows support for the npm distribution, and expand the public
release/distribution matrix to cover:

- `linux-arm64`
- `linux-musl-x64`
- `windows-arm64`

Keep docs and tests up to date.

## Why this is a real task

This benchmark combines two adjacent historical problem shapes that actually appeared in this
repo's history:

- an earlier Windows support mismatch where `win32` users could still be blocked even though the
  npm side looked close to supported
- a later target expansion where `linux-arm64`, `linux-musl-x64`, and `windows-arm64` had to be
  added without letting release, npm, docs, and verification drift apart

The repo already has:

- a raw draft about the same failure class:
  - `ai-wiki/people/bochengyin/drafts/distribution-target-matrix-must-match-published-assets.md`
- a promoted shared convention:
  - `ai-wiki/conventions/distribution-target-matrix-must-match-published-assets.md`

Without relevant memory, an agent could easily:

- patch npm target resolution without making the public release matrix match
- add workflow targets without fixing package metadata or docs
- assume only one archive format even though Windows uses `.zip`
- stop after one surface looks right and miss release-facing verification

The historical user request behind this combined task was essentially:

- Windows npm support should be real end-to-end, not a partial declaration
- new public targets should be added in one coordinated pass instead of drifting across layers
- release assets, npm target resolution, docs, and verification should stay aligned

## Expected implementation shape

A strong solution will usually:

- update the public release workflow matrix and matching asset expectations
- update npm target resolution and package metadata to match the public matrix
- handle Windows archive differences where needed
- update release and installation docs
- add or update release-facing tests and checks

A weak solution often:

- changes only one layer such as docs, npm metadata, or workflow targets
- advertises support that the public release flow does not actually publish
- misses Windows `.zip` handling while adding Windows targets
- leaves release-facing verification behind

## What varies across variants

- `plain_repo_no_aiwiki`: no AI wiki at all
- `aiwiki_no_relevant_memory`: AI wiki exists, but not the relevant release/distribution docs
- `aiwiki_raw_drafts`: relevant raw draft evidence exists, no consolidated shared guidance for this
  cluster
- `aiwiki_consolidated`: consolidated shared guidance exists, raw drafts removed
- `aiwiki_raw_plus_consolidated`: both raw and consolidated evidence exist

## What stays fixed across prompt levels

The task itself stays the same. Only prompt specificity changes:

- `short.md`: task requirements only
- `medium.md`: the same task requirements plus one coordination boundary sentence

No `full.md` is included for this benchmark family because over-specifying the release surfaces
would reduce the benchmark's ability to measure memory effects.

## Human evaluation questions

- Did the agent make Windows support real end-to-end instead of patching npm alone?
- Did it keep public release targets aligned across workflows, npm metadata, archive handling,
  docs, and release-facing checks?
- Did it add the later targets without leaving obvious target drift behind?
- Did it avoid unrelated product or wiki churn?
- Did the chosen memory state help it coordinate more of the relevant surfaces with less prompt
  detail?
