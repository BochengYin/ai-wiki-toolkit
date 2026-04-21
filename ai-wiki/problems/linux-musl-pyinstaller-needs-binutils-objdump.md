# Linux Musl PyInstaller Needs Binutils Objdump

## Symptom

The `linux-musl-x64` release lane fails inside the Alpine baseline before the packaged binary is ready, even though the same build path works on glibc-based Linux targets.

## Cause

PyInstaller's analysis path expects `binutils`, including `objdump`, to be available in the musl container. The Alpine lane also needs to run the setup command as root so `apk add --no-cache binutils` can succeed before the build environment is created.

## Solution

Run the musl release build container with a root setup phase and install `binutils` before creating the venv, running tests, and packaging the release archive.

## Applies When

- editing the `linux-musl-x64` release lane
- changing `scripts/build_linux_release_in_container.py`
- changing `src/ai_wiki_toolkit/release_build.py`
- troubleshooting Alpine-based release builds

## Do Not Use When

- working on host-built macOS or Windows release lanes
- debugging a runtime issue after the musl archive has already been built successfully

## Related Files

- `.github/workflows/release-binaries.yml`
- `scripts/build_linux_release_in_container.py`
- `src/ai_wiki_toolkit/release_build.py`

## Source Pointer

- Commit: `c8463de` `Install binutils in musl release builds`
- Commit: `7201946` `Allow musl release setup to run as root`

## History

- 2026-04-21: The musl release lane was updated to install `binutils` and then allow that setup step to run as root in the container baseline.
