---
name: ai-wiki-release-tag
description: Use after a release-prep PR is merged when the repo is ready to create and push a semantic release tag from main.
---

# AI Wiki Release Tag

Use this skill when a release-prep PR has already merged to `main` and the user wants the release tag created and pushed without manually typing the git commands.

## Workflow

1. Confirm the requested release version, such as `0.1.12` or `v0.1.12`.
2. Make sure the release-prep PR is already merged to `main`.
3. Run the repo-local helper:

   ```bash
   uv run python scripts/pr_flow.py tag-release <version>
   ```

4. Report the pushed tag and remind the user that GitHub Release, Homebrew, and npm publish workflows are triggered by the tag.

## Important Rules

- Do not tag from a topic branch head. The helper syncs `main` before tagging.
- Do not recreate a tag that already exists locally or on `origin`.
- Let `scripts/check_release_version.py` be the version guard before creating the tag.
- If the user only wants a local dry run, use `--local-only`.

## References

- `docs/releasing.md`
- `scripts/pr_flow.py`
