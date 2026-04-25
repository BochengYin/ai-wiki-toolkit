# Output Contract

Choose exactly one user-facing write-back status line:

- `AI Wiki Write-Back: none`
- `AI Wiki Write-Back: draft recorded`
- `AI Wiki Write-Back: promotion candidate`

If the outcome is `Draft` or `PromotionCandidate`, also print:

- `AI Wiki Write-Back Path: <path>`

## Examples

No durable lesson:

```text
AI Wiki Write-Back: none
```

Durable lesson, not yet ready for promotion:

```text
AI Wiki Write-Back: draft recorded
AI Wiki Write-Back Path: ai-wiki/people/<handle>/drafts/<file>.md
```

Ready to ask for promotion:

```text
AI Wiki Write-Back: promotion candidate
AI Wiki Write-Back Path: ai-wiki/people/<handle>/drafts/<file>.md
```
