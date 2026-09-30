from __future__ import annotations

import copy
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
SPEC = importlib.util.spec_from_file_location("scientific_contract", ROOT / "scripts" / "scientific_contract.py")
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(MODULE)


def write(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


class ScientificContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.case = Path(self.temp.name) / "case"
        self.case.mkdir()
        (self.case / "reports").mkdir()
        (self.case / "theory").mkdir()
        self.core = self._base()
        for relative, value in self.core.items():
            write(self.case / relative, value)
        generator = ROOT / "tools" / "simulation-package" / "generate_package.py"
        generated = subprocess.run(
            [sys.executable, str(generator), "--route", "elmer_fem", "--output", str(self.case / "linux-simulation"), "--model-id", "reduced"],
            capture_output=True, text=True,
        )
        if generated.returncode:
            raise AssertionError(generated.stdout + generated.stderr)
        self._write_report()
        (self.case / "theory" / "predictions.csv").write_text(
            "dependent_variable,independent_variable,equation_id\n"
            "tip displacement,drive voltage,eq-state\n",
            encoding="utf-8",
        )

    def tearDown(self) -> None:
        self.temp.cleanup()

    def _base(self) -> dict[str, dict]:
        exact = "Drive a vented electromechanical strip and measure its tip displacement."
        return {
            "project_state.yaml": {"contract_version": 3, "simulation_contract_version": 1, "case_id": "test", "exact_prompt": exact, "stage": "simulation_routed", "scientific_readiness": "model_closed", "software_readiness": "implementation_ready", "claim_ceiling": "implementation_ready_only", "claims": []},
            "problem_contract.yaml": {
                "contract_version": 3, "case_id": "test", "exact_prompt": exact,
                "primary_observables": ["tip displacement"], "controlled_inputs": ["drive voltage"],
                "experimental_parameter_ranges": [{"name": "drive voltage", "unit": "V", "range": "0-10"}],
                "constraints": ["vent remains open"], "apparatus_branches": ["spectacle-plane mask is distinct from pupil plane"],
            },
            "source_registry.yaml": {"sources": [
                {"id": "S1", "title": "Canonical constitutive source", "authors": ["A"], "year": 2020, "venue": "Journal", "doi_or_stable_id": "doi:test", "access_status": "full_text", "quality_tier": "A", "directness": "direct_same_mechanism", "url": "https://example.test/paper"},
                {"id": "S2", "title": "Apparatus measurement", "authors": ["B"], "year": 2021, "venue": "Journal", "doi_or_stable_id": "doi:apparatus", "access_status": "full_text", "quality_tier": "A", "directness": "direct_same_apparatus", "url": "https://example.test/apparatus"},
            ]},
            "model_registry.yaml": {
                "selection_outcome": "selected_working_baseline",
                "selected_candidate_ids": ["reduced"],
                "single_candidate_exception": "",
                "comparison_table": [
                    {"candidate_id": "reduced", "explains": ["tip displacement"], "limitations": ["small strain only"], "required_parameters": ["stiffness"], "experimental_discriminator": "linear voltage scaling"},
                    {"candidate_id": "competitor", "explains": ["tip displacement"], "limitations": ["higher data need"], "required_parameters": ["nonlinear coefficient"], "experimental_discriminator": "quadratic voltage scaling"},
                ],
                "selection_rationale_against_alternatives": "The reduced model matches the measured low-voltage scaling; the competitor remains testable at higher voltage.",
                "stopping_decision": {"status": "continue", "rationale": "model and data are sufficient to continue", "blocking_items": [], "allowed_claim_level": "working_model", "resumption_conditions": []},
                "candidates": [
                    self._candidate("reduced", "selected_working_baseline", "minimal_analytical", "competitor"),
                    self._candidate("competitor", "retained_competitor", "competing_mechanism", "reduced"),
                ],
            },
            "simulation_route.yaml": {
                "selected_model_id": "reduced", "selected_route": "elmer_fem", "primary_solver": "Elmer FEM",
                "openfoam_classification": "Unsuitable", "single_solver_baseline": "Closed electromechanical FEM",
                "second_solver_escalation": {"status": "not_required", "condition": "closed baseline"},
                "governing_physics": ["electromechanical strain"], "required_fields": ["displacement"],
                "rationale": "Closed equations require coupled finite elements.", "solver_requirements_id": "solver_requirements.yaml",
                "selection_chain": {
                    "phenomenon": "voltage-driven strip displacement",
                    "physics": ["electromechanical strain", "elastic deformation"],
                    "governing_equation_ids": ["eq-drive", "eq-state"],
                    "numerical_requirements": ["coupled electric and displacement fields", "resolved strip geometry"],
                    "solver": "Elmer FEM",
                },
            },
            "apparatus_fidelity.yaml": {
                "geometry_topology": "A vented enclosure surrounds a clamped moving strip.",
                "features": [
                    {"apparatus_feature": "vent is open", "model_representation": "ambient pressure boundary", "match_status": "matched", "justification": "matches drawing", "consequence_if_wrong": "sealed pressure changes stiffness", "required_measurement_or_source": "vent clearance"},
                    {"apparatus_feature": "mask is at spectacle plane", "model_representation": "propagation from mask to pupil", "match_status": "matched", "justification": "planes remain separate", "consequence_if_wrong": "incorrect transfer function", "required_measurement_or_source": "mask-pupil spacing"},
                ],
                "observable": "tip displacement", "parameter_ranges": [{"name": "drive voltage", "range": "0-10 V"}],
            },
            "evidence_matrix.yaml": {
                "claims": [
                    {"claim_id": "C1", "claim": "voltage produces strain", "importance": "central_quantitative", "source_ids": ["S1"], "directness": ["direct_same_mechanism"], "status": "sufficient", "evidence_direction": "supporting"},
                    {"claim_id": "C2", "claim": "vented apparatus geometry", "importance": "central_qualitative", "source_ids": ["S2"], "directness": ["direct_same_apparatus"], "status": "sufficient", "evidence_direction": "limiting"},
                ],
                "negative_evidence_review": [
                    {"candidate_id": "reduced", "supporting_evidence_ids": ["C1"], "opposing_evidence_ids": [], "opposing_search_outcome": "No direct contradiction found after targeted nonlinear-response search.", "limitations": ["small-strain evidence only"], "competing_interpretations": ["nonlinear constitutive response"]},
                    {"candidate_id": "competitor", "supporting_evidence_ids": ["C1"], "opposing_evidence_ids": ["C2"], "opposing_search_outcome": "Apparatus evidence limits the competitor's sealed-cavity interpretation.", "limitations": ["coefficient not measured"], "competing_interpretations": ["linear strain response"]},
                ],
            },
            "solver_requirements.yaml": {
                "model_closure_status": "closed", "fields_and_degrees_of_freedom": ["electric potential", "displacement"],
                "geometry_and_moving_interfaces": ["clamped strip"], "constitutive_laws": ["linear piezoelectric law"],
                "multiphysics_coupling": ["electric to strain"], "expected_regimes": ["small strain"],
                "required_outputs": ["tip displacement"], "numerical_challenges": ["coupled stiffness"],
                "verification_benchmarks": ["static beam limit"], "simpler_tools_insufficient_because": "spatial modes affect the observable",
                "dimensionless_analysis": {
                    "applicability": "applicable",
                    "groups": [{"name": "slenderness", "definition": "L/t", "physical_meaning": "beam slenderness", "value_or_range": "100-200", "regime_implication": "beam-like deformation", "parameter_sources": ["measured length", "measured thickness"]}],
                    "regime_identification": "slender, small-strain beam regime",
                    "not_applicable_justification": "",
                },
            },
            "simulation_handoff.yaml": {
                "simulation_contract_version": 1, "primary_solver": "Elmer FEM", "version_policy": "locked supported release",
                "solver_distribution": "external_reference", "highest_state": "implementation_ready", "scientific_readiness": "model_closed", "software_readiness": "implementation_ready", "claim_ceiling": "implementation_ready_only", "state_evidence": [],
                "official_installation_source": "https://www.elmerfem.org/", "documentation_locator": "Models Manual, piezoelectric section",
                "parameter_mapping": [{"parameter": "drive voltage", "destination_kind": "Elmer SIF boundary condition", "destination": "native/case.sif:Boundary Condition 1 Potential", "equation_id": "eq-drive", "implemented_file": "src/model.py", "implemented_symbol": "compute", "units": "V", "notation_conversion": "V is passed as the controlled voltage", "discretization_or_approximation": "static synthetic benchmark", "implementation_assumptions": ["small strain"]}],
                "boundary_and_initial_conditions": ["clamped root", "zero initial displacement"],
                "discretization_plan": "mesh and timestep refinement", "controls": "nonlinear tolerance and timestep",
                "output_extraction": "tip displacement probe", "verification_plan": ["static beam limit", "mesh sensitivity"],
                "validation_plan": ["compare independent displacement measurements with uncertainty"],
                "validation_chain": [{
                    "experiment_measurement": "camera-measured tip displacement versus voltage",
                    "simulation_input": "measured voltage and strip geometry",
                    "solver_quantity": "nodal displacement field",
                    "output_metric": "tip displacement amplitude",
                    "comparison_method": "weighted residual and confidence-band coverage",
                    "uncertainty_treatment": "propagate camera and geometry uncertainty",
                    "acceptance_criterion": "reduced chi-square <= 2 and 95% interval coverage",
                }],
                "beginner_readme": "linux-simulation/README.md",
            },
            "parameter_equation_map.yaml": {
                "mappings": [{"experimental_parameter": "drive voltage", "model_symbol": "V", "entry_kind": "boundary_condition", "equation_or_boundary_id": "eq-drive", "intermediate_state": "strain", "predicted_observable": "tip displacement"}],
                "symbols": [
                    {"symbol": "V", "meaning": "drive voltage", "si_unit": "V", "status": "controlled", "parameter_class": "control_variable", "uncertainty_or_provenance": "meter specification", "admissible_range": "0-10 V", "history_variable": False},
                    {"symbol": "q", "meaning": "modal displacement", "si_unit": "m", "status": "calculated", "parameter_class": "measured_state_variable", "uncertainty_or_provenance": "model", "admissible_range": "small strain", "history_variable": True},
                    {"symbol": "Y", "meaning": "tip displacement", "si_unit": "m", "status": "observable", "parameter_class": "measured_state_variable", "uncertainty_or_provenance": "camera", "admissible_range": "0-1 mm", "history_variable": False},
                ],
            },
            "theory/equations.yaml": {"equations": [
                {
                    "id": "eq-drive", "latex": "S=dV", "role": "constitutive", "provenance_class": "adapted_source_equation",
                    "source_claims": [{"source_id": "S1", "supports": ["functional_form"], "retrieval_status": "verified_full_text", "exact_locator": {"section": "3.2", "pages": "114-116", "equation": "Eq. (7)"}, "locator_verification": {"status": "verified_against_source", "evidence": "page audit"}}],
                    "derivation_steps": ["map electric field to applied voltage", "substitute apparatus thickness"],
                    "assumptions": ["linear response"], "dimensional_check": "strain is dimensionless", "limiting_cases": ["V=0 gives S=0"],
                    "falsifier": "nonlinear strain at low voltage", "symbols": ["V"], "produces": ["strain"],
                    "transformation_map": {"source_equation": "S=dE", "source_notation": "E", "substitutions_or_approximations": ["E=V/t"], "apparatus_specific_changes": ["measured thickness"], "resulting_equation": "S=dV/t", "dimensional_check": "dimensionless", "new_assumptions": ["uniform field"]},
                    "lineage": {
                        "source_basis": [{"source_id": "S1", "source_title": "Canonical constitutive source", "source_authors": ["A"], "exact_locator": {"availability": "verified", "section": "3.2", "pages": "114-116", "equation": "Eq. (7)"}}],
                        "original_equation": "S=dE", "assumptions": ["linear response", "uniform field"],
                        "transformations_made": ["substitute E=V/t"], "final_equation": "S=dV",
                        "adaptation_justification": "map the source electric field to the controlled apparatus voltage",
                    },
                },
                {
                    "id": "eq-state", "latex": "M q''+Kq=F(S)", "role": "governing", "provenance_class": "original_derivation",
                    "source_claims": [], "starting_principles": [{"source_id": "S1", "exact_locator": {"section": "2", "equation": "Eq. (2)"}}],
                    "derivation_steps": ["apply virtual work", "project onto the measured mode"], "assumptions": ["small displacement"],
                    "dimensional_check": "each term is force", "limiting_cases": ["static beam limit"], "falsifier": "unpredicted mode",
                    "symbols": ["q", "Y"], "produces": ["tip displacement"], "closes_variables": ["q"],
                    "lineage": {
                        "source_basis": [{"source_id": "S1", "source_title": "Canonical constitutive source", "source_authors": ["A"], "exact_locator": {"availability": "verified", "section": "2", "equation": "Eq. (2)"}}],
                        "original_equation": "virtual-work balance", "assumptions": ["small displacement"],
                        "transformations_made": ["project onto the measured mode"], "final_equation": "M q''+Kq=F(S)",
                        "adaptation_justification": "retain the apparatus mode that produces the measured tip displacement",
                    },
                },
            ]},
        }

    @staticmethod
    def _candidate(candidate_id: str, status: str, kind: str, competitor: str) -> dict:
        return {
            "id": candidate_id, "name": candidate_id, "status": status, "candidate_kind": kind,
            "causal_mechanism": "voltage to strain to displacement", "governing_equation_ids": ["eq-drive", "eq-state"],
            "validity_range": "small strain", "predicted_observables": ["tip displacement"],
            "identifiable_parameters": ["stiffness"], "decisive_falsifier": "wrong voltage scaling",
            "discriminating_experiment": {"competitor_id": competitor, "predicted_difference": "linear versus quadratic voltage scaling"},
            "computational_cost": "low", "solver_needs": "coupled FEM", "evidence_quality": "direct mechanism plus apparatus data",
            "comparison_scores": {"apparatus_fidelity": 4, "closure": 4}, "variables": [{"symbol": "V", "unit": "V"}],
            "assumptions": ["small strain"], "prohibited_assumptions": ["sealed enclosure"],
        }

    def _write_report(self) -> None:
        (self.case / "reports" / "theoretical-model.tex").write_text(
            "\\begin{equation}S=dV\\label{eq:eq-drive}\\end{equation}\n"
            "Provenance [eq-drive]: Adapted from S1, Section 3.2, pp. 114-116, Eq. (7), after E=V/t.\n"
            "\\begin{equation}Mq''+Kq=F(S)\\label{eq:eq-state}\\end{equation}\n"
            "Provenance [eq-state]: Original derivation from S1 Section 2 Eq. (2), with virtual-work steps shown.\n"
            "Source $\\rightarrow$ Original equation $\\rightarrow$ Assumptions $\\rightarrow$ Adaptation $\\rightarrow$ Final model\n"
            "Candidate & Explains & Limitations & Required parameters & Experimental discriminator\n",
            encoding="utf-8",
        )

    def errors(self) -> list[str]:
        return MODULE.validate_v3(self.case, self.core, ROOT)

    def mutate(self, relative: str, callback) -> None:
        value = copy.deepcopy(self.core[relative])
        callback(value)
        self.core[relative] = value
        write(self.case / relative, value)

    def assert_error(self, needle: str) -> None:
        errors = self.errors()
        self.assertTrue(any(needle in error for error in errors), errors)

    def test_complete_external_solver_adapter_and_exact_locator_pass(self):
        self.assertEqual(self.errors(), [])
        report = (self.case / "reports" / "theoretical-model.tex").read_text()
        self.assertIn("Eq. (7)", report)

    def test_open_apparatus_incorrectly_sealed_fails(self):
        self.mutate("apparatus_fidelity.yaml", lambda x: x["features"][0].update(match_status="contradicted", model_representation="sealed cavity"))
        self.assert_error("apparatus fidelity contradiction")

    def test_spectacle_mask_silently_moved_to_pupil_fails(self):
        self.mutate("apparatus_fidelity.yaml", lambda x: x["features"][1].update(match_status="contradicted", model_representation="pupil-plane mask"))
        self.assert_error("apparatus fidelity contradiction")

    def test_experimental_variable_absent_from_equations_fails(self):
        self.mutate("problem_contract.yaml", lambda x: x["controlled_inputs"].append("drive frequency"))
        self.assert_error("experimental controls absent")

    def test_history_variable_without_evolution_law_fails(self):
        self.mutate("theory/equations.yaml", lambda x: x["equations"][1].update(closes_variables=[]))
        self.assert_error("history/state variables lack")

    def test_homepage_only_when_exact_locator_retrievable_fails(self):
        def change(x):
            claim = x["equations"][0]["source_claims"][0]
            claim["exact_locator"] = {"url_anchor": ""}
        self.mutate("theory/equations.yaml", change)
        self.assert_error("omits a discoverable exact locator")

    def test_fabricated_page_or_equation_locator_fails(self):
        self.mutate("theory/equations.yaml", lambda x: x["equations"][0]["source_claims"][0]["locator_verification"].update(status="unsupported_or_inconsistent"))
        self.assert_error("unsupported or fabricated locator")

    def test_context_source_cannot_solely_support_constitutive_law(self):
        self.mutate("source_registry.yaml", lambda x: x["sources"][0].update(directness="contextual_only"))
        self.assert_error("supported only by contextual")

    def test_theory_package_solver_mismatch_fails(self):
        self.mutate("simulation_handoff.yaml", lambda x: x.update(primary_solver="OpenFOAM"))
        self.assert_error("solver and simulation handoff solver do not match")

    def test_problem_omitted_from_batch_matrix_fails(self):
        write(self.case / "batch_manifest.yaml", {"problems": ["Problem A", "Problem B"]})
        (self.case / "data").mkdir()
        (self.case / "data" / "solver-prompt-matrix.csv").write_text("problem,solver\nProblem A,Elmer FEM\n", encoding="utf-8")
        self.assert_error("Problem B")

    def test_claimed_run_without_receipts_fails(self):
        self.mutate("simulation_handoff.yaml", lambda x: x.update(highest_state="executed", state_evidence=[]))
        self.mutate("project_state.yaml", lambda x: x["claims"].append({"stage": "executed", "status": "completed"}))
        self.assert_error("lacks evidence for smoke_tested")

    def test_adapted_equation_without_transformation_map_fails(self):
        self.mutate("theory/equations.yaml", lambda x: x["equations"][0].pop("transformation_map"))
        self.assert_error("source-to-report transformation map")

    def test_original_derivation_with_cited_principles_passes(self):
        self.assertEqual(self.errors(), [])

    def test_genuinely_unavailable_locator_with_search_record_passes(self):
        def change(x):
            claim = x["equations"][0]["source_claims"][0]
            claim["retrieval_status"] = "not_available"
            claim.pop("exact_locator")
            claim.pop("locator_verification")
            claim["locator_searches"] = ["publisher PDF", "author manuscript", "canonical alternative"]
            claim["support_limit"] = "metadata supports source identity only; coefficient remains provisional"
        self.mutate("theory/equations.yaml", change)
        self.assertEqual(self.errors(), [])

    def test_unresolved_selection_is_allowed(self):
        def change(x):
            x["selection_outcome"] = "unresolved"
            x["selected_candidate_ids"] = []
            x["candidates"][0]["status"] = "unresolved"
        self.mutate("model_registry.yaml", change)
        self.mutate("model_registry.yaml", lambda x: x["stopping_decision"].update(
            status="stop_unresolved_mechanism",
            rationale="the experiment cannot yet discriminate the mechanisms",
            blocking_items=["missing high-voltage response"],
            allowed_claim_level="competing_hypotheses",
            resumption_conditions=["measure the high-voltage scaling"],
        ))
        self.mutate("simulation_route.yaml", lambda x: (
            x.update(primary_solver="No numerical solver", selected_model_id="unresolved"),
            x["selection_chain"].update(solver="No numerical solver"),
        ))
        self.mutate("simulation_handoff.yaml", lambda x: x.update(primary_solver="No numerical solver", highest_state="not_applicable", scientific_readiness="scientific_stop", software_readiness="not_applicable", claim_ceiling="scientific_stop"))
        with (self.case / "reports" / "theoretical-model.tex").open("a", encoding="utf-8") as stream:
            stream.write("\nstop_unresolved_mechanism\ncompeting_hypotheses\n")
        self.assertEqual(self.errors(), [])

    def test_equation_without_complete_lineage_fails(self):
        self.mutate("theory/equations.yaml", lambda x: x["equations"][0].pop("lineage"))
        self.assert_error("lacks Source -> Original equation")

    def test_comparison_table_must_cover_every_candidate(self):
        self.mutate("model_registry.yaml", lambda x: x["comparison_table"].pop())
        self.assert_error("comparison table must cover")

    def test_negative_evidence_review_is_mandatory(self):
        self.mutate("evidence_matrix.yaml", lambda x: x["negative_evidence_review"].pop())
        self.assert_error("negative-evidence review must cover")

    def test_dimensionless_regime_analysis_is_mandatory(self):
        self.mutate("solver_requirements.yaml", lambda x: x.pop("dimensionless_analysis"))
        self.assert_error("lack dimensionless analysis")

    def test_parameter_class_is_mandatory(self):
        self.mutate("parameter_equation_map.yaml", lambda x: x["symbols"][0].pop("parameter_class"))
        self.assert_error("lacks required parameter classification")

    def test_physics_first_selection_chain_is_mandatory(self):
        self.mutate("simulation_route.yaml", lambda x: x.pop("selection_chain"))
        self.assert_error("Phenomenon -> Physics")

    def test_experiment_to_simulation_validation_chain_is_mandatory(self):
        self.mutate("simulation_handoff.yaml", lambda x: x.update(validation_chain=[]))
        self.assert_error("experiment-to-simulation validation chain")


if __name__ == "__main__":
    unittest.main()
