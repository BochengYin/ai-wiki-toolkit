# Homebrew Tap Plan

This repository does not publish directly to Homebrew yet. Instead, it now generates a versioned formula file from the GitHub Release assets.

## Intended Tap Layout

Homebrew recommends using a separate tap repository whose name starts with `homebrew-`, for example:

- `your-org/homebrew-tap`

The formula for this project should live at:

- `Formula/aiwiki-toolkit.rb`

Reference:

- [How to Create and Maintain a Tap](https://docs.brew.sh/How-to-Create-and-Maintain-a-Tap)

## Formula Source Of Truth

The generated formula consumes the GitHub Release archives produced by the main repository release workflow.

It selects among these release assets:

- `ai-wiki-toolkit-vX.Y.Z-macos-arm64.tar.gz`
- `ai-wiki-toolkit-vX.Y.Z-macos-x64.tar.gz`
- `ai-wiki-toolkit-vX.Y.Z-linux-x64.tar.gz`

The formula installs the extracted `aiwiki-toolkit` executable into Homebrew’s `bin`.

## Release Workflow Integration

The `Release Binaries` workflow now generates:

1. the platform release archives
2. a Homebrew formula file at `release-assets/aiwiki-toolkit.rb`

That formula file can be copied into the tap repository and committed there.

## Manual Tap Update

After a tagged release completes:

1. Download the generated `aiwiki-toolkit.rb` file from the GitHub Release assets.
2. In the tap repository, replace `Formula/aiwiki-toolkit.rb` with the generated file.
3. Commit and push the tap update.
4. Verify installation from the tap:

   ```bash
   brew tap your-org/tap
   brew install your-org/tap/aiwiki-toolkit
   aiwiki-toolkit --version
   ```

## Optional Automatic Tap Sync

The release workflow now supports an optional automatic tap update.

If you configure:

- repository secret: `HOMEBREW_TAP_PAT`
- repository variable: `HOMEBREW_TAP_REPOSITORY` (optional)

then the release workflow will:

1. check out the tap repository
2. copy the generated `Formula/aiwiki-toolkit.rb`
3. commit the change
4. push it back to the tap repository

If `HOMEBREW_TAP_REPOSITORY` is not set, the workflow defaults to:

- `<repo-owner>/homebrew-tap`

For example, if the main repository owner is `BochengYin`, the default tap repository is:

- `BochengYin/homebrew-tap`

If `HOMEBREW_TAP_PAT` is not configured, the workflow remains read-only and only uploads the generated formula as a release asset.
