#!/usr/bin/env python3
"""Thin Codex Stop wrapper for jinhua."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "jinhua.py"), "codex-stop"],
        input=sys.stdin.read(),
        text=True,
        encoding="utf-8",
        capture_output=True,
        check=False,
    )
    if result.stderr:
        print(result.stderr, file=sys.stderr, end="")
    print(result.stdout, end="")
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
