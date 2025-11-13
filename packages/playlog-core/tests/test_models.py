from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest
from playlog import (
    NightSession,
    PlayEvent,
    PlaylogConfig,
    floor_by_cutoff,
    get_timezone,
    sanitize_path_component,
)
from pydantic import ValidationError

FIXTURE = Path(__file__).parents[3] / "assets" / "fixtures" / "sample_play_events.json"


def load_events() -> list[PlayEvent]:
    raw = json.loads(FIXTURE.read_text())
    return [PlayEvent.model_validate(item) for item in raw]


def test_play_event_validation_accepts_fixture() -> None:
    events = load_events()
    assert len(events) == 2
    assert events[0].title == "Song A"
    assert events[0].played_at is not None
    assert events[0].played_at.tzinfo is not None


def test_play_event_rejects_invalid_payload() -> None:
    with pytest.raises(ValidationError):
        PlayEvent(app="djay", title="", duration_sec=-1)


def test_floor_by_cutoff_midnight_logic() -> None:
    tz = get_timezone("UTC")
    dt = datetime(2025, 11, 13, 7, 30, tzinfo=timezone.utc)
    night_date = floor_by_cutoff(dt, tz=tz)
    assert str(night_date) == "2025-11-12"


def test_sanitize_path_component() -> None:
    sanitized = sanitize_path_component("HIS/<>:*?")
    assert sanitized == "HIS______"


def test_night_session_requires_session_id() -> None:
    with pytest.raises(ValidationError):
        NightSession(app="serato", session_id="  ", night_date=datetime.now(timezone.utc).date())


def test_playlog_config_normalizes_serato_mode(tmp_path: Path) -> None:
    config = PlaylogConfig(out_dir=tmp_path, serato_mode="Logs")
    assert config.serato_mode == "logs"


def test_playlog_config_rejects_invalid_serato_mode(tmp_path: Path) -> None:
    with pytest.raises(ValidationError):
        PlaylogConfig(out_dir=tmp_path, serato_mode="invalid-mode")
