from __future__ import annotations

import importlib.util
import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "tools" / "solver-documentation" / "solver_documents.py"
BUNDLED_PYTHON = Path("/Users/vold/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3")
SPEC = importlib.util.spec_from_file_location("solver_documents", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(MODULE)


SOLVER = {
    "id": "hcipy", "official_name": "HCIPy", "version": "0.7.0", "official_homepage": "https://hcipy.org",
    "repository": "https://github.com/ehpor/hcipy", "license": "BSD-3-Clause", "citation": "[S1]",
    "installation_method": "locked Python environment", "execution_platform": "Linux x86_64 native",
    "modules": ["FraunhoferPropagator"], "physical_equations": ["scalar diffraction"],
    "numerical_algorithms": ["FFT propagation"], "chapter_id": "solver-hcipy", "actually_used": True,
    "numerical_method_family": "Fourier optics", "prompts": ["Pinhole sunglasses"],
    "batch_usage": "Uses Fraunhofer propagation to predict a pupil-to-retina PSF and compares against an analytic aperture limit.",
}


class SolverDocumentationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = Path(tempfile.mkdtemp(prefix="pt-solver-docs-"))

    def tearDown(self) -> None:
        shutil.rmtree(self.temp)

    def test_prompt_catalog_requires_actual_solver_and_cross_reference(self) -> None:
        case = self.temp / "case"; MODULE.scaffold_prompt(case, "batch-2027")
        text = "# Solver Usage Catalog\n\n" + "\n\n".join(f"## {heading}\n\nDocumented for HCIPy 0.7.0." for heading in MODULE.CATALOG_HEADINGS) + "\n\nFor the mathematical and numerical mechanism of this solver, see the Batch Solver-Mechanism Compendium, Chapter solver-hcipy.\n"
        (case / "reports" / "solver-usage-catalog.md").write_text(text, encoding="utf-8")
        (case / "provenance" / "solver-inventory.yaml").write_text(json.dumps({"batch_id": "batch-2027", "solvers": [SOLVER]}), encoding="utf-8")
        (case / "provenance" / "installation-record.md").write_text("# Installation\n\nOfficial source and smoke test recorded.\n", encoding="utf-8")
        (case / "provenance" / "software-citations.bib").write_text("@software{hcipy, title={HCIPy}}\n", encoding="utf-8")
        (case / "provenance" / "licenses.md").write_text("# License\n\nBSD-3-Clause.\n", encoding="utf-8")
        self.assertEqual(MODULE.validate_prompt(case), [])

    def test_batch_compendium_uses_actual_solver_once(self) -> None:
        batch = self.temp / "batch"; MODULE.scaffold_batch(batch)
        (batch / "data" / "batch-solver-index.yaml").write_text(json.dumps({"batch_id": "batch", "solvers": [SOLVER]}), encoding="utf-8")
        (batch / "data" / "solver-prompt-matrix.csv").write_text("prompt,primary_solver,module,numerical_method,role,evidence_level,chapter_id\nPinhole sunglasses,HCIPy,FraunhoferPropagator,FFT propagation,primary,idealized,solver-hcipy\n", encoding="utf-8")
        (batch / "data" / "software-citations.bib").write_text("@software{hcipy, title={HCIPy}}\n", encoding="utf-8")
        MODULE.build_compendium(batch)
        self.assertEqual(MODULE.validate_batch(batch), [])
        report = (batch / "reports" / "solver-mechanism-compendium.md").read_text(encoding="utf-8")
        self.assertIn("U(x,y)", report)
        self.assertIn("solver-hcipy", report)

    @unittest.skipUnless(BUNDLED_PYTHON.exists(), "bundled PDF runtime is unavailable")
    def test_catalog_renderer_writes_pdf(self) -> None:
        markdown = self.temp / "catalog.md"
        markdown.write_text("# Solver Usage Catalog\n\n## Solver decision\n\nHCIPy 0.7.0 is the actual primary solver.\n", encoding="utf-8")
        output = self.temp / "catalog.pdf"
        result = subprocess.run([str(BUNDLED_PYTHON), str(SCRIPT), "render", str(markdown), "--output", str(output)], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertTrue(output.read_bytes().startswith(b"%PDF-"))


if __name__ == "__main__":
    unittest.main()
