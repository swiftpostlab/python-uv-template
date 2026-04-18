"""Backward-compatible wrapper for direct script execution."""

from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"

if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from my_project.sync_ai_policy import main


if __name__ == "__main__":
    raise SystemExit(main())
