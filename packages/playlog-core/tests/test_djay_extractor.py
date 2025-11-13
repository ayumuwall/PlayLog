from __future__ import annotations

from pathlib import Path

from playlog import PlaylogConfig
from playlog.extractors import djay

FIXTURES = Path(__file__).parents[3] / "assets" / "fixtures" / "djay"


def test_discover_plists_returns_samples() -> None:
    plists = djay.discover_plists([FIXTURES])
    filenames = sorted(path.name for path in plists)
    assert "20251112_ClubNight.plist" in filenames
    assert "AfterHours_2025-11-13.plist" in filenames


def test_load_session_normalizes_tracks(tmp_path: Path) -> None:
    config = PlaylogConfig(out_dir=tmp_path, timezone="UTC")
    plist = FIXTURES / "20251112_ClubNight.plist"

    session, events = djay.load_session(plist, config)

    assert session.session_id == "Club Night Main Floor"
    assert session.night_date.isoformat() == "2025-11-12"
    assert session.session_start is not None
    assert len(events) == 2
    assert events[0].title == "Set Song A"
    assert events[0].deck == "A"
    assert events[0].played_at is not None


def test_load_session_handles_missing_fields(tmp_path: Path) -> None:
    config = PlaylogConfig(out_dir=tmp_path, timezone="UTC")
    plist = FIXTURES / "AfterHours_2025-11-13.plist"

    session, events = djay.load_session(plist, config)

    assert session.session_id == "After Hours Loft"
    assert session.night_date.isoformat() == "2025-11-12"
    assert len(events) == 2
    assert events[0].played_at is not None
    assert events[1].played_at is None
    assert events[0].title == "Late Groove"
