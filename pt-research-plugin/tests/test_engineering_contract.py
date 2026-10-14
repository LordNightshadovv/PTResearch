from __future__ import annotations

import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import scaffold_research_software as scaffold  # noqa: E402
from artifact_lib import basic_schema_errors, dump_artifact, load_schema  # noqa: E402
from engineering_contract import (  # noqa: E402
    validate_engineering_contract,
    validate_engineering_manifest,
)

VALIDATOR = ROOT / "scripts" / "validate_engineering_standards.py"


def declared_manifest(interface: str = "cli") -> dict:
    return scaffold.build_manifest("demo-project", "demo_project", interface, "A demo.")


class EngineeringManifestTests(unittest.TestCase):
    def errors(self, manifest: dict, root: Path | None = None) -> list[str]:
        return validate_engineering_manifest(manifest, root)

    def test_scaffold_manifest_is_valid_without_file_checks(self) -> None:
        for interface in scaffold.INTERFACES:
            self.assertEqual(self.errors(declared_manifest(interface)), [], interface)

    def test_schema_accepts_declared_manifest(self) -> None:
        schema = load_schema(ROOT, "engineering-standards")
        self.assertEqual(basic_schema_errors(declared_manifest(), schema), [])

    def test_not_started_stub_passes_and_not_applicable_needs_justification(self) -> None:
        stub = {"engineering_contract_version": 1, "status": "not_started",
                "validation_scope": "declaration_and_structure_only", "claim_ceiling": "none"}
        self.assertEqual(self.errors(stub), [])
        stub["status"] = "not_applicable"
        self.assertTrue(self.errors(stub))
        stub["not_applicable_justification"] = "Pure derivation, no code is produced in this stage."
        self.assertEqual(self.errors(stub), [])

    def test_validation_scope_must_be_declaration_only(self) -> None:
        manifest = declared_manifest()
        manifest["validation_scope"] = "scientifically_validated"
        self.assertTrue(self.errors(manifest))

    def test_adr_needs_two_concrete_alternatives(self) -> None:
        manifest = declared_manifest()
        manifest["stack_decision"]["alternatives_considered"] = manifest["stack_decision"]["alternatives_considered"][:1]
        self.assertTrue(any("at least two alternatives" in e for e in self.errors(manifest)))
        manifest = declared_manifest()
        manifest["stack_decision"]["alternatives_considered"][0]["rejected_because"] = "tbd"
        self.assertTrue(any("rejected_because" in e for e in self.errors(manifest)))

    def test_language_and_paradigm_need_justification(self) -> None:
        manifest = declared_manifest()
        manifest["stack_decision"]["language"]["justification"] = "faster"
        manifest["stack_decision"]["paradigm"]["justification"] = "ok"
        errors = self.errors(manifest)
        self.assertTrue(any("language.justification" in e for e in errors))
        self.assertTrue(any("paradigm.justification" in e for e in errors))
        manifest["stack_decision"]["paradigm"]["style"] = "dogmatic"
        self.assertTrue(self.errors(manifest))  # schema enum rejects unknown paradigms

    def test_semver_is_required(self) -> None:
        manifest = declared_manifest()
        manifest["project"]["version"] = "v1"
        self.assertTrue(any("semantic version" in e for e in self.errors(manifest)))

    def test_gui_requires_headless_core_thin_layer_and_accessibility(self) -> None:
        manifest = declared_manifest("desktop_gui")
        self.assertEqual(self.errors(manifest), [])
        broken = copy.deepcopy(manifest)
        broken["interface"]["headless_core"] = False
        broken["interface"]["thin_layer"] = False
        del broken["interface"]["accessibility"]["keyboard_operable"]
        errors = self.errors(broken)
        self.assertTrue(any("headless_core" in e for e in errors))
        self.assertTrue(any("thin_layer" in e for e in errors))
        self.assertTrue(any("keyboard_operable" in e for e in errors))

    def test_false_accessibility_flag_needs_limitation(self) -> None:
        manifest = declared_manifest("web_ui")
        manifest["interface"]["accessibility"]["text_alternatives"] = False
        self.assertTrue(any("limitations" in e for e in self.errors(manifest)))
        manifest["interface"]["accessibility"]["limitations"] = "Plots lack alt text until the export feature ships."
        self.assertEqual(self.errors(manifest), [])

    def test_rust_tui_needs_rust_rationale(self) -> None:
        manifest = declared_manifest("desktop_gui")
        manifest["interface"]["primary"] = "tui_rust"
        errors = self.errors(manifest)
        self.assertTrue(any("implementation_language" in e for e in errors))
        self.assertTrue(any("rust_rationale" in e for e in errors))
        manifest["interface"]["implementation_language"] = "Rust"
        manifest["interface"]["rust_rationale"] = "Streams 1e6 log lines per second with bounded memory; profiled Python TUI dropped frames."
        self.assertEqual(self.errors(manifest), [])

    def test_numerical_verification_requires_tolerances_and_convergence_test(self) -> None:
        manifest = declared_manifest()
        manifest["numerical_verification"]["tolerances"] = {"abs": 0}
        self.assertTrue(any("tolerances" in e for e in self.errors(manifest)))
        manifest = declared_manifest()
        manifest["test_plan"]["tests"] = [t for t in manifest["test_plan"]["tests"] if t["kind"] != "convergence"]
        self.assertTrue(any("'convergence' test" in e for e in self.errors(manifest)))

    def test_dimensional_test_required_with_units_policy(self) -> None:
        manifest = declared_manifest()
        manifest["test_plan"]["tests"] = [t for t in manifest["test_plan"]["tests"] if t["kind"] != "dimensional"]
        self.assertTrue(any("'dimensional' test" in e for e in self.errors(manifest)))

    def test_not_required_numerics_needs_justification(self) -> None:
        manifest = declared_manifest()
        manifest["numerical_verification"] = {"required": False}
        self.assertTrue(any("justification" in e for e in self.errors(manifest)))

    def test_uncertainty_sources_must_all_be_separated(self) -> None:
        manifest = declared_manifest()
        del manifest["uncertainty_treatment"]["error_sources"]["model_form"]
        self.assertTrue(any("model_form" in e for e in self.errors(manifest)))

    def test_planned_comparison_needs_error_bars_and_split(self) -> None:
        manifest = declared_manifest()
        manifest["experiment_comparison"] = {"planned": True, "metrics": ["reduced_chi2"]}
        errors = self.errors(manifest)
        self.assertTrue(any("overlay_with_error_bars" in e for e in errors))
        self.assertTrue(any("fit_validation_separation" in e for e in errors))

    def test_reproducibility_metadata_fields_are_required(self) -> None:
        manifest = declared_manifest()
        manifest["reproducibility"]["run_metadata_fields"] = ["seed"]
        self.assertTrue(any("lacks required fields" in e for e in self.errors(manifest)))

    def test_referenced_files_must_exist_and_be_safe(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            errors = self.errors(declared_manifest(), root)
            self.assertTrue(any("adr_path" in e for e in errors))
            manifest = declared_manifest()
            manifest["stack_decision"]["adr_path"] = "../outside.md"
            self.assertTrue(any("adr_path" in e for e in self.errors(manifest, root)))

    def test_evidenced_test_requires_existing_receipt(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "project"
            scaffold.scaffold(root, "demo-project")
            manifest = json.loads((root / "engineering_standards.yaml").read_text())
            self.assertEqual(self.errors(manifest, root), [])
            manifest["test_plan"]["tests"][0]["evidence_status"] = "evidenced"
            manifest["test_plan"]["tests"][0]["evidence"] = "receipts/pytest.txt"
            self.assertTrue(any("evidence" in e for e in self.errors(manifest, root)))
            (root / "receipts").mkdir()
            (root / "receipts" / "pytest.txt").write_text("30 passed\n", encoding="utf-8")
            self.assertEqual(self.errors(manifest, root), [])


class CaseIntegrationTests(unittest.TestCase):
    def make_case(self, root: Path, **state: object) -> Path:
        case = root / "case"
        case.mkdir()
        base = {"case_id": "c", "exact_prompt": "p", "stage": "intake", "claims": [],
                "engineering_contract_version": 1, "software_readiness": "not_applicable"}
        base.update(state)
        dump_artifact(case / "project_state.yaml", base)
        return case

    def run_gate(self, case: Path) -> list[str]:
        from artifact_lib import load_artifact
        return validate_engineering_contract(case, {"project_state.yaml": load_artifact(case / "project_state.yaml")})

    def test_legacy_case_without_version_or_manifest_is_unaffected(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            case = Path(temp) / "case"
            case.mkdir()
            self.assertEqual(validate_engineering_contract(case, {"project_state.yaml": {"case_id": "x"}}), [])

    def test_versioned_case_requires_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            case = self.make_case(Path(temp))
            self.assertTrue(any("required" in e for e in self.run_gate(case)))

    def test_not_started_stub_ok_until_implementation_ready(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            case = self.make_case(Path(temp))
            dump_artifact(case / "engineering_standards.yaml", {
                "engineering_contract_version": 1, "status": "not_started",
                "validation_scope": "declaration_and_structure_only", "claim_ceiling": "none"})
            self.assertEqual(self.run_gate(case), [])
            dump_artifact(case / "project_state.yaml", {
                "case_id": "c", "exact_prompt": "p", "stage": "x", "claims": [],
                "engineering_contract_version": 1, "software_readiness": "implementation_ready"})
            self.assertTrue(any("requires status 'declared'" in e for e in self.run_gate(case)))

    def test_readiness_ladder_requires_lockfile_and_receipts(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            case = Path(temp) / "case"
            scaffold.scaffold(case, "demo-project")
            dump_artifact(case / "project_state.yaml", {
                "case_id": "c", "exact_prompt": "p", "stage": "x", "claims": [],
                "engineering_contract_version": 1, "software_readiness": "implementation_ready"})
            self.assertEqual(self.run_gate(case), [])
            state = {"case_id": "c", "exact_prompt": "p", "stage": "x", "claims": [], "engineering_contract_version": 1}
            dump_artifact(case / "project_state.yaml", {**state, "software_readiness": "executed_unverified"})
            self.assertTrue(any("lockfile" in e for e in self.run_gate(case)))
            dump_artifact(case / "project_state.yaml", {**state, "software_readiness": "numerically_verified"})
            self.assertTrue(any("numerically_verified" in e for e in self.run_gate(case)))
            dump_artifact(case / "project_state.yaml", {**state, "software_readiness": "experimentally_compared"})
            self.assertTrue(any("experimentally_compared" in e for e in self.run_gate(case)))

    def test_fully_evidenced_manifest_satisfies_numerical_gate(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            case = Path(temp) / "case"
            scaffold.scaffold(case, "demo-project")
            (case / "uv.lock").write_text("# lock\n", encoding="utf-8")
            (case / "receipts").mkdir()
            (case / "receipts" / "numerical.txt").write_text("convergence order 4.01\n", encoding="utf-8")
            manifest = json.loads((case / "engineering_standards.yaml").read_text())
            manifest["dependency_management"]["lockfile_status"] = "committed"
            manifest["numerical_verification"]["evidence_status"] = "evidenced"
            manifest["numerical_verification"]["evidence"] = "receipts/numerical.txt"
            dump_artifact(case / "engineering_standards.yaml", manifest)
            dump_artifact(case / "project_state.yaml", {
                "case_id": "c", "exact_prompt": "p", "stage": "x", "claims": [],
                "engineering_contract_version": 1, "software_readiness": "numerically_verified"})
            self.assertEqual(self.run_gate(case), [])


class ValidatorCliTests(unittest.TestCase):
    def test_cli_passes_on_scaffold_and_fails_on_broken_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            project = Path(temp) / "demo-project"
            scaffold.scaffold(project, "demo-project")
            ok = subprocess.run([sys.executable, str(VALIDATOR), str(project)], capture_output=True, text=True)
            self.assertEqual(ok.returncode, 0, ok.stdout + ok.stderr)
            self.assertIn("declaration and structure only", ok.stdout)
            manifest = json.loads((project / "engineering_standards.yaml").read_text())
            manifest["stack_decision"]["alternatives_considered"] = []
            (project / "engineering_standards.yaml").write_text(json.dumps(manifest), encoding="utf-8")
            bad = subprocess.run([sys.executable, str(VALIDATOR), str(project)], capture_output=True, text=True)
            self.assertEqual(bad.returncode, 1)
            self.assertIn("alternatives", bad.stdout)

    def test_cli_reports_unreadable_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            result = subprocess.run([sys.executable, str(VALIDATOR), temp], capture_output=True, text=True)
            self.assertEqual(result.returncode, 1)


if __name__ == "__main__":
    unittest.main()
