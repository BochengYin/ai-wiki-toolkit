# ai-wiki-toolkit

`ai-wiki-toolkit` is a local-first scaffold for AI wiki files, managed prompt blocks, and review-pattern workflows.

It creates two isolated namespaces:

- `repo/ai-wiki/` for project-specific AI wiki files
- `~/ai-wiki/system/` for reusable cross-project AI wiki files

The current scope is intentionally strict about compatibility:

- initialize the repo and home AI wiki folders
- create starter Markdown files only if they do not already exist
- create managed `_toolkit/` files that package updates are allowed to refresh
- create `review-patterns/` and `people/<handle>/drafts/` scaffolding
- update managed instruction blocks inside `AGENT.md` and `CLAUDE.md`
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
- if you already ran Claude Code or Codex init and already have `AGENT.md` or `CLAUDE.md`, the toolkit will update that file in place

Claude Code / Codex init is not required. If neither `AGENT.md` nor `CLAUDE.md` exists, `ai-wiki-toolkit` creates `AGENT.md` automatically.

## Usage

Run inside a git repository:

```bash
aiwiki-toolkit install --handle your-handle
```

`install` will:

- create `ai-wiki/` inside the current repository
- create `~/ai-wiki/system/`
- create `ai-wiki/review-patterns/`, `ai-wiki/people/<handle>/drafts/`, and repo/home `_toolkit/`
- update `AGENT.md` and/or `CLAUDE.md` with a managed instruction block

If neither prompt file exists, it creates `AGENT.md`.

If `--handle` is not passed, the tool resolves a handle from:

1. `AIWIKI_TOOLKIT_HANDLE`
2. local or global git config
3. `unknown`

The tool works best when `git user.name` and `git user.email` are configured first.

`init` remains as a backward-compatible alias for `install`.

To remove the managed layer while keeping your user-owned wiki documents:

```bash
aiwiki-toolkit uninstall
```

This removes:

- managed prompt blocks from `AGENT.md` / `CLAUDE.md`
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
