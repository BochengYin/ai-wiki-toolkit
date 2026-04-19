# Output Contract

Choose exactly one reuse status line:

- `AI Wiki Reuse Check: wiki_used`
- `AI Wiki Reuse Check: no_wiki_use`

If the result is `wiki_used`, also print:

- `AI Wiki Reuse Docs: <comma-separated doc ids>`

## Examples

No AI wiki docs were used:

```text
AI Wiki Reuse Check: no_wiki_use
```

AI wiki docs were used:

```text
AI Wiki Reuse Check: wiki_used
AI Wiki Reuse Docs: workflows, review-patterns/shared-prompt-files-must-be-user-agnostic
```
