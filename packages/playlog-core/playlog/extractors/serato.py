"""Extractor for Serato DJ crate/history + logs data."""
from __future__ import annotations

import logging
import re
import sys
from dataclasses import dataclass
from datetime import datetime, time, timedelta
from pathlib import Path
from typing import Iterable, Sequence
from zoneinfo import ZoneInfo

from ..models import (
    NightSession,
    PlayEvent,
    PlaylogConfig,
    floor_by_cutoff,
    get_timezone,
    sanitize_path_component,
)

LOGGER = logging.getLogger(__name__)

DEFAULT_MAC_ROOT = Path.home() / "Music" / "_Serato_"
DEFAULT_WIN_ROOT = Path.home() / "Music" / "_Serato_"

MODE_AUTO = "auto"
MODE_CRATE = "crate"
MODE_LOGS = "logs"

DATE_IN_NAME = re.compile(r"(20\d{2})[-_](0[1-9]|1[0-2])[-_](0[1-9]|[12]\d|3[01])")
LOG_SESSION_START = re.compile(r"Session Start @ (?P<dt>.+)")
LOG_LINE = re.compile(
    r"(?P<time>\d{2}:\d{2}:\d{2})\s+"
    r"(?P<deck>Deck\s+\w+|DECK\s+\w+)\s+"
    r"(?P<body>.+)"
)


class SeratoExtractorError(RuntimeError):
    """Raised when Serato extraction cannot proceed."""


@dataclass(slots=True)
class TrackPayload:
    """Intermediate payload before PlayEvent creation."""

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
    raw: dict[str, str] | None


def extract(
    config: PlaylogConfig,
    *,
    root: Path | None = None,
    mode: str | None = None,
) -> list[tuple[NightSession, list[PlayEvent]]]:
    """Extract Serato sessions from crate or log sources."""

    selected_mode = (mode or config.serato_mode or MODE_AUTO).lower()
    if selected_mode not in {MODE_AUTO, MODE_CRATE, MODE_LOGS}:
        msg = f"serato extractor mode must be one of {MODE_AUTO}/{MODE_CRATE}/{MODE_LOGS}"
        raise ValueError(msg)

    root_path = _resolve_root(root or config.serato_root)
    if root_path is None:
        LOGGER.info("serato-root-not-found", extra={"component": "serato"})
        return []

    tz = get_timezone(config.timezone)

    if selected_mode in {MODE_AUTO, MODE_CRATE}:
        try:
            crate_sessions = _extract_from_crates(root_path, config, tz)
            if crate_sessions or selected_mode == MODE_CRATE:
                LOGGER.info(
                    "serato-mode-selected",
                    extra={"component": "serato", "mode": "crate", "sessions": len(crate_sessions)},
                )
                return crate_sessions
        except SeratoExtractorError as exc:
            if selected_mode == MODE_CRATE:
                raise
            LOGGER.error("serato-crate-failed", exc_info=exc, extra={"component": "serato"})

    if selected_mode in {MODE_AUTO, MODE_LOGS}:
        log_sessions = _extract_from_logs(root_path, config, tz)
        LOGGER.info(
            "serato-mode-selected",
            extra={"component": "serato", "mode": "logs", "sessions": len(log_sessions)},
        )
        return log_sessions

    return []


def default_roots() -> list[Path]:
    """Return Serato default roots for the host OS."""

    if sys.platform == "darwin":
        return [DEFAULT_MAC_ROOT]
    if sys.platform in {"win32", "cygwin"}:
        return [DEFAULT_WIN_ROOT]
    # Linux/dev 環境は macOS と同じ配置に倣う
    return [DEFAULT_MAC_ROOT]


def _resolve_root(candidate: Path | None) -> Path | None:
    if candidate is not None:
        expanded = candidate.expanduser()
        if expanded.exists():
            return expanded
    for root in default_roots():
        expanded = root.expanduser()
        if expanded.exists():
            return expanded
    return None


def _extract_from_crates(
    root: Path,
    config: PlaylogConfig,
    tz: ZoneInfo,
) -> list[tuple[NightSession, list[PlayEvent]]]:
    history_dir = root / "History"
    if not history_dir.exists():
        if config.serato_mode == MODE_CRATE:
            msg = "Serato History directory not found"
            raise SeratoExtractorError(msg)
        return []

    sessions: list[tuple[NightSession, list[PlayEvent]]] = []
    for crate_path in sorted(history_dir.glob("*.crate")):
        payloads = _parse_crate(crate_path, tz)
        if not payloads:
            continue
        session = _build_session_from_payloads(
            config=config,
            tz=tz,
            session_label=_session_label_from_path(crate_path),
            payloads=payloads,
            anchor_hint=_anchor_from_filename(crate_path, tz),
        )
        sessions.append(session)
    return sessions


def _parse_crate(crate_path: Path, tz: ZoneInfo) -> list[TrackPayload]:
    data = crate_path.read_bytes()
    offset = 0
    payloads: list[TrackPayload] = []
    while offset + 8 <= len(data):
        tag = data[offset : offset + 4].decode("ascii", errors="ignore")
        length = int.from_bytes(data[offset + 4 : offset + 8], "big")
        payload = data[offset + 8 : offset + 8 + length]
        offset += 8 + length
        if tag == "otrk":
            payloads.append(_track_from_chunk(payload, tz))
    return payloads


def _track_from_chunk(chunk: bytes, tz: ZoneInfo) -> TrackPayload:
    fields: dict[str, bytes] = {}
    raw: dict[str, str] = {}
    offset = 0
    while offset + 8 <= len(chunk):
        tag = chunk[offset : offset + 4].decode("ascii", errors="ignore")
        length = int.from_bytes(chunk[offset + 4 : offset + 8], "big")
        payload = chunk[offset + 8 : offset + 8 + length]
        offset += 8 + length
        fields[tag] = payload
        raw[tag] = _decode_text(payload)

    title = _decode_text(fields.get("ttxt", b"")).strip() or "Unknown Track"
    artist = _decode_text(fields.get("aART", b"")).strip()
    album = _decode_text(fields.get("albm", b"")).strip()
    deck = _decode_text(fields.get("deck", b"")).strip() or None
    bpm = _decode_float(fields.get("bpmf"))
    duration = _decode_int(fields.get("dura"))
    key = _decode_text(fields.get("key", b"")).strip() or None
    source_path = _decode_text(fields.get("path", b"")).strip() or None
    track_id = _decode_text(fields.get("pidx", b"")).strip() or None
    played_at = _decode_datetime(fields.get("pdat"), tz)

    return TrackPayload(
        title=title,
        artist=artist,
        album=album,
        duration_sec=max(duration, 0),
        deck=deck,
        bpm=bpm,
        key=key,
        source_path=source_path,
        source_track_id=track_id,
        played_at=played_at,
        raw=raw or None,
    )


def _extract_from_logs(
    root: Path,
    config: PlaylogConfig,
    tz: ZoneInfo,
) -> list[tuple[NightSession, list[PlayEvent]]]:
    logs_dir = root / "Logs"
    if not logs_dir.exists():
        if config.serato_mode == MODE_LOGS:
            msg = "Serato Logs directory not found"
            raise SeratoExtractorError(msg)
        return []

    sessions: list[tuple[NightSession, list[PlayEvent]]] = []
    for log_path in sorted(logs_dir.glob("*.log")) + sorted(logs_dir.glob("*.txt")):
        session = _parse_log(log_path, config, tz)
        if session:
            sessions.append(session)
    return sessions


def _parse_log(
    log_path: Path,
    config: PlaylogConfig,
    tz: ZoneInfo,
) -> tuple[NightSession, list[PlayEvent]] | None:
    lines = log_path.read_text(encoding="utf-8").splitlines()
    base_dt = _session_start_from_log(lines, tz) or _anchor_from_filename(log_path, tz)
    session_label = _session_label_from_path(log_path)
    session_id = session_label

    events: list[PlayEvent] = []
    last_dt: datetime | None = None
    current_date = base_dt.date()

    for line in lines:
        match = LOG_LINE.match(line.strip())
        if not match:
            continue
        played_time = _parse_time(match.group("time"))
        played_dt = datetime.combine(current_date, played_time, tzinfo=tz)
        if last_dt and played_dt < last_dt:
            played_dt += timedelta(days=1)
            current_date = played_dt.date()
        body = match.group("body").strip()
        artist, title = _split_artist_title(body)
        deck = match.group("deck").strip()
        events.append(
            PlayEvent(
                app="serato",
                app_version=None,
                session_id=session_id,
                session_date=played_dt.date(),
                night_date=floor_by_cutoff(played_dt, config.cutoff, tz),
                played_at=played_dt,
                title=title,
                artist=artist,
                album="",
                duration_sec=0,
                deck=deck,
                bpm=None,
                key=None,
                source_path=None,
                source_track_id=None,
                raw={"line": line.strip()},
            ),
        )
        last_dt = played_dt

    if not events:
        return None

    session_start = events[0].played_at
    session_end = events[-1].played_at
    night_date = events[0].night_date or floor_by_cutoff(base_dt, config.cutoff, tz)

    session = NightSession(
        app="serato",
        session_id=session_id,
        night_date=night_date,
        session_label=session_label,
        app_version=None,
        session_start=session_start,
        session_end=session_end,
        timeline_mode="actual",
    )
    return session, events


def _build_session_from_payloads(
    *,
    config: PlaylogConfig,
    tz: ZoneInfo,
    session_label: str,
    payloads: list[TrackPayload],
    anchor_hint: datetime,
) -> tuple[NightSession, list[PlayEvent]]:
    session_id = sanitize_path_component(session_label)
    timeline_mode = "actual"

    if config.timeline_estimate and not any(payload.played_at for payload in payloads):
        _estimate_timeline(payloads, anchor_hint)
        timeline_mode = "estimated"

    played_times = [payload.played_at for payload in payloads if payload.played_at]
    anchor = (min(played_times) if played_times else anchor_hint)
    night_date = floor_by_cutoff(anchor, config.cutoff, tz)
    session_start = min(played_times) if played_times else anchor
    session_end = max(played_times) if played_times else anchor

    events = [
        PlayEvent(
            app="serato",
            app_version=None,
            session_id=session_id,
            session_date=(payload.played_at or anchor).date(),
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
        for payload in payloads
    ]

    session = NightSession(
        app="serato",
        session_id=session_id,
        night_date=night_date,
        session_label=session_label,
        app_version=None,
        session_start=session_start,
        session_end=session_end,
        timeline_mode=timeline_mode,
    )

    return session, events


def _estimate_timeline(payloads: Sequence[TrackPayload], anchor: datetime) -> None:
    current = anchor
    for payload in payloads:
        payload.played_at = current
        duration = payload.duration_sec if payload.duration_sec > 0 else 60
        current = current + timedelta(seconds=duration)


def _decode_text(value: bytes | None) -> str:
    if not value:
        return ""
    for encoding in ("utf-8", "utf-16-be", "utf-16-le", "latin-1"):
        try:
            text = value.decode(encoding).strip("\x00")
            return text
        except UnicodeDecodeError:
            continue
    return ""


def _decode_int(value: bytes | None) -> int:
    if not value:
        return 0
    text = _decode_text(value)
    if text.isdigit():
        return int(text)
    try:
        return int(float(text))
    except ValueError:
        if len(value) in {2, 4}:
            return int.from_bytes(value, "big", signed=False)
    return 0


def _decode_float(value: bytes | None) -> float | None:
    if not value:
        return None
    text = _decode_text(value)
    try:
        return float(text)
    except ValueError:
        return None


def _decode_datetime(value: bytes | None, tz: ZoneInfo) -> datetime | None:
    if not value:
        return None
    text = _decode_text(value)
    for fmt in ("%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%d %H:%M:%S", "%Y/%m/%d %H:%M:%S"):
        try:
            parsed = datetime.strptime(text, fmt)
            if parsed.tzinfo is None:
                return parsed.replace(tzinfo=tz)
            return parsed
        except ValueError:
            continue
    return None


def _session_label_from_path(path: Path) -> str:
    return path.stem.replace("_", " ")


def _anchor_from_filename(path: Path, tz: ZoneInfo) -> datetime:
    match = DATE_IN_NAME.search(path.stem)
    if match:
        year, month, day = (int(part) for part in match.groups())
        base = datetime(year, month, day, 22, 0, tzinfo=tz)
    else:
        base = datetime.fromtimestamp(path.stat().st_mtime, tz)
    return base


def _session_start_from_log(lines: Sequence[str], tz: ZoneInfo) -> datetime | None:
    for line in lines:
        match = LOG_SESSION_START.search(line.strip())
        if not match:
            continue
        dt_text = match.group("dt")
        for fmt in ("%Y-%m-%d %H:%M:%S", "%Y/%m/%d %H:%M:%S"):
            try:
                return datetime.strptime(dt_text, fmt).replace(tzinfo=tz)
            except ValueError:
                continue
    return None


def _split_artist_title(body: str) -> tuple[str, str]:
    if " - " in body:
        artist, title = body.split(" - ", 1)
        return artist.strip(), title.strip() or "Unknown Track"
    return "", body.strip() or "Unknown Track"


def _parse_time(text: str) -> time:
    hour, minute, second = (int(part) for part in text.split(":"))
    return time(hour=hour, minute=minute, second=second)
