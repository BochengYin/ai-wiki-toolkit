# AI Wiki PostToolUse Codex Error Matching

- Trigger: Implementing or evaluating `PostToolUse` reminders for Codex lifecycle hooks.
- Public/Local Signal: Codex Desktop and host-runner shell tools can appear as `exec_command`, not only `Bash`.
- Failed Attempt: Matching only `^Bash$` made `PostToolUse` effectively inactive in Codex Desktop experiments. Broad output regexes such as generic `error`, `exception`, `failed`, or standalone exception class names then caused false positives when successful source reads contained text like `BuildError`, `HTTPException`, or `except ImportError:`.
- Fix Or Rule: Match both `Bash` and `exec_command`. Prefer explicit nonzero exit-code fields when available. If only raw output is available, use high-precision runtime signatures such as traceback headers, pytest failure lines, shell command-not-found messages, and CLI invalid-flag diagnostics. Do not treat ordinary source-code exception names as command failure.
- Applies When: Writing or reviewing `ai_wiki_toolkit.hooks.codex` `PostToolUse` logic, SWE-chain hook lifecycle ablations, or hook configs generated for Codex Desktop.
- Do Not Use When: The hook payload provider guarantees structured exit status and separate stdout/stderr; in that case prefer those structured fields directly.
- Related Files: `src/ai_wiki_toolkit/hooks/codex.py`, `tests/test_codex_hooks.py`, `groups/aiwiki-lifecycle-hooks/generate/task.py`
- Source Pointer: Learned during the 020 Flask hook lifecycle `UserPromptSubmit + PostToolUse + Stop` strict4 ablation after invalid partial runs exposed both missed `exec_command` matching and source-read false positives.
