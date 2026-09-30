#!/usr/bin/env python3
"""Run the IYPT 2027 package checks and write the per-case evidence table."""

from __future__ import annotations

import csv
import json
import math
import os
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
ARCHIVE = ROOT / "deliverables" / "iypt-2027-consolidated"
IMPLEMENTED = {
    "01-pinhole-sunglasses",
    "02-disc-spectrometer",
    "04-singing-capacitor",
    "06-seeing-sound",
    "08-upward-driven-disc",
    "09-photographic-bokeh",
    "10-air-vortex",
    "12-dotted-line-trick",
    "15-cold-drink",
    "17-falling-book-cover",
}
PROVISIONAL = {
    "05-y-shaped-pendulum",
    "07-sinking-funnel",
    "11-sound-isolation",
    "16-magnetic-carousel",
}
STOP = {"03-snail-ball", "13-vortex-pendulum", "14-non-newtonian-worms"}


def subprocess_environment() -> dict[str, str]:
    """Build a clean child environment with archive-level test imports available."""
    env = dict(os.environ)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env["PYTHONPYCACHEPREFIX"] = "/private/tmp/iypt2027-package-pycache"
    existing = env.get("PYTHONPATH", "")
    archive_paths = (str(ARCHIVE), str(ARCHIVE / "tests"), existing)
    env["PYTHONPATH"] = os.pathsep.join(part for part in archive_paths if part)
    # Keep this invariant close to the fix so a future refactor cannot silently
    # restore package-cwd execution without the archive-level test helpers.
    if env["PYTHONPATH"].split(os.pathsep)[:2] != [str(ARCHIVE), str(ARCHIVE / "tests")]:
        raise AssertionError("archive roots must be first on the child PYTHONPATH")
    return env


def run(command: list[str], cwd: Path, *, timeout: int = 120) -> tuple[bool, str]:
    env = subprocess_environment()
    result = subprocess.run(command, cwd=cwd, text=True, capture_output=True, timeout=timeout, env=env)
    output = (result.stdout + result.stderr).strip()
    return result.returncode == 0, output


def finite_tree(value: Any) -> bool:
    if isinstance(value, bool) or value is None or isinstance(value, str):
        return True
    if isinstance(value, (int, float)):
        return math.isfinite(float(value))
    if isinstance(value, list):
        return all(finite_tree(item) for item in value)
    if isinstance(value, dict):
        return all(finite_tree(item) for item in value.values())
    return False


def validate_case(case_dir: Path) -> dict[str, str]:
    case_id = case_dir.name
    package = case_dir / "linux-simulation"
    if case_id in IMPLEMENTED or case_id in PROVISIONAL:
        shell_ok, shell_output = run(["bash", "-n", "check_system.sh", "run_gate.sh", "run.sh", "install.sh"], package)
        python_files = [str(path.relative_to(package)) for path in package.rglob("*.py")]
        compile_ok, compile_output = run([sys.executable, "-c", "import py_compile,sys; [py_compile.compile(p,doraise=True) for p in sys.argv[1:]]", *python_files], package)
        tests_ok, tests_output = run([sys.executable, "tests/test_synthetic.py"], package)
        route_ok, route_output = run([sys.executable, "tests/test_route_contract.py"], package)
        extractor_ok, extractor_output = run([sys.executable, "extract_results.py", "--raw", "outputs/raw.json", "--output", "outputs/results.json"], package)
        receipt_path = package / "receipts" / "synthetic-smoke.json"
        receipt_ok = False
        output_ok = False
        if receipt_path.is_file():
            receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
            receipt_ok = receipt.get("exit_status") == 0 and receipt.get("validation_state") == "runnable_synthetic" and bool(receipt.get("exact_command"))
        result_path = package / "outputs" / "results.json"
        if result_path.is_file():
            result = json.loads(result_path.read_text(encoding="utf-8"))
            validation_state = result.get("validation_state")
            execution_mode = result.get("execution_mode")
            state_ok = (
                validation_state == "runnable_synthetic"
                and execution_mode not in {"native-synthetic", "native-apparatus"}
            ) or (validation_state == "reduced_runnable" and execution_mode == "reduced")
            output_ok = state_ok and finite_tree(result.get("outputs")) and isinstance(result.get("value"), (int, float)) and math.isfinite(float(result["value"]))
        artifact_ok, artifact_output = run([sys.executable, str(ROOT / "pt-research-plugin" / "scripts" / "validate_artifacts.py"), str(case_dir)], ROOT)
        checks = {
            "shell_syntax": shell_ok,
            "python_compile": compile_ok,
            "synthetic_unit_tests": tests_ok,
            "route_tests": route_ok,
            "synthetic_smoke_receipt": receipt_ok,
            "finite_machine_outputs": output_ok,
            "extractor": extractor_ok,
            "artifact_validation": artifact_ok,
        }
        provisional = case_id in PROVISIONAL
        return {
            "case_id": case_id,
            "scientific_readiness": "model_selected_not_closed" if provisional else "model_closed",
            "software_readiness": "runnable_synthetic",
            "implementation_status": "runnable_provisional" if provisional else "runnable_synthetic",
            "shell_syntax": "pass" if shell_ok else "fail",
            "python_compile": "pass" if compile_ok else "fail",
            "synthetic_unit_tests": "pass" if tests_ok else "fail",
            "route_tests": "pass" if route_ok else "fail",
            "synthetic_smoke_receipt": "pass" if receipt_ok else "fail",
            "finite_machine_outputs": "pass" if output_ok else "fail",
            "extractor": "pass" if extractor_ok else "fail",
            "artifact_validation": "pass" if artifact_ok else "fail",
            "external_solver_execution": "not run",
            "notes": "provisional implementation; external solver, apparatus fidelity and predictive claims remain unexecuted" if provisional and all(checks.values()) else "all package and archive checks passed" if all(checks.values()) else "failed checks: " + ", ".join(name for name, passed in checks.items() if not passed),
        }
    readiness = "scientific_stop"
    software = "not_applicable"
    artifact_ok, artifact_output = run([sys.executable, str(ROOT / "pt-research-plugin" / "scripts" / "validate_artifacts.py"), str(case_dir)], ROOT)
    return {
        "case_id": case_id,
        "scientific_readiness": readiness,
        "software_readiness": software,
        "implementation_status": "scientific_stop",
        "shell_syntax": "not_applicable",
        "python_compile": "not_applicable",
        "synthetic_unit_tests": "not_applicable",
        "route_tests": "not_applicable",
        "synthetic_smoke_receipt": "not_applicable",
        "finite_machine_outputs": "not_applicable",
        "extractor": "not_applicable",
        "artifact_validation": "pass" if artifact_ok else "fail",
        "external_solver_execution": "not applicable",
        "notes": "artifact validation passed; runtime checks are not applicable" if artifact_ok else "artifact validation failed",
    }


def main() -> int:
    cases = sorted(path for path in ARCHIVE.iterdir() if path.is_dir() and path.name[:2].isdigit())
    rows = [validate_case(case) for case in cases]
    output = ARCHIVE / "IYPT_2027_PER_CASE_TEST_REPORT.csv"
    fields = list(rows[0])
    with output.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    failures = [row for row in rows if "fail" in row.values()]
    print(f"wrote {output}; cases={len(rows)} failures={len(failures)}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
