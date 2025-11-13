"""Verify developer environment prerequisites."""
from __future__ import annotations

import shutil
import sys

REQUIRED_BINARIES = [
    "python3",
    "node",
    "npm",
]


def main() -> None:
    missing: list[str] = []
    for binary in REQUIRED_BINARIES:
        if shutil.which(binary) is None:
            missing.append(binary)
    if missing:
        joined = ", ".join(missing)
        print(f"Missing required tools: {joined}", file=sys.stderr)
        raise SystemExit(1)
    print("Environment looks good ✨")


if __name__ == "__main__":
    main()
