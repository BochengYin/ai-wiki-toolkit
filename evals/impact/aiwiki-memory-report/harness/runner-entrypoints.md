# Runner Entrypoints

A group-level launcher wraps the Python chain runner.

Representative shape:

```bash
python -m generate.chain \
  --data "$DATA" \
  --agent "$AGENT" \
  --provider "$PROVIDER" \
  --model "$MODEL" \
  --resume
```

Optional arguments:

- `--effort <level>` for model reasoning effort.
- `--container-id <id>` to attach to an existing container and resume.
- `--max-iters <n>`, default `2`, for build plus bounded fix turns.

The launcher is group-specific. Public docs should identify it by logical run
ID and artifact registry entry, not by local absolute path.
