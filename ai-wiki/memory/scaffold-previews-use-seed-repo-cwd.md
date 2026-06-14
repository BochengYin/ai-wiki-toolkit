# Run scaffold previews from the seed repo cwd

## Trigger

Previewing or installing an ai-wiki-toolkit scaffold into a synthetic seed repo,
fixture repo, or SWE-Chain harness setup.

## Public/Local Signal

During a local scaffold-preview recovery, the preview command was first run from
the ai-wiki-toolkit source checkout instead of the intended seed repo. Local
`git status --short` showed generated AI Wiki changes in the source checkout.

## Failed Attempt

The preview setup assumed the target path was enough, but the toolkit install
workflow also uses the current working directory as the repo context.

## Fix Or Rule

Create the seed repo first, run scaffold/install preview commands with cwd set to
that seed repo, then verify the source checkout is still clean with
`git status --short`.

## Applies When

- Recovering historical scaffold behavior.
- Building SWE-Chain or harness fixtures that seed `/app/ai-wiki`.
- Running local install previews for generated AGENTS.md or AI Wiki scaffolds.

## Do Not Use When

The explicit goal is to initialize or update the ai-wiki-toolkit source checkout
itself.

## Related Files

- `artifacts/dogfood-5c3c93d-seed-preview/`
- `logs/dogfood_seed_preview_install.log`

## Source Pointer

Public/local trial-error from the SWE-Chain 014 experiment setup.
