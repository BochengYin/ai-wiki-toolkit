# ai-wiki-toolkit

`ai-wiki-toolkit` is a repository-native memory harness for coding agents.

It gives agents a durable, reviewable place to read project memory from and write reusable lessons
back to, so future sessions do not keep rediscovering the same repo-specific rules, mistakes, and
workflow details.

The core idea is simple: keep agent memory in Markdown files next to the code, wire the repo prompt
so agents know how to use it, and record whether memory actually helped during real work.

## Why This Exists

Coding agents often repeat the same trial-and-error loops:

- repo conventions live in chats, review comments, and individual memory
- previous release mistakes and debugging fixes are rediscovered instead of reused
- ad hoc RAG or file uploads answer one question but do not maintain project memory
- shared prompt files drift when multiple people and agents edit them

`ai-wiki-toolkit` turns that scattered knowledge into a repo-local memory workflow. The goal is not
to replace the agent. The goal is to give Claude Code, Codex, and similar coding agents a stable
project memory layer they can consult before acting and update after learning something durable.

It is inspired by Andrej Karpathy's LLM Wiki idea: a persistent Markdown knowledge base that an
agent can keep organized over time instead of starting from scratch on every task.

- Karpathy's X post: https://x.com/karpathy/status/2039805659525644595
- Karpathy's gist: https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f

## What You Get

- A repo-local `ai-wiki/` tree with a bounded `memory/index.md` entrypoint plus compatibility
  areas for constraints, conventions, decisions, workflows, problems, features, trails, work state,
  metrics, and personal drafts.
- A home-level `~/ai-wiki/system/` namespace for cross-project memory.
- A managed prompt block in `AGENTS.md` by default, with compatibility for existing `AGENT.md`
  or `CLAUDE.md` files.
- A bounded memory workflow: read `ai-wiki/memory/index.md` first, open at most one strongly
  relevant memory file, and avoid dumping the whole wiki into every task.
- Repo-local skills for clarify-before-code, reuse evidence, write-back checks, review-learning
  capture, and draft consolidation.
- A no-router default path: agents use the memory index and their own retrieval judgment, then
  write durable public/local lessons from the main task thread.
- Optional `aiwiki-toolkit route` diagnostics for inspecting memory selection quality when you are
  deliberately tuning or debugging routing behavior.
- Local telemetry and reports that show which memory was reused, where routing was noisy, and which
  drafts may deserve human review.
- An impact-eval harness for replaying historical repo failures with and without ambient AI wiki
  memory.

This is deliberately file-based. It does not require a server, vector database, embeddings service,
or hidden agent state.

## Why Believe This?

The current public evidence is a set of dogfooded case studies, not a statistically powered
benchmark.

I replayed five real historical problems from building `ai-wiki-toolkit` itself. Each family
compared a fresh agent run with no AI wiki workflow against a fresh agent run using the normal
ambient AI wiki workflow. The task prompt did not point at the target memory or provide the expected
solution.

Aggregate primary comparison:

- 4 of 5 families directionally favored the ambient AI wiki workflow.
- 1 of 5 families was neutral.
- 0 of 5 families favored the no-AI-wiki workflow.

| family | historical problem | no AI wiki | ambient AI wiki | artifact |
| --- | --- | --- | --- | --- |
| `ownership_boundary` | Would the agent put a contributor-only PR helper into package code instead of repo-local workflow code? | fail | success | [notes](evals/impact/notes/manual_v2_cli_original_ownership_20260425_findings.md) |
| `release_distribution_integrity` | Would the agent keep release assets, npm metadata, runtime target maps, docs, and smoke checks aligned? | partial | success | [notes](evals/impact/notes/manual_v2_cli_original_release_distribution_20260425_findings.md) |
| `windows_arm_smoke_cli_output` | Would the agent compare Windows ARM smoke output against the full CLI version string? | success | success | [notes](evals/impact/notes/manual_v2_cli_original_windows_arm_20260425_findings.md) |
| `release_runtime_compatibility` | Would the agent catch Linux binary runtime compatibility before publishing, instead of only checking install success? | partial | success | [notes](evals/impact/notes/manual_v2_cli_original_release_runtime_20260425_findings.md) |
| `scaffold_prompt_workflow_compliance` | Would the agent keep scaffold names, prompt routing, docs, and tests aligned with the repo memory workflow? | partial | success | [notes](evals/impact/notes/manual_v2_cli_original_scaffold_prompt_workflow_20260425_findings.md) |

The conservative claim is that repo-visible AI memory helped fresh agents avoid repeated historical
mistakes in this pilot suite, especially around ownership boundaries, release hazards, runtime
verification, and scaffold workflow discipline.

The caveats matter: this is one repository, the memories were written from the same project's
history, and the result should be read as artifact-backed case-study evidence rather than a general
success-rate estimate. The full pilot write-up is in
[evals/impact/public/ai_wiki_impact_eval_pilot.md](evals/impact/public/ai_wiki_impact_eval_pilot.md).

The current default workflow is also informed by the Flask SWE-Chain no-router dogfood run. In that
case study, the no-router setup completed the full Flask `2.0.0 -> 2.3.3` chain and matched the
strongest prior Build+fix F1 band without a separate router or forked writeback session. See
[evals/impact/public/flask_swe_chain_dogfood_no_router_report.md](evals/impact/public/flask_swe_chain_dogfood_no_router_report.md).

## Quickstart

Install the CLI, enter a git repository, then run `install`.

### Homebrew

```bash
brew install BochengYin/tap/aiwiki-toolkit
cd /path/to/your/repo
aiwiki-toolkit install
```

### npm

```bash
npm install -g ai-wiki-toolkit
cd /path/to/your/repo
aiwiki-toolkit install
```

The npm package is a thin meta package that installs the matching platform-specific binary package.
It does not run install-time download scripts, so `npm install -g ai-wiki-toolkit --ignore-scripts`
is compatible with the package topology.

### Local Development

```bash
python -m pip install -e ".[dev]"
cd /path/to/your/repo
aiwiki-toolkit install
```

The tool works best when `git user.name` and `git user.email` are configured. If no handle can be
detected, `install` prompts for a stable local team ID or accepts `--handle your-handle`.

## How It Works

The normal agent workflow is:

1. `aiwiki-toolkit install` creates the repo-local wiki, managed prompt block, repo-local skills,
   local identity file, and generated toolkit layer.
2. At task start, the managed `AGENTS.md` block performs one cheap local check for
   `ai-wiki/_toolkit/system.md`.
3. If AI Wiki is enabled, the agent follows the bounded read workflow: read
   `ai-wiki/memory/index.md` when present, then open at most one strongly relevant linked memory
   file.
4. The agent works normally. No router or forked writeback session is required for the default path.
5. At task end, the same task thread records which user-owned memory was actually consulted, prints
   reuse evidence, and writes back only to `ai-wiki/memory/` when there was a durable public/local
   trial-error signal or reusable clarification.

Markdown remains the source of truth. Metrics, diagnostics, route packets, and reports are generated
views that help humans audit whether the workflow is working.

## What Gets Created

Inside the repo:

```text
ai-wiki/
  index.md
  constraints.md
  conventions/
  decisions.md
  features/
  memory/index.md
  metrics/
  people/<handle>/drafts/
  problems/
  review-patterns/
  trails/
  work/
  workflows.md
  _toolkit/
.agents/skills/ai-wiki-*/
.env.aiwiki
AGENTS.md managed block (or an existing AGENT.md / CLAUDE.md)
```

At home scope:

```text
~/ai-wiki/system/
  index.md
  _toolkit/
```

`repo/ai-wiki/` is for project-specific memory. `~/ai-wiki/system/` is for reusable cross-project
memory.

## Safety Model

The compatibility boundary is intentionally strict:

- User-owned Markdown under `ai-wiki/` is stable project data.
- `install` creates missing starter files but does not overwrite existing user-owned wiki docs.
- Package-managed writes are limited to `ai-wiki/_toolkit/**`,
  `~/ai-wiki/system/_toolkit/**`, managed prompt blocks, `.gitignore` managed blocks,
  package-owned `.agents/skills/ai-wiki-*`, and the namespaced `aiwikiToolkit` key in
  `opencode.json`.
- Routine local telemetry is sharded by handle and gitignored by default.
- Generated metrics, work views, diagnostics, reports, eval views, and consolidation queues are
  regenerated under `_toolkit/**`.
- Uninstall preserves user-owned `ai-wiki/**/*.md` and `~/ai-wiki/system/**/*.md` by default.

Prompt files are updated only inside:

```md
<!-- aiwiki-toolkit:start -->
<!-- aiwiki-toolkit:end -->
```

## Core Commands

```bash
# Install or refresh the managed layer in the current git repo.
aiwiki-toolkit install

# Optional: generate a diagnostic context packet when tuning or debugging memory selection.
aiwiki-toolkit route --task "fix the failing release smoke test"

# Check starter docs, managed prompt blocks, local state, and rule drift.
aiwiki-toolkit doctor --strict

# Append one document-level reuse observation.
aiwiki-toolkit record-reuse \
  --doc-id problems/retry-loop \
  --task-id followup-using-memory \
  --retrieval-mode lookup \
  --evidence-mode explicit \
  --reuse-outcome resolved \
  --reuse-effect avoided_retry

# Record that a completed task checked AI wiki reuse.
aiwiki-toolkit record-reuse-check \
  --task-id followup-using-memory \
  --check-outcome wiki_used

# Inspect memory quality from local evidence.
aiwiki-toolkit diagnose memory
aiwiki-toolkit diagnose memory --focus route

# Generate a local repo evaluation and improvement advisor report.
aiwiki-toolkit evaluate repo --since 30d

# Generate a local usefulness report.
aiwiki-toolkit report usefulness --handle your-handle

# Generate a human-reviewable weekly queue.
aiwiki-toolkit report weekly --handle your-handle

# Inspect impact-eval families and captured runs.
aiwiki-toolkit eval impact families
aiwiki-toolkit eval impact report --run-dir /path/to/eval-run
```

See [docs/usage.md](docs/usage.md) for the longer command guide.

`aiwiki-toolkit evaluate repo --since 30d` is a local operator report for reviewing workflow
coverage, route quality, memory quality, draft queues, impact-eval readiness, and asset-selection
opportunities. It is report-only and human-review-first; it is not a public benchmark proof.

## Documentation

- [Detailed usage and command guide](docs/usage.md)
- [Impact eval pilot](evals/impact/public/ai_wiki_impact_eval_pilot.md)
- [Impact eval reports](evals/impact/reports/README.md)
- [Releasing](docs/releasing.md)
- [Homebrew tap](docs/homebrew-tap.md)
- [npm wrapper](docs/npm-wrapper.md)
- [npm publishing](docs/npm-publish.md)
- [Usefulness metrics v2](docs/ai-wiki-usefulness-metrics-v2.md)

## Compatibility And Distribution

The public distribution model is:

- GitHub Releases are the source of truth for versioned release binaries.
- Homebrew tap `BochengYin/tap` consumes those release assets for macOS and Linux users.
- npm package `ai-wiki-toolkit` is a meta package that depends on platform-specific npm binary
  packages for macOS, Linux, and Windows users who prefer `npm install -g`.
- `python -m pip install -e ".[dev]"` remains the simplest contributor setup inside this repo.

For npm installs, use npm itself to update both the meta package and the matching platform binary:

```bash
npm update -g ai-wiki-toolkit
```

`aiwiki-toolkit` does not implement a self-update command. The package manager remains the source of
truth for install and upgrade state.

Release history is tracked in [CHANGELOG.md](CHANGELOG.md).

## Path Examples

The repo-local wiki is always:

```text
ai-wiki/
```

The home-level system wiki resolves from the current user's home directory:

```text
macOS:   /Users/<username>/ai-wiki/system
Linux:   /home/<username>/ai-wiki/system
Windows: C:\Users\<username>\ai-wiki\system
```

In Python terms, the path comes from `Path.home() / "ai-wiki" / "system"`, so it follows the current
platform automatically.
