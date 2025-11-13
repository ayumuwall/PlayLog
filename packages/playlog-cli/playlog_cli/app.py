from __future__ import annotations

import typer

from playlog import __version__ as core_version

app = typer.Typer(help="PlayLog CLI scaffolding")


@app.command()
def version() -> None:
    """Print currently installed component versions."""
    typer.echo(f"playlog-core: {core_version}")


def main() -> None:
    app()


if __name__ == "__main__":
    main()
