from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import typer
from playlog import PlaylogConfig, __version__ as core_version
from playlog.extractors import djay, rekordbox, serato
from playlog.writers import render_per_night

DEFAULT_OUT_DIR = Path.home() / "Desktop" / "PlayLog Archives"

app = typer.Typer(help="PlayLog CLI")


def _emit(event: str, **details: object) -> None:
    payload = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "component": "cli",
        "event": event,
        "details": details,
    }
    typer.echo(json.dumps(payload, ensure_ascii=False))


@app.command()
def version() -> None:
    """Print currently installed component versions."""
    typer.echo(f"playlog-core: {core_version}")


@app.command()
def run(
    apps: str = typer.Option(
        "djay,rekordbox,serato",
        "--apps",
        help="Comma-separated list of apps to process.",
    ),
    out: Path = typer.Option(
        DEFAULT_OUT_DIR,
        "--out",
        help="Output directory (defaults to Desktop/PlayLog Archives).",
    ),
    formats: str = typer.Option(
        "json,txt,csv",
        "--formats",
        help="Comma-separated output formats.",
    ),
    tz: str = typer.Option(
        "UTC",
        "--tz",
        help="IANA timezone name (e.g. Asia/Tokyo).",
    ),
    serato_mode: str = typer.Option(
        "auto",
        "--serato-mode",
        help="Serato extraction mode: auto, crate, logs.",
    ),
    serato_root: Path | None = typer.Option(
        None,
        "--serato-root",
        help="Override the Serato `_Serato_` directory.",
    ),
    timeline_estimate: bool = typer.Option(
        False,
        "--timeline-estimate",
        help="Estimate Serato played_at when timestamps are missing.",
    ),
) -> None:
    """Run extraction for the selected apps."""

    format_set = {item.strip() for item in formats.split(",") if item.strip()}
    requested_apps = [item.strip() for item in apps.split(",") if item.strip()] or [
        "djay",
        "rekordbox",
        "serato",
    ]

    config_kwargs: dict[str, object] = {
        "out_dir": out,
        "timezone": tz,
        "timeline_estimate": timeline_estimate,
        "serato_mode": serato_mode,
        "serato_root": serato_root,
    }
    if format_set:
        config_kwargs["formats"] = format_set
    config = PlaylogConfig(**config_kwargs)

    extractors = {
        "djay": lambda: djay.extract(config),
        "rekordbox": lambda: rekordbox.extract(config),
        "serato": lambda: serato.extract(config),
    }

    for app_name in requested_apps:
        extractor = extractors.get(app_name)
        if extractor is None:
            _emit("app-skipped", app=app_name, reason="unsupported")
            continue
        _emit("app-start", app=app_name)
        sessions = extractor()
        for session, events in sessions:
            render_per_night(session, events, config, formats=format_set or None)
            _emit(
                "session-written",
                app=app_name,
                session_id=session.session_id,
                night_date=session.night_date.isoformat(),
                formats=sorted(format_set or config.formats),
                tracks=len(events),
            )
    _emit("run-complete", apps=requested_apps)


def main() -> None:
    app()


if __name__ == "__main__":
    main()
