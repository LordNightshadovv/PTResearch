from __future__ import annotations

import shutil
import sys
import tempfile
import unittest
from pathlib import Path


SKILL_DIR = Path(__file__).resolve().parents[1]
SCRIPTS = SKILL_DIR / "scripts"
sys.path.insert(0, str(SCRIPTS))

from scaffold_case import scaffold  # noqa: E402
from validate_case import validate  # noqa: E402


def fixture_prompt(name: str) -> str:
    lines = (SKILL_DIR / "tests" / "fixtures" / name).read_text(encoding="utf-8").splitlines()
    quoted = [line[2:].rstrip() for line in lines if line.startswith("> ")]
    return "\n".join(quoted).replace("  \n", "\n")


def write(path: Path, text: str) -> None:
    path.write_text(text.strip() + "\n", encoding="utf-8")


def complete_case(case_dir: Path, kind: str) -> None:
    if kind == "pinhole":
        essence = """# Phenomenon essence (本质)
- **Status:** provisional
- **Statement:** The aperture array changes the effective pupil: admitted ray angle controls geometric defocus, diffraction limits small apertures, and pupil-overlapped open area controls transmitted power.
- **Mechanistic necessity test:** Removing angular restriction removes the myopia-correction mechanism; removing open area removes throughput.
## Main causal chain
array geometry → pupil mask → defocused propagation → retinal PSF/MTF → correction metric
array geometry → pupil overlap and open area → transmitted power → intensity metric
## Link table
| Link ID | Input | Model | Output | Assumptions | Prediction | Evidence | Confidence | Role |
|---|---|---|---|---|---|---|---|---|
| L1 | hole geometry [m] | aperture transmission | pupil field [a.u.] | paraxial branch | PSF changes | S1 | medium | essential |
"""
        candidates = """selection_outcome: coupled_model_stack
candidates:
  - candidate_id: P1
    name: "Fourier-optics pupil-mask model"
    status: selected_primary
    candidate_type: whole_chain
    provenance: literature_integrated
    equations:
      - equation: "PSF = abs(FT(P))^2"
        provenance_class: standard_textbook_relation
        source_or_derivation: "S1, optics text, section 4"
    selection_or_filter_reason: "Covers arrangement to retinal image and throughput interfaces."
  - candidate_id: P2
    name: "Geometric-defocus plus diffraction scaling"
    status: selected_alternative
    candidate_type: whole_chain
    provenance: constructed_first_principles
    equations:
      - equation: "b_geo scales with d times defocus; b_diff scales with wavelength over d"
        provenance_class: derived_in_this_report
        source_or_derivation: "Derived by combining S1 limiting relations under stated assumptions."
    selection_or_filter_reason: "Provides interpretable limiting behavior and a finite blur optimum."
  - candidate_id: P3
    name: "Pure geometric pinhole model"
    status: filtered
    candidate_type: component
    provenance: named_theory
    equations: []
    equations_unavailable_reason: "Not selected; its limiting relation is represented in P2."
    selection_or_filter_reason: "Insufficient alone because it predicts continued improvement as aperture shrinks and omits diffraction and throughput."
"""
        report_body = """The two prompt objectives—intensity reduction and myopia correction—are retained without comfort, ghosting, or field of view becoming mandatory objectives. No scalar weights are imposed; a Pareto front may represent the correction-throughput tradeoff.

The linked branches are optical correction and intensity attenuation. P1 Fourier-optics pupil-mask model is primary; P2 geometric-defocus plus diffraction scaling is the limiting model.

## 12. Filtered/rejected candidate ledger
P3 Pure geometric pinhole model entered through the large-aperture limit. It is plausible for geometric blur but filtered as complete because diffraction and intensity are absent. It remains a limiting component and would be reconsidered only where diffraction is demonstrably negligible.
"""
    else:
        essence = """# Phenomenon essence (本质)
- **Status:** competing_hypotheses
- **Statement:** Alternating electric field creates electromechanical strain; mounting transfers motion into a ceramic or board resonator whose surface velocity radiates the measured sound.
- **Mechanistic necessity test:** Removing voltage-to-strain coupling removes intrinsic vibration and fundamentally changes the sound.
## Main causal chain
voltage → electric field → electromechanical strain → equivalent force → structural modes → surface velocity → acoustic pressure
## Apparatus branches
Board-mounted MLCC: PCB modes dominate. Free body: ceramic modes dominate.
## Link table
| Link ID | Input | Model | Output | Assumptions | Prediction | Evidence | Confidence | Role |
|---|---|---|---|---|---|---|---|---|
| L1 | field [V/m] | nonlinear constitutive relation | strain [1] | material branch | harmonics | S1 | medium | essential |
"""
        candidates = """selection_outcome: competing_whole_chain_models
candidates:
  - candidate_id: S1
    name: "Electromechanical source to PCB modes to acoustic radiation"
    status: selected_primary
    candidate_type: whole_chain
    provenance: constructed_first_principles
    equations:
      - equation: "strain = d_eff E + Q E^2"
        provenance_class: standard_textbook_relation
        source_or_derivation: "S1, constitutive discussion, section 2"
      - equation: "M u_ddot + C u_dot + K u = B F"
        provenance_class: standard_textbook_relation
        source_or_derivation: "S1, structural dynamics section 3"
      - equation: "pressure is mapped from normal surface velocity"
        provenance_class: derived_in_this_report
        source_or_derivation: "Observation mapping assembled from S1 with radiation regime unresolved."
    selection_or_filter_reason: "Complete board-mounted voltage-to-sound chain with harmonic predictions."
  - candidate_id: S2
    name: "Free ceramic resonator and direct radiator"
    status: selected_alternative
    candidate_type: whole_chain
    provenance: constructed_first_principles
    equations: []
    equations_unavailable_reason: "Geometry-specific modal equation awaits apparatus dimensions; the unresolved gap is explicit."
    selection_or_filter_reason: "Branch-specific whole chain for a free or lightly supported body."
  - candidate_id: S3
    name: "Lumped RLC electrical resonance alone"
    status: filtered
    candidate_type: component
    provenance: named_theory
    equations: []
    equations_unavailable_reason: "Not selected as a whole-chain model."
    selection_or_filter_reason: "Electrical-only model cannot map voltage to displacement or acoustic pressure; retained as an input-stage correction."
  - candidate_id: S4
    name: "PCB resonance with unspecified forcing"
    status: filtered
    candidate_type: component
    provenance: named_theory
    equations: []
    equations_unavailable_reason: "Not selected as a whole-chain model."
    selection_or_filter_reason: "Structural-only model omits voltage-to-force transduction; retained as the mechanical component."
"""
        report_body = """Board-mounted and free-body branches remain separate. The constitutive relation predicts nonlinear harmonics and DC-bias dependence; the structural stage selects resonances; acoustic radiation maps surface velocity to pressure.

S1 Electromechanical source to PCB modes to acoustic radiation is primary for board mounting. S2 Free ceramic resonator and direct radiator is the free-body alternative.

## 12. Filtered/rejected candidate ledger
S3 Lumped RLC electrical resonance alone is plausible as an input correction but filtered as complete because it produces neither displacement nor pressure. S4 PCB resonance with unspecified forcing is plausible for peaks but filtered as complete because it omits transduction. Both remain components and would be reconsidered only as parts of a verified stack.
"""

    write(case_dir / "essence_and_chain.md", essence)
    write(case_dir / "model_registry.yaml", candidates)
    write(case_dir / "sources.yaml", """sources:
  - paper_id: S1
    title: "Verified canonical source"
    authors: ["Researcher, A."]
    year: 2024
    venue: "Physics source"
    doi_or_stable_id: "not_available"
    url: ""
    source_tier: "A"
    access_level: "full_text"
    identity_verified: true
    inclusion_reason: "Provides governing relations for an essential link."
""")
    write(case_dir / "problem_contract.yaml", (case_dir / "problem_contract.yaml").read_text(encoding="utf-8").replace('source: "TODO"', 'source: "official problem list"').replace('access_date: "TODO"', 'access_date: "2026-07-19"').replace('system_boundary: "TODO"', 'system_boundary: "apparatus to measured observable"'))
    write(case_dir / "candidate_decision_log.md", """# Candidate decision log
## Hard-gate results
All candidates are retained and every filtered whole-chain claim has an explicit reason.
## Advisory scores
Scores aid comparison and do not override hard gates.
## Filtered/rejected candidate ledger
See the final report for named candidates, evidence, residual uses, and reconsideration conditions.
""")
    write(case_dir / "handoff.md", """# Later-stage handoff
## Simulation-method handoff
Use the selected governing relations, measured geometry, boundary conditions, and discriminating outputs in a later simulation stage; no simulation was run.
## Experimental-observable handoff
Measure the predicted terminal observables and signatures that separate candidates; no full campaign was designed.
""")
    headings = [
        "1. Executive summary", "2. Official prompt and problem contract", "3. Phenomenon essence (本质)",
        "4. Causal-chain diagram and link table", "5. Apparatus branches and ambiguities",
        "6. Search strategy and source coverage", "7. Literature synthesis by causal link and model family",
        "8. Whole-chain candidate models", "9. Component-model mapping", "10. Mathematical audit",
        "11. Selected working model(s)",
    ]
    report = "# Theoretical research report\n\n" + "\n\n".join(f"## {h}\nEvidence-backed case section." for h in headings) + "\n\n" + report_body + "\n\n" + "\n\n".join(
        f"## {h}\nEvidence-backed case section." for h in [
            "13. Competing predictions and discrimination opportunities", "14. Research gaps and uncertainty",
            "15. Simulation-method handoff", "16. Experimental-observable handoff", "17. References",
            "18. Appendices: search log, paper matrix, model registry",
        ]
    )
    write(case_dir / "final_report.md", report)
    theory = case_dir / "theory"
    write(theory / "theory-model.md", "# Theoretical model\n\nA selected model relates a measurable output to controlled inputs.")
    write(theory / "equations.md", "# Equations\n\nY = f(X; p), derived here under the stated assumptions.")
    write(theory / "variables.csv", "symbol,meaning,unit,status,source\nY,observable,1,measured,experiment")
    write(theory / "assumptions.md", "# Assumptions\n\nThe stated reduced-model regime applies.")
    write(theory / "predictions.csv", "dependent_variable,independent_variable,value,unit,prediction_basis,parameter_values,provenance\nY,X,1,1,scaling,p=1,derived here")
    write(theory / "parameter-provenance.csv", "parameter,value,unit,status,source_or_method\np,1,1,assumed,stated assumption")
    write(theory / "literature-notes.md", "# Literature\n\nS1 supports the governing relation.")
    write(theory / "model-validation.md", "# Model validation\n\nDimensional and limiting-case checks are specified.")


class ScaffoldAndValidationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = Path(tempfile.mkdtemp(prefix="iypt-skill-test-"))

    def tearDown(self) -> None:
        shutil.rmtree(self.temp)

    def make_case(self, slug: str, fixture: str, kind: str) -> Path:
        case_dir = self.temp / slug
        scaffold(case_dir, fixture_prompt(fixture))
        complete_case(case_dir, kind)
        return case_dir

    def test_scaffold_creates_required_tree_and_preserves_existing_files(self) -> None:
        case_dir = self.temp / "sample-case"
        created, skipped = scaffold(case_dir, "Exact prompt")
        self.assertEqual(len(created), 18)
        self.assertFalse(skipped)
        self.assertTrue((case_dir / "papers").is_dir())
        write(case_dir / "prompt.md", "User-authored substantive prompt")
        created_again, skipped_again = scaffold(case_dir, "Different prompt")
        self.assertFalse(created_again)
        self.assertEqual(len(skipped_again), 18)
        self.assertIn("User-authored", (case_dir / "prompt.md").read_text(encoding="utf-8"))

    def test_unfinished_scaffold_fails_actionably(self) -> None:
        case_dir = self.temp / "draft-case"
        scaffold(case_dir, "Exact prompt")
        errors = validate(case_dir)
        self.assertTrue(any("placeholder" in error or "essence statement" in error for error in errors))

    def test_prompt_mismatch_fails(self) -> None:
        case_dir = self.make_case("prompt-mismatch", "pinhole-sunglasses.md", "pinhole")
        write(case_dir / "prompt.md", "A different prompt")
        self.assertTrue(any("exact prompt" in error for error in validate(case_dir)))

    def test_pinhole_fixture_passes_and_preserves_required_structure(self) -> None:
        case_dir = self.make_case("pinhole-sunglasses", "pinhole-sunglasses.md", "pinhole")
        self.assertEqual(validate(case_dir), [])
        report = (case_dir / "final_report.md").read_text(encoding="utf-8").lower()
        for phrase in ("intensity", "myopia", "fourier-optics", "diffraction", "pareto", "pure geometric"):
            self.assertIn(phrase, report)
        self.assertNotIn("mandatory objective: comfort", report)

    def test_singing_fixture_passes_and_preserves_required_structure(self) -> None:
        case_dir = self.make_case("singing-capacitor", "singing-capacitor.md", "singing")
        self.assertEqual(validate(case_dir), [])
        joined = ((case_dir / "final_report.md").read_text(encoding="utf-8") + (case_dir / "essence_and_chain.md").read_text(encoding="utf-8")).lower()
        for phrase in ("voltage", "electromechanical", "board-mounted", "free-body", "structural", "acoustic", "harmonic", "dc-bias"):
            self.assertIn(phrase, joined)

    def test_filtered_candidate_without_reason_fails(self) -> None:
        case_dir = self.make_case("broken-ledger", "pinhole-sunglasses.md", "pinhole")
        registry = (case_dir / "model_registry.yaml").read_text(encoding="utf-8")
        registry = registry.replace('    selection_or_filter_reason: "Insufficient alone because it predicts continued improvement as aperture shrinks and omits diffraction and throughput."\n', "")
        write(case_dir / "model_registry.yaml", registry)
        self.assertTrue(any("filtered candidate P3" in error for error in validate(case_dir)))

    def test_upstream_and_notice_artifacts_cover_all_sources(self) -> None:
        patterns = (SKILL_DIR / "references" / "upstream-patterns.md").read_text(encoding="utf-8")
        notices = (SKILL_DIR / "THIRD_PARTY_NOTICES.md").read_text(encoding="utf-8")
        for marker in ("OpenAI", "K-Dense", "DeerFlow", "Auto-Empirical"):
            self.assertIn(marker, patterns)
            self.assertIn(marker, notices)
        for sha in (
            "49f948faa9258a0c61caceaf225e179651397431",
            "3f825caafe149b7853ec8c4d1dd7f4553ea6b2a5",
            "0cd55067f39823e7f0950498b5197a8195512481",
            "b8912a3677f83d0abc3e3cccb06a35be04b146fc",
        ):
            self.assertIn(sha, patterns)


if __name__ == "__main__":
    unittest.main()
