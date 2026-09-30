from __future__ import annotations

import hashlib
import importlib.util
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("calibration_contract", ROOT / "scripts" / "calibration_contract.py")
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
sys.path.insert(0, str(ROOT / "scripts"))
SPEC.loader.exec_module(MODULE)
from artifact_lib import basic_schema_errors, load_schema  # noqa: E402


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class CalibrationContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.case = Path(self.temp.name) / "case"
        shutil.copytree(ROOT / "tests" / "fixtures" / "pinhole-sunglasses", self.case)
        self.model_id = "fourier-pupil"
        # Preserve the fixture's complete simulation specification so the
        # positive test exercises validate_artifacts.py end to end.
        (self.case / "project_state.yaml").write_text(
            json.dumps({"case_id": "calibration", "exact_prompt": "p", "stage": "physically_validated", "calibration_contract_version": 1, "claims": []}),
            encoding="utf-8",
        )
        contract = json.loads((self.case / "problem_contract.yaml").read_text())
        contract["exact_prompt"] = "p"
        (self.case / "problem_contract.yaml").write_text(json.dumps(contract), encoding="utf-8")
        self._write_valid_plan()

    def tearDown(self) -> None:
        self.temp.cleanup()

    def _write_valid_plan(self) -> None:
        fit_hash = "a" * 64
        validation_hash = "b" * 64
        dataset_hash = "c" * 64
        records = [
            {"observation_id": "o1", "group_id": "g1", "replicate_id": "r1", "split": "fit"},
            {"observation_id": "o2", "group_id": "g2", "replicate_id": "r2", "split": "fit"},
            {"observation_id": "o3", "group_id": "g3", "replicate_id": "r3", "split": "validation"},
            {"observation_id": "o4", "group_id": "g4", "replicate_id": "r4", "split": "validation"},
        ]
        self.fit_artifact = self.case / "frozen_fit.json"
        fit_content = {
            "model_id": self.model_id,
            "dataset_content_hash": dataset_hash,
            "fit_data_hash": fit_hash,
            "objective_value": 0.05,
            "parameter_values": [{"name": "alpha", "value": 1.0, "unit": "m"}],
        }
        self.fit_artifact.write_text(json.dumps(fit_content, sort_keys=True), encoding="utf-8")
        evidence = self.case / "evidence.json"
        evidence.write_text("evidence\n", encoding="utf-8")
        self.evidence_hash = sha256(evidence)
        fit_artifact_hash = sha256(self.fit_artifact)
        plan = {
            "calibration_contract_version": 1,
            "status": "physically_validated",
            "claim_ceiling": "independent_validation_supported",
            "dataset": {
                "dataset_id": "bench-1",
                "source": "bench record",
                "source_locator": "records/bench-1.csv",
                "content_hash": dataset_hash,
                "unit_system": "SI",
                "variables": [{"name": "height", "unit": "m", "uncertainty_status": "measured", "uncertainty": {"value": 0.01, "unit": "m"}}],
                "observation_index": records,
            },
            "objective": {
                "metric": "weighted_rmse",
                "formula": "sqrt(sum(w*r^2)/sum(w))",
                "direction": "minimize",
                "predeclared_at": "2026-01-01T00:00:00+00:00",
                "target_observables": ["height"],
                "acceptance_threshold": {"value": 0.1, "unit": "m"},
            },
            "parameter_definitions": [{
                "name": "alpha", "unit": "m", "lower_bound": 0.0, "upper_bound": 2.0, "role": "calibrated",
                "identifiability": {"method": "profile_likelihood", "status": "pass", "evidence_locator": "evidence.json", "metric": 0.02},
            }],
            "split": {
                "strategy": "grouped_holdout",
                "fit_observation_ids": ["o1", "o2"], "validation_observation_ids": ["o3", "o4"],
                "fit_group_ids": ["g1", "g2"], "validation_group_ids": ["g3", "g4"],
                "fit_replicate_ids": ["r1", "r2"], "validation_replicate_ids": ["r3", "r4"],
                "fit_data_hash": fit_hash, "validation_data_hash": validation_hash,
            },
            "fit_result": {
                "status": "frozen", "fit_artifact_locator": "frozen_fit.json", "fit_artifact_hash": fit_artifact_hash,
                "fit_data_hash": fit_hash, "fit_started_at": "2026-01-02T00:00:00+00:00", "frozen_at": "2026-01-03T00:00:00+00:00",
                "parameter_values": [{"name": "alpha", "value": 1.0, "unit": "m"}], "objective_value": 0.05,
                "residual_summary": {"n": 2, "rmse": 0.05, "max_abs": 0.08, "normalized_rmse": 0.05, "computed_by": "fit-check", "computed_at": "2026-01-03T00:00:00+00:00", "evidence_locator": "evidence.json"},
                "numerical_error": {"estimate": 0.001, "tolerance": 0.01, "unit": "m", "method": "mesh-refinement", "computed_by": "verification", "computed_at": "2026-01-03T00:00:00+00:00"},
            },
            "independent_validation": {
                "status": "passed", "dataset_id": "bench-1", "data_hash": validation_hash, "fit_artifact_hash": fit_artifact_hash,
                "observation_ids": ["o3", "o4"], "group_ids": ["g3", "g4"], "replicate_ids": ["r3", "r4"],
                "comparison_method": "held-out weighted RMSE", "uncertainty_method": "propagated standard uncertainty",
                "acceptance_criterion": "objective_value <= predeclared threshold", "objective_value": 0.08,
                "residual_summary": {"n": 2, "rmse": 0.08, "max_abs": 0.09, "normalized_rmse": 0.08, "computed_by": "validation-check", "computed_at": "2026-01-04T00:00:00+00:00", "evidence_locator": "evidence.json"},
                "numerical_error": {"estimate": 0.001, "tolerance": 0.01, "unit": "m", "method": "mesh-refinement", "computed_by": "verification", "computed_at": "2026-01-04T00:00:00+00:00"},
                "performed_at": "2026-01-04T00:00:00+00:00",
            },
        }
        (self.case / "calibration_plan.yaml").write_text(json.dumps(plan), encoding="utf-8")
        report = {
            "status": "passed", "checks": [], "accepted_for_scientific_use": True,
            "numerical_verification": {"status": "passed", "criterion_value": 0.001, "criterion_threshold": 0.01, "computed_by": "verification", "computed_at": "2026-01-04T00:00:00+00:00", "evidence_locator": "evidence.json", "evidence_hash": self.evidence_hash},
            "physical_validation": {"status": "passed", "independent": True, "independent_dataset_id": "bench-1", "data_hash": validation_hash, "fit_artifact_hash": fit_artifact_hash, "observation_ids": ["o3", "o4"], "uncertainty_method": "propagated standard uncertainty", "criterion_value": 0.08, "criterion_threshold": 0.1, "computed_by": "validation-check", "computed_at": "2026-01-04T00:00:00+00:00", "evidence_locator": "evidence.json", "evidence_hash": self.evidence_hash},
        }
        (self.case / "validation_report.yaml").write_text(json.dumps(report), encoding="utf-8")

    def _loaded(self) -> dict[str, object]:
        return {
            "project_state.yaml": json.loads((self.case / "project_state.yaml").read_text()),
            "simulation_spec.yaml": json.loads((self.case / "simulation_spec.yaml").read_text()),
        }

    def test_valid_frozen_fit_and_held_out_validation_pass(self) -> None:
        self.assertEqual(MODULE.validate_calibration_contract(self.case, self._loaded()), [])

    def test_full_artifact_validator_accepts_the_valid_calibration_case(self) -> None:
        result = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "validate_artifacts.py"), str(self.case)],
            capture_output=True, text=True,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_overlap_is_rejected_even_when_report_says_passed(self) -> None:
        path = self.case / "calibration_plan.yaml"
        plan = json.loads(path.read_text())
        plan["split"]["validation_observation_ids"] = ["o1", "o4"]
        path.write_text(json.dumps(plan), encoding="utf-8")
        errors = MODULE.validate_calibration_contract(self.case, self._loaded())
        self.assertTrue(any("overlap" in error for error in errors), errors)

    def test_stale_fit_bytes_are_rejected(self) -> None:
        self.fit_artifact.write_text(self.fit_artifact.read_text() + "stale\n", encoding="utf-8")
        errors = MODULE.validate_calibration_contract(self.case, self._loaded())
        self.assertTrue(any("hash does not match" in error for error in errors), errors)

    def test_calibration_fit_cannot_count_as_physical_validation(self) -> None:
        path = self.case / "calibration_plan.yaml"
        plan = json.loads(path.read_text())
        plan["independent_validation"]["status"] = "not_started"
        report = json.loads((self.case / "validation_report.yaml").read_text())
        report["physical_validation"]["status"] = "not_started"
        path.write_text(json.dumps(plan), encoding="utf-8")
        (self.case / "validation_report.yaml").write_text(json.dumps(report), encoding="utf-8")
        errors = MODULE.validate_calibration_contract(self.case, self._loaded())
        self.assertTrue(any("independent_validation.status=passed" in error for error in errors), errors)
        self.assertTrue(any("physical_validation status is not passed" in error for error in errors), errors)

    def test_not_required_uses_frozen_model_and_input_hashes(self) -> None:
        model = self.case / "frozen_model.json"
        inputs = self.case / "frozen_inputs.json"
        model.write_text('{"model":"fixed"}\n', encoding="utf-8")
        inputs.write_text('{"input":"held-out"}\n', encoding="utf-8")
        path = self.case / "calibration_plan.yaml"
        plan = json.loads(path.read_text())
        plan["status"] = "not_required"
        plan["not_required_justification"] = "All model parameters are fixed by independently measured geometry."
        plan["parameter_definitions"] = []
        plan["dataset"]["observation_index"] = [record for record in plan["dataset"]["observation_index"] if record["observation_id"] in {"o3", "o4"}]
        plan["split"]["strategy"] = "external_validation"
        plan["split"]["fit_observation_ids"] = []
        plan["split"]["fit_group_ids"] = []
        plan["split"]["fit_replicate_ids"] = []
        plan["fit_result"] = {"status": "not_applicable", "fit_artifact_hash": "", "fit_data_hash": ""}
        validation = plan["independent_validation"]
        validation.pop("fit_artifact_hash", None)
        validation["frozen_model_artifact_locator"] = "frozen_model.json"
        validation["frozen_model_artifact_hash"] = sha256(model)
        validation["frozen_input_artifact_locator"] = "frozen_inputs.json"
        validation["frozen_input_artifact_hash"] = sha256(inputs)
        path.write_text(json.dumps(plan), encoding="utf-8")
        self.assertEqual(MODULE.validate_calibration_contract(self.case, self._loaded()), [])
        result = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "validate_artifacts.py"), str(self.case)],
            capture_output=True, text=True,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_unknown_uncertainty_and_unit_mismatch_are_rejected(self) -> None:
        path = self.case / "calibration_plan.yaml"
        plan = json.loads(path.read_text())
        plan["dataset"]["variables"][0]["uncertainty_status"] = "guessed"
        plan["fit_result"]["parameter_values"][0]["unit"] = "s"
        path.write_text(json.dumps(plan), encoding="utf-8")
        errors = MODULE.validate_calibration_contract(self.case, self._loaded())
        self.assertTrue(any("unknown uncertainty_status" in error for error in errors), errors)
        self.assertTrue(any("unit disagrees" in error for error in errors), errors)

    def test_legacy_physical_claim_requires_explicit_plan(self) -> None:
        legacy = self.case / "legacy"
        shutil.copytree(ROOT / "tests" / "fixtures" / "pinhole-sunglasses", legacy)
        state = json.loads((legacy / "project_state.yaml").read_text())
        state["stage"] = "physically_validated"
        (legacy / "project_state.yaml").write_text(json.dumps(state), encoding="utf-8")
        errors = MODULE.validate_calibration_contract(legacy, {"project_state.yaml": state})
        self.assertTrue(any("requires calibration_plan.yaml" in error for error in errors), errors)

    def test_version_one_marker_cannot_be_removed_with_the_plan(self) -> None:
        (self.case / "calibration_plan.yaml").unlink()
        errors = MODULE.validate_calibration_contract(self.case, self._loaded())
        self.assertTrue(any("requires calibration_plan.yaml" in error for error in errors), errors)

    def test_physical_plan_status_requires_numerical_report(self) -> None:
        state = json.loads((self.case / "project_state.yaml").read_text())
        state["stage"] = "simulation_specified"
        (self.case / "project_state.yaml").write_text(json.dumps(state), encoding="utf-8")
        report = json.loads((self.case / "validation_report.yaml").read_text())
        report.pop("numerical_verification")
        (self.case / "validation_report.yaml").write_text(json.dumps(report), encoding="utf-8")
        errors = MODULE.validate_calibration_contract(self.case, self._loaded())
        self.assertTrue(any("numerical_verification" in error for error in errors), errors)

    def test_calibrated_status_cannot_hide_a_fixed_model(self) -> None:
        path = self.case / "calibration_plan.yaml"
        plan = json.loads(path.read_text())
        plan["status"] = "calibrated"
        plan["parameter_definitions"] = []
        plan["fit_result"] = {"status": "not_started"}
        path.write_text(json.dumps(plan), encoding="utf-8")
        errors = MODULE.validate_calibration_contract(self.case, self._loaded())
        self.assertTrue(any("at least one fitted parameter" in error for error in errors), errors)

    def test_failed_outcome_is_valid_record_but_does_not_advance(self) -> None:
        path = self.case / "calibration_plan.yaml"
        plan = json.loads(path.read_text())
        plan["status"] = "failed"
        plan["fit_result"] = {"status": "failed", "failure_reason": "objective did not converge"}
        plan["independent_validation"] = {"status": "failed", "failure_reason": "not attempted after fit failure"}
        state = json.loads((self.case / "project_state.yaml").read_text())
        state["stage"] = "simulation_specified"
        (self.case / "project_state.yaml").write_text(json.dumps(state), encoding="utf-8")
        path.write_text(json.dumps(plan), encoding="utf-8")
        self.assertEqual(MODULE.validate_calibration_contract(self.case, self._loaded()), [])
        result = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "validate_artifacts.py"), str(self.case)],
            capture_output=True, text=True,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_report_binding_and_naive_timestamps_are_rejected(self) -> None:
        path = self.case / "calibration_plan.yaml"
        plan = json.loads(path.read_text())
        plan["fit_result"]["fit_started_at"] = "2026-01-02T00:00:00"
        report = json.loads((self.case / "validation_report.yaml").read_text())
        report["physical_validation"]["data_hash"] = "d" * 64
        path.write_text(json.dumps(plan), encoding="utf-8")
        (self.case / "validation_report.yaml").write_text(json.dumps(report), encoding="utf-8")
        errors = MODULE.validate_calibration_contract(self.case, self._loaded())
        self.assertTrue(any("aware ISO-8601" in error or "timestamp" in error for error in errors), errors)
        self.assertTrue(any("data_hash does not match" in error for error in errors), errors)

    def test_maximize_objective_uses_maximize_report_criterion(self) -> None:
        path = self.case / "calibration_plan.yaml"
        plan = json.loads(path.read_text())
        plan["objective"]["direction"] = "maximize"
        plan["objective"]["acceptance_threshold"]["value"] = 0.05
        plan["independent_validation"]["acceptance_criterion"] = "objective_value >= predeclared threshold"
        report = json.loads((self.case / "validation_report.yaml").read_text())
        report["physical_validation"]["criterion_threshold"] = 0.05
        path.write_text(json.dumps(plan), encoding="utf-8")
        (self.case / "validation_report.yaml").write_text(json.dumps(report), encoding="utf-8")
        self.assertEqual(MODULE.validate_calibration_contract(self.case, self._loaded()), [])

    def test_physical_report_computed_at_must_be_aware_and_after_validation(self) -> None:
        report_path = self.case / "validation_report.yaml"
        report = json.loads(report_path.read_text())
        report["physical_validation"]["computed_at"] = "2026-01-04T00:00:00"
        report_path.write_text(json.dumps(report), encoding="utf-8")
        errors = MODULE.validate_calibration_contract(self.case, self._loaded())
        self.assertTrue(any("physical_validation computed_at is not an aware ISO-8601 timestamp" in error for error in errors), errors)

    def test_missing_validation_fit_hash_is_rejected(self) -> None:
        path = self.case / "calibration_plan.yaml"
        plan = json.loads(path.read_text())
        plan["independent_validation"]["fit_artifact_hash"] = ""
        path.write_text(json.dumps(plan), encoding="utf-8")
        errors = MODULE.validate_calibration_contract(self.case, self._loaded())
        self.assertTrue(any("does not identify the frozen calibration artifact" in error for error in errors), errors)

    def test_malformed_status_and_nested_objects_return_errors(self) -> None:
        path = self.case / "calibration_plan.yaml"
        plan = json.loads(path.read_text())
        plan["status"] = []
        plan["fit_result"] = []
        path.write_text(json.dumps(plan), encoding="utf-8")
        errors = MODULE.validate_calibration_contract(self.case, self._loaded())
        self.assertTrue(errors)
        self.assertTrue(any("unsupported status" in error for error in errors), errors)

    def test_schema_union_types_report_bad_values_without_crashing(self) -> None:
        schema = load_schema(ROOT, "calibration-plan")
        bad = {
            "calibration_contract_version": 1,
            "status": "planned",
            "claim_ceiling": "planned",
            "dataset": {"dataset_id": "d", "source": "s", "source_locator": "l", "content_hash": "h", "unit_system": "SI", "variables": [], "observation_index": []},
            "objective": {"metric": "m", "formula": "f", "direction": "minimize", "predeclared_at": "t", "target_observables": [], "acceptance_threshold": {}},
            "parameter_definitions": [], "split": {"strategy": "predeclared_holdout", "fit_observation_ids": [], "validation_observation_ids": [], "fit_group_ids": [], "validation_group_ids": [], "fit_replicate_ids": [], "validation_replicate_ids": [], "fit_data_hash": "", "validation_data_hash": ""},
            "fit_result": {"status": "not_started", "fit_artifact_locator": "", "fit_artifact_hash": "", "fit_data_hash": "", "fit_started_at": "", "frozen_at": "", "parameter_values": [], "objective_value": "bad", "residual_summary": {}, "numerical_error": {}},
            "independent_validation": {"status": "not_started", "dataset_id": "", "data_hash": "", "observation_ids": [], "group_ids": [], "replicate_ids": [], "comparison_method": "", "uncertainty_method": "", "acceptance_criterion": "", "objective_value": None, "residual_summary": {}, "performed_at": ""},
        }
        errors = basic_schema_errors(bad, schema)
        self.assertTrue(any("objective_value" in error for error in errors), errors)

    def test_scaffold_partial_validation_preserves_planned_ceiling(self) -> None:
        runs = Path(self.temp.name) / "runs"
        result = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "scaffold_research_case.py"), "fresh", "--prompt", "prompt", "--runs-root", str(runs)],
            capture_output=True, text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        case = runs / "fresh"
        validation = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "validate_artifacts.py"), str(case), "--allow-partial"],
            capture_output=True, text=True,
        )
        self.assertEqual(validation.returncode, 0, validation.stdout + validation.stderr)
        state = json.loads((case / "project_state.yaml").read_text())
        plan = json.loads((case / "calibration_plan.yaml").read_text())
        self.assertEqual(state["calibration_contract_version"], 1)
        self.assertEqual(plan["status"], "planned")
        self.assertIn("no_calibration", plan["claim_ceiling"])


if __name__ == "__main__":
    unittest.main()
