"""Extractor for Algoriddim djay Set history (.plist) files."""
from __future__ import annotations

import plistlib
import re
import sys
from collections.abc import Iterable, Iterator, Sequence
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from ..models import (
    NightSession,
    PlayEvent,
    PlaylogConfig,
    floor_by_cutoff,
    get_timezone,
)

DEFAULT_MAC_SETS = Path.home() / "Music" / "djay" / "History" / "Sets"
DEFAULT_WIN_SETS = Path.home() / "Music" / "djay" / "History" / "Sets"

TRACK_LIST_KEYS = {
    "History Tracks",
    "HistoryTracks",
    "Tracks",
    "Track Entries",
    "Root",
}

TITLE_KEYS = ["Song Title", "Title", "Name", "Track Title"]
ARTIST_KEYS = ["Artist", "Song Artist"]
ALBUM_KEYS = ["Album", "Song Album"]
START_KEYS = ["Start Time", "StartTime", "Played At", "Play Time", "Date"]
END_KEYS = ["End Time", "EndTime", "Stop Time", "Date Ended"]
DECK_KEYS = ["Deck", "Deck Name", "DeckName"]
DURATION_KEYS = ["Duration", "Track Duration", "Play Duration", "Playtime"]
BPM_KEYS = ["BPM", "Tempo"]
KEY_KEYS = ["Key", "Musical Key"]
SOURCE_PATH_KEYS = ["Location", "File Path", "URI"]
TRACK_ID_KEYS = ["Persistent ID", "PersistentID", "Track ID"]

SESSION_ID_KEYS = ["History Name", "Session Name", "Name", "Title"]
SESSION_LABEL_KEYS = ["History Name", "Venue", "Comments"]
SESSION_START_KEYS = ["Date Started", "Session Start", "Start Time", "StartTime"]
SESSION_END_KEYS = ["Date Ended", "Session End", "End Time", "EndTime"]
APP_VERSION_KEYS = ["Software Version", "App Version", "Version"]

DATE_NUMERIC_PATTERN = re.compile(r"(20\d{2})(0[1-9]|1[0-2])(0[1-9]|[12]\d|3[01])")
DATE_DASH_PATTERN = re.compile(
    r"(20\d{2})[-_](0[1-9]|1[0-2])[-_](0[1-9]|[12]\d|3[01])",
)

DATETIME_FORMATS = [
    "%Y-%m-%d %H:%M:%S",
    "%Y-%m-%d %H:%M",
    "%Y/%m/%d %H:%M:%S",
    "%Y/%m/%d %H:%M",
]


PlistDict = dict[str, object]
TRACK_HINT_KEYS = set(
    ARTIST_KEYS
    + START_KEYS
    + END_KEYS
    + DECK_KEYS
    + DURATION_KEYS
    + BPM_KEYS
    + KEY_KEYS
    + SOURCE_PATH_KEYS
)


@dataclass(slots=True)
class EventPayload:
    """Intermediate representation before PlayEvent construction."""

    title: str
    artist: str
    album: str
    duration_sec: int
    deck: str | None
    bpm: float | None
    key: str | None
    source_path: str | None
    source_track_id: str | None
    played_at: datetime | None
    raw: PlistDict


def default_roots() -> list[Path]:
    """Return default djay Set directories based on OS."""

    if sys.platform == "darwin":
        return [DEFAULT_MAC_SETS]
    if sys.platform in {"win32", "cygwin"}:
        return [DEFAULT_WIN_SETS]
    # Linux (for dev/testing) mirrors mac パス構成に
    return [DEFAULT_MAC_SETS]


def discover_plists(roots: Sequence[Path] | None = None) -> list[Path]:
    """Discover djay Set .plist files from known roots."""

    candidates = list(roots) if roots is not None else default_roots()
    found: list[Path] = []
    for root in candidates:
        if not root:
            continue
        expanded = root.expanduser()
        if not expanded.exists():
            continue
        if expanded.is_file() and expanded.suffix == ".plist":
            found.append(expanded)
            continue
        found.extend(sorted(expanded.glob("*.plist")))
    return sorted({path for path in found})


def extract(
    config: PlaylogConfig,
    roots: Sequence[Path] | None = None,
) -> list[tuple[NightSession, list[PlayEvent]]]:
    """Extract sessions from all discovered .plist files."""

    sessions: list[tuple[NightSession, list[PlayEvent]]] = []
    for plist_path in discover_plists(roots):
        session, events = load_session(plist_path, config)
        sessions.append((session, events))
    return sessions


def load_session(
    plist_path: Path,
    config: PlaylogConfig,
) -> tuple[NightSession, list[PlayEvent]]:
    """Load a single djay .plist file and normalize it."""

    plist_data = _read_plist(plist_path)
    tz = get_timezone(config.timezone)

    session_id = _derive_session_id(plist_data, plist_path)
    session_label = _derive_session_label(plist_data, plist_path)
    app_version = _get_first_str(plist_data, APP_VERSION_KEYS)

    track_dicts = list(_iter_track_dicts(plist_data))
    event_payloads = [_build_event_payload(track, tz) for track in track_dicts]

    session_start = _first_datetime(plist_data, SESSION_START_KEYS, tz)
    session_end = _first_datetime(plist_data, SESSION_END_KEYS, tz)
    played_times = [payload.played_at for payload in event_payloads if payload.played_at]

    if session_start is None and played_times:
        session_start = min(played_times)
    if session_end is None and played_times:
        session_end = max(played_times)

    anchor = (
        (min(played_times) if played_times else None)
        or session_start
        or _fallback_datetime(plist_path, tz)
    )
    night_date = floor_by_cutoff(anchor, cutoff=config.cutoff, tz=tz)
    session_date = (session_start or anchor).date()

    events = [
        PlayEvent(
            app="djay",
            app_version=app_version,
            session_id=session_id,
            session_date=session_date,
            night_date=night_date,
            played_at=payload.played_at,
            title=payload.title,
            artist=payload.artist,
            album=payload.album,
            duration_sec=payload.duration_sec,
            deck=payload.deck,
            bpm=payload.bpm,
            key=payload.key,
            source_path=payload.source_path,
            source_track_id=payload.source_track_id,
            raw=payload.raw,
        )
        for payload in event_payloads
    ]

    session = NightSession(
        app="djay",
        session_id=session_id,
        night_date=night_date,
        session_label=session_label,
        app_version=app_version,
        session_start=session_start,
        session_end=session_end,
    )

    return session, events


def _read_plist(path: Path) -> PlistDict:
    with path.expanduser().open("rb") as fp:
        data: object = plistlib.load(fp)
        if not isinstance(data, dict):
            msg = f"djay plist {path} did not contain a top-level dict"
            raise ValueError(msg)
        return data


def _iter_track_dicts(node: object) -> Iterator[PlistDict]:
    if isinstance(node, list):
        for item in node:
            yield from _iter_track_dicts(item)
        return
    if isinstance(node, dict):
        if _looks_like_track(node):
            yield node
            return
        for key, value in node.items():
            if key in TRACK_LIST_KEYS:
                yield from _iter_track_dicts(value)
            elif isinstance(value, (list, dict)):
                yield from _iter_track_dicts(value)


def _looks_like_track(node: PlistDict) -> bool:
    title_present = any(key in node for key in TITLE_KEYS)
    hint_present = any(key in node for key in TRACK_HINT_KEYS)
    return title_present and hint_present


def _build_event_payload(track: PlistDict, tz: ZoneInfo) -> EventPayload:
    played_at = _first_datetime(track, START_KEYS, tz)

    return EventPayload(
        title=_get_first_str(track, TITLE_KEYS) or "Unknown Title",
        artist=_get_first_str(track, ARTIST_KEYS) or "",
        album=_get_first_str(track, ALBUM_KEYS) or "",
        duration_sec=_coerce_int(_get_first_value(track, DURATION_KEYS)),
        deck=_get_first_str(track, DECK_KEYS),
        bpm=_coerce_float(_get_first_value(track, BPM_KEYS)),
        key=_get_first_str(track, KEY_KEYS),
        source_path=_get_first_str(track, SOURCE_PATH_KEYS),
        source_track_id=_to_str(_get_first_value(track, TRACK_ID_KEYS)),
        played_at=played_at,
        raw=dict(track),
    )


def _derive_session_id(plist_data: PlistDict, plist_path: Path) -> str:
    return _get_first_str(plist_data, SESSION_ID_KEYS) or plist_path.stem


def _derive_session_label(plist_data: PlistDict, plist_path: Path) -> str:
    return _get_first_str(plist_data, SESSION_LABEL_KEYS) or plist_path.stem


def _first_datetime(
    container: PlistDict,
    keys: Iterable[str],
    tz: ZoneInfo,
) -> datetime | None:
    for key in keys:
        if key not in container:
            continue
        dt_value = _coerce_datetime(container[key], tz)
        if dt_value:
            return dt_value
    return None


def _coerce_datetime(value: object, tz: ZoneInfo) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        if value.tzinfo is None:
            return value.replace(tzinfo=tz)
        return value.astimezone(tz)
    if isinstance(value, (int, float)):
        return datetime.fromtimestamp(value, tz=tz)
    if isinstance(value, str):
        try:
            normalized = value.replace("Z", "+00:00")
            return datetime.fromisoformat(normalized)
        except ValueError:
            for fmt in DATETIME_FORMATS:
                try:
                    naive = datetime.strptime(value, fmt)
                    return naive.replace(tzinfo=tz)
                except ValueError:
                    continue
    return None


def _get_first_str(container: PlistDict, keys: Iterable[str]) -> str | None:
    for key in keys:
        value = container.get(key)
        if isinstance(value, str):
            stripped = value.strip()
            if stripped:
                return stripped
    return None


def _get_first_value(container: PlistDict, keys: Iterable[str]) -> object | None:
    for key in keys:
        if key in container:
            return container[key]
    return None


def _coerce_int(value: object | None) -> int:
    if value is None:
        return 0
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, (int, float)):
        return max(int(round(value)), 0)
    if isinstance(value, str) and value.strip():
        try:
            return max(int(float(value)), 0)
        except ValueError:
            return 0
    return 0


def _coerce_float(value: object | None) -> float | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return float(value)
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str) and value.strip():
        try:
            return float(value)
        except ValueError:
            return None
    return None


def _to_str(value: object | None) -> str | None:
    if value is None:
        return None
    if isinstance(value, str):
        stripped = value.strip()
        return stripped or None
    return str(value)


def _fallback_datetime(plist_path: Path, tz: ZoneInfo) -> datetime:
    text_hint = _parse_date_hint(plist_path.stem, tz)
    if text_hint:
        return text_hint
    try:
        return datetime.fromtimestamp(plist_path.stat().st_mtime, tz=tz)
    except FileNotFoundError:
        return datetime.now(tz)


def _parse_date_hint(name: str, tz: ZoneInfo) -> datetime | None:
    match = DATE_DASH_PATTERN.search(name)
    if match:
        year, month, day = match.groups()
        return datetime(int(year), int(month), int(day), 12, 0, tzinfo=tz)

    match = DATE_NUMERIC_PATTERN.search(name)
    if match:
        year, month, day = match.groups()
        return datetime(int(year), int(month), int(day), 12, 0, tzinfo=tz)

    return None
