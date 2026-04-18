# ai-wiki-toolkit

`ai-wiki-toolkit` is a local-first scaffold for repo and home AI wiki files.

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

## Current Scope

The current scope is intentionally strict about compatibility:

- initialize the repo and home AI wiki folders
- create starter Markdown files only if they do not already exist
- create managed `_toolkit/` files that package updates are allowed to refresh
- create `review-patterns/` and `people/<handle>/drafts/` scaffolding
- create a repo-local `.agents/skills/ai-wiki-update-check/` skill only when files are missing
- update managed instruction blocks inside `AGENT.md`, `AGENTS.md`, and `CLAUDE.md`
- avoid rewriting existing user-owned `ai-wiki/**/*.md` documents outside `_toolkit/`

## Install For Local Development

```bash
pip install -e .
```

This is the current developer install path. Public binary distribution is planned separately.

## Recommendations

Recommended before running `install`:

- initialize the repository with git
- configure `git user.name` and `git user.email` so the toolkit can derive a stable handle
- if you already ran Claude Code, Codex, or another agent bootstrap and already have `AGENT.md`, `AGENTS.md`, or `CLAUDE.md`, the toolkit will update that file in place

Claude Code / Codex init is not required. If no supported prompt file exists, `ai-wiki-toolkit` creates `AGENT.md` automatically.

## Usage

Run inside a git repository:

```bash
aiwiki-toolkit install --handle your-handle
```

`install` will:

- create `ai-wiki/` inside the current repository
- create `~/ai-wiki/system/`
- create `ai-wiki/review-patterns/`, `ai-wiki/people/<handle>/drafts/`, and repo/home `_toolkit/`
- create `.agents/skills/ai-wiki-update-check/` if the repo-local skill does not already exist
- update `AGENT.md`, `AGENTS.md`, and/or `CLAUDE.md` with a managed instruction block

If no supported prompt file exists, it creates `AGENT.md`.

If `--handle` is not passed, the tool resolves a handle from:

1. `AIWIKI_TOOLKIT_HANDLE`
2. local or global git config
3. `unknown`

The tool works best when `git user.name` and `git user.email` are configured first.

If repo-local skill files already exist at `.agents/skills/ai-wiki-update-check/`, the installer does not overwrite them. It skips those files and prints a manual merge URL back to this repository so you can compare and resolve changes yourself.

`init` remains as a backward-compatible alias for `install`.

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
- `ai-wiki/_toolkit/**` and `~/ai-wiki/system/_toolkit/**` are package-managed and may be refreshed by future versions.
- `.agents/skills/ai-wiki-update-check/**` is installed as starter scaffolding only. Existing files at those paths are skipped instead of overwritten.
- Prompt files are updated only inside the managed block marked by:

```md
<!-- aiwiki-toolkit:start -->
<!-- aiwiki-toolkit:end -->
```

- Future `opencode.json` integration is limited to a single top-level `aiwikiToolkit` key.

## Planned Distribution

The intended public distribution model is:

- GitHub Releases for versioned release binaries, with macOS and Linux as the current public matrix
- Homebrew tap for macOS and Linux users
- npm wrapper for Node users who prefer `npm install -g`

The goal is to make the final end-user install independent of a local Python setup. Until that release pipeline exists, the repository uses the Python developer install shown above.

The first release skeleton is documented in [docs/releasing.md](docs/releasing.md).
The Homebrew tap plan is documented in [docs/homebrew-tap.md](docs/homebrew-tap.md).
The npm wrapper plan is documented in [docs/npm-wrapper.md](docs/npm-wrapper.md).
The npm publishing plan is documented in [docs/npm-publish.md](docs/npm-publish.md).

## Path examples

The repo-local wiki is always:

- `ai-wiki/`

The home-level system wiki resolves from the current user's home directory:

- macOS: `/Users/<username>/ai-wiki/system`
- Linux: `/home/<username>/ai-wiki/system`
- Windows: `C:\Users\<username>\ai-wiki\system`

In Python terms, the path comes from `Path.home() / "ai-wiki" / "system"`, so it follows the current platform automatically.
