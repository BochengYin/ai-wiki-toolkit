# Output Contract

Use the AI wiki footer as the user-facing evidence surface.

Choose exactly one user-facing reuse status line:

- `AI Wiki Reuse: user-owned memory used`
- `AI Wiki Reuse: no user-owned memory used`

Also print:

- `AI Wiki Task Relevance: relevant | optional | not_relevant`

If user-owned memory was used, also print:

- `AI Wiki Docs Used: <comma-separated doc ids>`

When relevant, also print:

- `AI Wiki Impact: <short user-facing impacts or none>`
- `AI Wiki Missed Memory: none known | <short note>`

## Examples

No AI wiki docs were needed for an operational task:

```text
AI Wiki Reuse: no user-owned memory used
AI Wiki Task Relevance: not_relevant
AI Wiki Missed Memory: none known
```

AI wiki docs were used in a relevant task:

```text
AI Wiki Reuse: user-owned memory used
AI Wiki Task Relevance: relevant
AI Wiki Docs Used: conventions/python-typing, review-patterns/shared-prompt-files-must-be-user-agnostic
AI Wiki Impact: changed the plan, reused an existing convention
AI Wiki Missed Memory: none known
```
