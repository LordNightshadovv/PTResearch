#!/usr/bin/env python3
"""Check license evidence for every vendored PT source."""

from __future__ import annotations

import json
from pathlib import Path

from provenance_lib import SOURCES


def check(plugin_root: Path) -> list[str]:
    errors: list[str] = []
    lock = json.loads((plugin_root / "upstream-lock.yaml").read_text(encoding="utf-8"))
    locked = {item["local_skill"]: item for item in lock["sources"]}
    for source in SOURCES:
        name = source["local_skill"]
        if not locked.get(name, {}).get("license"):
            errors.append(f"missing license classification: {name}")
        if name == "tool-foam-agent":
            license_path = plugin_root / "tools" / "foam-agent" / "LICENSE"
        else:
            license_path = plugin_root / "skills" / name / "LICENSE"
        if not license_path.is_file() or license_path.stat().st_size < 20:
            errors.append(f"missing license record: {name}")
    notices = plugin_root / "THIRD_PARTY_NOTICES.md"
    if not notices.is_file():
        errors.append("missing THIRD_PARTY_NOTICES.md")
    return errors


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    errors = check(root)
    if errors:
        print("FAIL: license gate")
        for error in errors:
            print(f"- {error}")
        return 1
    print("PASS: all vendored sources have license evidence and notices")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
