from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ROOT / "tools" / "solver-runtime" / "solver_runtime.py"
LOCKS = json.loads((ROOT / "tools" / "solver-runtime" / "solver-locks.json").read_text(encoding="utf-8"))


class SolverRuntimeTests(unittest.TestCase):
    def test_every_routable_solver_has_a_locked_official_runtime(self):
        self.assertEqual(set(LOCKS["solvers"]), {"OpenFOAM", "HCIPy", "Project Chrono", "Elmer FEM", "YADE", "Python/SciPy"})
        for name, item in LOCKS["solvers"].items():
            self.assertTrue(item["version"], name)
            self.assertTrue(item["probe_command"], name)
            self.assertTrue(item["official_source"].startswith("https://"), name)
            self.assertTrue(item["targets"], name)
            self.assertTrue(item["smoke_test"], name)
            self.assertTrue((ROOT / "tools" / "solver-runtime" / "containerfiles" / f"{name.lower().replace(' ', '-').replace('/', '-')}.Dockerfile").is_file(), name)

    def test_install_refuses_without_authorization(self):
        result = subprocess.run(["python3", str(RUNTIME), "install", "--solver", "HCIPy"], text=True, capture_output=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("--authorized", result.stderr)

    def test_installer_is_official_source_and_does_not_embed_binary(self):
        result = subprocess.run(["python3", str(RUNTIME), "installer", "--solver", "OpenFOAM", "--target", "ubuntu-x86_64-cpu"], text=True, capture_output=True, check=True)
        self.assertIn("dl.openfoam.org", result.stdout)
        self.assertNotIn("base64", result.stdout.lower())

    def test_package_requires_exact_passed_receipt_including_backend(self):
        with tempfile.TemporaryDirectory() as directory:
            temp = Path(directory)
            receipt = temp / "receipt.json"
            receipt.write_text(json.dumps({"solver": "HCIPy", "version": "0.7.0", "target": "ubuntu-x86_64-cpu", "gpu_backend": "cpu", "passed": True, "executed_at": "2026-07-24T00:00:00Z", "evidence": ["logs/hcipy-smoke.log"]}), encoding="utf-8")
            output = temp / "package"
            result = subprocess.run(["python3", str(RUNTIME), "package", "--solver", "HCIPy", "--target", "ubuntu-x86_64-cpu", "--gpu-backend", "cpu", "--receipt", str(receipt), "--output", str(output), "--offline"], text=True, capture_output=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            manifest = json.loads((output / "simulation_package_manifest.json").read_text(encoding="utf-8"))
            self.assertFalse(manifest["runnable_claim"])
            self.assertEqual(manifest["software_readiness"], "handoff_only")
            self.assertIn("case implementation", manifest["claim_ceiling"])
            self.assertEqual(manifest["gpu_backend"], "cpu")
            self.assertTrue((output / "OFFLINE-MISSING.md").is_file())
            self.assertIn("python3", (output / "scripts" / "check-system.sh").read_text())
            self.assertIn("runnable_claim", (output / "scripts" / "run.sh").read_text())


if __name__ == "__main__":
    unittest.main()
