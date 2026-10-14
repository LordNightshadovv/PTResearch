from __future__ import annotations

import ast
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "scaffold_research_software.py"
sys.path.insert(0, str(ROOT / "scripts"))

import scaffold_research_software as scaffold  # noqa: E402


def have(*modules: str) -> bool:
    return all(importlib.util.find_spec(m) is not None for m in modules)


class ScaffoldResearchSoftwareTests(unittest.TestCase):
    def run_cli(self, *args: str) -> subprocess.CompletedProcess:
        return subprocess.run([sys.executable, str(SCRIPT), *args], capture_output=True, text=True)

    def test_cli_scaffolds_expected_layout_and_substitutes_placeholders(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            project = Path(temp) / "spin-top"
            result = self.run_cli(str(project), "--description", "Gyroscope study")
            self.assertEqual(result.returncode, 0, result.stderr)
            for relative in (
                "pyproject.toml", "README.md", "CHANGELOG.md", ".gitignore", ".github/workflows/ci.yml",
                "config/default.toml", "docs/adr/0001-stack-decision.md", "docs/verification-plan.md",
                "engineering_standards.yaml", "src/spin_top/model.py", "src/spin_top/provenance.py",
                "src/spin_top/py.typed", "tests/test_units.py", "tests/test_convergence.py",
            ):
                self.assertTrue((project / relative).is_file(), relative)
            self.assertFalse((project / "src" / "spin_top" / "gui").exists())
            self.assertFalse((project / "tests" / "test_gui_controller.py").exists())
            readme = (project / "README.md").read_text(encoding="utf-8")
            self.assertIn("Assumptions and validity range", readme)
            self.assertIn("Gyroscope study", readme)
            for path in project.rglob("*"):
                if path.is_file():
                    self.assertNotIn("@@", path.read_text(encoding="utf-8"), path)
                    self.assertFalse(path.name.endswith(".tmpl"), path)
            pyproject = (project / "pyproject.toml").read_text(encoding="utf-8")
            for token in ("ruff", "mypy", "pytest", 'name = "spin-top"'):
                self.assertIn(token, pyproject)

    def test_generated_python_parses_and_manifest_is_truthful(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            project = Path(temp) / "demo"
            scaffold.scaffold(project, "demo", interface="web_ui")
            for path in project.rglob("*.py"):
                ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            self.assertTrue((project / "src" / "demo" / "gui" / "controller.py").is_file())
            manifest = json.loads((project / "engineering_standards.yaml").read_text(encoding="utf-8"))
            self.assertEqual(manifest["validation_scope"], "declaration_and_structure_only")
            self.assertEqual(manifest["dependency_management"]["lockfile_status"], "pending_generation")
            self.assertFalse((project / "uv.lock").exists())
            self.assertTrue(all(t["evidence_status"] != "evidenced" for t in manifest["test_plan"]["tests"]))
            self.assertEqual(manifest["interface"]["primary"], "web_ui")
            self.assertTrue(manifest["interface"]["thin_layer"])

    def test_refuses_existing_nonempty_destination_and_bad_names(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            occupied = Path(temp) / "occupied"
            occupied.mkdir()
            (occupied / "keep.txt").write_text("keep", encoding="utf-8")
            self.assertNotEqual(self.run_cli(str(occupied)).returncode, 0)
            self.assertEqual((occupied / "keep.txt").read_text(encoding="utf-8"), "keep")
            self.assertNotEqual(self.run_cli(str(Path(temp) / "Bad Name")).returncode, 0)
            self.assertNotEqual(self.run_cli(str(Path(temp) / "9lives")).returncode, 0)
            self.assertNotEqual(self.run_cli(str(Path(temp) / "ok"), "--description", 'has "quote"').returncode, 0)

    def test_package_name_derivation(self) -> None:
        self.assertEqual(scaffold.package_name("air-vortex_ring"), "air_vortex_ring")
        with self.assertRaises(scaffold.ScaffoldError):
            scaffold.validate_project_name("Upper")

    @unittest.skipUnless(have("numpy", "scipy", "pytest"), "numpy, scipy, and pytest are required to run the generated suite")
    def test_generated_project_test_suite_passes_when_dependencies_exist(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            project = Path(temp) / "runme"
            scaffold.scaffold(project, "runme", interface="desktop_gui")
            result = subprocess.run(
                [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider"],
                cwd=project, capture_output=True, text=True,
                env={**__import__("os").environ, "PYTHONDONTWRITEBYTECODE": "1"},
            )
            self.assertEqual(result.returncode, 0, result.stdout[-3000:] + result.stderr[-1000:])


if __name__ == "__main__":
    unittest.main()
