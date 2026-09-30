from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ROUTER = (ROOT / "skills" / "pt-simulation-router" / "SKILL.md").read_text(encoding="utf-8")


class SingleSolverRoutingTests(unittest.TestCase):
    def test_router_requires_single_solver_before_coupling(self):
        self.assertIn("`primary_solver` is exactly one", ROUTER)
        self.assertIn("Why one solver is insufficient", ROUTER)
        self.assertIn("If any item is unknown, do not add the solver", ROUTER)

    def test_router_is_general_not_year_specific(self):
        self.assertNotIn("2027 canonical routes", ROUTER)
        self.assertIn("solver_requirements.yaml", ROUTER)
        self.assertIn("Refuse a route when closure is", ROUTER)

    def test_packager_rejects_false_native_claims(self):
        text = (ROOT / "skills" / "pt-simulation-packager" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("never native macOS", text)
        self.assertIn("container cannot supply a missing GPU backend", text)

    def test_packager_separates_handoff_and_synthetic_readiness(self):
        text = (ROOT / "skills" / "pt-simulation-packager" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("handoff_only", text)
        self.assertIn("runnable_synthetic", text)
        self.assertIn("executable source", text)

    def test_packager_exposes_the_four_execution_modes(self):
        text = (ROOT / "skills" / "pt-simulation-packager" / "SKILL.md").read_text(encoding="utf-8")
        for choice in ("run locally now", "produce a Linux/Ubuntu package", "produce both", "stop before implementation"):
            self.assertIn(choice, text)

    def test_router_treats_numerical_python_models_as_routes(self):
        text = (ROOT / "skills" / "pt-simulation-router" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("Python/SciPy", text)
        self.assertIn("analytical_closed_form", text)


if __name__ == "__main__":
    unittest.main()
