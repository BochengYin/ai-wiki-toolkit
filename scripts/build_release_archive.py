"""Create a GitHub Release archive for a built binary."""

from __future__ import annotations

import argparse
import tarfile
import zipfile
from pathlib import Path

from ai_wiki_toolkit.release_artifacts import archive_extension, release_archive_path


def build_release_archive(binary_path: Path, version: str, target: str, output_dir: Path) -> Path:
    if not binary_path.exists():
        raise FileNotFoundError(f"Binary does not exist: {binary_path}")

    output_dir.mkdir(parents=True, exist_ok=True)
    archive_path = release_archive_path(output_dir, version, target)
    extension = archive_extension(target)

    if extension == "zip":
        with zipfile.ZipFile(archive_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            archive.write(binary_path, arcname=binary_path.name)
        return archive_path

    with tarfile.open(archive_path, "w:gz") as archive:
        archive.add(binary_path, arcname=binary_path.name)
    return archive_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--binary", required=True, type=Path, help="Path to the built executable.")
    parser.add_argument("--version", required=True, help="Release version, with or without leading v.")
    parser.add_argument("--target", required=True, help="Platform target label such as macos-arm64.")
    parser.add_argument(
        "--output-dir",
        required=True,
        type=Path,
        help="Directory where the release archive should be written.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    archive_path = build_release_archive(
        binary_path=args.binary,
        version=args.version,
        target=args.target,
        output_dir=args.output_dir,
    )
    print(archive_path)


if __name__ == "__main__":
    main()
