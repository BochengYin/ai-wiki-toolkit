A Linux npm install smoke test exposed a runtime compatibility problem.

In a clean `node:24-bookworm` linux/amd64 container, `npm install -g ai-wiki-toolkit@0.1.7` succeeds, but running `aiwiki-toolkit --version` fails at runtime with a Python shared library / GLIBC version error.

Please update the release process so this class of Linux binary runtime compatibility issue is caught before publishing.

Keep docs and tests up to date.
