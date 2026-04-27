# npm Publish Workflow

This repository now includes an npm publishing workflow at `.github/workflows/publish-npm.yml`.

## Publishing Model

The npm publish flow uses a meta package plus platform-specific binary packages. The intended publish order is:

1. `Release Binaries` runs for a version tag such as `v0.1.0`
2. GitHub Release assets are uploaded
3. `Publish npm Package` runs after the release workflow completes successfully
4. the workflow stages one npm platform package per release target
5. the workflow publishes those platform packages first
6. the workflow publishes the `ai-wiki-toolkit` meta package last
7. npm users can install with:

   ```bash
   npm install -g ai-wiki-toolkit
   ```

## Trigger

The npm workflow has two entrypoints:

- automatic `workflow_run` after `Release Binaries`
- manual `workflow_dispatch` for bootstrap or recovery publishes

Manual recovery publishes also accept `npm_auth_mode`:

- `auto`: use `NPM_PUBLISH_TOKEN` when present, otherwise use trusted publishing
- `trusted`: ignore `NPM_PUBLISH_TOKEN` and publish with GitHub Actions OIDC provenance
- `token`: require `NPM_PUBLISH_TOKEN` and publish with token auth

The automatic path runs only after:

- the `Release Binaries` workflow completes
- the conclusion is `success`
- the repository variable `NPM_PUBLISH_ENABLED` is set to `true`

## Recommended Authentication: Trusted Publishing

The recommended setup is npm trusted publishing with GitHub Actions OIDC.

References:

- [Publishing Node.js packages](https://docs.github.com/en/actions/tutorials/publishing-packages/publishing-nodejs-packages)
- [Trusted publishing for npm packages](https://docs.npmjs.com/trusted-publishers)

### npm-side setup

On npmjs.com, open the package settings for `ai-wiki-toolkit` and add a trusted publisher for GitHub Actions with:

- Owner or organization: `BochengYin`
- Repository: `ai-wiki-toolkit`
- Workflow file: `publish-npm.yml`
- Environment name: leave empty unless you intentionally use a GitHub Actions environment

The workflow filename must match exactly.

### GitHub-side setup

Set this repository variable:

- `NPM_PUBLISH_ENABLED=true`

For the normal steady-state path, no npm token secret is required when trusted publishing is configured correctly.

For first-time package-name bootstraps or recovery publishes, you can also set:

- `NPM_PUBLISH_TOKEN`

When that secret is present, the automatic path falls back to token-based `npm publish` instead of relying on trusted publishing. For manual recovery publishes, choose `npm_auth_mode=trusted` to ignore a stale or expired token without deleting the secret.

## Workflow Behavior

The workflow:

1. checks out the exact commit released by `Release Binaries`
2. sets up Python 3.11 and Node.js 24
3. resolves the release tag from package metadata
4. selects npm publish auth mode:
   - automatic publish uses token auth when `NPM_PUBLISH_TOKEN` is present, otherwise trusted publishing
   - manual recovery publish can force `auto`, `trusted`, or `token`
5. downloads the matching GitHub Release archives
6. stages the platform npm packages from those archives
7. publishes the platform npm packages
8. runs `npm pack --dry-run --ignore-scripts` for the meta package
9. publishes the meta package when requested

Recovery publishes are idempotent: if a platform package or the meta package already exists for the requested version, the workflow skips that package and continues with the remaining publish steps.

Before enabling `NPM_PUBLISH_ENABLED`, make sure the npm platform target map only advertises targets that the `Release Binaries` workflow actually publishes, including any Linux `libc` split such as glibc versus musl.

The meta package is published from `package.json` in this repository, so its version must stay in sync with:

- `package.json`
- `pyproject.toml`
- `src/ai_wiki_toolkit/__init__.py`

The platform package versions are generated from that same root version and must be published before the meta package for the same release.

## Optional Token-Based Fallback

This repository keeps trusted publishing as the default path, but now also includes a token-based fallback for bootstrap publishes.

Recommended use:

1. Use trusted publishing for the steady-state release train.
2. Use `workflow_dispatch` plus `NPM_PUBLISH_TOKEN` when you introduce brand-new package names and need a bootstrap publish path.
3. Use `workflow_dispatch` with `npm_auth_mode=trusted` when a stale token blocks an otherwise normal release.
4. After the bootstrap publish succeeds, return to the default trusted-publishing path when possible.
