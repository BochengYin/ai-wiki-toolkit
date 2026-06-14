# Output Contract

Choose exactly one user-facing write-back status line:

- `AI Wiki Write-Back: none`
- `AI Wiki Write-Back: memory recorded`

If the outcome is `MemoryRecorded`, also print:

- `AI Wiki Write-Back Path: <path>`

## Examples

No durable lesson:

```text
AI Wiki Write-Back: none
```

Public/local trial-error memory recorded:

```text
AI Wiki Write-Back: memory recorded
AI Wiki Write-Back Path: ai-wiki/memory/<file>.md
```
