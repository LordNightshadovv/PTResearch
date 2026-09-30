#!/usr/bin/env python3
"""Stage pinned upstream snapshots for manual diff; never mutates the plugin."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--destination", type=Path, required=True)
    parser.add_argument("--only")
    args = parser.parse_args()
    script = Path(__file__).with_name("fetch_upstream_skills.py")
    command = [sys.executable, str(script), "--destination", str(args.destination)]
    if args.only:
        command.extend(["--only", args.only])
    result = subprocess.run(command, check=False)
    if result.returncode == 0:
        print("No plugin files were changed. Compare staged snapshots, audit licenses/security, then update pins explicitly.")
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
