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
- generate package-managed `_toolkit/index.md`, `_toolkit/workflows.md`, `_toolkit/catalog.json`, `_toolkit/schema/reuse-v1.md`, `_toolkit/schema/team-memory-v1.md`, `_toolkit/schema/work-v1.md`, `_toolkit/metrics/*.json`, and `_toolkit/work/*`
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

If package-owned repo-local skill files already exist under `.agents/skills/ai-wiki-*`, the installer refreshes them from the current package so new workflow and footer contracts propagate on upgrade. Because these files live in git, local customizations remain visible in `git diff` after running `install`.

`init` remains as a backward-compatible alias for `install`. The actual scaffold creation does not happen at package install time; it happens when you run `aiwiki-toolkit install` or `aiwiki-toolkit init` inside a git repository.

To append one explicit knowledge-reuse observation and refresh managed aggregates:

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

This appends to the user-owned `ai-wiki/metrics/reuse-events/<handle>.jsonl` shard and refreshes the package-managed aggregate views under `ai-wiki/_toolkit/metrics/`. The installer ignores both the shard and the generated aggregate views by default so these telemetry updates stay local.

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

This appends to the user-owned `ai-wiki/metrics/task-checks/<handle>.jsonl` shard and refreshes the package-managed aggregate views under `ai-wiki/_toolkit/metrics/`. The installer ignores both the shard and the generated aggregate views by default so these telemetry updates stay local.

Both metrics logs are sharded by handle under:

- `ai-wiki/metrics/reuse-events/<handle>.jsonl`
- `ai-wiki/metrics/task-checks/<handle>.jsonl`

These logs are intended as local telemetry by default, not merge-heavy source files.

If you need a fresh local telemetry and work snapshot, regenerate package-managed aggregate views such as `ai-wiki/_toolkit/catalog.json`, `ai-wiki/_toolkit/metrics/*.json`, or `ai-wiki/_toolkit/work/*` with:

```bash
aiwiki-toolkit refresh-metrics
```

To inspect memory quality from local reuse and task-check evidence:

```bash
aiwiki-toolkit diagnose memory
aiwiki-toolkit diagnose memory --since 14d --handle your-handle
```

This writes regenerated local reports under `ai-wiki/_toolkit/diagnostics/` and prints the report to stdout. The report highlights high-ROI memory, noisy memory, stale or missing docs, conflict notes, missed-memory signals, and coverage gaps such as document reuse events that were never paired with a task-level reuse check. It does not edit user-owned AI wiki docs.

To turn diagnostics and handle-local drafts into a human-reviewable consolidation queue:

```bash
aiwiki-toolkit consolidate queue
aiwiki-toolkit consolidate queue --since 14d --handle your-handle
```

This writes regenerated local reports under `ai-wiki/_toolkit/consolidation/` and prints the queue to stdout. The queue suggests one action per draft cluster: keep, refine, promotion candidate, conflict, or supersession. It does not edit user-owned AI wiki docs or create shared conventions, review patterns, problems, features, or decisions; those still require human confirmation.

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
- `ai-wiki/metrics/reuse-events/<handle>.jsonl` and `ai-wiki/metrics/task-checks/<handle>.jsonl` are user-owned evidence data. `ai-wiki/work/events/<handle>.jsonl` is user-owned work state. Package-managed aggregate views are regenerated under `ai-wiki/_toolkit/metrics/` and `ai-wiki/_toolkit/work/`; memory diagnostics are generated under `ai-wiki/_toolkit/diagnostics/`; consolidation queues are generated under `ai-wiki/_toolkit/consolidation/`. The installer ignores those generated paths by default in `.gitignore`.
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
