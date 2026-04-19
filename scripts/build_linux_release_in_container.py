"""Build the linux-x64 release archive inside a Dockerized bookworm baseline."""

from __future__ import annotations

import argparse
from pathlib import Path

from ai_wiki_toolkit.release_build import (
    DEFAULT_DOCKER_PLATFORM,
    DEFAULT_LINUX_BUILD_IMAGE,
    DEFAULT_LINUX_CONTAINER_BUILD,
    LinuxContainerBuildConfig,
    build_linux_release_archive_in_container,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build the Linux release archive inside a baseline Docker container.",
    )
    parser.add_argument(
        "--version",
        required=True,
        help="Release version or tag passed to build_release_archive.py.",
    )
    parser.add_argument(
        "--repository-root",
        type=Path,
        default=Path.cwd(),
        help="Repository root mounted into the container. Defaults to the current directory.",
    )
    parser.add_argument(
        "--image",
        default=DEFAULT_LINUX_BUILD_IMAGE,
        help="Docker image used for the Linux build baseline.",
    )
    parser.add_argument(
        "--docker-platform",
        default=DEFAULT_DOCKER_PLATFORM,
        help="Docker platform passed to docker run. Defaults to linux/amd64.",
    )
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    config = LinuxContainerBuildConfig(
        image=args.image,
        docker_platform=args.docker_platform,
        target=DEFAULT_LINUX_CONTAINER_BUILD.target,
        output_dir=DEFAULT_LINUX_CONTAINER_BUILD.output_dir,
        venv_dir=DEFAULT_LINUX_CONTAINER_BUILD.venv_dir,
        dist_dir=DEFAULT_LINUX_CONTAINER_BUILD.dist_dir,
        pyinstaller_work_dir=DEFAULT_LINUX_CONTAINER_BUILD.pyinstaller_work_dir,
        pyinstaller_spec_dir=DEFAULT_LINUX_CONTAINER_BUILD.pyinstaller_spec_dir,
    )
    build_linux_release_archive_in_container(
        args.repository_root,
        args.version,
        config=config,
    )


if __name__ == "__main__":
    main()
