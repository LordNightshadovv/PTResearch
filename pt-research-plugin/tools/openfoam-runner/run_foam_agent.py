#!/usr/bin/env python3
"""Guarded PT wrapper for the separately preserved Foam-Agent framework."""

from __future__ import annotations

import argparse
import importlib.util
import json
import subprocess
import sys
from pathlib import Path


def report() -> dict:
    packages = {name: importlib.util.find_spec(name) is not None for name in ("langchain", "chromadb", "streamlit")}
    return {"mode": "operational" if all(packages.values()) else "reduced_capability", "dependencies": [{"name": k, "available": v} for k, v in packages.items()], "limitations": [] if all(packages.values()) else ["Foam-Agent Python dependencies are incomplete; framework execution is blocked."]}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--spec", type=Path)
    parser.add_argument("--report", type=Path)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    result = report()
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    else:
        print(json.dumps(result, indent=2))
    if not args.execute:
        return 0
    if result["mode"] != "operational":
        print("REFUSED: missing Foam-Agent dependencies", file=sys.stderr)
        return 2
    if not args.spec or not args.spec.is_file():
        print("REFUSED: --execute requires a validated simulation spec", file=sys.stderr)
        return 2
    framework = Path(__file__).resolve().parents[1] / "foam-agent" / "app.py"
    return subprocess.run([sys.executable, str(framework)], cwd=framework.parent).returncode


if __name__ == "__main__":
    raise SystemExit(main())
