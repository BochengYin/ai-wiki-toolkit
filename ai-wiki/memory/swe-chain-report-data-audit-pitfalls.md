# SWE-Chain Report Data Audit Pitfalls

## Trigger

Read when auditing, summarizing, or writing the AI Wiki SWE-Chain report from
the 019/020/021 experiment outputs.

## Public/Local Signal

On 2026-06-27, a local audit compared Claude-generated report materials under
`<local-writing-worktree>/outputs/`
against raw `eval.json` and selected `chain.json` artifacts under
`artifacts://local-swe-chain/`.

The C-group pure data tables mostly matched raw eval artifacts, but several
report-writing pitfalls were found:

- `conan_2.12.0_to_2.20.1 / exact` is a valid partial eval with 14 of 16 steps.
- `xarray_2022.11.0_to_2023.7.0 / native` is a valid partial eval with 9 of 10
  steps.
- `aiwiki_perstep_delta_vs_raw*.md` total deltas use overlapping steps when a
  comparison arm is partial, not full-chain totals.
- `eval.json.chain[]` is phase-granular. Count migration steps by unique
  `(prev_version, next_version)` pairs, not by the number of `chain[]` entries;
  otherwise full runs look like 30/48 phase rows and partial detection is wrong.
- 020 Flask has two valid stop-hook numbers: the best stop-only archive
  `stop-only-strict-20260623T0730` has build+fix F1 0.9953, precision 1.0, FP 0;
  current `results/flask/.../eval.json` points to `stop-post-strict-20260623T0935`
  with build+fix F1 0.9862, precision 0.9817, FP 2.
- Some status prose in the data packet lagged the current eval files, especially
  019-claudecode, 020 xarray harness-fix, and 021 exact-match conan.
- For FP mechanism claims, checking only the agent diff is not enough: at least
  the conan `untargz` rename and xarray pandas shim also appeared in `gold_diff`.

## Failed Attempt

Treating every valid `eval.json` as a full-chain comparable result makes partial
runs look stronger or weaker than they are. Treating current `results/` as the
only source for 020 Flask also conflicts with the stop-only-all summary, which
explicitly skipped Flask and points to the best stop-only archive.

Mechanism prose that says "the model made an over-boundary edit" is too strong
unless the corresponding `gold_diff` is checked. If the same line appears in
`gold_diff`, the safer wording is that the live patch produced a true regression
under the SWE-Chain FP metric, while causal attribution to memory or agent
overreach remains weaker.

## Fix Or Rule

For this report:

- Use raw `eval.json` as the numeric source of truth, but separately track step
  coverage for every valid cell.
- When generating coverage tables, derive step coverage from unique
  `(prev_version, next_version)` pairs in `eval.json.chain[]`.
- Mark partial evals explicitly and compare them only against overlapping steps
  unless reporting them as partial absolute metrics.
- Keep 020 Flask hook ablation and 020 cross-repo stop-only tables separate.
  Decide explicitly whether the cross-repo stop table uses the stop-only-all
  summary archive or current `results/`, then use that choice consistently.
- Treat C-group pure TP/FP/FN and rate tables as mostly trustworthy after this
  audit, but refresh stale status prose before report writing.
- For FP mechanism claims, cite both `agent_step_diff` and `gold_diff` status.
  Use "live patch regression" when `gold_diff` contains the same change; reserve
  "agent overreach" for changes absent from gold or otherwise locally justified.
- In report prose and tables, avoid the official SWE-Chain `TP`/`FN`/`FP`/`TN`
  terminology except when mapping back to raw `eval.json`. AI Wiki memory here
  is not ML model training; these are real repo upgrade outcomes from test
  behavior, and ML confusion-matrix labels can mislead readers.
- Use reader-facing IT terms:
  `fixed target behavior` for official `TP`, `missed target behavior` for
  official `FN`, `introduced unrelated regression` for official `FP`, and
  `preserved unrelated behavior` for official `TN`.
- Prefer positive report metrics: `target fix rate =
  fixed target behavior / (fixed target behavior + missed target behavior)` and
  `unrelated-behavior preservation rate = preserved unrelated behavior /
  (preserved unrelated behavior + introduced unrelated regression)`.
- When a cost-oriented metric is needed, describe official `FP/(FP+TN)` as
  `introduced unrelated regression rate`, not as a generic `regression rate` or
  as tests being damaged.
- In the cross-model report table, include scale columns before difficulty:
  `steps` from unique codex raw migration pairs and `raw ref scored tests` from
  the codex raw build+fix `evaluated` total. Treat this as scored test outcomes
  across steps, not a de-duplicated count of test files or test names.
- Treat Codex-vs-Claude Code cells as directional until runner parity is fixed:
  current Codex runs use host Codex mode, `effort=high`, and same-step
  build/fix session resume, while Claude Code runs use container mode,
  `effort=max`, and independent build/fix conversations. Report this as a
  comparability limitation and planned harness improvement, not an only-model
  changed A/B.
- In the Runner Parity section, frame these differences as a post-run analysis
  finding. The first round can still provide directional evidence about memory
  behavior, but it should not be presented as strict Codex-vs-Claude model-only
  evidence. The next harness round should align execution location, build/fix
  conversation continuity, reasoning effort, and per-turn token/cost/latency
  logging before making stronger cross-model claims.
- Frame the report around AI Wiki as a repo-level self-improvement layer for
  coding agents. SWE-Chain software upgrades are the first controlled external
  testbed, not the product thesis or the only target domain.
- In the report framework, explain what AI Wiki-style repo memory means before
  asking whether it helps. The core question should be about repo-level agent
  memory improving future coding-agent work without adding introduced unrelated
  regressions.
- Do not describe the original dogfood motivation as "task leakage" unless
  there is specific evidence. The better framing is narrower generalization:
  dogfood was a replay suite over real historical `ai-wiki-toolkit` problems.
  It restored earlier repo states and asked whether ambient repo memory could
  help a fresh agent solve on the first attempt, instead of repeating the
  original trial-and-error. That showed memory can help with known historical
  failures, but it could not prove usefulness for future unknown tasks whose
  shape was not visible when the memory was written. SWE-Chain was adopted
  because its chained real-repo upgrade steps create a controlled way to test
  that future-task question.
- Write harness reliability as an empirical run description first: how this
  round actually launched groups, ran build/fix turns, resumed chains, scored
  `eval.json`, and audited source-of-truth tables. Put proposed reliability
  fixes in a separate "next harness fix" section.
- In the harness reliability section, distinguish "already used" safeguards from
  "next harness fixes" by automation level. The former can be manual, ad hoc, or
  experiment-family-specific checks used to reduce this round's report risk; the
  latter should be uniform harness flags or publish-time review gates that
  surface stale, partial, empty, or cross-contaminated data before it reaches
  headline tables.
- Do not list the same data-quality action as both already done and future work.
  For empty `0/0/0` eval shells, the current-round statement is that they are
  quarantined in `coverage-status.md` and excluded from current result tables;
  the next-round harness fix is an automatic report-generation flag if an empty
  shell appears outside the coverage/quarantine table, not necessarily a hard
  failure.
- Frame source-of-truth drift as a dependency invalidation problem. The future
  fix should be a report-refresh skill or workflow with explicit file
  dependencies: raw `eval.json` and audit overrides feed `source-of-truth/`
  tables; those tables feed report sections and imported narrative summaries.
  When an upstream artifact changes, regenerate downstream files or mark them
  stale before publication.
- For public-facing experiment artifact structure, do not expose local absolute
  paths as the reproducibility interface. Use logical artifact IDs, sanitized
  relative paths, provenance metadata, checksums, schemas, and selected public
  examples or downloadable archives. Local paths can stay in ignored local manifests
  or developer notes, but the report should explain how to map results to
  artifacts without revealing the author's local machine layout.
- Version exploration setup separately from result artifacts. Each exploration
  should have a setup manifest that records harness script versions, runner/task
  component fingerprints, AI Wiki install surface, prompt gate, hooks, writeback
  timing, memory policy, and staleness triggers. When `run.sh`,
  `generate/chain.py`, `generate/task.py`, hooks, or AI Wiki setup changes,
  create a new setup version instead of mutating old run records in place.
- Protocol arm definitions must be compositional: `native`, `stop`, and `exact`
  are all `/init` plus an AI Wiki mechanism. Do not describe them as if they
  were independent alternatives to `/init`.
- Treat runner parity gaps as post-run analysis findings and next-round harness
  work, not as intentional design choices. Explain that Codex currently used
  host mode with same-step build/fix session continuity, while Claude Code used
  container mode with independent build/fix conversations.
- Keep 015/017/018/020/021 mechanism references separate in the report:
  015 is runner-normal-end fork/quarantine writeback into `ai-wiki/memory`, 017
  is package-managed `.agent` hook/runtime plumbing, 018 is the cleaner real
  install/no-router/main-thread dogfood structure, 020 is lifecycle Stop-hook
  ablation, and 021 is Stop plus prompt-time exact-match gate. For 017, say that
  it did not test the normal product install surface (`aiwiki-toolkit install`
  creating `ai-wiki/` plus the standard prompt gate); it tested package-shaped
  `.agent/` hook/runtime plumbing. Do not cite 017 as a headline performance
  cell unless the intended `chain.json`/`eval.json` is complete and audited.
- Future-work framing should include progressive memory classification. Do not
  treat every writeback as the same passive note: stable lessons may become
  convention memory, one-off failures can stay trial-error notes, and repeated
  repair workflows may become repo-local skills that future steps call and
  refine. If this is tested, measure skill invocation, reduced repeated
  trial-and-error, and introduced unrelated regressions, not only target fix
  rate.
- Write the report as first-person solo research where appropriate. Avoid
  saying "we" when describing the researcher's decisions or interpretation.
  Also avoid presenting the current protocol as final; call it the current
  working point or current frontier unless a concrete final decision has been
  made.
- Router framing should be simple and product-oriented: the router grew
  naturally out of dogfood AI Wiki Toolkit design, but SWE-Chain provided the
  evidence that toolkit-selected routing can give certain files special
  attention without enough precision proof. The report conclusion should be
  that routine memory selection belongs to the agent using a bounded index/read
  rules, while the toolkit router stays out of the default path.
- Do not say the hook/writeback experiments "moved" the product to hooks.
  Earlier dogfood was prompt/main-thread writeback; 015/017 explored whether
  hook/fork/package-managed writeback could help; 018 showed that no-router
  main-thread dogfood remained the cleaner product baseline. Treat hooks as
  infrastructure experiments unless later data proves a clear product advantage.
- Before the experiment timeline, explain the concrete AI Wiki architecture:
  the managed `AGENTS.md`/`CLAUDE.md` prompt gate used by the Codex/Claude
  SWE-Chain harness, the repo-local `ai-wiki/` tree, `_toolkit/system.md`,
  repo-local skills, bounded `memory/index.md` progressive disclosure, and
  where the old `aiwiki-toolkit route` packet sat relative to the coding turn.
  Include an abbreviated view of the `_toolkit/system.md` rules instead of only
  saying that the prompt gate reads it. Frame the following experiments around
  two product problems: what writeback mechanism should make useful memory
  durable, and what safe-reuse mechanism should expose that memory without
  over-framing the next implementation.
- Add an architecture caveat that the current AI Wiki prompt/setup is the
  current experimental state after many dogfood and SWE-Chain revisions, not
  final product copy. Explain that benchmark prompts are intentionally explicit
  for auditability and should be tidied into a more formal surface after a
  better mechanism is selected.
- Document hook and prompt variants in a separate mechanism-exploration section,
  not as part of the default AI Wiki architecture. For each mechanism, state
  what prompt the agent sees, whether memory can affect implementation, what
  event invokes writeback, how the mechanism is tested, where candidate memory
  is written, and how the run avoids hidden/future/cross-run leakage. Keep
  main-thread native, 015 runner-normal-end writeback, 017 package-managed
  `.agent` hook runtime, 020 lifecycle/Stop hook, and 021 exact-match gate
  separate.
- When explaining 015 runner-normal-end writeback, define internal terms:
  `harness` means the SWE-Chain runner outside the coding agent, and
  `turn.completed` means the Codex session emitted a normal-completion event
  for the build/fix turn, not that tests passed. Explain that 015 originally
  tried agent-self-invoked hook timing, found it unreliable, and moved timing to
  the runner: only after normal turn completion should `after_conversation.py`
  run; timeout, crash, nonzero exit, or missing `turn.completed` should skip
  writeback. Also clarify that hook timing before the next revealed-feedback
  pass blocks new feedback/final/future/cross-group leakage, while fix turns may
  still include already-revealed failure data in the prompt.
- In the formal report, keep the main mechanism table compact. Do not keep a
  wide `How it tests` column in the reader-facing table. Instead, put the 1-9
  execution flows in Appendix A with the source files and terminology. The main
  table should keep only mechanism, prompt/memory surface, invocation model,
  `What it tests`, `Observed result`, and `Caveat`.
- Clarify that 015 uses a runner-managed hook-like script, not a Codex lifecycle
  Stop hook. In the treatment group, `after_conversation.py` calls
  `hooks/codex_fork_once.py` with the parent Codex session id to create a child
  writeback session. That child receives a narrow
  `ai-wiki-trial-error-writeback` prompt, must not modify source or run tests,
  and can only write `candidate.md` plus `decision.json` under quarantine or
  skip. The reference group uses deterministic harness candidate generation
  rather than a real forked writeback agent.
- When writing the 015 caveat, do not leave it at "not a clean product UX
  decision." Spell out the concrete product problem: the forked child Codex
  writeback sessions polluted the local Codex session history, so benchmark/test
  sessions could bury the user's real development sessions. That makes 015 useful
  harness evidence, but not a product-clean UX shape.
- Apply the same step-level execution-flow treatment to all mechanism rows in
  Appendix A, not only 015. Before writing steps, verify the corresponding
  manifest, prompt, hook config, source-of-truth table, or runtime/log artifact.
  For main-thread native, use 018 no-router dogfood and 019 Claude notes; for
  017, use `run_group.sh`, benchmark `AGENTS.md`,
  `.codex/hooks/aiwiki_enqueue_writeback.py`, and
  `.agent/_toolkit/writeback/runtime`; for 020, use the hook-ablation
  source-of-truth table, `.codex/hooks.json`, and lifecycle hook source; for
  021, use the exact-match `AGENTS.md` and Stop hook config.
- When describing `/init` arms, do not say "add `/init` guidance" as if it were
  hand-written. The accurate order is: run `/init` for the target agent, or use
  the harness's frozen `/init` output, to create the instruction file
  (`AGENTS.md` for Codex, `CLAUDE.md` for Claude Code), then install/overlay the
  AI Wiki gate and memory mechanism on top of that file.
- When contrasting 015 and 017, write the difference directly into 017's
  invocation model: 015 uses the outer SWE-Chain runner to directly trigger a
  harness script (`after_conversation.py`) after `turn.completed`; 017 packages
  writeback into the repo/app runtime, where `.codex/hooks/aiwiki_enqueue_writeback.py`
  receives the hook payload and calls `.agent/_toolkit/writeback/runtime/enqueue.py`.
  In both mechanisms, the coding agent returns normally and does not call
  writeback itself.
- In mechanism tables, keep `What it tests`, `Observed result`, and `Caveat`
  separate. `What it tests` is the hypothesis or question, `Observed result` is
  what the current evidence showed, and `Caveat` is the interpretation limit.
  Do not hide empirical results inside the caveat column. Current key results:
  018 Flask no-router completed 17/17 with build+fix F1 0.9907 and 1 introduced
  unrelated regression; 015 completed both formal Flask groups with 31 formal
  hook/fork attempts, 20 published notes, 11 skips, and no audited leakage; 017
  produced 15 enqueued/15 finished package-runtime jobs and 13 indexed notes;
  020 Stop-only strict was best in Flask hook ablation with F1 0.9953 and 0
  introduced unrelated regressions; 021 Flask exact-match + Stop regressed badly
  with F1 0.2524 and 439 introduced unrelated regressions.

## Applies When

- Writing the AI Wiki memory research report.
- Recomputing 019/020/021 SWE-Chain tables.
- Comparing exact-match, stop-only, native, init, and raw groups.
- Explaining FP mechanisms from `chain.json` diffs.

## Do Not Use When

- Running unrelated ai-wiki-toolkit code changes.
- Reporting a different benchmark that has different partial-run semantics.
- Making claims from hidden evaluator answers or hidden test names.

## Related Files

- `<local-writing-worktree>/outputs/aiwiki_perstep_fp_fn.md`
- `<local-writing-worktree>/outputs/aiwiki_rate_metrics.md`
- `<local-writing-worktree>/outputs/aiwiki_rate_metrics_merged.md`
- `artifacts://swe-chain-020/run_config/run-logs/stop-only-strict-all-20260623T134503/summary.tsv`

## Source Pointer

Source: local audit by Codex during report-data review on 2026-06-27; user
terminology clarification on 2026-06-27; user motivation-framing correction on
2026-06-28; user progressive-memory/skillization future-work idea on
2026-06-28; user router/hook framing correction on 2026-06-28; user AI Wiki
architecture framing correction on 2026-06-28; user request to add experimental
setup caveat and separate hook mechanism section on 2026-06-28; user request to
define 015 harness and `turn.completed` terminology on 2026-06-28; user request
to add `How it tests` mechanism-table column and expanded 015 flow on
2026-06-28; user clarification that 015 treatment uses `after_conversation.py`
to fork a child writeback session on 2026-06-28; user request to put 015's
detailed 1-9 sequence inside the `How it tests` table cell on 2026-06-28; user
request to make all mechanism rows step-level and verify them against docs/logs
on 2026-06-28; user correction that `/init` creates the agent instruction file
before AI Wiki is layered on top on 2026-06-28; user clarification to put the
015-vs-017 trigger/runtime distinction directly in 017's invocation model on
2026-06-28; user request to separate mechanism hypotheses from observed results
on 2026-06-28; user clarification that 015's product caveat is local Codex
session-history pollution from forked benchmark writeback sessions on
2026-06-28; user decision to use a compact main mechanism table plus Appendix A
detailed execution flows on 2026-06-28; user Runner Parity framing and planned
harness-fix outline on 2026-06-28; user clarification that harness reliability
"already used" items are manual/local safeguards while "next fixes" are automated
guardrails on 2026-06-28.
