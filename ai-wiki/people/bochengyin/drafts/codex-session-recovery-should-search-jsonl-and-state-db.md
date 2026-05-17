---
title: "Codex session recovery should search JSONL and state DB"
author_handle: "bochengyin"
model: "gpt-5"
source_kind: "tooling"
status: "draft"
created_at: "2026-05-17T12:55:00+10:00"
updated_at: "2026-05-17T12:55:00+10:00"
promotion_candidate: false
promotion_basis: "single local recovery signal"
---
# Draft

## Context

When asked to find a missing historical Codex chat window from a remembered Chinese prompt, the
fastest path was to search local Codex session files first, not ChatGPT app conversation caches.

The matching prompt appeared in:

```text
~/.codex/sessions/<year>/<month>/<day>/rollout-*.jsonl
```

The corresponding thread metadata came from:

```text
~/.codex/session_index.jsonl
~/.codex/state_5.sqlite
```

## Lesson

For local Codex session recovery, first search `~/.codex/sessions` with a distinctive prompt
fragment, then map the session id through `~/.codex/state_5.sqlite` table `threads` to recover
the title, cwd, archived status, timestamps, and rollout path.

Use `codex resume <session-id>` when the user wants to reopen the session in the CLI.

## Useful Commands

```bash
rg -n --hidden -S "<remembered prompt fragment>" ~/.codex/sessions ~/.codex/session_index.jsonl
sqlite3 -header -column ~/.codex/state_5.sqlite \
  "select id,title,cwd,datetime(created_at,'unixepoch','localtime') created,datetime(updated_at,'unixepoch','localtime') updated,archived,rollout_path from threads where id='<session-id>';"
codex resume <session-id>
```

## Reuse Assessment

This should help future agents recover Codex Desktop / VS Code-originated sessions for manual eval
work without depending on temporary exported session directories that may have been cleaned from
`/private/tmp`.
