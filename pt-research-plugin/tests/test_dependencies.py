from __future__ import annotations

import importlib.util
import json
import os
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("probe_openfoam", ROOT / "tools" / "openfoam-runner" / "probe_openfoam.py")
PROBE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(PROBE)


class DependencyTests(unittest.TestCase):
    def test_missing_openfoam_is_honest(self):
        report = PROBE.probe(path="", environ={})
        self.assertEqual(report["mode"], "reduced_capability")
        self.assertFalse(report["dependencies"][0]["available"])
        fixture = json.loads((ROOT / "tests" / "fixtures" / "unavailable-dependency" / "dependency_report.yaml").read_text())
        self.assertTrue(all(not d["available"] for d in fixture["dependencies"]))
        self.assertIn("No dictionary generation", fixture["limitations"][0])

    def test_probe_records_distribution_before_design(self):
        with tempfile.TemporaryDirectory() as temp:
            executable = Path(temp) / "simpleFoam"
            executable.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
            executable.chmod(0o755)
            report = PROBE.probe(path=temp, environ={"PATH": temp, "WM_PROJECT_DIR": "/opt/OpenFOAM/OpenFOAM-10", "WM_PROJECT_VERSION": "10", "WM_PROJECT": "OpenFOAM"})
            self.assertEqual(report["mode"], "operational")
            self.assertEqual(report["distribution"], "openfoam-foundation")
            self.assertEqual(report["version"], "10")

    def test_solver_exit_code_is_not_scientific_acceptance(self):
        schemas = (ROOT / "schemas" / "case-manifest.schema.json").read_text(encoding="utf-8")
        self.assertIn("accepted_for_scientific_use", schemas)
        experiment = (ROOT / "skills" / "upstream-cfd-experiment" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("exit", experiment.lower())
        self.assertIn("accept", experiment.lower())


if __name__ == "__main__":
    unittest.main()
