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
- repo-local Codex skills for repeatable end-of-task checks

That gives the repo and the user a stable Markdown place to accumulate knowledge without turning the package into a knowledge platform.

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
- `.agents/skills/ai-wiki-update-check/` provides a repeatable end-of-task check for Codex-style agent runs

## Prompt File Integration

Many coding-agent setups already create one of these repo-shared prompt files:

- `CLAUDE.md` for Claude Code style workflows
- `AGENTS.md` or `AGENT.md` for Codex or other agent bootstraps

`ai-wiki-toolkit` does not expect you to choose all of them manually.

When you run `aiwiki-toolkit install`, it looks for supported prompt files in the repository root and updates whichever ones already exist. It only manages the `aiwiki-toolkit` block inside those files, so your surrounding user-written instructions stay in place.

If none of those files exist yet, the toolkit creates `AGENT.md` as a generic default so the repo still has one stable prompt entrypoint.

## Why The Files Look Like This

The AI wiki structure is deliberately inspired by how `SKILL.md` files work well: keep a small stable entrypoint, then fan out into focused references.

Each wiki namespace starts with an `index.md` and then links to narrower files such as `constraints.md`, `workflows.md`, `decisions.md`, `review-patterns/`, `trails/`, and personal `drafts/`. That keeps the top-level entrypoint easy for both humans and agents to scan, while still letting the repo accumulate detailed guidance without collapsing into one giant prompt blob.

## Current Scope

The current scope is intentionally strict about compatibility:

- initialize the repo and home AI wiki folders
- create starter Markdown files only if they do not already exist
- create managed `_toolkit/` files that package updates are allowed to refresh
- create `review-patterns/` and `people/<handle>/drafts/` scaffolding
- create a repo-local `.agents/skills/ai-wiki-update-check/` skill only when files are missing
- update managed instruction blocks inside `AGENT.md`, `AGENTS.md`, and `CLAUDE.md`
- avoid rewriting existing user-owned `ai-wiki/**/*.md` documents outside `_toolkit/`

## Install

For end users on macOS and Linux, the simplest install paths are Homebrew and npm.

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
- create starter indexes such as `ai-wiki/review-patterns/index.md`, `ai-wiki/trails/index.md`, and `ai-wiki/people/<handle>/index.md`
- create `ai-wiki/review-patterns/`, `ai-wiki/people/<handle>/drafts/`, `ai-wiki/metrics/`, and repo/home `_toolkit/`
- generate package-managed `_toolkit/catalog.json`, `_toolkit/schema/reuse-v1.md`, and `_toolkit/metrics/*.json`
- create `.agents/skills/ai-wiki-update-check/` if the repo-local skill does not already exist
- update `AGENT.md`, `AGENTS.md`, and/or `CLAUDE.md` with a managed instruction block

If no supported prompt file exists, it creates `AGENT.md`.

If `--handle` is not passed, the tool resolves a handle from:

1. `AIWIKI_TOOLKIT_HANDLE`
2. local or global git config
3. `unknown`

The tool works best when `git user.name` and `git user.email` are configured first.

If repo-local skill files already exist at `.agents/skills/ai-wiki-update-check/`, the installer does not overwrite them. It skips those files and prints a manual merge URL back to this repository so you can compare and resolve changes yourself.

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

This appends to the user-owned `ai-wiki/metrics/reuse-events.jsonl` log and refreshes the package-managed aggregate views under `ai-wiki/_toolkit/metrics/`.

To remove the managed layer while keeping your user-owned wiki documents:

```bash
aiwiki-toolkit uninstall
```

This removes:

- managed prompt blocks from `AGENT.md` / `AGENTS.md` / `CLAUDE.md`
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
- Starter indexes such as `ai-wiki/index.md`, `review-patterns/index.md`, `trails/index.md`, `people/<handle>/index.md`, and `metrics/index.md` become user-owned once created and are not rewritten by future package updates.
- `ai-wiki/_toolkit/**` and `~/ai-wiki/system/_toolkit/**` are package-managed and may be refreshed by future versions.
- `ai-wiki/metrics/reuse-events.jsonl` is user-owned evidence data. Package-managed aggregate views are regenerated under `ai-wiki/_toolkit/metrics/`.
- `.agents/skills/ai-wiki-update-check/**` is installed as starter scaffolding only. Existing files at those paths are skipped instead of overwritten.
- Prompt files are updated only inside the managed block marked by:

```md
<!-- aiwiki-toolkit:start -->
<!-- aiwiki-toolkit:end -->
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
