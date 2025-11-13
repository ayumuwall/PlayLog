"""File writers for PlayLog outputs."""
from __future__ import annotations

import csv
import json
from collections.abc import Iterable, Sequence
from datetime import date, datetime
from pathlib import Path

from .models import NightSession, PlayEvent, PlaylogConfig, SessionPaths, sanitize_path_component


def _json_default(value: object) -> str:
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, Path):
        return str(value)
    raise TypeError(f"Object of type {type(value).__name__} is not JSON serializable")


class Writer:
    """Base writer with shared helpers."""

    def __init__(self, config: PlaylogConfig) -> None:
        self.config = config

    def _paths_for(self, session: NightSession) -> SessionPaths:
        safe_session = sanitize_path_component(session.session_id)
        return SessionPaths(
            root=self.config.out_dir,
            app=session.app,
            night_date=session.night_date,
            session_id=safe_session,
        )

    def write(self, session: NightSession, events: Sequence[PlayEvent]) -> Path:
        raise NotImplementedError


class JsonWriter(Writer):
    filename = "session.json"

    def write(self, session: NightSession, events: Sequence[PlayEvent]) -> Path:
        paths = self._paths_for(session)
        paths.session_dir.mkdir(parents=True, exist_ok=True)
        payload = {
            "session": session.model_dump(),
            "events": [event.model_dump() for event in events],
        }
        paths.json_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2, default=_json_default),
            encoding="utf-8",
        )
        return paths.json_path


TXT_TEMPLATE = (
    "[PlayLog]\n"
    "App: {app}\n"
    "NightDate: {night_date}  (cutoff={cutoff}, tz={tz})\n"
    "Session: {session_id}\n"
    "Start: {session_start}\n"
    "End: {session_end}\n"
    "Tracks: {tracks}\n"
    "Timeline: {timeline_mode}\n"
    "\n"
    "--- Tracks ---\n"
)


class TxtWriter(Writer):
    filename = "session.txt"

    def write(self, session: NightSession, events: Sequence[PlayEvent]) -> Path:
        paths = self._paths_for(session)
        paths.session_dir.mkdir(parents=True, exist_ok=True)
        header = TXT_TEMPLATE.format(
            app=f"{session.app} ({session.app_version or 'n/a'})",
            night_date=session.night_date.isoformat(),
            cutoff=self.config.cutoff.strftime("%H:%M"),
            tz=self.config.timezone,
            session_id=session.session_id,
            session_start=_format_dt(session.session_start),
            session_end=_format_dt(session.session_end),
            tracks=len(events),
            timeline_mode=session.timeline_mode,
        )
        body_lines = []
        for idx, event in enumerate(events, start=1):
            artist = event.artist or "Unknown Artist"
            track_line = f"{idx}. [{_format_dt(event.played_at)}] {artist} - {event.title}"
            meta_line = (
                f"  (Album: {event.album or 'n/a'}, BPM: {event.bpm or 'n/a'}, "
                f"Key: {event.key or 'n/a'}, DurationSec: {event.duration_sec})"
            )
            body_lines.append(track_line + meta_line)
        content = header + "\n".join(body_lines)
        paths.txt_path.write_text(content, encoding="utf-8")
        return paths.txt_path


def _format_dt(value: datetime | None) -> str:
    if value is None:
        return "n/a"
    return value.astimezone().isoformat(timespec="seconds")


class CsvBatchWriter(Writer):
    filename = "session.csv"

    header = [
        "index",
        "played_at",
        "title",
        "artist",
        "album",
        "duration_sec",
        "deck",
        "bpm",
        "key",
        "source_path",
        "source_track_id",
    ]

    def write(self, session: NightSession, events: Sequence[PlayEvent]) -> Path:
        paths = self._paths_for(session)
        paths.session_dir.mkdir(parents=True, exist_ok=True)
        with open(paths.csv_path, "w", newline="", encoding="utf-8") as fp:
            writer = csv.writer(fp)
            writer.writerow(self.header)
            for idx, event in enumerate(events, start=1):
                writer.writerow(
                    [
                        idx,
                        _format_dt(event.played_at),
                        event.title,
                        event.artist,
                        event.album,
                        event.duration_sec,
                        event.deck or "",
                        event.bpm or "",
                        event.key or "",
                        event.source_path or "",
                        event.source_track_id or "",
                    ]
                )
        return paths.csv_path


def render_per_night(
    session: NightSession,
    events: Sequence[PlayEvent],
    config: PlaylogConfig,
    formats: Iterable[str] | None = None,
) -> list[Path]:
    """Render selected formats for a session."""

    requested = set(formats or config.formats)
    writers: list[Writer] = []
    if "json" in requested:
        writers.append(JsonWriter(config))
    if "txt" in requested:
        writers.append(TxtWriter(config))
    if "csv" in requested:
        writers.append(CsvBatchWriter(config))

    outputs: list[Path] = []
    for writer in writers:
        outputs.append(writer.write(session, events))
    return outputs
