from __future__ import annotations

import json
from pathlib import Path

from playlog_cli.app import app
from typer.testing import CliRunner

FIXTURES = Path(__file__).parents[3] / "assets" / "fixtures" / "serato" / "_Serato_"
runner = CliRunner()


def test_run_command_generates_serato_outputs(tmp_path: Path) -> None:
    result = runner.invoke(
        app,
        [
            "run",
            "--apps",
            "serato",
            "--serato-mode",
            "crate",
            "--serato-root",
            str(FIXTURES),
            "--out",
            str(tmp_path),
            "--formats",
            "json",
            "--tz",
            "UTC",
            "--timeline-estimate",
        ],
    )
    assert result.exit_code == 0, result.stdout
    assert '"event": "session-written"' in result.stdout

    session_path = (
        tmp_path
        / "serato"
        / "2025-05-05"
        / "History-2025-05-05-Estimate"
        / "session.json"
    )
    data = json.loads(session_path.read_text())
    assert data["session"]["timeline_mode"] == "estimated"
    assert len(data["events"]) == 2
    assert all(event["played_at"] for event in data["events"])
