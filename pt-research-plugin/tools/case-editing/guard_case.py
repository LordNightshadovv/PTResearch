#!/usr/bin/env python3
"""Reject a generated case whose assumptions drift from the selected model."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("model_registry", type=Path)
    parser.add_argument("case_manifest", type=Path)
    args = parser.parse_args()
    registry = json.loads(args.model_registry.read_text(encoding="utf-8"))
    manifest = json.loads(args.case_manifest.read_text(encoding="utf-8"))
    models = {m["id"]: m for m in registry["candidates"]}
    model = models.get(manifest.get("selected_model_id"))
    errors = []
    if not model or manifest.get("selected_model_id") not in registry.get("selected_candidate_ids", []):
        errors.append("case model is not selected")
    elif set(manifest.get("assumptions", [])) & set(model.get("prohibited_assumptions", [])):
        errors.append("case contains a prohibited assumption")
    if errors:
        print("REFUSED: " + "; ".join(errors))
        return 1
    print("PASS: generated case preserves the selected physical model")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
