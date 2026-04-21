"""Verify a Linux release asset against older and current glibc baselines."""

from __future__ import annotations

import argparse
from pathlib import Path

from ai_wiki_toolkit.release_runtime import (
    DEFAULT_DOCKER_PLATFORM,
    DEFAULT_LINUX_RUNTIME_CHECKS,
    DEFAULT_RUNTIME_SHELL,
    parse_linux_runtime_check,
    verify_linux_runtime_asset,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run Linux runtime checks for a release archive inside Docker containers.",
    )
    parser.add_argument(
        "--asset",
        required=True,
        type=Path,
        help="Path to the Linux release archive to verify.",
    )
    parser.add_argument(
        "--check",
        action="append",
        default=[],
        help="Override runtime checks with <name>=<docker-image>. Repeat to define multiple checks.",
    )
    parser.add_argument(
        "--docker-platform",
        default=DEFAULT_DOCKER_PLATFORM,
        help="Docker platform passed to docker run. Defaults to linux/amd64.",
    )
    parser.add_argument(
        "--shell",
        default=DEFAULT_RUNTIME_SHELL,
        help="Shell binary used inside the runtime container. Defaults to bash.",
    )
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    checks = (
        tuple(parse_linux_runtime_check(value) for value in args.check)
        if args.check
        else DEFAULT_LINUX_RUNTIME_CHECKS
    )
    verify_linux_runtime_asset(
        args.asset,
        checks=checks,
        docker_platform=args.docker_platform,
        shell=args.shell,
    )


if __name__ == "__main__":
    main()
