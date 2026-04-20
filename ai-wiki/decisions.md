# Project Decisions

Capture durable architectural and process decisions here.

## AI Wiki Core Docs Stay User-Owned

Do not treat `ai-wiki/constraints.md`, `ai-wiki/workflows.md`, or `ai-wiki/decisions.md` like prompt files with mixed managed and user-customized blocks.

Those files are actively edited by the team, so putting package-managed and user-managed regions in the same file would blur ownership and still leave frequent merge pressure in the exact files people are collaborating on.

If the toolkit later needs evolvable baseline guidance for those areas, prefer separate managed companion docs under `_toolkit/` plus user-owned overlay docs in the existing top-level paths.

That preserves the current no-touch compatibility contract for user-owned AI wiki docs while still leaving room for package-managed defaults to evolve independently.

## 2026-04-20 - Keep Repo-Owned AI Wiki Indexes Out Of Package Upgrade Surfaces

Treat `ai-wiki/index.md` as a repo-owned map, not as a package-managed upgrade surface.

Package-versioned start-of-task routing belongs in `ai-wiki/_toolkit/system.md`, where the toolkit can refresh it without creating churn in user-owned repo docs.

Why:

- user-owned AI wiki docs should not require routine rewrites when the package evolves
- managed docs are the correct place for package-controlled read order and routing
- `doctor` should warn about missing starter docs and stale managed entrypoints, not compare existing repo-owned indexes against the latest starter text

Source:

- `ai-wiki/people/bochengyin/drafts/user-owned-ai-wiki-index-should-not-be-an-upgrade-surface.md`
- PR #13 `Move managed routing to _toolkit system doc`
