from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from playlog import NightSession, PlayEvent, PlaylogConfig
from playlog.writers import CsvBatchWriter, JsonWriter, TxtWriter, render_per_night

FIXTURE = Path(__file__).parents[3] / "assets" / "fixtures" / "sample_play_events.json"


def load_events() -> list[PlayEvent]:
    raw = json.loads(FIXTURE.read_text())
    return [PlayEvent.model_validate(item) for item in raw]


def build_session() -> NightSession:
    return NightSession(
        app="rekordbox",
        session_id="HISTORY-001",
        night_date=datetime(2025, 11, 12, tzinfo=timezone.utc).date(),
        session_start=datetime(2025, 11, 12, 23, 10, tzinfo=timezone.utc),
        session_end=datetime(2025, 11, 12, 23, 25, tzinfo=timezone.utc),
        timeline_mode="actual",
    )


def test_json_writer_outputs_file(tmp_path: Path) -> None:
    config = PlaylogConfig(out_dir=tmp_path, timezone="UTC")
    session = build_session()
    events = load_events()
    out_path = JsonWriter(config).write(session, events)
    assert out_path.exists()
    payload = json.loads(out_path.read_text())
    assert payload["session"]["session_id"] == "HISTORY-001"
    assert len(payload["events"]) == 2


def test_txt_writer_renders_template(tmp_path: Path) -> None:
    config = PlaylogConfig(out_dir=tmp_path, timezone="UTC")
    session = build_session()
    events = load_events()
    out_path = TxtWriter(config).write(session, events)
    content = out_path.read_text()
    assert "PlayLog" in content
    assert "Tracks: 2" in content
    assert "Song A" in content


def test_csv_writer_has_all_rows(tmp_path: Path) -> None:
    config = PlaylogConfig(out_dir=tmp_path, timezone="UTC")
    session = build_session()
    events = load_events()
    out_path = CsvBatchWriter(config).write(session, events)
    lines = out_path.read_text().splitlines()
    assert lines[0].startswith("index,played_at,title")
    assert len(lines) == 3


def test_render_per_night_creates_selected_formats(tmp_path: Path) -> None:
    config = PlaylogConfig(out_dir=tmp_path, formats={"json", "txt"}, timezone="UTC")
    session = build_session()
    events = load_events()
    outputs = render_per_night(session, events, config)
    assert len(outputs) == 2
    assert outputs[0].exists()
    assert outputs[1].exists()
