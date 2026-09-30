from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
GENERATOR = ROOT / "tools" / "simulation-package" / "generate_package.py"
OPENFOAM_EXPORTER = ROOT / "tools" / "openfoam-runner" / "export_linux_package.py"
VALIDATE_ARTIFACTS = ROOT / "scripts" / "validate_artifacts.py"
sys.path.insert(0, str(ROOT / "scripts"))
from runnable_contract import package_status, validate_package


ROUTES = (
    "fourier_optics",
    "elmer_fem",
    "openfoam_continuum",
    "project_chrono",
    "yade",
    "python_ode",
    "python_optimization",
    "reduced_order_model",
)


class RunnableSimulationContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def generate(self, route: str) -> Path:
        package = self.root / route
        result = subprocess.run(
            [sys.executable, str(GENERATOR), "--route", route, "--output", str(package), "--model-id", f"test-{route}"],
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        return package

    def test_every_supported_route_has_a_synthetic_smoke_package(self) -> None:
        for route in ROUTES:
            package = self.generate(route)
            result = subprocess.run(["bash", "run.sh"], cwd=package, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, route + "\n" + result.stdout + result.stderr)
            self.assertEqual(validate_package(package), [], route)
            manifest = json.loads((package / "simulation_package_manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["software_readiness"], "runnable_synthetic", route)
            self.assertTrue(manifest["runnable_claim"], route)
            receipt = json.loads((package / "receipts" / "synthetic-smoke.json").read_text(encoding="utf-8"))
            for field in (
                "timestamp", "operating_system", "architecture", "package_version",
                "solver_version", "package_revision", "exact_command", "input_file_hash", "generated_case_hash",
                "exit_status", "runtime_seconds", "output_hashes", "warnings",
                "errors", "validation_state",
            ):
                self.assertIn(field, receipt, route)
            self.assertEqual(receipt["exit_status"], 0, route)

    def test_generated_native_python_assets_are_syntax_valid(self) -> None:
        for route in ROUTES:
            package = self.generate(route)
            for path in package.glob("native/**/*.py"):
                compile(path.read_text(encoding="utf-8"), str(path), "exec")

    def test_apparatus_gate_rejects_synthetic_input(self) -> None:
        package = self.generate("python_ode")
        result = subprocess.run(
            ["bash", "run_gate.sh", "--apparatus", "examples/synthetic.json"],
            cwd=package,
            capture_output=True,
            text=True,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("apparatus", result.stderr.lower())

    def test_measured_input_advances_only_to_runnable_apparatus(self) -> None:
        package = self.generate("python_ode")
        synthetic = subprocess.run(["bash", "run.sh"], cwd=package, capture_output=True, text=True)
        self.assertEqual(synthetic.returncode, 0, synthetic.stdout + synthetic.stderr)
        measured = json.loads((package / "examples" / "synthetic.json").read_text(encoding="utf-8"))
        measured["metadata"] = {"synthetic": False, "measured": True, "provenance": "calibrated bench record"}
        measured["uncertainties"] = {"initial_position_m": {"standard_uncertainty": 0.01, "unit": "m"}}
        measured_path = package / "examples" / "measured.json"
        measured_path.write_text(json.dumps(measured), encoding="utf-8")
        result = subprocess.run(["bash", "run.sh", "--apparatus", str(measured_path)], cwd=package, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        manifest = json.loads((package / "simulation_package_manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["software_readiness"], "runnable_apparatus")
        self.assertTrue((package / "receipts" / "apparatus-run.json").is_file())
        self.assertEqual(validate_package(package), [])

    def test_state_gate_names_missing_case_generation(self) -> None:
        package = self.generate("python_ode")
        result = subprocess.run(
            [sys.executable, "scripts/run_gate.py", "--manifest", "simulation_package_manifest.json", "--mode", "production"],
            cwd=package,
            capture_output=True,
            text=True,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("case generation", result.stderr.lower())

    def test_echo_only_system_check_is_rejected(self) -> None:
        package = self.generate("python_ode")
        (package / "check_system.sh").write_text("#!/bin/sh\necho preflight\nexit 0\n", encoding="utf-8")
        errors = validate_package(package)
        self.assertTrue(any("echo-only" in error for error in errors), errors)

    def test_unconditional_run_gate_is_rejected(self) -> None:
        package = self.generate("python_ode")
        (package / "run_gate.sh").write_text("#!/bin/sh\necho BLOCKED\nexit 2\n", encoding="utf-8")
        errors = validate_package(package)
        self.assertTrue(any("unconditionally blocks" in error for error in errors), errors)

    def test_documentation_shell_and_json_without_implementation_is_rejected(self) -> None:
        package = self.generate("python_ode")
        shutil.rmtree(package / "src")
        errors = validate_package(package)
        self.assertTrue(any("no executable source" in error for error in errors), errors)
        self.assertEqual(package_status(package), "handoff-only")

    def test_output_like_fields_are_not_required_inputs(self) -> None:
        package = self.generate("python_ode")
        input_path = package / "examples" / "synthetic.json"
        value = json.loads(input_path.read_text(encoding="utf-8"))
        value["observables"] = {"pressure_field": 1.0}
        input_path.write_text(json.dumps(value), encoding="utf-8")
        errors = validate_package(package)
        self.assertTrue(any("output-like category" in error for error in errors), errors)

    def test_imported_measured_output_is_allowed_only_with_justification(self) -> None:
        package = self.generate("python_ode")
        input_path = package / "examples" / "synthetic.json"
        value = json.loads(input_path.read_text(encoding="utf-8"))
        value["observables"] = {"retinal_irradiance": {"value": 1.0, "unit": "W/m2", "imported_measured_field": True, "source": "calibrated sensor"}}
        input_path.write_text(json.dumps(value), encoding="utf-8")
        errors = validate_package(package)
        self.assertFalse(any("output-like category" in error or "obvious output" in error for error in errors), errors)

    def test_placeholder_solver_mapping_is_rejected(self) -> None:
        package = self.generate("python_ode")
        manifest_path = package / "simulation_package_manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["parameter_mapping"][0]["destination"] = "apparatus-specific input"
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
        errors = validate_package(package)
        self.assertTrue(any("placeholder destination" in error for error in errors), errors)

    def test_numerical_verification_claim_requires_execution_receipt(self) -> None:
        package = self.generate("python_ode")
        manifest_path = package / "simulation_package_manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["software_readiness"] = "numerically_verified"
        manifest["runnable_claim"] = True
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
        errors = validate_package(package)
        self.assertTrue(any("execution receipt" in error or "passed machine-readable" in error for error in errors), errors)

    def test_current_2027_synthetic_package_is_runnable_and_partial_mode_reports_state(self) -> None:
        case = ROOT.parent / "deliverables" / "iypt-2027-consolidated" / "06-seeing-sound"
        strict = subprocess.run([sys.executable, str(VALIDATE_ARTIFACTS), str(case)], capture_output=True, text=True)
        self.assertEqual(strict.returncode, 0, strict.stdout + strict.stderr)
        self.assertIn("runnable-simulation contract", strict.stdout)
        partial = subprocess.run([sys.executable, str(VALIDATE_ARTIFACTS), str(case), "--allow-partial"], capture_output=True, text=True)
        self.assertEqual(partial.returncode, 0, partial.stdout + partial.stderr)
        self.assertIn("package_status=runnable_synthetic", partial.stdout)

    def test_openfoam_exporter_uses_complete_shared_package_contract(self) -> None:
        case = self.root / "case"
        (case / "openfoam" / "generated_case").mkdir(parents=True)
        (case / "openfoam" / "generated_case" / "controlDict").write_text("application interFoam;\n", encoding="utf-8")
        (case / "simulation_spec.yaml").write_text(json.dumps({"selected_model_id": "vortex"}), encoding="utf-8")
        (case / "runtime.yaml").write_text(json.dumps({"runtime": {"solver": "interFoam"}, "execution": {}, "validation": {}}), encoding="utf-8")
        output = self.root / "exported"
        result = subprocess.run(
            [sys.executable, str(OPENFOAM_EXPORTER), str(case), "--output", str(output)],
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(validate_package(output), [], result.stdout + result.stderr)
        self.assertTrue((output / "native" / "openfoam-case" / "controlDict").is_file())


if __name__ == "__main__":
    unittest.main()
