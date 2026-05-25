# ai-wiki-toolkit

**Agents keep repeating the same trial-and-error loops — across tasks, across developers, and across agents.**

What they need is not more prompts.  
They need a **memory harness**.

`ai-wiki-toolkit` is a **repository-native agent memory harness** for coding workflows.

It provides a persistent, structured memory layer inside the repo,  
along with a workflow that lets agents continuously write back what they learn.

It is inspired by Andrej Karpathy's LLM Wiki idea: a persistent Markdown knowledge base that an agent can keep organized over time instead of rediscovering from scratch on every task.

Reference inspiration:

- Karpathy's X post: https://x.com/karpathy/status/2039805659525644595
- Karpathy's gist: https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f

## The Problem

Teams doing vibe coding usually hit the same problems:

- durable project knowledge ends up scattered across chats, review comments, and individual memory
- agents have to relearn repo conventions, past mistakes, and operating rules over and over
- raw file uploads or ad hoc RAG help answer one question, but they do not leave behind a maintained project memory
- shared instruction files are easy to drift or overwrite when multiple people and multiple agents touch them

The result is that useful knowledge exists, but it does not compound.

## The Flywheel

The point of an AI wiki is not just to answer one more question today. It is to create a compounding loop where each completed task can leave behind better repo context for the next one.

As you accumulate more constraints, workflows, decisions, review patterns, and draft notes, the agent starts each task with a better prior. Over time it becomes more familiar with your repository, your development habits, and the kinds of mistakes you want to avoid. That usually means less re-explaining, fewer repeated errors, and noticeably faster execution.

## What This Tool Does

`ai-wiki-toolkit` applies a harness engineering approach to agent work: make the repo memory, prompt wiring, and reusable workflow checks explicit enough that agents can reliably follow them without rediscovering them from scratch.

Instead of trying to solve the problem with a server, embeddings, or hidden state, it turns the harness itself into repo-visible artifacts:

- repo-local AI wiki files
- home-level cross-project AI wiki files
- managed prompt blocks
- repo-local Codex skills for repeatable end-of-task reuse and write-back checks

That gives the repo and the user a stable Markdown place to accumulate knowledge without turning the package into a knowledge platform.

For small teams, the AI wiki is also a shared coding-memory layer.

It helps agents reuse:

- team conventions
- PR review learnings
- feature clarifications
- durable decisions
- past debugging solutions
- personal draft observations that may later be promoted

It creates two isolated namespaces:

- `repo/ai-wiki/` for project-specific AI wiki files
- `~/ai-wiki/system/` for reusable cross-project AI wiki files

It also adds a managed instruction block to your agent prompt file so the agent knows where to read from and where to write back durable notes.

## How It Fits Coding Agents

`ai-wiki-toolkit` is not meant to be a standalone end-user app by itself.

It is a scaffold layer for coding-agent workflows. The point is to give tools like Claude Code, Codex, and similar repo agents a stable place to read project memory from and a stable place to write durable lessons back to.

In practice, the toolkit becomes useful when an agent is already working inside a git repository and needs shared instructions plus persistent repo memory.

That is why the installer manages both wiki files and prompt wiring together:

- `ai-wiki/` and `~/ai-wiki/system/` hold the durable Markdown memory
- `AGENT.md`, `AGENTS.md`, or `CLAUDE.md` tell the agent to read that memory and follow the workflow
- `aiwiki-toolkit route` generates a task-aware context packet so the agent can load the most relevant memory before falling back to the broader read order
- `.agents/skills/ai-wiki-reuse-check/` and `.agents/skills/ai-wiki-update-check/` provide repeatable end-of-task checks for Codex-style agent runs
- `.agents/skills/ai-wiki-clarify-before-code/` and `.agents/skills/ai-wiki-capture-review-learning/` help agents clarify ambiguous requests and preserve reusable review feedback

Some runtimes can discover repo-local `.agents/skills/` files on disk but still not expose those
skills to the active model session. The managed `ai-wiki/_toolkit/system.md` includes fallback
paths so agents can manually read the relevant `SKILL.md` and `references/` files when runtime skill
exposure is missing.

The toolkit does not replace coding agents. It gives them a shared repo-local memory layer so they can avoid repeating the same review issues, misunderstanding the same requirements, or rediscovering the same fixes.

## Task-Aware Context Routing

The managed prompt block asks agents to run `aiwiki-toolkit route --task "<current user request>"`
at the start of a task when the command is available.

Users do not need to run this manually during normal agent use. The agent supplies the current task
text because the CLI cannot see the private chat request on its own.

The command emits a transient AI Wiki Context Packet with:

- a coarse task type and risk tags
- an effort level so simple operational tasks can stay lightweight
- generated success criteria and verification checks so non-trivial tasks start with a clear finish line
- index cards with short descriptions and reference links for relevant memory
- `must_load` docs to consult first when direct context is required
- source-cited `must_follow` rules extracted from authoritative user-owned docs
- exploratory `context_notes` from drafts or other non-authoritative docs
- lower-confidence `maybe_load` docs and explicit skip reasons

Markdown remains the source of truth. A context packet is a generated, auditable working set for the
current task, not canonical memory. Agents should record reuse only for user-owned docs they actually
consult or materially use. Packet word limits are safety caps, not fill targets; agents should open
linked reference files at runtime when an index card is relevant and the task needs more detail.

## Prompt File Integration

Many coding-agent setups already create one of these repo-shared prompt files:

- `CLAUDE.md` for Claude Code style workflows
- `AGENTS.md` or `AGENT.md` for Codex or other agent bootstraps

`ai-wiki-toolkit` does not expect you to choose all of them manually.

When you run `aiwiki-toolkit install`, it looks for supported prompt files in the repository root and updates whichever ones already exist. It only manages the `aiwiki-toolkit` block inside those files, so your surrounding user-written instructions stay in place.

If none of those files exist yet, the toolkit creates `AGENT.md` as a generic default so the repo still has one stable prompt entrypoint.

## Why The Files Look Like This

The AI wiki structure is deliberately inspired by how `SKILL.md` files work well: keep a small stable entrypoint, then fan out into focused references.

Each wiki namespace starts with an `index.md` and then links to narrower files such as `constraints.md`, `conventions/`, `workflows.md`, `decisions.md`, `review-patterns/`, `problems/`, `features/`, `trails/`, `work/`, and personal `drafts/`. The package-managed start-of-task routing lives in `ai-wiki/_toolkit/system.md`, while repo-owned indexes stay stable maps that humans can customize without turning them into package upgrade surfaces.

## Current Scope

The current scope is intentionally strict about compatibility:

- initialize the repo and home AI wiki folders
- create starter Markdown files only if they do not already exist
- create managed `_toolkit/` files that package updates are allowed to refresh
- create `conventions/`, `review-patterns/`, `problems/`, `features/`, `work/`, and `people/<handle>/drafts/` scaffolding
- create or refresh package-owned repo-local `.agents/skills/ai-wiki-reuse-check/`, `.agents/skills/ai-wiki-update-check/`, `.agents/skills/ai-wiki-clarify-before-code/`, `.agents/skills/ai-wiki-capture-review-learning/`, and `.agents/skills/ai-wiki-consolidate-drafts/` skills
- create a managed `_toolkit/schema/team-memory-v1.md` guide for lightweight team coding memory
- create a managed `_toolkit/schema/work-v1.md` guide and local generated work views for repo-native todo/epic lifecycle state
- update managed instruction blocks inside `AGENT.md`, `AGENTS.md`, and `CLAUDE.md`
- avoid rewriting existing user-owned `ai-wiki/**/*.md` documents outside `_toolkit/`

## Install

For end users, the simplest install paths are Homebrew on macOS/Linux and npm on macOS/Linux/Windows. The npm distribution now splits supported Linux targets by `glibc` versus `musl` where needed, so the installed platform package can match the published release asset family.

### Homebrew

1. Install the command:

```bash
brew tap BochengYin/tap
brew install aiwiki-toolkit
```

Or in one command:

```bash
brew install BochengYin/tap/aiwiki-toolkit
```

2. Enter the target git repository and initialize the wiki scaffolding:

```bash
cd /path/to/your/repo
aiwiki-toolkit install
```

### npm

1. Install the command:

```bash
npm install -g ai-wiki-toolkit
```

The Homebrew formula and npm distribution both consume the same versioned GitHub Release assets.

The npm package is a thin meta package that installs the matching platform-specific binary package for the current machine. It does not fetch release assets during `postinstall`.

Enterprise/security notes for npm installs:

- the root npm package does not define `preinstall`, `install`, `postinstall`, `prepare`, or other lifecycle scripts
- the platform binary packages are installed through normal npm package resolution instead of an install-time downloader
- `npm install -g ai-wiki-toolkit --ignore-scripts` is compatible with the package topology because install scripts are not required
- global installation adds the `aiwiki-toolkit` command, but repo files are modified only when a user explicitly runs `aiwiki-toolkit install` inside a git repository

2. Enter the target git repository and initialize the wiki scaffolding:

```bash
cd /path/to/your/repo
aiwiki-toolkit install
```

### Local development

1. Install the command from this repository checkout:

```bash
pip install -e .
```

This remains the simplest contributor workflow inside the repository.

2. Enter the target git repository and initialize the wiki scaffolding:

```bash
cd /path/to/your/repo
aiwiki-toolkit install
```

## Recommendations

Recommended before running `install`:

- initialize the repository with git
- configure `git user.name` and `git user.email` so the toolkit can derive a stable handle
- if you already ran Claude Code, Codex, or another agent bootstrap and already have `AGENT.md`, `AGENTS.md`, or `CLAUDE.md`, the toolkit will update the managed `aiwiki-toolkit` block in that file instead of replacing the whole file

Claude Code / Codex init is not required. If no supported prompt file exists, `ai-wiki-toolkit` creates `AGENT.md` automatically.

## Update

For npm installs, use npm itself to update both the meta package and the matching platform binary:

```bash
npm update -g ai-wiki-toolkit
```

Or install the latest version explicitly:

```bash
npm install -g ai-wiki-toolkit@latest
```

`aiwiki-toolkit` does not implement a self-update command. The package manager remains the source of truth for install and upgrade state.

## Customizing Your AI Wiki

`ai-wiki-toolkit` ships a starter structure, not a locked schema.

- Files under `ai-wiki/_toolkit/**` and `~/ai-wiki/system/_toolkit/**` are package-managed.
- Files such as `ai-wiki/index.md`, `ai-wiki/workflows.md`, and other docs you add under `ai-wiki/` are user-owned.
- Starter files such as `ai-wiki/constraints.md` and `ai-wiki/decisions.md` may look mostly empty
  after install. That is intentional: they are placeholders for rules and decisions your team has
  actually made, not generic package defaults.
- `ai-wiki/_toolkit/system.md` is the managed entrypoint for package-managed repo guidance and evolving read order.
- `ai-wiki/_toolkit/system.md` also includes runtime skill fallback guidance for agents whose active session does not expose repo-local `.agents/skills/`.
- `ai-wiki/index.md` is a repo-owned map, not a package upgrade surface.
- `ai-wiki/_toolkit/workflows.md` carries the managed baseline workflows that package upgrades can refresh.
- Agents should extend user-owned workflow docs instead of editing `_toolkit/**`.

After upgrading the package, refresh the managed layer and then check for missing starter docs, stale managed prompt blocks, or rule drift:

```bash
aiwiki-toolkit install
aiwiki-toolkit doctor --strict
```

If `doctor` reports missing starter pointers, print the latest suggested starter content with:

```bash
aiwiki-toolkit doctor --suggest-index-upgrade
```

## Usage

Run inside a git repository:

```bash
aiwiki-toolkit install
```

Override the detected handle only when you need to:

```bash
aiwiki-toolkit install --handle your-handle
```

Or use the backward-compatible alias:

```bash
aiwiki-toolkit init
```

`install` will:

- create `ai-wiki/` inside the current repository
- create `~/ai-wiki/system/`
- create a gitignored `.env.aiwiki` file for the current local actor identity
- create starter indexes such as `ai-wiki/conventions/index.md`, `ai-wiki/review-patterns/index.md`, `ai-wiki/problems/index.md`, `ai-wiki/features/index.md`, `ai-wiki/trails/index.md`, `ai-wiki/work/index.md`, and `ai-wiki/people/<handle>/index.md`
- create `ai-wiki/conventions/`, `ai-wiki/review-patterns/`, `ai-wiki/problems/`, `ai-wiki/features/`, `ai-wiki/work/`, `ai-wiki/people/<handle>/drafts/`, `ai-wiki/metrics/`, and repo/home `_toolkit/`
- generate package-managed `_toolkit/index.md`, `_toolkit/workflows.md`, `_toolkit/catalog.json`, `_toolkit/schema/reuse-v1.md`, `_toolkit/schema/team-memory-v1.md`, `_toolkit/schema/work-v1.md`, `_toolkit/metrics/*`, and `_toolkit/work/*`
- upsert a managed `.gitignore` block that ignores `.env.aiwiki`, AI wiki telemetry, and generated aggregate snapshots so routine agent use does not dirty `git status`
- create or refresh package-owned `.agents/skills/ai-wiki-reuse-check/`, `.agents/skills/ai-wiki-update-check/`, `.agents/skills/ai-wiki-clarify-before-code/`, `.agents/skills/ai-wiki-capture-review-learning/`, and `.agents/skills/ai-wiki-consolidate-drafts/`
- update `AGENT.md`, `AGENTS.md`, and/or `CLAUDE.md` with a short managed instruction block that points agents to `ai-wiki/_toolkit/system.md` when the repo contains `ai-wiki/`

If no supported prompt file exists, it creates `AGENT.md`.

If `--handle` is not passed, the tool resolves a handle from:

1. `AIWIKI_TOOLKIT_HANDLE`
2. the repo-local `.env.aiwiki`
3. local or global git config
4. an interactive team ID prompt

The prompt appears only when no usable handle can be resolved:

```text
Could not detect a git user.name or user.email.

AI wiki needs a stable local ID for your team identity.
What ID would you prefer to use in this team?
```

The entered ID is normalized into a path- and branch-safe handle, stored in
`.env.aiwiki`, and used for paths such as `ai-wiki/people/<handle>/`. In
non-interactive shells, pass `--handle your-name` or set `AIWIKI_TOOLKIT_HANDLE`.

The tool works best when `git user.name` and `git user.email` are configured first.

For stronger trial/error capture, configure your agent runner to call the post-turn capture command
after completed AI Wiki write-back turns:

```bash
aiwiki-toolkit source-incident capture-post-turn --apply
```

This hook is recommended when your runner supports it, but `install` does not enable hooks
automatically or mutate agent runtime configuration.

If package-owned repo-local skill files already exist under `.agents/skills/ai-wiki-*`, the installer refreshes them from the current package so new workflow and footer contracts propagate on upgrade. Because these files live in git, local customizations remain visible in `git diff` after running `install`.

`init` remains as a backward-compatible alias for `install`. The actual scaffold creation does not happen at package install time; it happens when you run `aiwiki-toolkit install` or `aiwiki-toolkit init` inside a git repository.

To append one explicit knowledge-reuse observation and refresh handle-scoped managed metrics:

```bash
aiwiki-toolkit record-reuse \
  --doc-id review-patterns/shared-prompt-files-must-be-user-agnostic \
  --task-id release-followup \
  --retrieval-mode lookup \
  --evidence-mode explicit \
  --reuse-outcome resolved \
  --reuse-effect avoided_retry \
  --saved-tokens 1200 \
  --saved-seconds 45
```

This appends to the user-owned `ai-wiki/metrics/reuse-events/<handle>.jsonl` shard and refreshes the handle-scoped generated views under `ai-wiki/_toolkit/metrics/by-handle/<handle>/`. The installer ignores both the shard and the generated aggregate views by default so these telemetry updates stay local.

For post-task diagnosis, reuse events can also carry optional provenance such as `--session-id`, `--source-session-id`, `--source-task-id`, `--consulted-order`, `--signal-status candidate`, `--not-helpful-reason superseded_by_later_doc`, `--resolved-by-doc-id`, and `--superseded-by-doc-id`. Candidate not-helpful signals are review hints; confirmed outcomes still require explicit human or agent judgment.

When a reused memory came from a real earlier incident, record the original trial/error acquisition cost separately from `--saved-seconds`:

```bash
aiwiki-toolkit record-reuse \
  --doc-id problems/retry-loop \
  --task-id followup-using-memory \
  --retrieval-mode lookup \
  --evidence-mode explicit \
  --reuse-outcome resolved \
  --reuse-effect avoided_retry \
  --source-task-id original-retry-loop \
  --source-incident-seconds 780 \
  --source-incident-source manual \
  --source-incident-note "Failed attempt plus correction turn."
```

If the source incident was a local Codex session, `record-reuse` can derive the active-turn estimate from `task_complete.duration_ms` plus timed `turn_aborted.duration_ms` records:

```bash
aiwiki-toolkit record-reuse \
  --doc-id problems/retry-loop \
  --task-id followup-using-memory \
  --retrieval-mode lookup \
  --evidence-mode explicit \
  --reuse-outcome resolved \
  --source-session-id 019dcf06-example \
  --source-incident-from-codex-session
```

Diagnostics and `eval impact discover` report this as `source_incident_timing`. Treat it as source active-turn context for research, not as exact human time saved or a formal no-AI-wiki baseline.

For older memories where the original `record-reuse` event did not include source timing, backfill a separate evidence ledger from local Codex write-back footers:

```bash
aiwiki-toolkit source-incident backfill-writeback \
  --writeback-path ai-wiki/problems/retry-loop.md \
  --apply
```

This scans local `~/.codex/sessions` for the first `AI Wiki Write-Back Path:` footer in a session whose `cwd` matches the current repository, counts active `task_complete.duration_ms` plus timed `turn_aborted.duration_ms` rows from the current user task start through that first write-back turn, and appends the result to `ai-wiki/metrics/source-incidents/<handle>.jsonl`. It does not mutate historical reuse events. Omit `--apply` for a dry run, or pass `--doc-id`/`--writeback-path` to scope the backfill.

For a post-turn hook or wrapper, capture only the latest completed write-back turn for the current repo:

```bash
aiwiki-toolkit source-incident capture-post-turn --apply
```

This command is idempotent. If the latest write-back was already captured, it reports `skipped_existing` instead of appending another row. A runner that knows the Codex session id can pass `--session-id <id>` to avoid scanning all local session files.

Only record user-owned AI wiki knowledge docs with `record-reuse`.

Managed control-plane docs under `_toolkit/**` should still be cited in user-facing notes when they affect behavior, but they should not be logged as knowledge-reuse events.

To turn conversation todos or epics into routeable repo-local work state:

```bash
aiwiki-toolkit work capture \
  --work-id aiwiki-framework-roadmap \
  --title "Build the coding agent working framework" \
  --item-type epic \
  --status proposed \
  --source conversation

aiwiki-toolkit work capture \
  --work-id work-ledger \
  --title "Capture conversation todos as AI wiki work state" \
  --status todo \
  --epic-id aiwiki-framework-roadmap \
  --assignee your-handle \
  --link ai-wiki/people/your-handle/drafts/agent-framework-roadmap.md

aiwiki-toolkit work status \
  --work-id work-ledger \
  --status processing
```

By default, `work capture` resolves the current actor from explicit CLI input, environment, `.env.aiwiki`, git config, then fallback. It uses that actor as `author_handle`, `reporter_handle`, and the default assignee. This appends to `ai-wiki/work/events/<handle>.jsonl` and regenerates local package-managed views under `ai-wiki/_toolkit/work/`. Route packets can then surface matching active, processing, blocked, planned, or todo work items before an agent starts acting. Work events are not knowledge-reuse evidence by themselves, so they are kept separate from `record-reuse`.

For team use, canonical work stays in the central `ai-wiki/work/events/` ledger. People are linked through `reporter_handle` and `assignee_handles`; work is not stored inside `people/<handle>/`. Use these views when you need owner-scoped state:

```bash
aiwiki-toolkit work mine
aiwiki-toolkit work list --assignee your-handle
aiwiki-toolkit work list --reporter your-handle --include-closed
```

Generated local views are also written under `ai-wiki/_toolkit/work/by-assignee/` and `ai-wiki/_toolkit/work/by-reporter/`. Route packets treat work assigned to the current `.env.aiwiki` actor as actionable by default; another person's work appears only when directly matched by the current task request.

To record that a completed task was checked for AI wiki reuse, even when no wiki docs were needed:

```bash
aiwiki-toolkit record-reuse-check \
  --task-id release-followup \
  --check-outcome wiki_used
```

This appends to the user-owned `ai-wiki/metrics/task-checks/<handle>.jsonl` shard and refreshes the handle-scoped generated views under `ai-wiki/_toolkit/metrics/by-handle/<handle>/`. The installer ignores both the shard and the generated aggregate views by default so these telemetry updates stay local.

The local metrics logs are sharded by handle under:

- `ai-wiki/metrics/reuse-events/<handle>.jsonl`
- `ai-wiki/metrics/task-checks/<handle>.jsonl`
- `ai-wiki/metrics/source-incidents/<handle>.jsonl`

These logs are intended as local telemetry by default, not merge-heavy source files.

If you need a fresh local telemetry and work snapshot, regenerate package-managed aggregate views such as `ai-wiki/_toolkit/catalog.json`, `ai-wiki/_toolkit/metrics/*`, or `ai-wiki/_toolkit/work/*` with:

```bash
aiwiki-toolkit refresh-metrics
```

To inspect memory quality from local reuse and task-check evidence:

```bash
aiwiki-toolkit diagnose memory
aiwiki-toolkit diagnose memory --since 14d --handle your-handle
aiwiki-toolkit diagnose memory --focus trial-error
```

This writes regenerated local reports under `ai-wiki/_toolkit/diagnostics/<handle-or-all>/` and prints the report to stdout. The report highlights high-ROI memory, noisy memory, stale or missing docs, conflict notes, missed-memory signals, and coverage gaps such as document reuse events that were never paired with a task-level reuse check. It does not edit user-owned AI wiki docs.

Use `--focus trial-error` to generate a focused trial/error reduction report from existing
AI wiki evidence. It summarizes material effects such as `avoided_retry`,
`blocked_wrong_path`, `changed_plan`, and `faster_resolution`, separates missed or repeated issue
signals from unproven wiki use, and lists replay candidates that still need source incident
artifacts before becoming formal impact-eval families. Source incident timing can come either from
new `record-reuse` provenance fields or from the separate `source-incident backfill-writeback`
ledger.

To turn diagnostics and handle-local drafts into a human-reviewable consolidation queue:

```bash
aiwiki-toolkit consolidate queue
aiwiki-toolkit consolidate queue --since 14d --handle your-handle
```

This writes regenerated local reports under `ai-wiki/_toolkit/consolidation/<handle>/` and prints the queue to stdout. The queue suggests one action per draft cluster: keep, refine, promotion candidate, conflict, or supersession. It does not edit user-owned AI wiki docs or create shared conventions, review patterns, problems, features, or decisions; those still require human confirmation.

To mark handle-local draft promotion candidates from confirmed-useful reuse evidence:

```bash
aiwiki-toolkit promote candidates --handle your-handle
aiwiki-toolkit promote candidates --handle your-handle --apply
```

The default run is report-only. With `--apply`, a draft is marked only when it has more than three distinct resolved task IDs, no `not_helpful` reuse events, and an existing non-stale source draft. The command refreshes stable links in `ai-wiki/people/<handle>/index.md`; exact reuse counts stay in generated reports under `ai-wiki/_toolkit/reports/promotion-candidates/<handle>/`.

To inspect referenced files and estimated time impact from local reuse evidence:

```bash
aiwiki-toolkit report usefulness --handle your-handle
aiwiki-toolkit report usefulness --handle your-handle --format json
```

This writes `ai-wiki/_toolkit/reports/usefulness/<handle-or-all>/latest.md` and `.json`. It lists referenced files and sums resolved-event `estimated_savings`. Baseline/current/remaining durations are reported as `unknown` until task logs include explicit timing evidence.

To generate a weekly local HTML review queue:

```bash
aiwiki-toolkit report weekly --handle your-handle
aiwiki-toolkit report weekly --handle your-handle --if-due
```

This writes a static HTML review queue and JSON payload under `ai-wiki/_toolkit/reports/weekly/<handle>/<iso-week>/`, refreshes `latest.html` and `latest.json`, and records the last generated period in `ai-wiki/_toolkit/reports/weekly/<handle>/state.json`. The HTML page focuses only on items that need human judgment: promotion candidates, personal drafts that may need diagnosis, and not-helpful signals. Coverage, referenced-file, and other raw evidence remains in the JSON payload and supporting reports; saved-time estimates belong in impact-eval reports, not the weekly HTML view. Use `--if-due` from cron, launchd, or an agent workflow so the same ISO week is generated once; use `--force` for local testing before a release.

To summarize first-attempt product impact from a captured eval run:

```bash
aiwiki-toolkit eval impact families
aiwiki-toolkit eval impact families --format json
aiwiki-toolkit eval impact discover
aiwiki-toolkit eval impact family show ownership_boundary
aiwiki-toolkit eval impact family candidates
aiwiki-toolkit eval impact family init --name retry_loop --from-candidate problems/retry-loop --baseline-ref HEAD^
aiwiki-toolkit eval impact family draft --candidate problems_retry_loop --baseline-ref HEAD^
aiwiki-toolkit eval impact family promote --candidate problems_retry_loop
aiwiki-toolkit eval impact family promote --candidate problems_retry_loop --apply
aiwiki-toolkit eval impact plan --family ownership_boundary
aiwiki-toolkit eval impact plan --family ownership_boundary --format json
aiwiki-toolkit eval impact prepare --family ownership_boundary
aiwiki-toolkit eval impact prepare --family ownership_boundary --format json
aiwiki-toolkit eval impact run --run-dir /path/to/eval-run --slot s01
aiwiki-toolkit eval impact run --run-dir /path/to/eval-run --all-slots --score-policy command-exit
aiwiki-toolkit eval impact run --run-dir /path/to/eval-run --all-slots --score-policy rubric --rubric evals/impact/rubrics/my-family.json
aiwiki-toolkit eval impact benchmark --family ownership_boundary --score-policy command-exit
aiwiki-toolkit eval impact schedule report --handle your-handle --candidate-max-items 25
aiwiki-toolkit eval impact schedule run --family ownership_boundary --score-policy command-exit
aiwiki-toolkit eval impact schedule run --all-runnable --if-due --score-policy rubric
aiwiki-toolkit eval impact capture --run-dir /path/to/eval-run --slot s01 --prompt-level original --first-pass-success
aiwiki-toolkit eval impact validate --run-dir /path/to/eval-run
aiwiki-toolkit eval impact score --run-dir /path/to/eval-run --slot s01 --prompt-level original --label success
aiwiki-toolkit eval impact manifest --run-dir /path/to/eval-run
aiwiki-toolkit eval impact manifest --run-dir /path/to/eval-run --format json
aiwiki-toolkit eval impact report --run-dir /path/to/eval-run
aiwiki-toolkit eval impact report --run-dir /path/to/eval-run --format json
aiwiki-toolkit eval impact summarize --run-dir /path/to/eval-run --run-dir /path/to/another-run
aiwiki-toolkit eval impact summarize --runs-file evals/impact/runs.json
```

Use `eval impact families` before running benchmarks. It discovers registered families from
`evals/impact/families/*/spec.toml`, reports readiness, prompt and rubric presence, memory fixture
counts, baseline refs, historical issues, and next commands. Use `eval impact family show <name>`
for one family.

Use `eval impact family candidates` to expose trial/error replay candidates from existing AI wiki
telemetry. It layers over `diagnose memory --focus trial-error` and reports candidate readiness
without writing user-owned AI wiki docs. Use `eval impact family init --from-candidate ...` only
after confirming a source incident, baseline ref, prompt shape, and rubric direction; it creates a
draft family scaffold under `evals/impact/`.

Use `eval impact discover` for the continuous loop. It refreshes the managed candidate queue under
`ai-wiki/_toolkit/evals/candidates/`, preserves first-seen/last-seen/seen-count state, and prints
the next draft, promotion, and schedule commands. Use `eval impact family draft` to create managed
candidate files under `ai-wiki/_toolkit/evals/drafts/<candidate>/` without registering a formal
family. Use `eval impact family promote` as a report-only gate; add `--apply` only after the draft
has a real baseline ref, prompt, and rubric and you want to write formal files under
`evals/impact/`.

Use `eval impact plan` to inspect the next run before creating workspaces or invoking agents. It
reads `evals/impact/families/<family>/spec.toml` and prompt files, then reports the planned
baseline ref, prompt hashes, workflow-primary variants, output paths, and script commands. The plan
command does not mutate eval artifacts or call an agent.

Use `eval impact prepare` to execute the planned setup only: it creates neutral slot workspaces,
creates the run directory and metadata, and writes initial `manifest.json` and `manifest.md` files.
It still does not call an agent.

Use `eval impact run` to invoke Codex CLI against one neutral slot or all slots in an already
prepared run. The command calls the repo-local slot runner, captures first-pass artifacts,
optionally exports visible Codex sessions, validates confounds, applies an explicit score policy,
and writes a report bundle under `<run-dir>/report_bundle/`. The default score policy is `none`.
`--score-policy command-exit` is useful for smoke tests and execution-health automation, but it
only scores Codex/save-result command completion; use manual or semantic scoring before making
research-quality correctness claims.
`--score-policy rubric` reads an `impact-eval-rubric-v1` JSON file, writes
`rubric_judgment.json` next to each slot score, then writes the normal `score.json` artifact.
Rubric criteria can inspect captured diffs, final messages, result fields, changed files, and
untracked files.

Use `eval impact benchmark` when you want one command to prepare a family and immediately run all
slots. It wraps `prepare` plus `run`, then returns the prepared run directory, run result, validation
status, scores, and report bundle.

Use `eval impact schedule report` to generate a periodic benchmark dashboard under
`ai-wiki/_toolkit/evals/reports/<period>/`. It combines registered families, the managed candidate
queue, and the run index. Pass the same candidate filters you use for discovery, such as `--handle`,
`--since`, and `--candidate-max-items`, so the scheduled report does not accidentally stale a
larger queue with a narrower refresh. Use `eval impact schedule run --family <name>` or
`--all-runnable` to run benchmarks, append `ai-wiki/_toolkit/evals/runs/index.json`, refresh the
report, and record `ai-wiki/_toolkit/evals/schedule/state.json`. `--if-due` is intended for cron,
launchd, or an agent workflow that should run at most once per period.

Use `eval impact capture` after a manual first pass or repaired pass to save `result.json`, the
workspace diff, status, head, and optional final-message artifact. It infers slot variant and
workspace from `metadata.json` when possible. Use `eval impact validate` after exporting visible
sessions to write `confounds.json`; missing exports are reported as critical confounds rather than
silently accepted. Use `eval impact score` to write the manual `score.json` artifact for a slot.
Each of these commands refreshes `manifest.json` and `manifest.md` so the run inventory stays
current.

The report and manifest commands read an existing run directory with `metadata.json`, result
captures, optional `score.json` files, and optional `confounds.json`. The `eval impact report`
command compares the run's primary variants, normally `no_aiwiki_workflow` versus
`aiwiki_ambient_memory_workflow`, using first-attempt metrics only: `first_pass` captures count
toward the signal, while `final` repair captures stay diagnostic. The command reports
first-attempt success rate, average score, attempts, human nudges, changed files, untracked files,
change-profile splits for project files versus AI wiki telemetry and user-owned wiki churn, and
whether the run is ready for shareable causal claims. It does not run agents.

Use `eval impact manifest` to audit run identity before interpreting scores. It reports the
baseline ref, prompt hashes, model, reasoning effort, execution surface, slot-to-variant mapping,
session export presence, confounds, and captured artifact paths.

Use `eval impact summarize` to aggregate multiple captured runs into a product-level dashboard.
It reports each family's primary outcome, product signal, shareability, success and score deltas,
and change-profile deltas so neutral success-rate runs can still surface quality or churn signals.

To diagnose missing starter pointers, stale managed prompt blocks, or rule drift and print copy-paste upgrade starters:

```bash
aiwiki-toolkit doctor --suggest-index-upgrade
```

This command does not rewrite user-owned repo docs. It prints which paths need attention and the latest starter content for those files so you can merge or copy it into:

- `ai-wiki/workflows.md`
- `ai-wiki/conventions/index.md`
- `ai-wiki/review-patterns/index.md`
- `ai-wiki/problems/index.md`
- `ai-wiki/features/index.md`
- `ai-wiki/trails/index.md`
- `ai-wiki/work/index.md`
- `ai-wiki/people/<handle>/index.md`
- `ai-wiki/metrics/index.md`

It also checks whether the managed `.gitignore` block is present, whether local identity, telemetry, or generated-view paths are still tracked in the git index from older versions, and whether managed system rules include the runtime skill fallback used when repo-local AI wiki skills are present but not exposed by the active agent runtime. If local-state paths are still tracked, `doctor` prints a one-time `git rm --cached` command to untrack them.

To remove the managed layer while keeping your user-owned wiki documents:

```bash
aiwiki-toolkit uninstall
```

This removes:

- managed prompt blocks from `AGENT.md` / `AGENTS.md` / `CLAUDE.md`
- the managed `.gitignore` block for AI wiki local identity and telemetry
- `ai-wiki/_toolkit/**`
- `~/ai-wiki/system/_toolkit/**`
- the `aiwikiToolkit` key from `opencode.json`

Your user-owned `ai-wiki/**/*.md` and `~/ai-wiki/system/**/*.md` documents are preserved by default.

To also remove repo-local user-owned docs, you must opt in explicitly:

```bash
aiwiki-toolkit uninstall --purge-user-docs --yes
```

Even with `--purge-user-docs --yes`, the shared home wiki under `~/ai-wiki/system/` is preserved.

## Compatibility rules

- Existing user-owned `ai-wiki/**/*.md` files are treated as stable data.
- `install`/`init` only create missing starter files; they do not merge or overwrite existing user wiki documents.
- Starter indexes such as `ai-wiki/index.md`, `conventions/index.md`, `review-patterns/index.md`, `problems/index.md`, `features/index.md`, `trails/index.md`, `work/index.md`, `people/<handle>/index.md`, and `metrics/index.md` become user-owned once created and are not rewritten by future package updates.
- `ai-wiki/_toolkit/**` and `~/ai-wiki/system/_toolkit/**` are package-managed and may be refreshed by future versions.
- `ai-wiki/index.md` is a repo-owned map and is not treated as a starter-drift upgrade target by `doctor`.
- `ai-wiki/workflows.md` remains user-owned; package-managed workflow updates land in `ai-wiki/_toolkit/workflows.md` instead of rewriting the repo-owned file.
- `.env.aiwiki` stores the current local actor identity in a managed block. It is gitignored and should not be committed.
- `ai-wiki/metrics/reuse-events/<handle>.jsonl` and `ai-wiki/metrics/task-checks/<handle>.jsonl` are user-owned evidence data. `ai-wiki/work/events/<handle>.jsonl` is user-owned work state. Package-managed aggregate views are regenerated under `ai-wiki/_toolkit/metrics/` and `ai-wiki/_toolkit/work/`; handle-scoped metrics are regenerated under `ai-wiki/_toolkit/metrics/by-handle/<handle>/`; memory diagnostics, consolidation queues, promotion reports, usefulness reports, and weekly reports are written under handle-scoped generated paths where they depend on a handle. The installer ignores those generated paths by default in `.gitignore`.
- Legacy flat files such as `ai-wiki/metrics/reuse-events.jsonl` and `ai-wiki/metrics/task-checks.jsonl` are still read for compatibility, but new writes should use the handle-sharded layout.
- `aiwiki-toolkit doctor --suggest-index-upgrade` prints suggested replacements for missing repo starter docs and repo-owned companion docs such as `ai-wiki/workflows.md`, but it does not overwrite them automatically.
- Package-owned `.agents/skills/ai-wiki-reuse-check/**`, `.agents/skills/ai-wiki-update-check/**`, `.agents/skills/ai-wiki-clarify-before-code/**`, `.agents/skills/ai-wiki-capture-review-learning/**`, and `.agents/skills/ai-wiki-consolidate-drafts/**` are refreshed by `install` so package workflow updates reach existing repos.
- Prompt files are updated only inside the managed block marked by:

```md
<!-- aiwiki-toolkit:start -->
<!-- aiwiki-toolkit:end -->
```

- `.gitignore` is updated only inside the managed block marked by:

```gitignore
# <!-- aiwiki-toolkit:start -->
# <!-- aiwiki-toolkit:end -->
```

- Future `opencode.json` integration is limited to a single top-level `aiwikiToolkit` key.

## Distribution

The public distribution model is:

- GitHub Releases are the source of truth for versioned release binaries
- Homebrew tap `BochengYin/tap` consumes those release assets for macOS and Linux users
- npm package `ai-wiki-toolkit` is a meta package that depends on platform-specific npm binary packages for macOS and Linux users who prefer `npm install -g`

The goal is to make end-user installation independent of a local Python setup, while keeping `pip install -e .` as the simplest contributor workflow inside this repository.

Release history is tracked in [CHANGELOG.md](CHANGELOG.md).

The first release skeleton is documented in [docs/releasing.md](docs/releasing.md).
The Homebrew tap plan is documented in [docs/homebrew-tap.md](docs/homebrew-tap.md).
The npm distribution plan is documented in [docs/npm-wrapper.md](docs/npm-wrapper.md).
The npm publishing plan is documented in [docs/npm-publish.md](docs/npm-publish.md).

## Path examples

The repo-local wiki is always:

- `ai-wiki/`

The home-level system wiki resolves from the current user's home directory:

- macOS: `/Users/<username>/ai-wiki/system`
- Linux: `/home/<username>/ai-wiki/system`
- Windows: `C:\Users\<username>\ai-wiki\system`

In Python terms, the path comes from `Path.home() / "ai-wiki" / "system"`, so it follows the current platform automatically.
