from __future__ import annotations
import shutil
from pathlib import Path

from playlog import PlaylogConfig
from playlog.extractors import serato

FIXTURES = Path(__file__).parents[3] / "assets" / "fixtures" / "serato" / "_Serato_"


def _session_by_id(
    sessions: list[tuple[object, object]],
    session_id: str,
) -> tuple[object, object]:
    for session, events in sessions:
        if session.session_id == session_id:
            return session, events
    raise AssertionError(f"session {session_id} not found")


def test_crate_mode_parses_tracks(tmp_path: Path) -> None:
    config = PlaylogConfig(out_dir=tmp_path, timezone="UTC")
    sessions = serato.extract(config, root=FIXTURES, mode="crate")

    session, events = _session_by_id(sessions, "History-2025-05-01")
    assert session.night_date.isoformat() == "2025-05-01"
    assert session.timeline_mode == "actual"
    assert len(events) == 2
    assert events[0].title == "Loft Intro"
    assert events[0].played_at is not None
    assert events[1].played_at is None


def test_logs_mode_generates_play_events(tmp_path: Path) -> None:
    config = PlaylogConfig(out_dir=tmp_path, timezone="UTC")
    sessions = serato.extract(config, root=FIXTURES, mode="logs")

    session, events = _session_by_id(sessions, "2025-05-03@Loft")
    assert session.timeline_mode == "actual"
    assert len(events) == 3
    assert all(event.played_at is not None for event in events)
    assert events[0].played_at.isoformat().startswith("2025-05-03T22:47:10")


def test_auto_mode_falls_back_to_logs_when_history_missing(tmp_path: Path) -> None:
    root = tmp_path / "_Serato_"
    logs_dir = root / "Logs"
    logs_dir.mkdir(parents=True)
    shutil.copy(FIXTURES / "Logs" / "2025-05-03@Loft.log", logs_dir / "session.log")

    config = PlaylogConfig(out_dir=tmp_path, timezone="UTC")
    sessions = serato.extract(config, root=root, mode="auto")

    assert sessions
    session, _ = sessions[0]
    assert session.session_id == "session"


def test_timeline_estimate_populates_missing_times(tmp_path: Path) -> None:
    config = PlaylogConfig(out_dir=tmp_path, timezone="UTC", timeline_estimate=True)
    sessions = serato.extract(config, root=FIXTURES, mode="crate")

    session, events = _session_by_id(sessions, "History-2025-05-05-Estimate")
    assert session.timeline_mode == "estimated"
    assert all(event.played_at is not None for event in events)
