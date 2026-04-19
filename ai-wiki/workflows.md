# Project Workflows

These are repeatable repo-specific workflows worth following when changing scaffold behavior or cutting releases.

See also `_toolkit/workflows.md` for package-managed baseline workflows that ship with `ai-wiki-toolkit`.

## Scaffold And Prompt Changes

1. Update or add state-transition tests in the same change.
2. Run `uv run pytest`.
3. If prompt handling changed, run `aiwiki-toolkit install` against this repo and inspect the resulting prompt file update.
4. Confirm that managed prompt content lands only inside the `aiwiki-toolkit` managed block and does not churn on user-specific values.
5. If the change exposed a reusable lesson, write a trail or shared review pattern before moving on.

## Branch And Merge Flow

1. Do not develop directly on `main`.
2. Before editing or committing, create or switch to a topic branch such as `feat/...`, `fix/...`, or `docs/...`.
3. Push that topic branch and open a pull request instead of pushing to `main`.
4. Treat GitHub branch protection and CI as the source of truth for whether the branch is ready to merge.
5. After the pull request is merged, switch back to `main` locally and sync it before starting the next task.

Recommended local sequence:

```bash
git switch main
git pull --ff-only
git switch -c your-branch-name
```

After merge:

```bash
git switch main
git pull --ff-only
```

## Release Preparation

1. Merge workflow fixes to `main` before tagging a release.
2. Keep versions aligned across `package.json`, `pyproject.toml`, and `src/ai_wiki_toolkit/__init__.py`.
3. Push `main`, then create and push the release tag.
4. Watch `Release Binaries` first.
5. After it succeeds, verify:
   - GitHub Release assets exist
   - `homebrew-tap` received the updated formula
   - npm publish status is correct for the current rollout stage

## Release Failure Triage

1. Identify the failing job before changing code.
2. If only `windows-x64` fails during tests, first suspect newline or path assumptions.
3. If a workflow fails immediately with zero useful jobs, first suspect GitHub Actions parsing or expression issues.
4. After fixing a release workflow issue, re-tag only after the fix is on `main`.
