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

- `no_aiwiki_workflow`: no AI wiki at all
- `aiwiki_ambient_memory_workflow`: realistic current AI wiki memory
- `aiwiki_scaffold_no_target_memory`: AI wiki exists, but not the target distribution memory
- `aiwiki_linked_raw_only`: target raw draft evidence exists
- `aiwiki_linked_consolidated_only`: linked consolidated guidance exists

## Manual v2 prompt

Manual v2 uses only:

- `original.md`: the historical task shape without the direct coordination boundary sentence

The old `short.md` and `medium.md` files are retained only for round1 interpretation. `medium.md`
should not be used for workflow-primary claims because it tells the agent the coordination answer.

## Human evaluation questions

- Did the agent make Windows support real end-to-end instead of patching npm alone?
- Did it keep public release targets aligned across workflows, npm metadata, archive handling,
  docs, and release-facing checks?
- Did it add the later targets without leaving obvious target drift behind?
- Did it avoid unrelated product or wiki churn?
- Did the AI wiki workflow help it coordinate more of the relevant surfaces without extra prompt
  detail?
