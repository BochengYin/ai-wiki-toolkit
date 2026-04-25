---
title: "Windows ARM smoke version checks need full CLI output"
status: "draft"
source_kind: "release-triage"
---
# Review Draft

## Context

The Windows ARM smoke workflow had two failing paths after the public package artifacts were already present:

- release-archive smoke
- npm-installed smoke

Both failures happened during version verification rather than during asset download or archive extraction.

## Lesson

When a smoke test executes `aiwiki-toolkit --version`, compare against the command's actual user-facing output. Do not assume the CLI prints only the package metadata version.

## Applies When

- editing Windows ARM release smoke workflows
- changing CLI version output
- adding npm-installed binary smoke tests
