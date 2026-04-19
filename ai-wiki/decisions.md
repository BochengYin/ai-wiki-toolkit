# Project Decisions

Capture durable architectural and process decisions here.

## AI Wiki Core Docs Stay User-Owned

Do not treat `ai-wiki/constraints.md`, `ai-wiki/workflows.md`, or `ai-wiki/decisions.md` like prompt files with mixed managed and user-customized blocks.

Those files are actively edited by the team, so putting package-managed and user-managed regions in the same file would blur ownership and still leave frequent merge pressure in the exact files people are collaborating on.

If the toolkit later needs evolvable baseline guidance for those areas, prefer separate managed companion docs under `_toolkit/` plus user-owned overlay docs in the existing top-level paths.

That preserves the current no-touch compatibility contract for user-owned AI wiki docs while still leaving room for package-managed defaults to evolve independently.
