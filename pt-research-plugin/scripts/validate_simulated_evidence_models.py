#!/usr/bin/env python3
"""Validate the archive's model-independence/evidence boundary."""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("archive", type=Path)
    args = parser.parse_args()
    archive = args.archive.resolve()
    audit = load(archive / "SIMULATED_EVIDENCE_MODEL_AUDIT.yaml")
    cases = {item["case_id"]: item for item in audit.get("cases", [])}
    expected = {
        path.name
        for path in archive.iterdir()
        if path.is_dir() and len(path.name) >= 2 and path.name[:2].isdigit()
    }
    if set(cases) != expected:
        raise SystemExit(f"audit case set mismatch: missing={sorted(expected - set(cases))}, extra={sorted(set(cases) - expected)}")

    case12 = archive / "12-dotted-line-trick"
    manifest12 = load(case12 / "linux-simulation" / "simulation_package_manifest.json")
    if manifest12.get("model_relationship") != "same_model_consequence":
        raise SystemExit("12 must remain classified as a same-model consequence")
    if manifest12.get("independent_simulated_evidence_eligible") is not False:
        raise SystemExit("12 must not be eligible for independent simulated evidence")
    if not (case12 / "linux-simulation" / "independence-gate.md").is_file():
        raise SystemExit("12 is missing its independent-evidence gate")

    case15 = archive / "15-cold-drink"
    package15 = case15 / "linux-simulation"
    manifest15 = load(package15 / "simulation_package_manifest.json")
    required15 = {
        "independent_model.py",
        "independent-model-equations.yaml",
        "independent-numerical-verification.json",
        "scripts/run_independent_pipeline.py",
        "scripts/run_independent_refinement.py",
    }
    missing = sorted(path for path in required15 if not (package15 / path).exists())
    if missing:
        raise SystemExit(f"15 independent route is incomplete: {missing}")
    if manifest15.get("independent_evidence_model_id") != "c2-independent-spatial":
        raise SystemExit("15 is missing the independent model id")
    source = (package15 / "independent_model.py").read_text(encoding="utf-8")
    if "from src.model" in source or "from native.scipy_case" in source:
        raise SystemExit("15 independent model imports the contested reduced implementation")
    result = load(package15 / "outputs" / "independent" / "results.json")
    if result.get("model_id") != "c2-independent-spatial" or result.get("model_relationship") != "independent_physical_model":
        raise SystemExit("15 independent output lacks its model-independence label")
    refinement = load(package15 / "verification" / "independent-refinement-results.json")
    if refinement.get("status") != "passed":
        raise SystemExit("15 independent numerical verification is not passed")

    print("simulated-evidence model audit passed: 12 blocked, 15 independent comparator verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
