# Skill Installer GitHub Download SSL Fallback

## Trigger

Read when installing a Codex skill from GitHub with the global skill installer,
especially if `install-skill-from-github.py` fails during direct download.

## Public/Local Signal

On 2026-06-27, installing `mattpocock/skills` path
`skills/productivity/handoff` with:

`python <codex-home>/skills/.system/skill-installer/scripts/install-skill-from-github.py --repo mattpocock/skills --path skills/productivity/handoff`

failed in Python `urllib` with:

`ssl.SSLCertVerificationError: certificate verify failed: unable to get local issuer certificate`

Retrying with the installer git method succeeded:

`python <codex-home>/skills/.system/skill-installer/scripts/install-skill-from-github.py --repo mattpocock/skills --path skills/productivity/handoff --method git`

The skill was installed to `<codex-home>/skills/handoff`.

## Failed Attempt

The helper's default public GitHub direct-download path used the local Python
SSL stack and failed before falling back automatically.

## Fix Or Rule

If the direct download path fails with the certificate verification error, rerun
the same installer command with `--method git`.

Verify the installed skill with:

`sed -n '1,120p' <codex-home>/skills/<skill-name>/SKILL.md`

## Applies When

- Installing global Codex skills from GitHub.
- The installer helper fails in `urllib.request.urlopen` with certificate
  verification errors.

## Do Not Use When

- The failure is an auth/permission error for a non-public repository.
- The destination skill directory already exists; inspect before retrying.

## Related Files

- `<codex-home>/skills/.system/skill-installer/scripts/install-skill-from-github.py`
- `<codex-home>/skills/handoff/SKILL.md`

## Source Pointer

Source: local install attempt by Codex on 2026-06-27.
