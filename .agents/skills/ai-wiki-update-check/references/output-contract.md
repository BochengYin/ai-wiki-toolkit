# Output Contract

Choose exactly one final status line:

- `AI Wiki Update Candidate: None`
- `AI Wiki Update Candidate: Draft`
- `AI Wiki Update Candidate: PromotionCandidate`

If the outcome is `Draft` or `PromotionCandidate`, also print:

- `AI Wiki Update Path: <path>`

## Examples

No durable lesson:

```text
AI Wiki Update Candidate: None
```

Durable lesson, not yet ready for promotion:

```text
AI Wiki Update Candidate: Draft
AI Wiki Update Path: ai-wiki/people/<handle>/drafts/<file>.md
```

Ready to ask for promotion:

```text
AI Wiki Update Candidate: PromotionCandidate
AI Wiki Update Path: ai-wiki/people/<handle>/drafts/<file>.md
```
