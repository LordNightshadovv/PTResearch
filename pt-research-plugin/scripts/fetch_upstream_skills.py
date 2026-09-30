#!/usr/bin/env python3
"""Fetch pinned PT upstream sources into a staging directory for review."""

from __future__ import annotations

import argparse
import subprocess
import tempfile
from pathlib import Path

from provenance_lib import SOURCES


def run(command: list[str], cwd: Path | None = None) -> None:
    subprocess.run(command, cwd=cwd, check=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--destination", type=Path, required=True, help="new or empty staging directory")
    parser.add_argument("--only", choices=[source["local_skill"] for source in SOURCES])
    args = parser.parse_args()
    destination = args.destination.resolve()
    if destination.exists() and any(destination.iterdir()):
        parser.error("destination must be new or empty; this script never overwrites preserved snapshots")
    destination.mkdir(parents=True, exist_ok=True)
    selected = [source for source in SOURCES if not args.only or source["local_skill"] == args.only]
    with tempfile.TemporaryDirectory(prefix="pt-upstream-fetch-") as temp:
        temp_root = Path(temp)
        repos: dict[tuple[str, str], Path] = {}
        for source in selected:
            key = (source["repository"], source["commit"])
            if key not in repos:
                checkout = temp_root / f"repo-{len(repos)}"
                run(["git", "clone", "--no-checkout", "--filter=blob:none", source["repository"], str(checkout)])
                run(["git", "checkout", source["commit"]], cwd=checkout)
                repos[key] = checkout
            checkout = repos[key]
            target = destination / source["local_skill"]
            target.mkdir(parents=True)
            archive = temp_root / f"{source['local_skill']}.tar"
            treeish = source["commit"] if source["source_path"] == "." else f"{source['commit']}:{source['source_path']}"
            run(["git", "archive", "--format=tar", f"--output={archive}", treeish], cwd=checkout)
            run(["tar", "-xf", str(archive), "-C", str(target)])
            print(f"staged {source['local_skill']} at {source['commit']}")
    print("Review licenses, security, and hashes before copying staged content into the plugin.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
