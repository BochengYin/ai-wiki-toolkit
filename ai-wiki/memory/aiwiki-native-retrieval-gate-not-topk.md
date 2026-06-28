# AI Wiki Native Retrieval Gate, Not Top-K

## Trigger

Read when designing, evaluating, or modifying AI Wiki Native Writeback,
pre-edit memory retrieval, or any follow-up experiment that tries to reduce
false positives from accumulated `ai-wiki/memory/` notes.

## Public/Local Signal

On 2026-06-25, a local audit of
`swe-chain-019-aiwiki-native-writeback-panel-v1` showed that native writeback's
high-FP runs were not solved by simply allowing more memory reads. In pytest 7,
the memory index grew from 1 to 20 entries across the chain, while final-holdout
precision stayed poor in several later steps. The worst pytest 7.3.0 step read
the index but no implementation memory, then later reported a missed
source-tree plugin-autoload memory. A lexical retrospective over that step's
index ranked several adjacent older compatibility notes near the top, showing
that unrestricted top-k would still include noisy adjacent memories.

Conan 2.12 showed a similar pattern: adjacent compatibility memories often
ranked plausibly but did not reliably prevent low-F1 steps. urllib3 was the
counterexample: tightly scoped HTTP/proxy/gzip memories were easier to retrieve
and often helped.

## Failed Attempt

Treating native false positives as a "read only one memory" problem is too
simple. Increasing the memory count without a stricter gate can amplify
retrieval drift, because adjacent version repairs and broad compatibility notes
look relevant by lexical overlap but can push the agent toward overbroad API
changes.

## Fix Or Rule

Default packaged hook behavior should keep `Stop` as the write-back/compliance
gate and should not automatically inject pre-edit memory. If native pre-edit
retrieval is enabled, add a retrieval gate that:

- can abstain when no memory strongly matches the current spec, files, API, or
  public/local failure surface;
- stays thin: it only decides whether any memory is safe to expose, and must
  not become a router that plans the implementation path for the agent;
- separates implementation memories from verification-environment memories;
- treats transient verification-environment notes as non-implementation by
  default. A note such as local pytest plugin autoload pollution should not be
  promoted as ordinary repo implementation memory; if retained at all, it
  should be scoped to local check/test invocation and exposed only as
  verification-only guidance when the same public/local failure surface
  recurs;
- returns a short ranked decision with reasons and conflicts, not raw broad
  memory dumps;
- treats "FP-heavy step" as an experiment-evaluator label, not live product
  input. Do not use hidden/future holdout outcomes to decide whether a memory is
  exposed inside the same run. Live quarantine can only use public/local signals
  such as user correction, explicit conflict, failed local checks, or rejected
  memory reuse;
- treats top-k as candidate generation, not permission to use every candidate.

## Concrete Gate V0

Use a conservative, evidence-first gate. The gate should not plan the
implementation. It only decides whether a memory is safe to expose and what the
memory is allowed to influence.

Inputs allowed before editing:

- the current task/spec text;
- cheap public repo anchors such as file paths, module names, public APIs, and
  command/error strings;
- `ai-wiki/memory/index.md` and candidate memory summaries/content;
- public/local command output from the current run, when available.

Inputs not allowed:

- hidden evaluator failures, hidden test names, holdout labels, or future
  outcomes from later steps;
- prior "FP-heavy" labels as live routing signals inside a run.

Candidate generation may be high recall, but internal only. It may collect up
to about 20 plausible memories by lexical/API/file/failure matching. These
candidates are not exposed to the implementation agent.

Implementation memories pass only when at least two hard anchors match the
current task, such as exact file/module, public API/class/function, spec
behavior, or same public/local failure signature. Generic compatibility notes,
adjacent-version repairs, or broad thematic matches should abstain.

Verification-environment memories pass only as check/test guidance, never as
implementation guidance, and only when the same local/public command or failure
surface recurs.

The gate output should be small: `no memory`, or at most 0-3 memories with
`allowed_use`, reasons, limits, and conflicts. Low confidence, conflicting
evidence, category mismatch, or missing hard anchors all return `no memory`.

## Paper-Inspired Gate V1

Use the paper pattern rather than a hand-tuned top-k rule:

1. Treat memory exposure as selective intervention. Following selective
   classification, the gate trades coverage for lower risk: it may abstain, and
   should be evaluated by risk among exposed memories, not by how many memories
   it finds.
2. Define a risk function before running the experiment. For AI Wiki, the
   primary risk is intervention harm: exposed memory causes or plausibly
   encourages extra false positives, overbroad edits, or code changes outside
   the current spec. Secondary risk is wrong-use: verification/workflow memory
   being used as implementation guidance.
3. Keep live gating and offline evaluation separate. Actual FP delta and
   post-run intervention harm are evaluation/calibration labels only; they are
   not live gate inputs. During a live step, the gate may only use pre-edit
   observable proxy signals such as relevance support, contradiction, scope
   overreach risk, snippet breadth, and allowed-use mismatch.
4. Calibrate the threshold on prior completed runs or a held-out calibration
   slice, not on future steps in the same run. Use a conformal/Neyman-Pearson
   style objective: maximize FN reduction subject to intervention harm or
   FP-delta staying under a preset bound.
5. Use a CRAG/Self-RAG style evaluator before exposing memory. Each candidate
   is classified as `correct`, `incorrect`, or `ambiguous` for the current
   task. Only `correct` can pass. `ambiguous` abstains by default.
6. Decompose then recompose the memory before exposure. Do not expose a whole
   broad note when only one line is relevant. Return the smallest scoped
   snippet plus its allowed use and limits.
   In the CRAG paper, this is not a JSON router and not an
   implementation/workflow taxonomy. CRAG decomposes retrieved documents into
   knowledge strips, scores the strips with the retrieval evaluator, filters
   irrelevant strips, and recomposes the relevant strips in order. For AI Wiki,
   prefer this strip-scoring adaptation: decompose memory notes into small
   strips, score query-strip relevance, expose only high-confidence strips, and
   make `ambiguous` abstain by default in coding tasks. Any `allowed_use` or
   scope label is AI Wiki audit metadata and should not become a planning
   router shown to the implementation agent unless a concrete product need
   proves it is useful.

Candidate scoring should estimate:

- retrieval_need: whether the current task actually needs memory;
- relevance/support: whether the memory is directly supported by current
  files/APIs/spec/failure surface;
- contradiction: whether the memory conflicts with the current task;
- harm_risk: whether the memory could push edits outside the task scope;
- use_scope: implementation, verification-only, workflow-only, or abstain.
  This is an AI Wiki permission/scope label, not a taxonomy copied from the
  papers.

Decision rule:

- if retrieval_need is low, return `no_memory`;
- if candidate is `incorrect` or `ambiguous`, return `no_memory`;
- if calibrated harm_risk exceeds the threshold, return `no_memory`;
- otherwise expose the smallest scoped memory snippet, with explicit
  `allowed_use` and `do_not_use_for` limits.

Metrics:

- coverage: percent of tasks where the gate exposes any memory;
- selective precision: exposed memories that were used correctly;
- intervention harm: FP delta after exposure versus Stop-only baseline;
- FN gain: recovered failures versus Stop-only baseline;
- abstention quality: abstained cases where exposure would likely have been
  noisy or unsupported.

Implementation adaptation for AI Wiki:

- implement strip extraction and gate scoring in the toolkit package or
  experiment runner, not as ad hoc agent reasoning inside a Skill;
- skills may wrap or instruct use of the toolkit command, but should not own
  the retrieval algorithm. This keeps the experiment reproducible across
  agents and lets tests cover the gate;
- split memory markdown by headings and paragraph/bullet blocks into small
  strips with metadata such as doc id, heading, original order, and extracted
  anchors. Prefer exposing strips from actionable sections such as `Fix Or
  Rule`, `Applies When`, or `Do Not Use When`; avoid exposing provenance,
  related-file paths, metric labels, or broad retrospective context;
- do not show a JSON router to the implementation agent. Agent-facing output
  should be either `no memory` or a short plain-text block of relevant AI Wiki
  snippets. Any confidence scores, candidate lists, or scope labels should be
  logged as audit metadata only.

## Simpler Experiment Option: Prompt-Only Exact-Match Gate

For the next experiment, a simpler native-style prompt gate may be preferable
to a CRAG-style scoring pipeline. Inject a short AGENTS.md rule directly into
the repo instead of adding a toolkit retrieval command:

- inspect `ai-wiki/memory/index.md` only;
- open at most one memory file only when the index entry exactly matches the
  current task by file path/module, public API/class/function, command/error
  signature, or named workflow;
- treat adjacent versions, broad compatibility, same framework/package, or
  semantic similarity as non-matches;
- if no exact match exists, do not read or use memory;
- if a memory is opened, use only directly matching content and ignore
  provenance, metrics, related-file lists, and broad retrospective context.

This is less powerful than learned retrieval, but it is a cleaner ablation: it
tests whether strict prompt-level abstention can reduce native false positives
without introducing another router or scorer as a confounder.

## 021 Pytest 7 Exact-Match Outcome

The `swe-chain-021-aiwiki-exact-match-stop` pytest 7 run showed that prompt-only
exact match is still not enough to beat Stop-only hook behavior.

Compared with `swe-chain-020` Stop-only on `pytest_7.0.0_to_7.4.4`, the 021
exact-match + Stop run had the same build+fix recall but twice the build+fix
false positives:

- 021 build+fix: `tp=173`, `fn=53`, `fp=136`, `f1=0.6468`
- 020 Stop-only build+fix: `tp=173`, `fn=53`, `fp=68`, `f1=0.7409`

Final holdout showed the same pattern: 021 recovered slightly more true
positives but added many more false positives:

- 021 final holdout: `tp=67`, `fn=30`, `fp=98`, `f1=0.5115`
- 020 Stop-only final holdout: `tp=62`, `fn=35`, `fp=43`, `f1=0.6139`

The regression was concentrated rather than uniform. The biggest case was
`7.3.0 -> 7.3.1` fix, where 021 opened
`pytest-731-unittest-tmp-path-hidden-traceback.md`; that phase had `fp=72`
versus Stop-only `fp=8`, and final-holdout false positives rose by 34. The
memory was exact by version and named surfaces, but the resulting repair still
expanded across broad adjacent compatibility areas. Treat this as evidence that
an index-title exact match can still be too broad; future gates need strip-level
scope or stronger abstention, not just "one exact memory file".

## Applies When

- Evaluating 019 native writeback results.
- Designing a native or hook-based pre-edit retrieval mechanism.
- Deciding whether to allow more than one memory file per task.
- Investigating false positives caused by accumulated local memory.

## Do Not Use When

- The task is only about end-of-task write-back footer compliance.
- The user asks for Stop-only hook behavior unrelated to retrieval.
- The repo lacks an AI Wiki memory index or the task has no memory relevance.

## Related Files

- `artifacts://swe-chain-019/groups/aiwiki-native-writeback/results/pytest_7.0.0_to_7.4.4/codex-openai-gpt-5.5/chain.json`
- `artifacts://swe-chain-019/groups/aiwiki-native-writeback/results/pytest_7.0.0_to_7.4.4/codex-openai-gpt-5.5/eval.json`
- `artifacts://swe-chain-019/groups/aiwiki-native-writeback/results/conan_2.12.0_to_2.20.1/codex-openai-gpt-5.5/eval.json`
- `artifacts://swe-chain-019/groups/aiwiki-native-writeback/results/urllib3_2.0.7_to_2.6.3/codex-openai-gpt-5.5/eval.json`

## Source Pointer

- Source: Local retrospective analysis in Codex while discussing native
  writeback false positives with the user.
- Captured by: Codex.
- Captured at: 2026-06-25.
