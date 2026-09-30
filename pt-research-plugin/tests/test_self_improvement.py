from __future__ import annotations

import copy
import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
SKILL_DIR = ROOT / "skills" / "pt-self-improvement"
sys.path.insert(0, str(SKILL_DIR / "scripts"))

import self_improvement as si  # noqa: E402


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path: Path, value: dict) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")
    return digest(path)


def build_ledger(root: Path) -> dict:
    ledger = si.default_ledger("demo")
    ledger["budget"].update({"max_lineages": 2, "max_iterations_per_lineage": 2, "max_review_cycles_per_lineage": 2})
    ledger["splits"].update({"development_ids": ["dev-1"], "held_out_ids": ["heldout-1"]})

    candidate_payload = root / "artifacts" / "candidate.patch"
    candidate_payload.parent.mkdir(parents=True, exist_ok=True)
    candidate_payload.write_text("explicit policy load before route\n", encoding="utf-8")
    candidate_payload_hash = digest(candidate_payload)
    dev_evidence = root / "artifacts" / "development-evidence.json"
    dev_evidence_hash = write_json(dev_evidence, {"trajectory": "dev-1", "events": [4, 6], "observation": "policy load was absent before route"})
    reduction_evidence = root / "artifacts" / "reduction-evidence.json"
    reduction_evidence_hash = write_json(reduction_evidence, {"record_id": "map-1", "source": dev_evidence_hash, "retained": "policy-load boundary"})
    map_ref = {"path": "artifacts/development-evidence.json", "sha256": dev_evidence_hash}

    acceptance_rule = "all capability floors pass and repair turns improve by at least one"
    promotion_metadata = {
        "rule_text": "At case resume, load workspace and plugin policy before selecting a route.",
        "scope": "PT research case resume and stage routing",
        "validation_limits": "Validated on one development trace and one sealed held-out manifest; no generalization beyond this scope.",
        "rollback": "Remove PTSI-R001 managed entry and restore the prior explicit routing step.",
    }
    acceptance_metrics = [{"name": "artifact_pass_rate", "direction": "min", "threshold": 1.0}, {"name": "repair_turns", "direction": "max", "threshold": 2.0}]
    candidate_receipt = {
        "role": "candidate", "rule_id": "PTSI-R001", "created_at": "2026-09-20T00:01:00Z",
        "implementer_id": "implementer-1", "candidate_digest": "candidate-v1",
        "candidate_artifact": {"path": "artifacts/candidate.patch", "sha256": candidate_payload_hash},
        "candidate_artifact_sha256": candidate_payload_hash,
        **promotion_metadata,
    }
    acceptance_receipt = {
        "role": "acceptance", "rule_id": "PTSI-R001", "created_at": "2026-09-20T00:10:00Z",
        "reviewer_id": "reviewer-1", "candidate_digest": "candidate-v1", "acceptance_rule": acceptance_rule,
        "acceptance_metrics": acceptance_metrics, **promotion_metadata,
    }
    evaluation_receipt = {
        "role": "held_out_evaluation", "rule_id": "PTSI-R001", "evaluated_at": "2026-09-20T00:30:00Z",
        "evaluator_id": "evaluator-1", "candidate_digest": "candidate-v1", "acceptance_rule": acceptance_rule,
        "passed": True, "metrics_passed": True, "feedback_to_search": False,
        "manifest_hash": "manifest-v1", "result_digest": "result-v1",
        "metrics": {"artifact_pass_rate": 1.0, "repair_turns": 1.0}, "acceptance_metrics": acceptance_metrics,
    }
    candidate_receipt_hash = write_json(root / "receipts" / "candidate.json", candidate_receipt)
    acceptance_receipt_hash = write_json(root / "receipts" / "acceptance.json", acceptance_receipt)
    evaluation_receipt_hash = write_json(root / "receipts" / "held-out-evaluation.json", evaluation_receipt)

    ledger["rules"] = [{
        "rule_id": "PTSI-R001", "lineage_id": "L001", "mechanism_id": "load-policy-before-routing", "status": "promoted",
        "proposal": {"claim": "A missing policy load causes repeated routing repair.", "map_record_ids": ["map-1"]},
        "map_records": [{
            "record_id": "map-1", "trajectory_id": "dev-1",
            "observation": "The case resumed twice without the plugin policy in context.",
            "evidence_locator": "trajectory/dev-1/event-4", "evidence_ref": map_ref,
        }],
        "reduction": {
            "input_record_ids": ["map-1"],
            "evidence_preserved": [{"record_id": "map-1", "locator": "trajectory/dev-1/event-4", "evidence_ref": {"path": "artifacts/reduction-evidence.json", "sha256": reduction_evidence_hash}}],
            "contradictions": [], "reducer_id": "reducer-1",
        },
        "implementation": {
            "implementer_id": "implementer-1", "iterations": 1,
            "exit_condition": "The policy is loaded before the first routing decision.", "changes": ["added explicit load step"],
        },
        "review": {"reviewer_id": "reviewer-1", "decision": "pass", "cycles": 1, "evidence": ["review/reviewer-1"]},
        "development_screen": {
            "capability_floor": {"passed": True, "metrics": [{"name": "artifact_pass_rate", "baseline": 1.0, "candidate": 1.0, "floor": 1.0, "tolerance": 0.0, "direction": "min", "evidence": [dev_evidence_hash]}]},
            "efficiency": {"improved": True, "metric": "repair_turns", "baseline": 3.0, "candidate": 2.0, "delta": -1.0, "direction": "lower", "minimum_improvement": 1.0, "evidence": [dev_evidence_hash]},
            "combined_regression_checks": {"passed": True, "checks": [{"name": "plugin validation", "passed": True, "evidence": ["test_plugin_structure"]}, {"name": "artifact validation", "passed": True, "evidence": ["validate_artifacts"]}]},
        },
        "freeze": {
            "frozen_at": "2026-09-20T00:20:00Z", "candidate_digest": "candidate-v1", "candidate_artifact_sha256": candidate_payload_hash,
            "acceptance_rule": acceptance_rule,
            "acceptance_metrics": acceptance_metrics, **promotion_metadata,
        },
        "timeline": [
            {"event": "candidate_prepared", "at": "2026-09-20T00:01:00Z"},
            {"event": "review_passed", "at": "2026-09-20T00:10:00Z"},
            {"event": "candidate_frozen", "at": "2026-09-20T00:20:00Z"},
            {"event": "held_out_evaluated", "at": "2026-09-20T00:30:00Z"},
        ],
        "held_out": {
            "available": True, "sealed": True, "manifest_hash": "manifest-v1", "result_digest": "result-v1",
            "passed": True, "feedback_to_search": False, "evaluator_id": "evaluator-1",
        },
        "evidence_artifacts": [
            {"role": "candidate", "path": "receipts/candidate.json", "sha256": candidate_receipt_hash},
            {"role": "acceptance", "path": "receipts/acceptance.json", "sha256": acceptance_receipt_hash},
            {"role": "held_out_evaluation", "path": "receipts/held-out-evaluation.json", "sha256": evaluation_receipt_hash},
        ],
        "promotion": {
            "title": "Load local policy before routing", **promotion_metadata,
            "provenance": ["trajectory/dev-1/event-4", "independent-evaluation-receipt:result-v1"],
            "supersedes": [],
        },
    }]
    return ledger


class SelfImprovementTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.ledger = build_ledger(self.root)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_valid_promoted_rule_passes_with_real_receipt_hashes(self) -> None:
        self.assertEqual(si.validate_ledger(self.ledger, self.root), [])

    def test_candidate_payload_mutation_invalidates_promotion(self) -> None:
        payload = self.root / "artifacts" / "candidate.patch"
        payload.write_text("changed candidate\n", encoding="utf-8")
        errors = si.validate_ledger(self.ledger, self.root)
        self.assertTrue(any("candidate payload" in error and "sha256" in error for error in errors), errors)

    def test_post_freeze_rule_or_threshold_tampering_invalidates_promotion(self) -> None:
        invalid = copy.deepcopy(self.ledger)
        invalid["rules"][0]["promotion"]["rule_text"] = "skip the evidence gate"
        invalid["rules"][0]["freeze"]["acceptance_metrics"][0]["threshold"] = 0.0
        errors = si.validate_ledger(invalid, self.root)
        self.assertTrue(any("rule_text differs" in error for error in errors), errors)
        self.assertTrue(any("acceptance metrics changed" in error for error in errors), errors)

    def test_heldout_id_in_proposal_is_rejected(self) -> None:
        leaked = copy.deepcopy(self.ledger)
        leaked["rules"][0]["proposal"]["note"] = "repair heldout-1 before retry"
        errors = si.validate_ledger(leaked, self.root)
        self.assertTrue(any("held-out id heldout-1" in error for error in errors), errors)

    def test_heldout_raw_results_and_feedback_are_rejected(self) -> None:
        invalid = copy.deepcopy(self.ledger)
        invalid["rules"][0]["held_out"]["raw_results"] = "private trace"
        invalid["rules"][0]["held_out"]["feedback_to_search"] = True
        errors = si.validate_ledger(invalid, self.root)
        self.assertTrue(any("raw held-out" in error for error in errors), errors)
        self.assertTrue(any("sealed and feedback-free" in error for error in errors), errors)

    def test_failed_numeric_screen_cannot_be_promoted(self) -> None:
        invalid = copy.deepcopy(self.ledger)
        invalid["rules"][0]["development_screen"]["efficiency"].update({"candidate": 4.0, "delta": 1.0, "improved": False})
        errors = si.validate_ledger(invalid, self.root)
        self.assertTrue(any("efficiency metric does not meet" in error for error in errors), errors)

    def test_malformed_collections_fail_closed_without_type_errors(self) -> None:
        mutations = []
        malformed = copy.deepcopy(self.ledger)
        malformed["rules"][0]["status"] = []
        malformed["rules"][0]["map_records"][0]["trajectory_id"] = {"id": "dev-1"}
        malformed["events"] = [{"event_id": [], "rule_id": [], "status": []}]
        mutations.append(malformed)
        malformed_budget = copy.deepcopy(self.ledger)
        malformed_budget["budget"]["max_lineages"] = True
        malformed_budget["budget"]["max_review_cycles_per_lineage"] = {"limit": 1}
        mutations.append(malformed_budget)
        malformed_receipts = copy.deepcopy(self.ledger)
        malformed_receipts["rules"][0]["held_out"] = []
        malformed_receipts["rules"][0]["promotion"] = []
        mutations.append(malformed_receipts)
        for candidate in mutations:
            try:
                errors = si.validate_ledger(candidate, self.root)
            except (TypeError, ValueError) as exc:  # pragma: no cover - the invariant under test
                self.fail(f"malformed ledger raised instead of failing closed: {exc}")
            self.assertTrue(errors)

    def test_provisional_without_isolated_evaluation_cannot_promote(self) -> None:
        provisional = copy.deepcopy(self.ledger)
        provisional["rules"][0]["status"] = "provisional"
        provisional["rules"][0].pop("held_out")
        provisional["rules"][0].pop("freeze")
        provisional["rules"][0].pop("timeline")
        provisional["rules"][0].pop("evidence_artifacts")
        provisional["rules"][0].pop("promotion")
        self.assertEqual(si.validate_ledger(provisional, self.root), [])
        ledger_path = self.root / "ledger.json"
        ledger_path.write_text(json.dumps(provisional), encoding="utf-8")
        with self.assertRaises(ValueError):
            si.promote_rule(ledger_path, "PTSI-R001", self.root / "plugin-AGENTS.md", self.root / "AGENTS.md")

    def test_promotion_preserves_surrounding_content_and_is_idempotent(self) -> None:
        ledger_path = self.root / "ledger.json"
        ledger_path.write_text(json.dumps(self.ledger), encoding="utf-8")
        plugin = self.root / "plugin-AGENTS.md"
        workspace = self.root / "AGENTS.md"
        plugin.write_text("# Existing plugin policy\n\nKeep this line.\n", encoding="utf-8")
        workspace.write_text("# Existing workspace policy\n", encoding="utf-8")

        first = si.promote_rule(ledger_path, "PTSI-R001", plugin, workspace)
        plugin_after_first = plugin.read_text(encoding="utf-8")
        workspace_after_first = workspace.read_text(encoding="utf-8")
        self.assertTrue(first["changed"])
        self.assertIn("Keep this line.", plugin_after_first)
        self.assertIn("# Existing workspace policy", workspace_after_first)
        self.assertEqual(plugin_after_first.count(si.MARKER_START), 1)
        self.assertEqual(plugin_after_first.count(si.MARKER_END), 1)
        self.assertNotIn("private trace", plugin_after_first + workspace_after_first)

        second = si.promote_rule(ledger_path, "PTSI-R001", plugin, workspace)
        self.assertFalse(second["changed"])
        self.assertFalse(second["event_added"])
        self.assertEqual(plugin_after_first, plugin.read_text(encoding="utf-8"))
        self.assertEqual(workspace_after_first, workspace.read_text(encoding="utf-8"))

    def test_second_policy_write_failure_rolls_back_all_targets_and_leaves_recovery_journal(self) -> None:
        ledger_path = self.root / "ledger.json"
        ledger_path.write_text(json.dumps(self.ledger), encoding="utf-8")
        plugin = self.root / "plugin-AGENTS.md"
        workspace = self.root / "AGENTS.md"
        plugin.write_text("# Existing plugin policy\n", encoding="utf-8")
        workspace.write_text("# Existing workspace policy\n", encoding="utf-8")
        original_plugin = plugin.read_text(encoding="utf-8")
        original_workspace = workspace.read_text(encoding="utf-8")

        original_write = si._write_text_atomic

        def fail_workspace(path: Path, data: str) -> None:
            if path.resolve() == workspace.resolve():
                raise OSError("simulated second target failure")
            original_write(path, data)

        with mock.patch.object(si, "_write_text_atomic", side_effect=fail_workspace):
            with self.assertRaises(ValueError):
                si.promote_rule(ledger_path, "PTSI-R001", plugin, workspace)
        self.assertEqual(original_plugin, plugin.read_text(encoding="utf-8"))
        self.assertEqual(original_workspace, workspace.read_text(encoding="utf-8"))
        persisted = json.loads(ledger_path.read_text(encoding="utf-8"))
        self.assertEqual([], persisted["events"])
        journal = self.root / "promotion-recovery-PTSI-R001.json"
        self.assertEqual("rolled_back", json.loads(journal.read_text(encoding="utf-8"))["status"])

    def test_ledger_write_failure_rolls_back_both_policy_targets(self) -> None:
        ledger_path = self.root / "ledger.json"
        ledger_path.write_text(json.dumps(self.ledger), encoding="utf-8")
        plugin = self.root / "plugin-AGENTS.md"
        workspace = self.root / "AGENTS.md"
        plugin.write_text("# Existing plugin policy\n", encoding="utf-8")
        workspace.write_text("# Existing workspace policy\n", encoding="utf-8")
        original_plugin = plugin.read_text(encoding="utf-8")
        original_workspace = workspace.read_text(encoding="utf-8")
        original_write = si._write_text_atomic

        def fail_ledger(path: Path, data: str) -> None:
            if path.resolve() == ledger_path.resolve():
                raise OSError("simulated ledger write failure")
            original_write(path, data)

        with mock.patch.object(si, "_write_text_atomic", side_effect=fail_ledger):
            with self.assertRaises(ValueError):
                si.promote_rule(ledger_path, "PTSI-R001", plugin, workspace)
        self.assertEqual(original_plugin, plugin.read_text(encoding="utf-8"))
        self.assertEqual(original_workspace, workspace.read_text(encoding="utf-8"))
        self.assertEqual([], json.loads(ledger_path.read_text(encoding="utf-8"))["events"])
        journal = self.root / "promotion-recovery-PTSI-R001.json"
        self.assertEqual("rolled_back", json.loads(journal.read_text(encoding="utf-8"))["status"])

    def test_init_refuses_overwrite(self) -> None:
        case = self.root / "runs" / "demo"
        path = si.init_ledger(case, "demo")
        self.assertTrue(path.is_file())
        with self.assertRaises(ValueError):
            si.init_ledger(case, "demo")


if __name__ == "__main__":
    unittest.main()
