---
title: "Computer Use VS Code Codex multiline prompts need clipboard paste"
author_handle: "bochengyin"
model: "gpt-5.5"
source_kind: "task"
status: "draft"
created_at: "2026-04-25T01:28:00+10:00"
updated_at: "2026-04-25T01:28:00+10:00"
promotion_candidate: false
promotion_basis: "none"
---
# Draft Note

## Context

While running a manual smoke of the workflow-primary impact eval through the VS Code Codex
extension with Computer Use, the benchmark prompt needed to be entered as one multi-line message.

An early attempt used direct text typing into the webview input. The embedded newlines were treated
as message submission or steering boundaries, which fragmented the prompt and left the original
workspace dirty.

## Fix

For future VS Code Codex UI eval runs driven through Computer Use:

- open the target repo in a fresh trusted VS Code window
- confirm the Codex extension is selected, not Chat or Claude Code
- put the full prompt on the macOS clipboard with `pbcopy`
- paste with `super+v`
- inspect the accessibility tree to confirm the whole prompt is present in one text entry area
- submit with the visible send button
- if a prompt-entry mistake dirties the workspace, clone a fresh copy and run the smoke there

## Reuse Assessment

This is task-specific but likely reusable for manual UI eval runs, especially when the prompt has
blank lines or bullet lists. Keep as a draft until repeated in another UI-driven eval workflow.
