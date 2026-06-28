# Arms

The protocol arms are compositional. AI Wiki arms build on `/init` rather than
replacing it.

| Arm | Agent surface | Memory or hook surface | Comparison role |
|---|---|---|---|
| `raw` | Agent without AI Wiki or frozen `/init` prompt | None | Codex baseline |
| `init` | Frozen `/init` output in `AGENTS.md` or `CLAUDE.md` | None | Separates repo orientation from memory |
| `native` | `/init` plus AI Wiki prompt workflow | Main-thread AI Wiki reuse/writeback | Tests prompt-time memory availability |
| `stop` | `/init` plus lifecycle/Stop hook setup | Stop/lifecycle writeback path | Mechanism exploration, not clean A/B versus native |
| `exact` | `/init` plus exact-match prompt gate and Stop path | Prompt-gated memory plus Stop path | Early exact-match gate exploration |
| `raw-cc` | Claude Code raw control | None | Directional cross-runner comparison |
| `init-cc` | Claude Code `/init` control | None | Directional cross-runner comparison |
| `native-cc` | Claude Code `/init` plus AI Wiki workflow | Claude Code AI Wiki workflow | Directional cross-runner comparison |

Do not infer model-only effects from cross-runner rows until runner parity is
fixed.
