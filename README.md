# ai-wiki-toolkit

Latest SWE-Chain memory report draft:
[evals/impact/aiwiki-memory-report/report.md](evals/impact/aiwiki-memory-report/report.md).

Historical public impact reports:

- [2026-04-25: Impact eval pilot](evals/impact/public/ai_wiki_impact_eval_pilot.md)
- [2026-06-14: Flask SWE-Chain memory eval](evals/impact/public/flask_swe_chain_memory_eval_report.md)
- [2026-06-15: Flask SWE-Chain agent-skill writeback](evals/impact/public/flask_swe_chain_agent_skill_writeback_report.md)
- [2026-06-16: Flask SWE-Chain dogfood no-router](evals/impact/public/flask_swe_chain_dogfood_no_router_report.md)
- [Public materials index](evals/impact/public/README.md)

`ai-wiki-toolkit` is a repository-native memory harness for coding agents. It
creates a durable, reviewable Markdown workspace where agents can read
repo-specific memory, record whether that memory helped, and write back small
public/local lessons after real work.

The larger research question is whether repository agents can become
self-improving without relying on hidden state, broad context dumps, or
unreviewable memory. Current experiments show a mixed answer: AI Wiki-style
memory can help on some repo tasks, but it is not the best mechanism for every
repository, agent, or workflow. This project is now focused on finding the most
reliable mechanism for repo-level agent self-improvement: what should be exposed
to the agent, when memory should be written, how retrieval should be bounded,
and how to measure improvements without introducing unrelated regressions.

## Current Research Status

Early dogfood experiments on `ai-wiki-toolkit` historical failures were
encouraging: repo-visible memory helped fresh agents avoid several repeated
mistakes around ownership boundaries, release hazards, runtime checks, and
scaffold workflow discipline.

The broader SWE-Chain experiments are more nuanced. Across real repository
upgrade chains, AI Wiki variants are not uniformly better than raw or `/init`
baselines. Some mechanisms help on specific repos; others over-frame the task or
increase unrelated regressions. The current report therefore treats AI Wiki as a
candidate repo-level self-improvement layer, not as a solved product claim.
There is not yet one AI Wiki setup that is known to fit every repository. The
product is still being shaped, and the setups described below are current
working designs that may change as the experiments continue.

For the latest results and artifact structure, see:

- [SWE-Chain memory report draft](evals/impact/aiwiki-memory-report/report.md)
- [Report artifact package](evals/impact/aiwiki-memory-report/README.md)
- [Source-of-truth tables](evals/impact/aiwiki-memory-report/source-of-truth/README.md)
- [Earlier impact pilot](evals/impact/public/ai_wiki_impact_eval_pilot.md)

## What It Installs

- A repo-local `ai-wiki/` tree with bounded memory, conventions, decisions,
  problems, workflows, metrics, and work state.
- A managed prompt block in `AGENTS.md` by default, with compatibility for
  existing `AGENT.md` or `CLAUDE.md`.
- Repo-local skills for clarify-before-code, reuse evidence, write-back checks,
  review-learning capture, and draft consolidation.
- A home-level `~/ai-wiki/system/` namespace for cross-project memory.
- Local telemetry and generated reports for auditing whether memory was used
  and whether it helped.

The default path is no-router: agents read `ai-wiki/memory/index.md`, open at
most one strongly relevant memory file, work normally, and write back only small
durable lessons when there is public/local evidence worth keeping.

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

The npm package is a thin meta package that installs the matching
platform-specific binary package. It does not run install-time download scripts,
so `npm install -g ai-wiki-toolkit --ignore-scripts` is compatible with the
package topology.

### Local Development

```bash
python -m pip install -e ".[dev]"
cd /path/to/your/repo
aiwiki-toolkit install
```

The tool works best when `git user.name` and `git user.email` are configured.
If no handle can be detected, `install` prompts for a stable local team ID or
accepts `--handle your-handle`.

## How It Works

1. `aiwiki-toolkit install` creates the repo-local wiki, managed prompt block,
   repo-local skills, local identity file, and generated toolkit layer.
2. At task start, the managed prompt block performs one cheap local check for
   `ai-wiki/_toolkit/system.md`.
3. If AI Wiki is enabled, the agent follows the bounded read workflow: read
   `ai-wiki/memory/index.md` when present, then open at most one strongly
   relevant linked memory file.
4. The agent works normally. No router or forked writeback session is required
   for the default path.
5. At task end, the same task thread records which user-owned memory was
   consulted, prints reuse evidence, and writes back only to `ai-wiki/memory/`
   when there was a durable public/local trial-error signal or reusable
   clarification.

Markdown remains the source of truth. Metrics, diagnostics, route packets, and
reports are generated views that help humans audit whether the workflow is
working.

## Created Files

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
AGENTS.md managed block (or existing AGENT.md / CLAUDE.md)
```

At home scope:

```text
~/ai-wiki/system/
  index.md
  _toolkit/
```

`repo/ai-wiki/` is for project-specific memory. `~/ai-wiki/system/` is for
reusable cross-project memory.

## Safety Model

- User-owned Markdown under `ai-wiki/` is stable project data.
- `install` creates missing starter files but does not overwrite existing
  user-owned wiki docs.
- Package-managed writes are limited to `ai-wiki/_toolkit/**`,
  `~/ai-wiki/system/_toolkit/**`, managed prompt blocks, `.gitignore` managed
  blocks, package-owned `.agents/skills/ai-wiki-*`, and the namespaced
  `aiwikiToolkit` key in `opencode.json`.
- Routine local telemetry is sharded by handle and gitignored by default.
- Generated metrics, work views, diagnostics, reports, eval views, and
  consolidation queues are regenerated under `_toolkit/**`.
- Uninstall preserves user-owned `ai-wiki/**/*.md` and
  `~/ai-wiki/system/**/*.md` by default.

Prompt files are updated only inside:

```md
<!-- aiwiki-toolkit:start -->
<!-- aiwiki-toolkit:end -->
```

## Core Commands

```bash
# Install or refresh the managed layer in the current git repo.
aiwiki-toolkit install

# Optional diagnostic context packet for tuning or debugging memory selection.
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

# Generate local reports.
aiwiki-toolkit evaluate repo --since 30d
aiwiki-toolkit report usefulness --handle your-handle
aiwiki-toolkit report weekly --handle your-handle
```

See [docs/usage.md](docs/usage.md) for the longer command guide.

## Documentation

- [Detailed usage and command guide](docs/usage.md)
- [Latest SWE-Chain memory report draft](evals/impact/aiwiki-memory-report/report.md)
- [SWE-Chain report artifact package](evals/impact/aiwiki-memory-report/README.md)
- [Impact eval pilot](evals/impact/public/ai_wiki_impact_eval_pilot.md)
- [Impact eval reports](evals/impact/reports/README.md)
- [Releasing](docs/releasing.md)
- [Homebrew tap](docs/homebrew-tap.md)
- [npm wrapper](docs/npm-wrapper.md)
- [npm publishing](docs/npm-publish.md)
- [Usefulness metrics v2](docs/ai-wiki-usefulness-metrics-v2.md)

## Distribution

- GitHub Releases are the source of truth for versioned release binaries.
- Homebrew tap `BochengYin/tap` consumes release assets for macOS and Linux.
- npm package `ai-wiki-toolkit` is a meta package that depends on
  platform-specific npm binary packages for macOS, Linux, and Windows.
- `python -m pip install -e ".[dev]"` remains the simplest contributor setup
  inside this repo.

For npm installs, use npm to update both the meta package and matching platform
binary:

```bash
npm update -g ai-wiki-toolkit
```

`aiwiki-toolkit` does not implement a self-update command. The package manager
remains the source of truth for install and upgrade state.

Release history is tracked in [CHANGELOG.md](CHANGELOG.md).
