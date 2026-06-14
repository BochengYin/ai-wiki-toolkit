---
title: "SWE-Chain first eval should start with smoke and A/B memory slice"
author_handle: "bochengyin"
model: "gpt-5"
source_kind: "feature_clarification"
status: "draft"
created_at: "2026-06-09T20:35:00+10:00"
updated_at: "2026-06-10T19:46:57+10:00"
promotion_candidate: false
promotion_basis: "none"
---
# Draft

## Context

The user identified SWE-Chain as the first benchmark to test for `ai-wiki-toolkit`.
SWE-Chain has a public GitHub harness at `CUHK-ARISE/SWE-Chain` and a Hugging Face dataset with
155 version transitions across 12 chains. The harness supports Claude Code, Codex, and OpenCode and
evaluates chained Python package upgrades.

## Product Implication

Treat SWE-Chain as the first external long-horizon coding-agent eval candidate for the
`eval-as-product-mvp` work, but start with a narrow reproducibility slice:

- clone and run the harness locally without changing `ai-wiki-toolkit`
- load the published specs dataset and confirm one chain can be selected
- run one short or truncated Codex chain as a smoke test
- score the run with the upstream `eval.sh`
- only after the harness works, run an A/B comparison with AI Wiki disabled vs enabled

The useful product metric is not just SWE-Chain's native resolving/precision/F1. For AI Wiki, also
capture chain survival, repeated context lookup reduction, regression notes reused across steps, and
whether start-of-task routing reduces repeated repo orientation work.

## Guardrails

- Do not start with full benchmark reproduction or leaderboard claims.
- Prefer Flask, attrs, or another shorter/lighter chain before xarray or conan.
- Keep first-run artifacts outside this repo or under generated work/output paths until a product
  surface is intentionally added.
- Preserve a clean A/B boundary: same agent/model/chain, one run with AI Wiki workflow disabled and
  one with it enabled.

## 2026-06-09 Smoke Test Notes

The first local SWE-Chain smoke used:

- root folder: `/Users/by/AI Project/AI wiki Toolkit test repos/swe-chain-001-smoke`
- benchmark repo: `CUHK-ARISE/SWE-Chain` at commit `4d4851222f6d64b48a9917af48dd5fd4d9df4a0d`
- chain slice: Flask `2.0.0 -> 2.0.1`, truncated to one JSONL row
- agent: Codex CLI with `gpt-5.5`, `max_iters=1`

Do not release npm before this kind of smoke test. A local editable install isolates benchmark and
injection failures from package publishing failures. Release/package-manager smoke should be a
separate follow-up after the benchmark path is stable.

Observed harness requirements:

- `gpt-5` was rejected for the local ChatGPT-backed Codex CLI login; `gpt-5.5` worked.
- Copying the host `~/.codex/config.toml` into the container loaded unrelated MCP servers and broke
  Codex startup. Patch SWE-Chain's Codex runner to copy only `auth.json` unless an explicit clean
  config path is provided.
- Truncating a chain changes SWE-Chain's derived oracle directory name. Add an oracle symlink such
  as `oracle/flask_2.0.0_to_2.0.1 -> flask_2.0.0_to_2.3.3`.
- For Codex, `AGENTS.md` at the execution root `/app` triggered the AI Wiki workflow gate. `AGENT.md`
  alone was visible but did not trigger the gate.
- Keep AI Wiki scaffold files at `/app`, not `/app/code`, so evaluation diffs remain package-only.
- The container did not have `aiwiki-toolkit` installed, so treatment used the managed fallback
  reads instead of `aiwiki-toolkit route`.
- Do not infer the scored treatment prompt from the host harness root prompt file. The first
  treatment checkout still had a root `AGENT.md` from an older local install, but the valid scored
  Docker run copied prompt content to `/app/AGENTS.md`. The earlier `/app/AGENT.md`-only attempt was
  archived as aborted.
- After changing the toolkit empty-repo default to `AGENTS.md`, keep the SWE-Chain injection patch
  aligned by sourcing `AGENTS.md` when available and writing `/app/AGENTS.md` for the container
  prompt.

Product implication from the prompt-file finding:

- `ai-wiki-toolkit` currently supports existing `AGENTS.md`, `AGENT.md`, and `CLAUDE.md`, but when
  no prompt file exists it falls back to creating `AGENT.md`.
- For Codex-first usage, the default fallback should be `AGENTS.md` because that is what triggered
  the workflow gate in SWE-Chain.
- Do not delete or stop refreshing existing `AGENT.md` files; keep them as compatibility for repos
  that already chose that filename. The change should be only the empty-repo default.

First smoke result:

- Baseline: hidden `464/470` pass, resolving `54.5%`, precision `85.7%`, F1 `66.7%`, elapsed
  `415.7s`.
- Treatment: hidden `465/470` pass, resolving `54.5%`, precision `100.0%`, F1 `70.6%`, elapsed
  `354.2s`.

This is only one stochastic one-step smoke with empty project memory, so it is not evidence of
causal improvement yet. It does prove that a local AI Wiki treatment can be made visible to Codex in
SWE-Chain without contaminating package diffs.

## 2026-06-09 Flask 3-Step Mini-Chain Notes

The next run used the first three Flask transitions:

- `2.0.0 -> 2.0.1`
- `2.0.1 -> 2.0.2`
- `2.0.2 -> 2.0.3`

Both sides used the same SWE-Chain commit, same `codex` agent, same `gpt-5.5` model,
`--effort medium`, and `--max-iters 1`. The three-row dataset was saved as
`data/flask_smoke_3step.jsonl`, with an oracle symlink
`oracle/flask_2.0.0_to_2.0.3 -> flask_2.0.0_to_2.3.3`.

Baseline generation survived all three steps:

- `2.0.0 -> 2.0.1`: hidden `465/470` pass, elapsed `396.7s`, tokens
  `input=1934476 output=16173 cache_read=1858560`
- `2.0.1 -> 2.0.2`: hidden `470/475` pass, elapsed `278.9s`, tokens
  `input=1445548 output=11479 cache_read=1306368`
- `2.0.2 -> 2.0.3`: hidden `474/475` pass, elapsed `183.4s`, tokens
  `input=396443 output=8375 cache_read=351744`

Treatment generation also survived all three steps:

- `2.0.0 -> 2.0.1`: hidden `464/470` pass, elapsed `450.3s`, tokens
  `input=2959534 output=17408 cache_read=2838656`
- `2.0.1 -> 2.0.2`: hidden `469/475` pass, elapsed `424.9s`, tokens
  `input=3080402 output=15249 cache_read=2889216`
- `2.0.2 -> 2.0.3`: hidden `469/475` pass, elapsed `289.8s`, tokens
  `input=986610 output=11893 cache_read=882816`

Upstream `eval.sh` scores:

- Baseline overall build: recall `65.38%`, precision `100.0%`, F1 `79.07%`
- Treatment overall build: recall `46.15%`, precision `100.0%`, F1 `63.15%`
- Baseline step F1: `70.6%`, `77.8%`, `100.0%`
- Treatment step F1: `62.5%`, `77.8%`, `0.0%`

Important interpretation:

- The 3-step mini-chain confirmed chain inheritance: later steps saw the previous step's version
  metadata and changelog state.
- The treatment run was strict AGENTS-only inside Docker: `/app/AGENTS.md` existed, `/app/AGENT.md`
  did not, `/app/ai-wiki` existed, and `/app/code/ai-wiki` did not.
- `chain.json` did not contain `ai-wiki`, `AGENTS.md`, `AGENT.md`, or `_toolkit` paths, so the
  `/app` injection strategy avoided Flask diff contamination.
- Each treatment Codex thread read `ai-wiki/_toolkit/system.md`; the container still lacked the
  `aiwiki-toolkit` CLI, so the agent used fallback reads rather than route output.
- Treatment did not beat baseline on this run. The decisive miss was Flask `2.0.2 -> 2.0.3`: all
  four upgrade-related nodes were CLI loading-error tests (`test_help_echo_loading_error`,
  `test_locate_app_suppress_raise`, `test_no_command_echo_loading_error`, and `test_scriptinfo`).
  Baseline passed all four; treatment failed all four, so step 3 scored `TP=0, FN=4, FP=0`.
- Treatment recovered 11 non-upgrade-related failures in step 3, but SWE-Chain reports those under
  `recovered`, not as F1 true positives. Track them as chain-survival evidence separately from
  native F1.
- The Flask container lacks `git`; `git status` fails with `command not found`.
- `compileall` can produce `__pycache__` files under `/app/code`. Agents should remove generated
  bytecode before finishing so final diffs stay source-only.

## 2026-06-10 Clean Rerun Notes

The clean rerun used root folder
`/Users/by/AI Project/AI wiki Toolkit test repos/swe-chain-002-clean-rerun` and wrote the detailed
report to `REPORT.md` in that folder.

An important isolation bug was found before accepting the treatment run:

- Running `aiwiki-toolkit install` in the treatment seed repo without overriding home printed
  `System wiki: /Users/by/ai-wiki/system`.
- Even if that only resolved a path, it was not a strict A/B boundary because the user has a local
  home AI wiki.
- The invalid treatment attempt was aborted and moved under
  `treatment-aiwiki-blank/aborted/flask-treatment-home-leak-aborted-20260610-003600/`.
- The treatment harness was corrected to set temporary `HOME`, `XDG_CONFIG_HOME`,
  `XDG_CACHE_HOME`, and `AIWIKI_TOOLKIT_HOME_DIR` while generating the scaffold.
- Valid treatment seed output used `.tmp/aiwiki_seed.../home-ai-wiki/system`, and valid logs had no
  `/Users/by`, `/root/ai-wiki`, or `/home/agent/ai-wiki` mentions.

The clean rerun covered two mini-chains:

- Flask `2.0.0 -> 2.0.3`
- attrs `21.3.0 -> 22.2.0`

All four runs survived all three steps.

Clean native results:

- Flask baseline: recall `46.15%`, precision `80.00%`, F1 `58.53%`, elapsed `1247.3s`
- Flask treatment: recall `50.00%`, precision `81.25%`, F1 `61.90%`, elapsed `1363.5s`
- attrs baseline: recall `20.51%`, precision `97.56%`, F1 `33.89%`, elapsed `1012.2s`
- attrs treatment: recall `18.46%`, precision `97.30%`, F1 `31.03%`, elapsed `1165.4s`

The clean Flask rerun did not reproduce the earlier asymmetry where only treatment scored `0.0` on
step 3. In the clean rerun both Flask variants scored `0.0` F1 on `2.0.2 -> 2.0.3`; all four
upgrade-related nodes were CLI tests:

- `tests/test_cli.py::test_help_echo_loading_error`
- `tests/test_cli.py::test_locate_app_suppress_raise`
- `tests/test_cli.py::test_no_command_echo_loading_error`
- `tests/test_cli.py::test_scriptinfo`

SWE-Chain's `Res` metric is recall: `TP / (TP + FN)`. The denominator is not source files; it is the
oracle-selected upgrade-related test node set from `VersionComparator(...).f2p | e2p`, using each
step's `v<next>_test_results.json` and `v<prev>_cross_test_results.json`.

Denominator files in the clean rerun:

- Flask `2.0.0 -> 2.0.1`: 11 nodes from `tests/test_blueprints.py` and `tests/test_cli.py`
- Flask `2.0.1 -> 2.0.2`: 11 nodes from `tests/test_async.py`, `tests/test_blueprints.py`,
  `tests/test_cli.py`, and `tests/test_json.py`
- Flask `2.0.2 -> 2.0.3`: 4 nodes from `tests/test_cli.py`
- attrs `21.3.0 -> 21.4.0`: 0 upgrade-related nodes, so recall/F1 are N/A
- attrs `21.4.0 -> 22.1.0`: 28 nodes from `tests/test_functional.py`, `tests/test_make.py`, and
  `tests/test_validators.py`
- attrs `22.1.0 -> 22.2.0`: 167 nodes from `tests/test_abc.py`, `tests/test_dunders.py`,
  `tests/test_functional.py`, `tests/test_hooks.py`, `tests/test_make.py`, `tests/test_slots.py`,
  and `tests/test_validators.py`

Product implication:

- Blank AI Wiki scaffold mainly measures workflow overhead and isolation, not memory value.
- Treatment had slightly fewer repeated orientation commands in this rough count, but more total
  commands and elapsed time because each thread ran the AI Wiki gate and failed `aiwiki-toolkit route`
  before fallback reads.
- There was no positive evidence of previous-failure reuse because no useful memory was seeded and no
  failure record was written back between steps.
- The next A/B should either seed project-specific prior-step notes or implement harness-level
  failure-memory writeback between steps.
- For benchmark claims, do not treat AI Wiki custom metrics as outcome metrics. They are diagnostic
  only. The primary A/B judgment should use SWE-Chain's original test-based evidence: hidden
  pass/fail/error counts, resolved/unresolved/regressed/recovered/unrecovered classifications, and
  derived recall/precision/F1. Custom metrics can explain mechanism and isolation, but must not
  override the native benchmark result.

## 2026-06-10 Metrics-Standard Fresh Flask A/B

The user clarified that benchmark judgment must use SWE-Chain's native test-based metrics. A fresh
Flask-only A/B was run under
`/Users/by/AI Project/AI wiki Toolkit test repos/swe-chain-003-metrics-rerun`, with the report at
`REPORT.md`.

Setup:

- chain: Flask `2.0.0 -> 2.0.3`
- agent/model: Codex CLI, OpenAI `gpt-5.5`
- effort: `medium`
- `max_iters=1`
- treatment: blank AI Wiki scaffold injected only in harness setup
- valid treatment boundary: `/app/AGENTS.md=yes`, `/app/AGENT.md=no`, `/app/ai-wiki=yes`,
  `/app/code/ai-wiki=no`
- no host AI Wiki paths appeared in valid treatment logs

Native benchmark result:

- Baseline: hidden `1404/1420`, `TP=15`, `FN=11`, `FP=0`, recall `57.69%`, precision `100.00%`,
  F1 `73.17%`
- Treatment: hidden `1402/1420`, `TP=16`, `FN=10`, `FP=4`, recall `61.54%`, precision `80.00%`,
  F1 `69.57%`

Interpretation:

- Treatment resolved one more upgrade-related node and left one fewer unresolved node.
- Treatment introduced four regression false positives, so native precision and F1 are lower.
- By SWE-Chain's native benchmark result, baseline wins on F1 and regressions; treatment wins only
  on recall/resolved count.
- Treatment diagnostic metrics: rough orientation commands decreased `16 -> 14`, but command events
  increased `143 -> 160` because the AI Wiki gate adds reads and failed route attempts.
- There was still no evidence of previous-step failure reuse through AI Wiki because the injected
  wiki was blank and no failure memory was written between steps.

Clarification for future runs:

- `max_iters=1` means each chain transition gets only the initial build phase. It does not mean the
  chain has one transition. In `generate/task.py`, the fix loop only runs while
  `round < max_iters - 1`, so `1` disables post-hidden-test fix iterations.
- The fresh Flask A/B used a three-transition mini-chain because the first eval goal was a controlled
  reproducibility slice, not full leaderboard reproduction. The full SWE-Chain specs set has 12
  chain files and 155 transitions.
- Raw hidden pass/fail counts are not the same as TP/FP/FN classification counts. In the fresh Flask
  A/B, treatment's total hidden pass was two lower because step 1 passed `462/470` instead of
  baseline's `464/470`; steps 2 and 3 had equal raw pass counts. The four treatment FP nodes were
  step-classified regressions and included repeated `tests/test_blueprints.py::test_endpoint_decorator`
  failures across multiple transitions.
- The treatment FP failure evidence pointed to blueprint behavior: `@bp.endpoint("bar")` failed with
  `KeyError: 'bar'`, and nested blueprint error handling returned the parent handler where the
  grandchild handler was expected.

Layer analysis from the treatment logs:

- The current treatment primarily measured empty-workflow overhead, not memory value. The injected
  wiki had no Flask-specific notes and no prior-step failure memory.
- The router layer did not actually run inside the SWE-Chain container because `aiwiki-toolkit` was
  not installed. Codex attempted `aiwiki-toolkit route`, got command-not-found or no route output,
  then fell back to reading broad default indexes.
- The fallback read order touched label/category surfaces such as `conventions`, `decisions`,
  `constraints`, `review-patterns`, `problems`, `features`, `workflows`, and `trails`. These were
  mostly empty meta-docs, so they added context without actionable Flask guidance.
- The writeback layer also appeared in the agent task: step 1 read reuse/update skill contracts, and
  step 2 attempted `record-reuse`/`record-reuse-check` commands even though the CLI was unavailable.
  This was unrelated to solving the Flask upgrade.
- The regression was not caused by AI Wiki scaffold paths entering the Flask diff. `chain.json`
  contained no `ai-wiki`, `AGENTS.md`, or `_toolkit` paths. The concrete FP cause was a Flask
  blueprint implementation choice: treatment prefixed `app.view_functions` entries with the blueprint
  name, breaking `@bp.endpoint("bar")`, and changed nested blueprint handler routing enough to return
  the parent error handler.
- Future A/Bs should separate three arms before making product claims: router-only compact context,
  router plus seeded project memory, and writeback enabled. In SWE-Chain, writeback is better handled
  by the harness between steps or after the run, not inside the coding agent's first-pass task.

## 2026-06-10 Route CLI Container Rerun Notes

The next rerun fixed the previous route fallback gap by copying a real `aiwiki-toolkit` binary into
the SWE-Chain Docker container. Direct source install was not viable for Flask images because they
use Python 3.9 while `ai-wiki-toolkit` requires Python 3.11+. A Linux standalone binary was built
from local source instead.

Important packaging details:

- the first Linux build was `linux-x64`, but the Flask SWE-Chain images were arm64, so the binary
  failed in-container
- rebuilding with `--docker-platform linux/arm64 --target linux-arm64` produced a working binary
- the working binary reported `ai-wiki-toolkit 0.1.39` inside `swe-chain:flask-2.0.0`
- the treatment harness copied the binary to `/usr/local/bin/aiwiki-toolkit`
- the harness also copied the seeded repo's `.git` directory to `/app/.git`, because `route` needs a
  repository root
- `chmod` and version checks must run with `workdir="/"` because `/app/code` may not exist yet or
  may be removed during setup

Result folder:

- `/Users/by/AI Project/AI wiki Toolkit test repos/swe-chain-004-route-cli`

Route behavior:

- `aiwiki-toolkit route` succeeded in all three Flask steps
- all three steps were classified as `release_distribution`, which is too broad for SWE-Chain
  code-upgrade tasks
- because the full CLI was available, the agent also ran `record-reuse` and `record-reuse-check`
  inside the benchmark task
- this run should therefore be labeled `router + writeback enabled`, not `router-only`

Native benchmark result for Flask `2.0.0 -> 2.0.3`:

- baseline003: hidden `1404/1420`, `TP=15`, `FN=11`, `FP=0`, recall `57.69%`, precision
  `100.00%`, F1 `73.17%`
- blank treatment003: hidden `1402/1420`, `TP=16`, `FN=10`, `FP=4`, recall `61.54%`, precision
  `80.00%`, F1 `69.57%`
- routecli004: hidden `1395/1420`, `TP=15`, `FN=11`, `FP=7`, recall `57.69%`, precision
  `68.18%`, F1 `62.50%`

Interpretation:

- copying the real toolkit into Docker fixed route execution but did not improve SWE-Chain native
  outcome
- routecli004 matched baseline recall but introduced seven regression false positives
- the result is evidence that route availability alone is insufficient when the route is too broad,
  the wiki is blank of package-specific memory, and writeback overhead runs inside the coding task
- the next clean experiment should isolate `router-only compact packet`, `router + seeded Flask
  memory`, and `router + seeded memory + harness-level writeback`

## 2026-06-10 No Default Label Rerun Notes

The next rerun followed the user decision to remove, not downgrade, repo/domain-specific default
labels such as `release_distribution`, `scaffold_prompt_workflow`, and `eval_workflow`.

Code change for the experiment:

- removed active route task-type keyword entries for release/scaffold/eval workflow labels
- disabled default domain tags, fixed workflow contracts, default intent buckets, eligible doc slots,
  and the `public_metrics` plan/question mode default
- built a temporary Linux arm64 benchmark binary from local source at
  `/Users/by/AI Project/ai-wiki-toolkit/build/linux-route-nolabel-dist/aiwiki-toolkit`

Route smoke for Flask upgrade, release, and impact-eval prompts produced `task_type=general`,
`domain_tags=[]`, `workflow_contract=None`, and `intent_buckets=[]`.

Result folder:

- `/Users/by/AI Project/AI wiki Toolkit test repos/swe-chain-005-no-default-labels`

SWE-Chain behavior:

- `aiwiki-toolkit route` succeeded in all three Flask steps
- all three route packets were `task_type=general` with no domain tags, no intent buckets, and no
  workflow contract
- route still selected only empty scaffold docs: `constraints`, `decisions`, and `workflows`
- no previous-step Flask failure memory was selected by the next step

Native Flask `2.0.0 -> 2.0.3` result:

- baseline003: hidden `1404/1420`, `TP=15`, `FN=11`, `FP=0`, recall `57.69%`, precision
  `100.00%`, F1 `73.17%`
- blank treatment003: hidden `1402/1420`, `TP=16`, `FN=10`, `FP=4`, recall `61.54%`, precision
  `80.00%`, F1 `69.57%`
- routecli004: hidden `1395/1420`, `TP=15`, `FN=11`, `FP=7`, recall `57.69%`, precision
  `68.18%`, F1 `62.50%`
- nolabel005: hidden `1396/1420`, `TP=11`, `FN=15`, `FP=2`, recall `42.31%`, precision
  `84.62%`, F1 `56.41%`

Interpretation:

- removing default labels fixed the over-classification problem, but it did not improve the native
  SWE-Chain outcome
- nolabel005 performed worse than baseline because it still had no useful Flask-specific memory and
  still ran writeback/reuse overhead inside the coding task
- this should not be treated as evidence against memory; it is evidence that empty scaffold plus
  cleaner routing is insufficient
- formalizing the no-default-label change requires migrating/deleting old route tests; current
  `uv run pytest tests/test_route.py` fails 15 old label/workflow assertions after the experiment

## 2026-06-10 Post-Hoc Memory Tuning Notes

This run must not be treated as clean A/B benchmark evidence. The 009 treatment used failure
evidence from the previous 008 run on the same Flask mini-chain to manually tighten the seeded
memory. That is useful for debugging the memory mechanism, but it leaks target benchmark feedback
into the next attempt.

Correct interpretation:

- valid as a closed-loop engineering diagnosis of which memory statements helped or hurt
- invalid as evidence that AI Wiki improves an unseen SWE-Chain task
- invalid as satisfying acceptance for a clean baseline-versus-treatment benchmark
- useful as dev-set input for designing a frozen setup to test on a held-out chain

Setup:

- result folder:
  `/Users/by/AI Project/AI wiki Toolkit test repos/swe-chain-009-json-cli-tight-memory`
- chain: Flask `2.0.0 -> 2.0.3`
- agent/model: Codex CLI, OpenAI `gpt-5.5`
- effort: `medium`
- `max_iters=1`
- treatment: AI Wiki injected at `/app`, current-version Flask memory activated one step at a time,
  `aiwiki-toolkit` binary available in Docker, and harness-level memory written between steps
- benchmark boundary: memory files were outside `/app/code`, so package diffs stayed Flask-only

Native result versus the stable baseline003, reported only as post-hoc diagnostic evidence:

- baseline003: hidden `1404/1420`, `TP=15`, `FN=11`, `FP=0`, recall `57.69%`, precision `100.00%`,
  F1 `73.17%`
- treatment009: hidden `1406/1420`, `TP=16`, `FN=10`, `FP=1`, recall `61.54%`, precision `94.12%`,
  F1 `74.42%`
- step 1 matched baseline: hidden `464/470`, F1 `62.5%`, precision `100%`
- step 2 improved recall but introduced one regression: hidden `469/475`, `TP=7`, `FN=4`, `FP=1`,
  F1 `73.68%`
- step 3 matched the best baseline behavior and fixed the earlier CLI miss: hidden `473/475`,
  `TP=4`, `FN=0`, `FP=0`, F1 `100%`

What leaked from the failing run into the tuned run:

- 008 added targeted CLI memory, and the agent did modify `cli.py`, but the first version still used
  `module_name.rpartition(".")[2]` for `"notanapp.py"`, producing `"py"` instead of `"notanapp"`.
  `test_locate_app_suppress_raise` stayed unresolved.
- 008 also told the agent that JSON dumps/loads should not force default classes. The agent
  interpreted this as falling back to Python's stdlib `json.JSONEncoder`, causing seven JSON false
  positives: dataclass, `__html__`, Decimal, datetime/date, UUID, and `tojson`.
- 009 tightened the memory: use `Path(module_name).stem` or the `.py` suffix-stripped name for
  missing target modules, and keep Flask's `JSONEncoder` as the default because it is behavioral,
  not a no-op customization.
- 009 required focused checks for `notanapp.py`, `wsgi.py` fallback, true internal import errors,
  CLI help/unknown-command display, Decimal, datetime/date, UUID, dataclasses, `__html__`, and
  `tojson`.

Correct next benchmark design:

- 008 and 009 should be treated as dev-set tuning artifacts only.
- Freeze the AI Wiki setup before the next scored run.
- Allowed setup changes: layer/component changes such as router-only versus seeded memory versus
  harness-level writeback, removing in-task writeback overhead, reducing scanned docs, changing
  prompt wiring, or changing how memory is selected.
- Disallowed setup changes: manually copying failure nodes, error messages, or implementation hints
  from an earlier run on the same target chain into memory for a later scored run.
- Test the frozen setup on a held-out chain or held-out transitions, such as attrs or later Flask
  transitions not used to write the memory.
- During the held-out chain, harness-level writeback may only use failures produced earlier in the
  same chain if that behavior is part of the frozen treatment and is also reported as such.

Design implication from the post-hoc run:

- Good benchmark memory should be sparse, version-scoped, and behaviorally negative where needed:
  name the exact over-broad interpretation that caused a regression.
- Harness-level writeback is useful when it records compact failure surfaces and the next step is
  told to reuse only surfaces present in the current spec or current version memory.
- Do not let route scan all stale version docs. The treatment harness removed non-current Flask
  memory docs before each step because `route` currently scans Markdown broadly.
- For SWE-Chain, in-task writeback/reuse metrics are overhead. Write failure memory in the harness
  between steps, then let the next coding turn read it as ordinary project memory.
- A single positive post-hoc mini-chain does not satisfy clean benchmark acceptance. It only proves
  that the agent can use hand-refined memory to avoid a previously observed failure.

## 2026-06-10 Clean Component Setup Result

Result folder:

- `/Users/by/AI Project/AI wiki Toolkit test repos/swe-chain-010-clean-component-setup`

This run is valid clean A/B evidence for an AI Wiki component setup, but not yet causal evidence for
writeback memory. It deliberately disabled seeded Flask memory, in-task writeback, harness hidden
failure writeback, and any target-specific notes from 008/009.

Treatment setup:

- Layer 1: clean `/app/ai-wiki`, `/app/AGENTS.md`, and managed
  `/app/ai-wiki/_toolkit/system.md`
- Layer 2: container-installed `aiwiki-toolkit 0.1.39`; normal `route` per step
- Layer 3: telemetry via live logs/eval only; no writeback memory between steps
- agent/model: Codex CLI, OpenAI `gpt-5.5`
- effort: `high`
- `max_iters=2`

Cleanliness evidence:

- the 010 treatment harness has `FLASK_VERSION_MEMORY_DOCS = {}`
- enabling `SWE_CHAIN_AIWIKI_SEED_FLASK_MEMORY` in a clean component run raises an error
- all three route packets classified the task as `general`, `code` mode
- all three route packets selected only placeholder guardrail docs:
  `constraints`, `decisions`, `workflows`
- no `Activated AI Wiki Flask memory` event appeared
- no manually copied 008/009 failure nodes, error messages, or implementation hints were available
  to the agent

Native Flask `2.0.0 -> 2.0.3` result versus stable baseline003:

- baseline003: hidden `1404/1420`, `TP=15`, `FN=11`, `FP=0`, recall `57.69%`, precision
  `100.00%`, F1 `73.17%`
- clean010 treatment: hidden `1409/1420`, `TP=17`, `FN=9`, `FP=0`, recall `65.38%`, precision
  `100.00%`, F1 `79.07%`

Per-step treatment:

- `2.0.0 -> 2.0.1`: hidden `465/470`, `TP=6`, `FN=5`, `FP=0`, F1 `70.59%`
- `2.0.1 -> 2.0.2`: hidden `470/475`, `TP=7`, `FN=4`, `FP=0`, F1 `77.78%`
- `2.0.2 -> 2.0.3`: hidden `474/475`, `TP=4`, `FN=0`, `FP=0`, F1 `100.00%`

Interpretation:

- clean010 beats baseline003 on hidden pass, recall, and F1 without introducing false positives
- the win may come from cleaner workflow framing, stochastic run variance, or the agent's own
  local validation choices; it should not be claimed as proof that writeback memory helped
- the next stricter experiment should enable automatic, non-hidden, chain-internal writeback only
  if the writeback is part of the frozen setup and does not include hidden evaluator node names,
  hidden failure messages, or implementation hints copied from prior scored runs

## 2026-06-10 Init-Only AGENTS.md Ablation

Result folder:

- `/Users/by/AI Project/AI wiki Toolkit test repos/swe-chain-011-init-agents-only`

This run isolates Codex `/init` style prompt framing from AI Wiki behavior. The treatment injected
only a frozen, generic Flask `AGENTS.md` at `/app/AGENTS.md`. It did not inject `ai-wiki/`,
`.agents/`, toolkit CLI, route packets, seeded memory, writeback memory, or hidden failure logs.

Setup:

- chain: Flask `2.0.0 -> 2.0.3`
- agent/model: Codex CLI, OpenAI `gpt-5.5`
- effort: `high`
- `max_iters=2`
- treatment env: `SWE_CHAIN_INIT_AGENTS_ONLY=1` with all `SWE_CHAIN_AIWIKI_*` vars unset
- frozen fixture: `fixtures/init-agents/AGENTS.md`

Native result versus stable baseline003 and clean010:

- baseline003: hidden `1404/1420`, `TP=15`, `FN=11`, `FP=0`, recall `57.69%`, precision
  `100.00%`, F1 `73.17%`
- clean010 treatment: hidden `1409/1420`, `TP=17`, `FN=9`, `FP=0`, recall `65.38%`, precision
  `100.00%`, F1 `79.07%`
- init011 AGENTS-only treatment: hidden `1406/1420`, `TP=17`, `FN=9`, `FP=1`, recall `65.38%`,
  precision `94.44%`, F1 `77.27%`

Step-level init011 result:

- `2.0.0 -> 2.0.1`: hidden `464/470`, `TP=6`, `FN=5`, `FP=1`, F1 `66.67%`
- `2.0.1 -> 2.0.2`: hidden `469/475`, `TP=7`, `FN=4`, `FP=0`, F1 `77.78%`
- `2.0.2 -> 2.0.3`: hidden `473/475`, `TP=4`, `FN=0`, `FP=0`, F1 `100.00%`

Important test-level finding:

- init011 and clean010 resolved the same upgrade-related nodes. In particular, they both fixed the
  nested blueprint URL-prefix tests in step 1 and `test_nested_callback_order` in step 2.
- init011 introduced one false positive:
  `tests/test_blueprints.py::test_endpoint_decorator`.
- That false positive stayed unrecovered through steps 2 and 3.
- clean010 did not introduce this regression, which explains its higher hidden pass and F1.

Interpretation:

- Plain `AGENTS.md` prompt framing already explains most of the clean010 improvement over
  baseline003. Clean010 should not be claimed as proof of AI Wiki memory value.
- Future AI Wiki experiments should compare against both the original SWE-Chain baseline and this
  init-only baseline. Beating baseline003 alone is insufficient if the treatment does not beat
  init011.
- To test memory causality, keep `AGENTS.md` constant across init-only and AI Wiki treatment, then
  add one AI Wiki component at a time.

## 2026-06-10 Init AGENTS + Public Writeback, No Router

Result folder:

- `/Users/by/AI Project/AI wiki Toolkit test repos/swe-chain-012-init-public-writeback-no-router`

This run tested Bocheng's proposed narrower memory question: keep Codex `/init` style
`AGENTS.md` as the common base for every step, remove the router layer, write public memory after
each step, and make later steps read all memory files.

Setup:

- chain: Flask `2.0.0 -> 2.0.3`
- agent/model: Codex CLI, OpenAI `gpt-5.5`
- effort: `high`
- `max_iters=2`
- frozen fixture: `fixtures/init-agents/AGENTS.md`
- treatment env: `SWE_CHAIN_INIT_AGENTS_ONLY=1` and
  `SWE_CHAIN_PUBLIC_MEMORY_WRITEBACK=1`, with all `SWE_CHAIN_AIWIKI_*` vars unset
- no `aiwiki-toolkit`, no route packet, no `_toolkit/system.md`

Memory behavior:

- step 1 started with an empty `/app/ai-wiki/memory` directory and wrote one public memory file
- step 2 read `index.md` and the step 1 memory file before editing
- step 3 read `index.md` plus both earlier memory files before editing
- the public memory was generated from agent trajectory and code diff metadata, not hidden
  evaluator failures

Native result versus baseline003 and init011:

- baseline003: hidden `1404/1420`, `TP=15`, `FN=11`, `FP=0`, recall `57.69%`, precision
  `100.00%`, F1 `73.17%`
- init011 AGENTS-only treatment: hidden `1406/1420`, `TP=17`, `FN=9`, `FP=1`, recall `65.38%`,
  precision `94.44%`, F1 `77.27%`
- init+public-writeback012 treatment: hidden `1406/1420`, `TP=17`, `FN=9`, `FP=1`, recall
  `65.38%`, precision `94.44%`, F1 `77.27%`

Step-level 012 result:

- `2.0.0 -> 2.0.1`: hidden `464/470`, `TP=6`, `FN=5`, `FP=1`, F1 `66.67%`
- `2.0.1 -> 2.0.2`: hidden `469/475`, `TP=7`, `FN=4`, `FP=0`, F1 `77.78%`
- `2.0.2 -> 2.0.3`: hidden `473/475`, `TP=4`, `FN=0`, `FP=0`, F1 `100.00%`

Auxiliary metrics:

- chain survival: `3/3` for both init011 and public-writeback012
- command events increased from 148 in init011 to 174 in public-writeback012
- search commands increased from 35 to 41
- file-read commands increased from 89 to 115
- memory commands in public-writeback012: 8

Interpretation:

- Public writeback memory was definitely read in steps 2 and 3.
- Public writeback memory did not improve native SWE-Chain metrics over the init-only control.
- It also did not reduce repeated exploration on this run; it added read overhead.
- The result still beats baseline003, but that gain is already explained by the `AGENTS.md`
  init-only ablation, so this run is not memory-causality evidence.

## 2026-06-10 Step Relatedness Audit For Flask 012

Bocheng pointed out a missing condition for memory evals: previous-step memory only has a fair
chance to help if the next step is related to the previous step. If steps are independent, a neutral
memory result is not very informative.

A lightweight audit of Flask 012 found real but uneven relatedness:

- `2.0.0->2.0.1` to `2.0.1->2.0.2`:
  - spec tag Jaccard: `0.75`
  - agent core file Jaccard: `0.36`
  - upgrade test-file Jaccard: `0.50`
  - upgrade node Jaccard: `0.29`
  - problem carryover: blueprint and CLI
- `2.0.1->2.0.2` to `2.0.2->2.0.3`:
  - spec tag Jaccard: `0.56`
  - agent core file Jaccard: `0.36`
  - upgrade test-file Jaccard: `0.25`
  - upgrade node Jaccard: `0.36`
  - problem carryover: blueprint

Specific carryover:

- Four CLI nodes were FN in step 1, remained FN in step 2, then became TP in step 3:
  `test_help_echo_loading_error`, `test_locate_app_suppress_raise`,
  `test_no_command_echo_loading_error`, and `test_scriptinfo`.
- One blueprint FP from step 1, `test_endpoint_decorator`, remained unrecovered through step 3.
- `test_unique_blueprint_names` was FN in step 1 and remained unrecovered through steps 2 and 3.

Interpretation:

- Flask 012 is not an invalid memory test due to unrelated steps; there is enough cross-step
  continuity for memory to matter.
- The negative result more likely means the public writeback was too coarse. It captured changed
  files, final summaries, and local command outcomes, but not a compact, actionable
  next-step troubleshooting packet.
- The next memory treatment should preserve the init-only control and change the memory payload:
  write public non-hidden failure surfaces, unresolved local probes, agent-stated uncertainties,
  repeated touched modules, and regression-risk notes. It must still exclude hidden evaluator node
  names and hidden failure messages.

## Reuse Assessment

Use this when continuing SWE-Chain experiments, designing AI Wiki impact evals, or packaging replay
evals as a user-run product surface.
