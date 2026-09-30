#!/usr/bin/env python3
"""Generate or verify pinned upstream source hashes without network access."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from provenance_lib import SOURCES, snapshot_path, tree_hash


def initialize(plugin_root: Path) -> None:
    lock_sources = []
    for source in SOURCES:
        snapshot = snapshot_path(plugin_root, source)
        digest, file_hashes = tree_hash(snapshot)
        entry = {
            **source,
            "retrieved_at": "2026-07-20",
            "reuse_mode": "pt_bridge_with_preserved_snapshot" if source["local_skill"] != "tool-foam-agent" else "vendored_tool_with_wrapper",
            "tree_hash": digest,
            "file_hashes": file_hashes,
        }
        lock_sources.append(entry)
        if source["local_skill"] == "tool-foam-agent":
            target = plugin_root / "tools" / "foam-agent.SOURCE.yaml"
        else:
            target = plugin_root / "skills" / source["local_skill"] / "SOURCE.yaml"
        target.write_text(json.dumps(entry, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    lock = {"version": 1, "sources": lock_sources}
    (plugin_root / "upstream-lock.yaml").write_text(json.dumps(lock, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def verify(plugin_root: Path) -> list[str]:
    lock_path = plugin_root / "upstream-lock.yaml"
    if not lock_path.is_file():
        return ["missing upstream-lock.yaml"]
    lock = json.loads(lock_path.read_text(encoding="utf-8"))
    errors: list[str] = []
    expected = {source["local_skill"]: source for source in lock.get("sources", [])}
    for source in SOURCES:
        name = source["local_skill"]
        locked = expected.get(name)
        if not locked:
            errors.append(f"missing lock entry: {name}")
            continue
        if locked.get("commit") != source["commit"]:
            errors.append(f"commit mismatch in lock: {name}")
        snapshot = snapshot_path(plugin_root, source)
        if not snapshot.is_dir():
            errors.append(f"missing snapshot: {name}")
            continue
        digest, file_hashes = tree_hash(snapshot)
        if digest != locked.get("tree_hash"):
            errors.append(f"tree hash mismatch: {name}")
        if file_hashes != locked.get("file_hashes"):
            errors.append(f"file hash map mismatch: {name}")
        source_file = plugin_root / ("tools/foam-agent.SOURCE.yaml" if name == "tool-foam-agent" else f"skills/{name}/SOURCE.yaml")
        if not source_file.is_file():
            errors.append(f"missing SOURCE metadata: {name}")
        elif json.loads(source_file.read_text(encoding="utf-8")) != locked:
            errors.append(f"SOURCE metadata differs from lock: {name}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("plugin_root", nargs="?", default=".", type=Path)
    parser.add_argument("--initialize", action="store_true", help="write SOURCE files and lock from current preserved snapshots")
    args = parser.parse_args()
    root = args.plugin_root.resolve()
    if args.initialize:
        initialize(root)
    errors = verify(root)
    if errors:
        print("FAIL: upstream integrity")
        for error in errors:
            print(f"- {error}")
        return 1
    print("PASS: 8 specialist snapshots and Foam-Agent match upstream-lock.yaml")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
