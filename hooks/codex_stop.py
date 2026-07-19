#!/usr/bin/env python3
"""Thin Codex Stop wrapper for jinhua."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    stdin = getattr(sys.stdin, "buffer", sys.stdin)
    input_data = stdin.read()
    if isinstance(input_data, str):
        input_data = input_data.encode("utf-8")
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "jinhua.py"), "codex-stop"],
        input=input_data,
        capture_output=True,
        check=False,
    )
    if result.stderr:
        sys.stderr.buffer.write(result.stderr)
    sys.stdout.buffer.write(result.stdout)
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
