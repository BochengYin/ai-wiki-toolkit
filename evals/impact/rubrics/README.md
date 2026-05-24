# Impact Eval Rubrics

Rubric JSON files let `aiwiki-toolkit eval impact run --score-policy rubric` assign audit-friendly
labels from captured first-pass artifacts.

Schema version: `impact-eval-rubric-v1`.

Each rubric contains:

- `success`: required criteria; all must match for `success`
- `partial`: optional criteria; any match can raise an otherwise failing run to `partial`
- `fail`: optional hard-failure criteria; any match forces `fail`

Supported criterion checks:

- `contains` / `not_contains` against an artifact text
- `changed_file` / `changed_file_prefix` against `result.json` changed files
- `untracked_file` / `untracked_file_prefix` against `result.json` untracked files

Supported artifacts are `workspace_diff`, `workspace_diff_stat`, `workspace_status`,
`final_message`, `result`, `changed_files`, and `untracked_files`.

Example:

```json
{
  "schema_version": "impact-eval-rubric-v1",
  "name": "example",
  "success": [
    {
      "id": "adds-test",
      "artifact": "changed_files",
      "changed_file_prefix": "tests/",
      "description": "The run adds or updates test coverage."
    }
  ],
  "partial": [],
  "fail": [
    {
      "id": "package-surface-churn",
      "artifact": "changed_files",
      "changed_file_prefix": "src/ai_wiki_toolkit/",
      "description": "The run changes package code where the rubric forbids it."
    }
  ]
}
```
