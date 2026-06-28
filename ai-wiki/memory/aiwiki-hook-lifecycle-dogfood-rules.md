# AI Wiki Hook Lifecycle Dogfood Rules

## Trigger

Read when implementing, reviewing, or dogfooding lifecycle hook support for
AI Wiki Toolkit, especially Codex `SessionStart`, `UserPromptSubmit`,
`PostToolUse`, and `Stop` hooks that replace the managed AI Wiki block in
`AGENTS.md` or `CLAUDE.md`.

## Public/Local Signal

On 2026-06-21/2026-06-22, a hook-only Flask SWE-chain dogfood run was executed
from local experiment:

`artifacts://local-swe-chain/swe-chain-020-flask-aiwiki-lifecycle-hooks`

The isolated host app had `.codex/hooks.json` installed and the managed
`<!-- aiwiki-toolkit:start -->` block stripped from `AGENTS.md`. The full
Flask `2.0.0 -> 2.3.3` chain completed `17/17` steps OK.

Key local outcomes:

- `AGENTS.md` did not contain `aiwiki-toolkit:start` or `AI Wiki Local Workflow Gate`.
- `.codex/hooks.json` invoked `python3 -m ai_wiki_toolkit.hooks.codex <event>`.
- Toolkit tests in the hook worktree passed: `297 passed, 1 skipped`.
- Full-chain pass rates were mostly `1.0`; the main outlier was
  `2.1.3 -> 2.2.0` with pass rate `0.0`, later recovered by subsequent steps.
- Final memory directory contained 9 non-index notes.
- Eval overall: build F1 `0.8298`, build+fix F1 `0.3321`, final-holdout F1
  `0.2857`.
- A follow-up log comparison found that the `2.1.3 -> 2.2.0` outlier was an
  implementation regression introduced during `fix_1`, not evidence that the
  hook runtime itself failed. The hook run changed `src/flask/globals.py` to
  `request_ctx = LocalProxy(lambda: _cv_request.get())`; with no request
  context, Flask's `tests/conftest.py` leak detector hit `while request_ctx:`
  and every revealed/holdout test teardown raised `LookupError`.

Follow-up stop-only run on 2026-06-22:

- `.codex/hooks.json` configured only `SessionStart`, `PostToolUse`, and
  `Stop`; `UserPromptSubmit` was intentionally absent.
- `Stop` used a conditional footer gate: complete AI Wiki reuse/write-back
  footer lines returned `continue`, while missing lines would block with the
  moved write-back decision reminder.
- The full Flask chain again completed `17/17` steps OK. Overall eval recovered
  from the earlier catastrophic run: build F1 `0.7685`, build+fix F1 `0.9861`,
  final-holdout F1 `0.9177`.
- The old `2.1.3 -> 2.2.0` `LookupError` cascade did not recur. That step's
  final holdout returned to the same small-failure range as the 018/019 runs.
- `Stop` final footer compliance was `32/32`, but this natural run did not
  exercise the block-and-retry path because all final messages already included
  the required footer.
- `PostToolUse` did not surface `<aiwiki-error-detected>` reminders in the live
  log despite failed command events, so treat Bash-failure reminders as an
  integration gap until a controlled hook-payload test proves the schema and
  matcher.
- `SessionStart` still caused agents to read broad AI Wiki indexes and record
  `not_helpful` reuse telemetry in some steps. Tighten the injected text so
  material memory reuse is recorded, but generic index checks are not counted as
  user-owned memory use.

Trusted Stop-only rerun on 2026-06-22:

- The isolated host app configured only the `Stop` hook in `.codex/hooks.json`,
  removed `.agents/`, kept `ai-wiki/_toolkit/system.md`, and ran host Codex with
  `--dangerously-bypass-hook-trust`.
- The full Flask `2.0.0 -> 2.3.3` chain completed `17/17` steps OK.
- Overall eval: build F1 `0.7935`, build+fix F1 `0.9515`, final-holdout F1
  `0.9286`.
- The old `2.1.3 -> 2.2.0` catastrophic holdout cascade did not recur. That
  step returned to a small residual failure/error range instead of the prior
  all-teardown-error pattern.
- `Stop` footer compliance was `30/30`, and `Stop` block events were `0`.
  This proves the `Stop` continue path worked in the natural run, but the
  natural run still did not exercise the block-and-retry path.
- The run still produced AI Wiki write-back/reuse behavior: 9 final messages
  reported memory reuse and 5 reported memory write-back with a path. This came
  from the agent voluntarily performing the final write-back check before
  stopping, not from `SessionStart`, `UserPromptSubmit`, or `PostToolUse`.
- The experiment evaluator initially undercounted write-back because it only
  matched `AI Wiki Write-Back: memory recorded`; Stop-only finals used
  `AI Wiki Write-Back: recorded`. Count both forms in experiment attribution.

Stop + PostToolUse ablation on 2026-06-22:

- The isolated host app configured only `Stop` and `PostToolUse`, removed
  `.agents/`, stripped the managed AI Wiki block from `AGENTS.md`, and used the
  same `gpt-5.5` high-effort Codex setup with `--dangerously-bypass-hook-trust`.
- The full Flask `2.0.0 -> 2.3.3` chain completed `17/17` steps OK.
- Overall eval: build F1 `0.7075`, build+fix F1 `0.9474`,
  final-holdout F1 `0.9047`.
- Compared with the trusted Stop-only run, adding `PostToolUse` improved build
  recall slightly but lowered build precision and final-holdout F1 in this
  single run. There was no catastrophic step or implementation-regression flag.
- `live_log.jsonl` did not show hook-provided context: it counted
  `aiwiki-error-detected` as `0` and `aiwiki-stop-writeback-check` as `0`.
  Codex session transcripts for the same run showed the real hook behavior:
  `315` PostToolUse developer reminders and `18` Stop hook continuation prompts.
- All 33 final answers that completed after hook handling reported
  `AI Wiki Write-Back: none`; no `AI Wiki Write-Back Path` was produced. The
  many Bash/test/import failures were therefore surfaced as write-back
  candidates but were not incorrectly written as memory.

Strict Stop-only and Stop + PostToolUse reruns on 2026-06-23:

- Both reruns used the hook-lifecycle worktree with the stricter `Stop` footer
  gate and high-precision `PostToolUse` matcher, the same `gpt-5.5` high-effort
  Codex setup, and stripped prompt-file AI Wiki blocks.
- Stop-only strict completed the full Flask `2.0.0 -> 2.3.3` chain `17/17`.
  Overall eval: build F1 `0.8210`, build+fix F1 `0.9953`, final-holdout F1
  `0.9425`. `Stop` produced `17` block prompts; all `28` task-complete final
  messages contained the required AI Wiki footer. It recorded `4` memories.
- Stop + strict PostToolUse completed the full chain `17/17`. Overall eval:
  build F1 `0.8394`, build+fix F1 `0.9862`, final-holdout F1 `0.9302`.
  `PostToolUse` produced `66` error-detected reminders, `Stop` produced `18`
  block prompts, and all `32` task-complete final messages contained the
  required AI Wiki footer. It recorded `2` memories:
  `ai-wiki/memory/flask-221-json-compat.md` and
  `ai-wiki/memory/flask-224-werkzeug-23-test-client.md`.
- In both reruns, the critical `2.1.3 -> 2.2.0` step did not reproduce the old
  all-teardown-error holdout cascade. Stop + strict PostToolUse still had small
  residual revealed/holdout errors in several later 2.2/2.3 steps, but no
  catastrophic request-context regression.
- Product interpretation from this pair: keep `Stop` as the mandatory footer
  and write-back decision gate. Add `PostToolUse` only if the product wants
  explicit Bash/test/build failure surfacing, because it slightly improved
  build F1 in this single run but lowered build+fix and holdout F1 relative to
  strict Stop-only while increasing reminder/write-back pressure.

## Failed Attempt

Treating hook injection as only a way to move the existing `AGENTS.md` block
misses two product issues:

- `Stop` cannot be solved by another passive reminder alone. It needs a hook
  decision that blocks missing or malformed AI Wiki footer lines, and avoids
  recursion when `stop_hook_active` is set.
- If the SessionStart/system prompt over-emphasizes exhaustive reuse evidence,
  agents over-record `not_helpful` telemetry for broad index docs even when only
  one memory materially affected the task.

The dogfood also repeatedly showed that stripped SWE-chain host checkouts often
do not have runtime dependencies such as `werkzeug` installed. Import smoke
checks may fail for environment reasons and should not automatically become
project memory.

## Fix Or Rule

Use a Python hook runner with JSON stdin/stdout and event subcommands:

- `session-start`: resolve the repo root, read `ai-wiki/_toolkit/system.md`,
  and inject it as additional context.
- Do not configure `UserPromptSubmit` for the hook-only treatment. The
  end-of-task write-back decision reminder belongs in `Stop`, where the runtime
  can block only when the final answer is missing the AI Wiki completion footer.
- `post-tool-use`: for Bash failures, emit a write-back-candidate reminder, but
  do not write memory automatically.
- `stop`: continue when the final answer already includes `AI Wiki Reuse:`,
  `AI Wiki Task Relevance:`, and `AI Wiki Write-Back:`. If any of those
  completion lines are missing, block and put the former `UserPromptSubmit`
  task-end write-back reminder in the block reason. Do not validate
  `AI Wiki Write-Back Path` in the runtime hook; path presence/existence and
  memory quality belong in the experiment evaluator.

For hook-only experiments, strip the managed AI Wiki prompt block from
`AGENTS.md` to prove the hooks carry the workflow. Keep prompt-file blocks as a
fallback for agents or environments without lifecycle hooks.

Tune the injected AI Wiki workflow so reuse telemetry records materially used
docs by default. It is acceptable to state that AI Wiki was checked but no
material user-owned memory was used; do not force broad index reads into
`user-owned memory used`.

When dogfooding on stripped SWE-chain repos, prefer syntax or AST checks when
dependencies are absent. Do not create Flask-specific memories from missing
local dependencies unless the missing dependency changed the implementation
strategy in a reusable way.

When comparing 020 hook lifecycle results against 018/019, treat the
`2.1.3 -> 2.2.0` all-error holdout as a central Flask context implementation
failure. Do not attribute that spike to `SessionStart`, `UserPromptSubmit`,
`PostToolUse`, or `Stop` behavior without separate evidence.

Keep failure-attribution fields such as `hook_compliance`, `memory_reuse`,
`memory_influence`, `implementation_regression`, and `catastrophic_step` in the
experiment evaluation layer. They are useful for interpreting SWE-chain runs,
but they should not be added to the packaged `ai_wiki_toolkit` runtime or hook
runner as product behavior.

In the SWE-chain hook lifecycle experiment generator, do not emit
`UserPromptSubmit` in `.codex/hooks.json`. The hook-only treatment should
generate only `SessionStart`, `PostToolUse`, and `Stop`; `Stop` carries the
former task-end write-back reminder.

For a true Stop-only ablation, generate only `Stop`, remove repo-local
`.agents/skills`, remove prompt-level AI Wiki instructions from the task prompt,
and run Codex with `--dangerously-bypass-hook-trust`. Without the hook-trust
flag, project hooks may be skipped in automated `codex exec` runs.

The experiment evaluator may add attribution evidence such as configured hook
names, final footer compliance, memory reuse/write-back counts, dominant error
signature, `catastrophic_step`, and `implementation_regression`. Do not present
those fields as proof that a specific hook caused a code bug in a single run.
Use `causal_claim: not_supported_by_single_run` unless there is ablation or
explicit log evidence.

When interpreting Stop-only runs, distinguish three separate facts:

- `hook_compliance`: configured hooks and footer/block counts.
- `memory_behavior`: whether the agent read or wrote memory during final
  write-back handling.
- `implementation_quality`: code regressions and catastrophic signatures.

Stop-only can show perfect footer compliance while still not proving block
effectiveness if no final answer omits the footer. Use a controlled hook smoke
test to prove block/retry mechanics, and use natural chain runs to assess
runtime overhead, implementation quality, and memory behavior.

For `Stop` hook effectiveness, distinguish controlled hook behavior from run
evidence. Earlier 020 logs only proved that final outputs were footer-compliant,
not whether a real run was blocked and retried. The current desired design is a
conditional Stop reminder: a complete AI Wiki footer returns `continue: true`,
while a missing footer returns `decision: block` with the moved write-back
reminder.

Natural strict reruns on 2026-06-23 did exercise the `Stop` block-and-retry
path: Stop-only strict saw `17` missing-footer block prompts and Stop + strict
PostToolUse saw `18`. Count completion compliance from `task_complete`
`last_agent_message`, not from all intermediate `final_answer` messages,
because blocked first finals are expected to be missing the footer.

When evaluating Codex hook experiments, do not rely only on the experiment
`live_log.jsonl` for hook compliance. Hook-generated developer context and Stop
continuation prompts may be present in `~/.codex/sessions/**/rollout-*.jsonl`
even when the experiment live log omits them. Count `PostToolUse` reminders from
developer messages containing `<aiwiki-error-detected>` and count Stop
continuations from user messages containing `hook_prompt hook_run_id="stop:`.

## Applies When

- Adding packaged Codex lifecycle hook support to `aiwiki-toolkit`.
- Evaluating whether hooks can replace the managed AI Wiki prompt-file block.
- Running follow-up SWE-chain experiments that compare prompt-file, hook-only,
  and native write-back treatments.
- Debugging AI Wiki footer or telemetry-noise behavior in hook-enabled sessions.

## Do Not Use When

- The task only concerns the older 015 runner-managed after-conversation
  writeback prototype.
- The user asks for the default no-hook `aiwiki-toolkit install` path.
- The task is a normal repo code change unrelated to hook injection,
  write-back, or AI Wiki dogfood evaluation.

## Related Files

- `<local-toolkit-hook-lifecycle-repo>/src/ai_wiki_toolkit/hooks/codex.py`
- `<local-toolkit-hook-lifecycle-repo>/tests/test_codex_hooks.py`
- `artifacts://swe-chain-020/run_config/run_one.sh`
- `artifacts://swe-chain-020/groups/aiwiki-lifecycle-hooks/generate/task.py`
- `artifacts://swe-chain-020/groups/aiwiki-lifecycle-hooks/results/flask_2.0.0_to_2.3.3/codex-openai-gpt-5.5/chain.json`
- `artifacts://swe-chain-020/groups/aiwiki-lifecycle-hooks/results/flask_2.0.0_to_2.3.3/codex-openai-gpt-5.5/eval.json`

## Source Pointer

- Source: Local hook-only implementation and Flask SWE-chain full-chain dogfood
  run requested by the user on 2026-06-21.
- Captured by: Codex.
- Captured at: 2026-06-22.
