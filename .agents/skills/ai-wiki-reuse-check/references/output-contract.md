# Output Contract

Use the AI wiki footer as the user-facing evidence surface.

Choose exactly one reuse evidence status line:

- `AI Wiki Reuse Evidence: wiki_used`
- `AI Wiki Reuse Evidence: no_wiki_use`

Also print:

- `AI Wiki Eligibility: eligible | optional | not_applicable`

If the result is `wiki_used`, also print:

- `AI Wiki Reuse Docs: <comma-separated doc ids>`

When relevant, also print:

- `AI Wiki Material Effects: <comma-separated effects or none>`
- `AI Wiki Missed Memory: none known | <short note>`

## Examples

No AI wiki docs were used:

```text
AI Wiki Reuse Evidence: no_wiki_use
AI Wiki Eligibility: not_applicable
AI Wiki Missed Memory: none known
```

AI wiki docs were used:

```text
AI Wiki Reuse Evidence: wiki_used
AI Wiki Eligibility: eligible
AI Wiki Reuse Docs: workflows, review-patterns/shared-prompt-files-must-be-user-agnostic
AI Wiki Material Effects: changed_plan, reused_convention
AI Wiki Missed Memory: none known
```
