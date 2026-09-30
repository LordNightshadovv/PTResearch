from __future__ import annotations

import importlib.util
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
SPEC = importlib.util.spec_from_file_location("validate_artifacts", ROOT / "scripts" / "validate_artifacts.py")
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(MODULE)


class RoutingArtifactTests(unittest.TestCase):
    def fixture(self, name: str) -> Path:
        return ROOT / "tests" / "fixtures" / name

    def test_three_scientific_fixtures_validate(self):
        for name in ("pinhole-sunglasses", "singing-capacitor", "air-vortex-routing"):
            self.assertEqual(MODULE.validate(self.fixture(name)), [], name)

    def test_pinhole_is_wave_optics_not_openfoam(self):
        chain = json.loads((self.fixture("pinhole-sunglasses") / "essence_and_chain.yaml").read_text())
        route = json.loads((self.fixture("pinhole-sunglasses") / "simulation_route.yaml").read_text())
        registry = json.loads((self.fixture("pinhole-sunglasses") / "model_registry.yaml").read_text())
        self.assertEqual(route["selected_route"], "fourier_optics")
        self.assertNotEqual(route["selected_route"], "openfoam_continuum")
        self.assertTrue({"arrangement", "propagation", "retina", "throughput"}.issubset({x["id"] for x in chain["causal_chain"]}))
        rejected = {m["id"]: m for m in registry["candidates"]}
        self.assertEqual(rejected["geometric-only"]["status"], "rejected")
        self.assertIn("diffraction", rejected["geometric-only"]["decision_reason"].lower())

    def test_singing_capacitor_is_complete_hybrid_chain(self):
        route = json.loads((self.fixture("singing-capacitor") / "simulation_route.yaml").read_text())
        registry = json.loads((self.fixture("singing-capacitor") / "model_registry.yaml").read_text())
        self.assertEqual(route["selected_route"], "elmer_fem")
        self.assertEqual(route["primary_solver"], "Elmer FEM")
        self.assertIn("stock OpenFOAM", route["rationale"])
        names = {m["id"] for m in registry["candidates"]}
        self.assertTrue({"electrical-only", "structural-only", "maxwell-rival"}.issubset(names))

    def test_air_vortex_route_maps_governing_fields(self):
        route = json.loads((self.fixture("air-vortex-routing") / "simulation_route.yaml").read_text())
        self.assertEqual(route["selected_route"], "openfoam_continuum")
        self.assertTrue({"velocity", "pressure", "phase fraction"}.issubset(route["required_fields"]))
        self.assertIn("transient incompressible flow", route["governing_physics"])
        self.assertIn("equations", route["rationale"])

    def test_sweep_before_baseline_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp) / "case"
            shutil.copytree(self.fixture("air-vortex-routing"), target)
            path = target / "openfoam" / "case_manifest.yaml"
            manifest = json.loads(path.read_text())
            manifest["parameter_sweep_started"] = True
            path.write_text(json.dumps(manifest), encoding="utf-8")
            self.assertTrue(any("sweep precedes" in e for e in MODULE.validate(target)))

    def test_model_drift_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp) / "case"
            shutil.copytree(self.fixture("air-vortex-routing"), target)
            path = target / "openfoam" / "case_manifest.yaml"
            manifest = json.loads(path.read_text())
            manifest["assumptions"].append("single phase only")
            path.write_text(json.dumps(manifest), encoding="utf-8")
            self.assertTrue(any("contradict" in e for e in MODULE.validate(target)))


if __name__ == "__main__":
    unittest.main()
