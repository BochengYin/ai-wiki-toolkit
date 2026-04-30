`npm install -g ai-wiki-toolkit` is failing during the npm wrapper postinstall step on a supported platform.

The GitHub Release asset URL exists and returns HTTP 200, but the installer still fails with an `ENOENT` for a path like:

```text
npm/vendor/macos-arm64/download.tar.gz
```

Please debug the npm wrapper, fix the installer, and add a regression test that reproduces the failure without hitting the real GitHub Release service. Keep the npm wrapper thin: it should still consume the release artifact rather than rebuilding or reimplementing the Python CLI.
