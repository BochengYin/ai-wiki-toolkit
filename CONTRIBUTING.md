# Contributing

Thanks for trying `ai-wiki-toolkit`.

This project is still early, so the best contributions are the ones that make bugs reproducible, behavior clearer, and install or release flows more reliable.

## Default Paths

Use GitHub Issues as the default place for feedback.

- Bug reports, install failures, and unexpected behavior: open an issue.
- Feature ideas, workflow changes, and integration suggestions: open an issue first.
- Small typo fixes or clearly scoped docs improvements: direct PRs are welcome.
- Larger code changes: open an issue first so we can align on direction before implementation.

## Branch And Review Flow

Please do not work directly on `main`.

Use a topic branch for your change:

```bash
git switch main
git pull --ff-only
git switch -c your-branch-name
```

Then push that branch and open a pull request.

The intended merge path for this repository is:

- changes are developed on a branch
- CI passes on the pull request
- the pull request is reviewed
- `main` is updated only by merging the reviewed PR

After the PR is merged, switch back to `main` locally and sync before starting the next task:

```bash
git switch main
git pull --ff-only
```

`CODEOWNERS` is configured so `@BochengYin` is the default code owner. If branch protection is enabled in GitHub settings, that review can be required before merge.

## Good Bug Reports

For install or runtime issues, please include:

- operating system and architecture
- install method: npm, Homebrew, editable pip, or source checkout
- `aiwiki-toolkit --version`
- the exact command you ran
- the full error output
- a minimal reproduction, ideally in a clean temporary git repo

If the problem is specific to package-manager distribution, include the relevant tool versions as well, such as `node -v`, `npm -v`, `brew --version`, or `python --version`.

## Local Setup

Use one of these development setups:

```bash
uv sync --extra dev
```

or

```bash
python -m pip install -e ".[dev]"
```

Useful verification commands:

```bash
uv run pytest
npm pack --dry-run --ignore-scripts
```

For release-related changes, also verify version alignment:

```bash
python scripts/check_release_version.py vX.Y.Z
```

## Change Expectations

- Add or update tests for behavior changes.
- Keep CLI wiring thin in `src/ai_wiki_toolkit/cli.py`.
- Update docs when install, release, or distribution behavior changes.
- Update `CHANGELOG.md` for notable user-facing changes.
- Do not overwrite user-owned `ai-wiki/**/*.md` content outside managed `_toolkit/` paths.
- Keep prompt-file edits inside the managed `aiwiki-toolkit` block.

## Pull Requests

Please keep PRs focused.

Good PRs usually include:

- a concise explanation of the change
- why the change is needed
- the commands used for verification
- any README, docs, or changelog updates required by the change
