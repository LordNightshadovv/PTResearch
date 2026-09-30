from __future__ import annotations

import importlib.util
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "tools" / "report-renderer" / "render_research_report.py"
BUNDLED_PYTHON = Path("/Users/vold/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3")
SPEC = importlib.util.spec_from_file_location("report_renderer", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(MODULE)


MODEL = """# Theoretical model
## Research question
How does the observable change with forcing?
## Observable
Y is the measured displacement in m.
## Independent variables
X is the controlled force in N.
## Proposed mechanism
Elastic restoring force balances the applied forcing.
## Governing equations
The governing relation is defined below.
## Derivation
Force balance gives the relationship.
## Predicted relationship
Holding k fixed, the model predicts that Y increases with X because the elastic response is linear.
## Simulation formulation
The solver implements the force balance with specified boundary conditions.
## Limitations
The model excludes geometric nonlinearity.
## References
[S1] Textbook source.
"""

LATEX = r"""\documentclass{article}
\begin{document}
\section{Problem and research question} Force-displacement response.
\section{Observables and variables} $Y$ is displacement in \si{m}; $X$ is force in \si{N}; $k$ is stiffness in \si{N/m}.
\section{Physical mechanism and model choice} Elastic restoring force balances the applied force \cite{S1}.
\section{Assumptions and validity range} Small deformation and linear elasticity.
\section{Governing equations and derivation}
\begin{equation} Y = \frac{X}{k}. \end{equation}
The left side is displacement; the numerator is forcing; the denominator is restoring stiffness. This is derived here from static force balance.
\section{Main prediction and limiting cases} Holding $k$ fixed, $Y$ increases with $X$; $X=0$ gives $Y=0$.
\section{Theory-to-solver mapping} The solver discretizes the stated equilibrium equation.
\section{Calculated example or prediction} For $X=1$ N and $k=100$ N/m, $Y=0.01$ m.
\section{Limitations and references} Geometric nonlinearity is omitted. \cite{S1}
\end{document}
"""


class TheoreticalReportRendererTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = Path(tempfile.mkdtemp(prefix="pt-renderer-test-"))
        theory = self.temp / "theory"; theory.mkdir()
        (theory / "theory-model.md").write_text(MODEL, encoding="utf-8")
        (theory / "equations.md").write_text("# Equations\n\n$$Y = \\frac{X}{k}$$\n\nDerived here from static force balance; valid for linear elasticity.\n", encoding="utf-8")
        (theory / "variables.csv").write_text("symbol,meaning,unit,status,source\nY,displacement,m,measured,experiment\nX,force,N,controlled,experiment\nk,stiffness,N/m,literature,[S1]\n", encoding="utf-8")
        (theory / "assumptions.md").write_text("# Assumptions\n\nSmall deformation and linear elasticity apply in the stated range.\n", encoding="utf-8")
        (theory / "predictions.csv").write_text("dependent_variable,independent_variable,value,unit,prediction_basis,parameter_values,provenance\nY,X,0.010,m,Y=X/k,k=100 N/m,derived here\n", encoding="utf-8")
        (theory / "parameter-provenance.csv").write_text("parameter,value,unit,status,source_or_method\nk,100,N/m,literature,[S1]\n", encoding="utf-8")
        (theory / "literature-notes.md").write_text("# Literature\n\n[S1] DOI: 10.1000/example. This source supplies the linear-elastic constitutive relation used in the force balance.\n", encoding="utf-8")
        (theory / "model-validation.md").write_text("# Validation\n\nCheck dimensions and compare the predicted displacement with a force-displacement calibration.\n", encoding="utf-8")
        reports = self.temp / "reports"; reports.mkdir()
        (reports / "theoretical-model.tex").write_text(LATEX, encoding="utf-8")

    def tearDown(self) -> None:
        shutil.rmtree(self.temp)

    def test_complete_package_passes_preflight(self) -> None:
        self.assertEqual(MODULE.validate_theory_package(self.temp), [])

    def test_internal_artifact_pointer_is_rejected(self) -> None:
        path = self.temp / "theory" / "theory-model.md"
        path.write_text(MODEL + "\nSee the model registry for equations.\n", encoding="utf-8")
        self.assertTrue(any("internal artifact" in error for error in MODULE.validate_theory_package(self.temp)))

    def test_equations_are_converted_without_raw_latex(self) -> None:
        rendered = MODULE.readable_math(r"Y = \frac{X}{k} \approx \lambda")
        self.assertEqual(rendered, "Y = (X)/(k) approximately lambda")
        self.assertNotIn("\\", rendered)

    def test_latex_without_numbered_equation_is_rejected(self) -> None:
        path = self.temp / "reports" / "theoretical-model.tex"
        path.write_text(LATEX.replace(r"\begin{equation} Y = \frac{X}{k}. \end{equation}", "Y = X/k."), encoding="utf-8")
        self.assertTrue(any("numbered LaTeX equations" in error for error in MODULE.validate_theory_package(self.temp)))

    @unittest.skipUnless(BUNDLED_PYTHON.exists(), "bundled PDF runtime is unavailable")
    def test_renderer_writes_standalone_pdf_with_equation(self) -> None:
        (self.temp / "problem_contract.yaml").write_text('{"exact_prompt": "Measure displacement under controlled force."}\n', encoding="utf-8")
        output = self.temp / "theoretical-report.pdf"
        result = subprocess.run([str(BUNDLED_PYTHON), str(SCRIPT), str(self.temp), "--output", str(output)], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertTrue(output.read_bytes().startswith(b"%PDF-"))
        check = subprocess.run([str(BUNDLED_PYTHON), "-c", "from pypdf import PdfReader; import sys; print('\\n'.join(page.extract_text() or '' for page in PdfReader(sys.argv[1]).pages))", str(output)], capture_output=True, text=True)
        self.assertEqual(check.returncode, 0, check.stdout + check.stderr)
        self.assertIn("Y = (X)/(k)", check.stdout)
        self.assertNotIn("See the model registry", check.stdout)


if __name__ == "__main__":
    unittest.main()
