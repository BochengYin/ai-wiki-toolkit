---
title: "Local dogfooding should check source CLI vs installed entrypoint"
author_handle: "bochengyin"
model: "gpt-5"
source_kind: "tooling"
status: "draft"
created_at: "2026-05-17T00:10:00+10:00"
updated_at: "2026-05-17T00:10:00+10:00"
promotion_candidate: false
promotion_basis: "single local dogfooding signal"
---
# Draft

## Context

While evaluating whether `ai-wiki-toolkit` is useful, the PATH executable at `/Users/by/.local/bin/aiwiki-toolkit` exposed only the older command set: `route`, `install`, `init`, `uninstall`, `refresh-metrics`, `record-reuse`, `record-reuse-check`, and `doctor`.

Running the source CLI with `python -m ai_wiki_toolkit.cli --help` from the repository exposed the newer product surfaces too: `work`, `diagnose`, `consolidate`, and `eval`.

## Lesson

When dogfooding local product usefulness from inside this repo, compare the installed entrypoint with the source CLI before judging feature availability.

## Practical Check

Use both commands when the CLI surface itself is part of the evaluation:

```bash
aiwiki-toolkit --help
python -m ai_wiki_toolkit.cli --help
```

If they differ, evaluate source behavior with `python -m ai_wiki_toolkit.cli ...` and treat the installed executable as a packaging or environment freshness signal.

## Reuse Assessment

This can prevent future agents from incorrectly concluding that newer toolkit features are missing when the local source tree already contains them.
