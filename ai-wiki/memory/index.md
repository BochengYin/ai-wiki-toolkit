# Memory Index

This folder contains bounded, public/local trial-error memory for future coding agents.

## Read Rule

Read this index first, then open at most one linked memory file before acting.

Open a memory file only when it strongly matches the current source file, API, command,
behavior, or repeated public/local failure surface.

Do not use hidden evaluator failures, hidden test names, private benchmark answers, or
prior hidden-derived fixes as memory.

## Entries

- [SWE-Chain 015 Agent Writeback PRD Rules](swe-chain-015-agent-writeback-prd-rules.md):
  read when running, reviewing, or modifying the `swe-chain-015-flask-agent-skill-writeback` experiment,
  especially runner normal-end hook protocol and quarantine/audit rules.
- [SWE-Chain 018 Dogfood No-Router Main-Thread Rules](swe-chain-018-dogfood-no-router-main-thread-rules.md):
  read when running, reviewing, or modifying the `swe-chain-018-flask-dogfood-no-router-writeback`
  experiment or the `AI Wiki Native Writeback` cross-repo panel, especially no-router dogfood setup,
  main-thread writeback rules, the three-group SWE-chain comparison protocol, and chain-level
  agent startup failures in the remaining-repo panel.
- [SWE-Chain 017 Toolkit Hook vs 015 Agent-Skill Rules](swe-chain-017-toolkit-hook-vs-015-agent-skill-rules.md):
  read when comparing the `swe-chain-017-flask-aiwiki-toolkit-hook-writeback` package-managed
  toolkit hook experiment with the `swe-chain-015-flask-agent-skill-writeback` bespoke fork/skill experiment.
- [NPM Global Install Path Shadowed By UV Tool](npm-global-install-path-shadowed-by-uv-tool.md):
  read when installing or verifying the latest npm `ai-wiki-toolkit` package locally, especially
  if `npm install -g` succeeds but the bare `aiwiki-toolkit` command still reports an older version.
- [AI Wiki Hook Design Should Integrate, Not Copy](aiwiki-hook-design-integrate-not-copy.md):
  read when designing, implementing, or evaluating hook-based AI Wiki workflow support,
  especially moving managed prompt guidance into Codex lifecycle hooks while preserving
  prompt-file fallback.
- [AI Wiki Hook Lifecycle Dogfood Rules](aiwiki-hook-lifecycle-dogfood-rules.md):
  read when implementing, reviewing, or dogfooding lifecycle hook support for AI Wiki Toolkit,
  especially hook-only Codex `SessionStart`, `UserPromptSubmit`, `PostToolUse`, and `Stop`
  behavior that replaces the managed AI Wiki prompt-file block, or diagnosing the 020 Flask
  hook-lifecycle holdout error spike.
- [AI Wiki PostToolUse Codex Error Matching](aiwiki-posttooluse-codex-error-matching.md):
  read when implementing or evaluating Codex lifecycle `PostToolUse` reminders, especially
  tool-name matching for `exec_command` and high-precision shell error detection without
  false positives from source-code exception names.
- [AI Wiki Native Retrieval Gate, Not Top-K](aiwiki-native-retrieval-gate-not-topk.md):
  read when designing or evaluating AI Wiki Native Writeback or pre-edit memory retrieval,
  especially when diagnosing false positives from accumulated local memories or deciding
  whether to allow more than one memory file per task.
- [SWE-Chain Long Runs Need Detached Screen](swe-chain-long-runs-use-screen.md):
  read when launching long-running SWE-chain or AI Wiki Toolkit experiment queues from Codex,
  especially if a plain background `nohup ... &` leaves only an idle Docker container and no
  `thread.started` or `turn.started` events in `live_log.jsonl`, or when using a watcher to
  start a dependent follow-up run after a partial SWE-Chain run completes.
- [SWE-Chain Report Data Audit Pitfalls](swe-chain-report-data-audit-pitfalls.md):
  read when auditing, summarizing, or writing the AI Wiki SWE-Chain report from the 019/020/021
  experiment outputs, especially partial evals, 020 Flask stop archive vs current results,
  step coverage counted by unique migration pairs rather than `chain[]` phase rows,
  overlapping-step delta totals, stale status prose, empty-shell current-vs-future guardrail
  wording, public artifact packaging without local absolute paths, versioned exploration setup
  manifests, and FP mechanism claims that require checking both `agent_step_diff` and
  `gold_diff`; also use the reader-facing IT terminology for official SWE-Chain TP/FN/FP/TN
  labels in report prose.
- [Skill Installer GitHub Download SSL Fallback](skill-installer-github-download-ssl-fallback.md):
  read when installing a Codex skill from GitHub with the global skill installer, especially if
  the helper fails in Python `urllib` with an SSL certificate verification error; retry the same
  install with `--method git`.

## Suggested Entry Shape

Each memory file should include:

- Trigger
- Public/Local Signal
- Failed Attempt
- Fix Or Rule
- Applies When
- Do Not Use When
- Related Files
- Source Pointer
