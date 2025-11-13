from typer.testing import CliRunner

from playlog_cli.app import app


runner = CliRunner()


def test_version_command_outputs_core_version() -> None:
    result = runner.invoke(app, ["version"])
    assert result.exit_code == 0
    assert "playlog-core" in result.stdout
