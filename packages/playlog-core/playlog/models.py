"""PlayLog core data models and utilities."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from pathlib import Path
from typing import Any, Literal
from zoneinfo import ZoneInfo

from pydantic import BaseModel, ConfigDict, Field, field_validator

PlayApp = Literal["djay", "rekordbox", "serato"]
TimelineMode = Literal["actual", "estimated"]
OutputFormat = Literal["json", "txt", "csv"]

RESERVED_FS_CHARS = "\\/:*?\"<>|"
DEFAULT_CUTOFF = time(hour=8, minute=0)
DEFAULT_SESSION_GAP_MINUTES = 60

def _default_formats() -> set[OutputFormat]:
    return {"json", "txt", "csv"}


class PlayEvent(BaseModel):
    """Normalized play event shared across extractors."""

    model_config = ConfigDict(str_strip_whitespace=True)

    app: PlayApp
    app_version: str | None = None
    session_id: str | None = None
    session_date: date | None = None
    night_date: date | None = None
    played_at: datetime | None = None
    title: str = Field(min_length=1)
    artist: str = ""
    album: str = ""
    duration_sec: int = Field(default=0, ge=0)
    deck: str | None = None
    bpm: float | None = Field(default=None, ge=0)
    key: str | None = None
    source_path: str | None = None
    source_track_id: str | None = None
    raw: dict[str, Any] | None = None

    @field_validator("played_at")
    @classmethod
    def _ensure_timezone(cls, value: datetime | None) -> datetime | None:
        if value is None:
            return None
        if value.tzinfo is None:
            return value.replace(tzinfo=ZoneInfo("UTC"))
        return value


class NightSession(BaseModel):
    """Nightly session metadata used for per-night outputs."""

    app: PlayApp
    session_id: str
    night_date: date
    session_label: str | None = None
    app_version: str | None = None
    session_start: datetime | None = None
    session_end: datetime | None = None
    timeline_mode: TimelineMode = "actual"

    @field_validator("session_id")
    @classmethod
    def _require_non_empty(cls, value: str) -> str:
        if not value.strip():
            msg = "session_id must not be empty"
            raise ValueError(msg)
        return value


class PlaylogConfig(BaseModel):
    """Runtime configuration shared between CLI/GUI."""

    out_dir: Path
    formats: set[OutputFormat] = Field(default_factory=_default_formats)
    cutoff: time = DEFAULT_CUTOFF
    session_gap_minutes: int = Field(default=DEFAULT_SESSION_GAP_MINUTES, ge=1)
    timezone: str = Field(default="UTC")
    timeline_estimate: bool = False
    redact_paths: bool = False
    serato_root: Path | None = None
    serato_mode: str = "auto"

    @field_validator("out_dir")
    @classmethod
    def _expand_home(cls, value: Path) -> Path:
        return value.expanduser().resolve()

    @field_validator("serato_root")
    @classmethod
    def _expand_serato_root(cls, value: Path | None) -> Path | None:
        if value is None:
            return None
        return value.expanduser().resolve()

    @field_validator("serato_mode")
    @classmethod
    def _normalize_serato_mode(cls, value: str) -> str:
        normalized = value.lower()
        if normalized not in {"auto", "crate", "logs"}:
            msg = "serato_mode must be one of auto|crate|logs"
            raise ValueError(msg)
        return normalized


def sanitize_path_component(value: str, replacement: str = "_") -> str:
    """Sanitize filesystem components by replacing reserved characters."""

    sanitized = value
    for char in RESERVED_FS_CHARS:
        sanitized = sanitized.replace(char, replacement)
    return sanitized.strip() or "session"


def get_timezone(tz_name: str | None) -> ZoneInfo:
    """Return ZoneInfo from a name, defaulting to localtime if unavailable."""

    if tz_name:
        return ZoneInfo(tz_name)
    return ZoneInfo("UTC")


def floor_by_cutoff(
    dt: datetime,
    cutoff: time = DEFAULT_CUTOFF,
    tz: ZoneInfo | None = None,
) -> date:
    """Return the "night date" given a cutoff time (defaults to 08:00)."""

    target_tz = tz or ZoneInfo("UTC")
    localized = dt.astimezone(target_tz)
    cutoff_dt = datetime.combine(localized.date(), cutoff, tzinfo=target_tz)
    if localized < cutoff_dt:
        return (localized - timedelta(days=1)).date()
    return localized.date()


@dataclass(frozen=True, slots=True)
class SessionPaths:
    """Derived filesystem paths for a given session."""

    root: Path
    app: str
    night_date: date
    session_id: str

    @property
    def session_dir(self) -> Path:
        return self.root / self.app / self.night_date.isoformat() / self.session_id

    @property
    def json_path(self) -> Path:
        return self.session_dir / "session.json"

    @property
    def txt_path(self) -> Path:
        return self.session_dir / "session.txt"

    @property
    def csv_path(self) -> Path:
        return self.session_dir / "session.csv"
