from __future__ import annotations

from typer.testing import CliRunner

from ai_wiki_toolkit import __version__
from ai_wiki_toolkit.cli import app

runner = CliRunner()


def test_cli_version_flag_prints_package_version() -> None:
    result = runner.invoke(app, ["--version"])

    assert result.exit_code == 0
    assert result.output.splitlines() == [f"ai-wiki-toolkit {__version__}"]
