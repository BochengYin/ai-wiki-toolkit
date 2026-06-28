# NPM Global Install Path Shadowed By UV Tool

## Trigger

Install or verify the latest npm `ai-wiki-toolkit` package locally on this
machine, then run `aiwiki-toolkit` from the shell.

## Public/Local Signal

On 2026-06-16, `npm install -g ai-wiki-toolkit@latest` updated the Homebrew/npm
global package under `/opt/homebrew` to `0.1.40`, but `which aiwiki-toolkit`
still resolved to:

`<home>/.local/bin/aiwiki-toolkit`

That entry was a uv tool shim for `ai-wiki-toolkit 0.1.39`.

The follow-up fix upgraded the uv tool shim in place:

`uv tool upgrade ai-wiki-toolkit`

After that, the bare `aiwiki-toolkit --version` and
`/opt/homebrew/bin/aiwiki-toolkit --version` both reported `0.1.40`.

## Failed Attempt

Assuming `npm install -g ai-wiki-toolkit@latest` makes the bare
`aiwiki-toolkit` command use the npm release can validate the wrong binary when
`~/.local/bin` appears before `/opt/homebrew/bin` in `PATH`.

## Fix Or Rule

For npm release or local npm install verification on this machine:

- Check `npm list -g ai-wiki-toolkit --depth=0`.
- Check `/opt/homebrew/bin/aiwiki-toolkit --version` for the npm-installed CLI.
- Also check `which aiwiki-toolkit` and `aiwiki-toolkit --version` before saying
  the default shell command points at the npm release.
- Use `/opt/homebrew/bin/aiwiki-toolkit` explicitly for npm package validation
  unless the uv tool shim has been upgraded or removed intentionally.
- If the uv tool shim is stale, first try `uv tool upgrade ai-wiki-toolkit`;
  only change symlinks or PATH ordering if upgrading the shim cannot resolve the
  mismatch.

## Applies When

- Verifying a new npm package release locally.
- Testing npm-installed scaffold behavior against a temporary repo.
- Debugging why the bare `aiwiki-toolkit` command reports an older version after
  a successful npm global install.

## Do Not Use When

- The task is verifying PyPI or uv tool installation instead of npm.
- `which aiwiki-toolkit` already resolves to the npm global bin.

## Related Files

- `<repo>/package.json`
- `<repo>/docs/npm-wrapper.md`
- `<repo>/docs/npm-publish.md`

## Source Pointer

- Source: Local npm install verification in Codex.
- Captured by: Codex.
- Captured at: 2026-06-16.
