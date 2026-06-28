# Runner Parity

Current cross-runner comparisons are directional, not strict model-only A/Bs.

Known differences in this round:

- Codex runs used host Codex mode.
- Claude Code runs used container Claude Code mode.
- Codex build/fix could resume one same-step session.
- Claude Code build/fix used independent conversations.
- Codex effort was `high`.
- Claude Code effort was `max`.
- Prompt files differ by agent surface: `AGENTS.md` versus `CLAUDE.md`.

Next parity work:

- Align execution location.
- Align build/fix conversation policy.
- Align effort settings as closely as possible.
- Record per-turn token, cost, latency, and timeout data in one schema.
