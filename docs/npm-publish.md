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

The npm workflow uses the `workflow_run` event and runs only after:

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

No npm token secret is required when trusted publishing is configured correctly.

## Workflow Behavior

The workflow:

1. checks out the exact commit released by `Release Binaries`
2. sets up Python 3.11 and Node.js 24
3. downloads the matching GitHub Release archives
4. stages the platform npm packages from those archives
5. publishes the platform npm packages
6. runs `npm pack --dry-run --ignore-scripts` for the meta package
7. runs `npm publish --provenance --ignore-scripts` for the meta package

Before enabling `NPM_PUBLISH_ENABLED`, make sure the npm platform target map only advertises targets that the `Release Binaries` workflow actually publishes.

The meta package is published from `package.json` in this repository, so its version must stay in sync with:

- `package.json`
- `pyproject.toml`
- `src/ai_wiki_toolkit/__init__.py`

The platform package versions are generated from that same root version and must be published before the meta package for the same release.

## Optional Token-Based Fallback

This repository currently documents and implements the trusted publishing path first.

If you later decide to publish with a traditional npm token instead, you can add a token-based variant, but the recommended approach is to keep trusted publishing and avoid long-lived publish secrets.
