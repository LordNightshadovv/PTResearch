#!/usr/bin/env python3
"""Validate an engineering-standards manifest (declaration and structure only).

Passing means the declaration is complete, internally consistent, and that referenced
project files exist.  It does not run tests and does not establish numerical accuracy or
scientific correctness.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from artifact_lib import load_artifact
from engineering_contract import ENGINEERING_MANIFEST, validate_engineering_manifest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("target", type=Path, help="manifest file or a project directory containing engineering_standards.yaml")
    parser.add_argument("--project-root", type=Path, help="root for referenced-file checks (default: the manifest's directory)")
    parser.add_argument("--no-file-checks", action="store_true", help="skip referenced-file existence checks")
    args = parser.parse_args(argv)
    target = args.target.resolve()
    manifest_path = target / ENGINEERING_MANIFEST if target.is_dir() else target
    try:
        manifest = load_artifact(manifest_path)
    except ValueError as exc:
        print(f"FAIL: engineering standards\n- {exc}")
        return 1
    root = None if args.no_file_checks else (args.project_root or manifest_path.parent).resolve()
    errors = validate_engineering_manifest(manifest, root)
    if errors:
        print("FAIL: engineering standards")
        for error in errors:
            print(f"- {error}")
        return 1
    status = manifest.get("status") if isinstance(manifest, dict) else "?"
    print(f"PASS: engineering-standards declaration is complete and consistent (status={status}): {manifest_path}")
    print("Note: this proves declaration and structure only; it does not run tests or establish scientific correctness.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
