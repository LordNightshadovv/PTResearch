#!/usr/bin/env python3
"""Validate and consolidate bounded PT workflow-learning ledgers.

The ledger deliberately uses JSON content so the helper stays dependency-free. Existing PT
artifacts use the same JSON-compatible convention for several ``.yaml`` files.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


SOURCE_URL = "https://nvlabs.github.io/SoL-Pi/"
ALLOWED_STATUSES = {
    "proposed",
    "rejected",
    "deferred",
    "provisional",
    "promoted",
}
EVENT_STATUSES = ALLOWED_STATUSES | {"held_out_evaluated", "development_screened"}
MAX_MANAGED_RULES = 64
MARKER_START = "<!-- BEGIN PT-SELF-IMPROVEMENT RULES (managed; preserve surrounding content) -->"
MARKER_END = "<!-- END PT-SELF-IMPROVEMENT RULES -->"
RULE_HEADING = re.compile(r"^###\s+(PTSI-[A-Za-z0-9._-]+):[^\n]*$", re.MULTILINE)


class LedgerError(ValueError):
    """Raised for a malformed or unsafe ledger/promotion request."""


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise LedgerError(f"cannot read JSON ledger {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise LedgerError(f"ledger must contain a JSON object: {path}")
    return value


def write_json_atomic(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    data = json.dumps(value, indent=2, ensure_ascii=False) + "\n"
    _write_text_atomic(path, data)


def _write_text_atomic(path: Path, data: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=str(path.parent), text=True)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    except Exception:
        try:
            os.unlink(temporary)
        except OSError:
            pass
        raise


def default_ledger(case_id: str) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "case_id": case_id,
        "source": {
            "method": "bounded PT process learning",
            "article": SOURCE_URL,
            "adaptation_scope": "workflow instructions and auditable artifacts only",
            "authority": "current authorized PT project; no new solver, network, or filesystem authority",
        },
        "budget": {
            "max_lineages": 3,
            "max_iterations_per_lineage": 3,
            "max_review_cycles_per_lineage": 2,
            "exit_condition": "Stop on accepted evidence, failed review, invalid evidence, or exhausted budget.",
            "spent_lineages": 0,
        },
        "splits": {
            "development_ids": [],
            "held_out_ids": [],
            "held_out_manifest_hash": "",
            "held_out_sealed": False,
            "isolation_mode": "procedural_blind_reviewer",
            "held_out_feedback_to_search": False,
        },
        "rules": [],
        "events": [],
        "pending_consolidation": [],
    }


def _as_dict(value: Any, path: str, errors: list[str]) -> dict[str, Any]:
    if not isinstance(value, dict):
        errors.append(f"{path} must be an object")
        return {}
    return value


def _as_list(value: Any, path: str, errors: list[str]) -> list[Any]:
    if not isinstance(value, list):
        errors.append(f"{path} must be a list")
        return []
    return value


def _nonempty(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _bool(value: Any) -> bool:
    return value is True or value is False


def _number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _parse_time(value: Any) -> datetime | None:
    if not _nonempty(value):
        return None
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed if parsed.tzinfo is not None else parsed.replace(tzinfo=timezone.utc)


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _safe_artifact_path(base_dir: Path | None, relative_path: Any, errors: list[str], label: str) -> Path | None:
    if not _nonempty(relative_path):
        errors.append(f"{label}: artifact path is required")
        return None
    candidate = Path(str(relative_path))
    if candidate.is_absolute() or ".." in candidate.parts:
        errors.append(f"{label}: artifact path must be relative and stay inside the ledger directory")
        return None
    if base_dir is None:
        return None
    resolved = (base_dir / candidate).resolve()
    try:
        resolved.relative_to(base_dir.resolve())
    except ValueError:
        errors.append(f"{label}: artifact path escapes the ledger directory")
        return None
    return resolved


def _validate_artifact_ref(ref: Any, base_dir: Path | None, errors: list[str], label: str, require_file: bool) -> tuple[Path | None, str]:
    if not isinstance(ref, dict):
        errors.append(f"{label}: artifact reference must be an object")
        return None, ""
    expected_hash = ref.get("sha256")
    if not isinstance(expected_hash, str) or not re.fullmatch(r"[0-9a-f]{64}", expected_hash):
        errors.append(f"{label}: sha256 must be a 64-character lowercase hex digest")
    path = _safe_artifact_path(base_dir, ref.get("path"), errors, label)
    if base_dir is None:
        if require_file:
            errors.append(f"{label}: hash verification requires the ledger directory")
        return None, str(expected_hash or "")
    if path is None:
        return None, str(expected_hash or "")
    if not path.is_file():
        errors.append(f"{label}: referenced artifact does not exist: {ref.get('path')}")
        return path, str(expected_hash or "")
    try:
        actual = _sha256_bytes(path.read_bytes())
    except OSError as exc:
        errors.append(f"{label}: cannot read referenced artifact: {exc}")
        return path, str(expected_hash or "")
    if actual != expected_hash:
        errors.append(f"{label}: sha256 does not match referenced artifact")
    return path, str(expected_hash or "")


def _heldout_leaks(value: Any, heldout_ids: set[str], path: tuple[str, ...] = ()) -> list[str]:
    """Find exact held-out tokens outside their declared/sealed locations."""

    leaks: list[str] = []
    allowed = (
        len(path) >= 2 and path[:2] == ("splits", "held_out_ids")
    ) or (
        len(path) >= 3 and path[0] == "rules" and path[1].isdigit() and path[2] == "held_out"
    )
    if isinstance(value, str):
        for token in sorted(heldout_ids):
            if token and token in value and not allowed:
                leaks.append(f"{'.'.join(path) or '<root>'} contains held-out id {token}")
        return leaks
    if isinstance(value, dict):
        for key, child in value.items():
            leaks.extend(_heldout_leaks(child, heldout_ids, path + (str(key),)))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            leaks.extend(_heldout_leaks(child, heldout_ids, path + (str(index),)))
    return leaks


def _validate_map_reduce(rule: dict[str, Any], development_ids: set[str], heldout_ids: set[str], base_dir: Path | None, errors: list[str]) -> None:
    rule_id = str(rule.get("rule_id", "<missing>"))
    maps = rule.get("map_records", [])
    if not isinstance(maps, list):
        errors.append(f"{rule_id}: map_records must be a list")
        return
    record_ids: list[str] = []
    for index, record in enumerate(maps):
        if not isinstance(record, dict):
            errors.append(f"{rule_id}: map_records[{index}] must be an object")
            continue
        record_id = record.get("record_id")
        if not _nonempty(record_id):
            errors.append(f"{rule_id}: map_records[{index}] lacks record_id")
        elif record_id in record_ids:
            errors.append(f"{rule_id}: duplicate map record_id {record_id}")
        else:
            record_ids.append(str(record_id))
        trajectory_id = record.get("trajectory_id")
        if isinstance(trajectory_id, str) and trajectory_id in heldout_ids:
            errors.append(f"{rule_id}: map record uses held-out trajectory {trajectory_id}")
        elif development_ids and (not isinstance(trajectory_id, str) or trajectory_id not in development_ids):
            errors.append(f"{rule_id}: map record trajectory is outside development split: {trajectory_id}")
        for required in ("observation", "evidence_locator"):
            if not _nonempty(record.get(required)):
                errors.append(f"{rule_id}: map record {record_id or index} lacks {required}")
        if isinstance(rule.get("status"), str) and rule.get("status") in {"provisional", "promoted"}:
            _validate_artifact_ref(record.get("evidence_ref"), base_dir, errors, f"{rule_id}: map record {record_id or index} evidence_ref", require_file=rule.get("status") == "promoted")

    reduction = rule.get("reduction")
    if not isinstance(reduction, dict):
        if rule.get("status") != "proposed" or maps:
            errors.append(f"{rule_id}: evidence-preserving reduction is required after mapping")
        return
    reduced = reduction.get("input_record_ids")
    if not isinstance(reduced, list) or any(not isinstance(item, str) for item in reduced) or set(reduced) != set(record_ids) or len(reduced) != len(record_ids):
        errors.append(f"{rule_id}: reduction must reference each map record exactly once")
    preserved = reduction.get("evidence_preserved")
    if not isinstance(preserved, list) or not preserved:
        errors.append(f"{rule_id}: reduction must list preserved evidence")
    else:
        preserved_ids: list[str] = []
        for item in preserved:
            if not isinstance(item, dict) or not _nonempty(item.get("record_id")):
                errors.append(f"{rule_id}: reduction evidence must identify a mapped record")
                continue
            preserved_ids.append(str(item["record_id"]))
            if "evidence_ref" in item:
                _validate_artifact_ref(item.get("evidence_ref"), base_dir, errors, f"{rule_id}: reduction evidence {item['record_id']}", require_file=rule.get("status") == "promoted")
        if set(preserved_ids) != set(record_ids):
            errors.append(f"{rule_id}: reduction must preserve evidence for every map record")
    if not _nonempty(reduction.get("reducer_id")):
        errors.append(f"{rule_id}: reduction lacks reducer_id")
    proposal = rule.get("proposal")
    if isinstance(proposal, dict) and "map_record_ids" in proposal:
        proposal_ids = proposal.get("map_record_ids", [])
        if not isinstance(proposal_ids, list) or any(not isinstance(item, str) for item in proposal_ids) or set(proposal_ids) != set(record_ids):
            errors.append(f"{rule_id}: proposal map_record_ids do not match map records")


def _validate_development_screen(screen: Any, rule_id: str, errors: list[str]) -> None:
    if not isinstance(screen, dict):
        errors.append(f"{rule_id}: development_screen required")
        return
    floor = screen.get("capability_floor")
    if not isinstance(floor, dict):
        errors.append(f"{rule_id}: capability_floor must be an object")
    else:
        metrics = floor.get("metrics")
        if not isinstance(metrics, list) or not metrics:
            errors.append(f"{rule_id}: capability floor needs numeric metrics and evidence")
        else:
            passes: list[bool] = []
            for index, metric in enumerate(metrics):
                if not isinstance(metric, dict):
                    errors.append(f"{rule_id}: capability metric {index} must be an object")
                    continue
                if not _nonempty(metric.get("name")) or not isinstance(metric.get("direction"), str) or metric.get("direction") not in {"min", "max"}:
                    errors.append(f"{rule_id}: capability metric {index} lacks name or direction")
                    continue
                if not all(_number(metric.get(field)) for field in ("baseline", "candidate", "floor", "tolerance")) or metric.get("tolerance") < 0:
                    errors.append(f"{rule_id}: capability metric {metric.get('name', index)} needs numeric baseline/candidate/floor/tolerance")
                    continue
                if not isinstance(metric.get("evidence"), list) or not metric.get("evidence"):
                    errors.append(f"{rule_id}: capability metric {metric.get('name', index)} lacks evidence")
                if metric["direction"] == "min":
                    passes.append(metric["candidate"] >= metric["floor"] and metric["candidate"] >= metric["baseline"] - metric["tolerance"])
                else:
                    passes.append(metric["candidate"] <= metric["floor"] and metric["candidate"] <= metric["baseline"] + metric["tolerance"])
            calculated = bool(passes) and all(passes)
            if floor.get("passed") is not calculated:
                errors.append(f"{rule_id}: capability_floor.passed does not match metric comparisons")
            if not calculated:
                errors.append(f"{rule_id}: capability floor metrics fail the declared floor/tolerance")

    efficiency = screen.get("efficiency")
    if not isinstance(efficiency, dict):
        errors.append(f"{rule_id}: efficiency check must be an object")
    else:
        direction = efficiency.get("direction")
        if not isinstance(direction, str) or direction not in {"lower", "higher"} or not all(_number(efficiency.get(field)) for field in ("baseline", "candidate", "minimum_improvement")) or efficiency.get("minimum_improvement") < 0:
            errors.append(f"{rule_id}: efficiency needs direction, numeric baseline/candidate/minimum_improvement")
        else:
            improvement = efficiency["baseline"] - efficiency["candidate"] if direction == "lower" else efficiency["candidate"] - efficiency["baseline"]
            if "delta" in efficiency and (not _number(efficiency["delta"]) or efficiency["delta"] != efficiency["candidate"] - efficiency["baseline"]):
                errors.append(f"{rule_id}: efficiency delta does not match baseline/candidate")
            calculated = improvement >= efficiency["minimum_improvement"] and improvement > 0
            if efficiency.get("improved") is not calculated:
                errors.append(f"{rule_id}: efficiency.improved does not match metric comparison")
            if not calculated:
                errors.append(f"{rule_id}: efficiency metric does not meet the declared improvement")
        if not isinstance(efficiency.get("evidence"), list) or not efficiency.get("evidence"):
            errors.append(f"{rule_id}: efficiency metric lacks evidence")

    regressions = screen.get("combined_regression_checks")
    if not isinstance(regressions, dict) or not isinstance(regressions.get("checks"), list) or not regressions.get("checks"):
        errors.append(f"{rule_id}: combined regression checks need named evidence")
    else:
        calculated = True
        for index, check in enumerate(regressions["checks"]):
            if not isinstance(check, dict) or not _nonempty(check.get("name")) or check.get("passed") is not True or not isinstance(check.get("evidence"), list) or not check.get("evidence"):
                errors.append(f"{rule_id}: regression check {index} lacks pass/evidence")
                calculated = False
        if regressions.get("passed") is not calculated:
            errors.append(f"{rule_id}: combined_regression_checks.passed does not match checks")


def _load_receipt(ref: Any, role: str, base_dir: Path | None, errors: list[str]) -> dict[str, Any]:
    path, _ = _validate_artifact_ref(ref, base_dir, errors, f"receipt {role}", require_file=True)
    if path is None or not path.is_file():
        return {}
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        errors.append(f"receipt {role}: must be readable JSON: {exc}")
        return {}
    if not isinstance(value, dict):
        errors.append(f"receipt {role}: must contain an object")
        return {}
    return value


def _validate_receipts(rule: dict[str, Any], base_dir: Path | None, errors: list[str]) -> dict[str, dict[str, Any]]:
    rule_id = str(rule.get("rule_id", "<missing>"))
    refs = rule.get("evidence_artifacts")
    if not isinstance(refs, list):
        errors.append(f"{rule_id}: promoted rule needs candidate, acceptance, and held-out receipt references")
        return {}
    by_role: dict[str, dict[str, Any]] = {}
    for ref in refs:
        role_value = ref.get("role") if isinstance(ref, dict) else None
        role = role_value if isinstance(role_value, str) else None
        if role in by_role:
            errors.append(f"{rule_id}: duplicate evidence receipt role {role}")
            continue
        if role not in {"candidate", "acceptance", "held_out_evaluation"}:
            errors.append(f"{rule_id}: unknown evidence receipt role {role!r}")
            continue
        by_role[role] = _load_receipt(ref, str(role), base_dir, errors)
    required = {"candidate", "acceptance", "held_out_evaluation"}
    if set(by_role) != required:
        errors.append(f"{rule_id}: evidence receipts must cover exactly {sorted(required)}")
        return by_role
    candidate = by_role["candidate"]
    acceptance = by_role["acceptance"]
    evaluation = by_role["held_out_evaluation"]
    for role, receipt in by_role.items():
        if receipt.get("role") != role or receipt.get("rule_id") != rule_id:
            errors.append(f"{rule_id}: {role} receipt identity is not bound to this rule")
    implementation_value = rule.get("implementation", {})
    review_value = rule.get("review", {})
    freeze_value = rule.get("freeze", {})
    heldout_value = rule.get("held_out", {})
    promotion_value = rule.get("promotion", {})
    implementation = implementation_value if isinstance(implementation_value, dict) else {}
    review = review_value if isinstance(review_value, dict) else {}
    freeze = freeze_value if isinstance(freeze_value, dict) else {}
    heldout = heldout_value if isinstance(heldout_value, dict) else {}
    promotion = promotion_value if isinstance(promotion_value, dict) else {}
    for field in ("rule_text", "scope", "validation_limits", "rollback"):
        if candidate.get(field) != promotion.get(field) or acceptance.get(field) != promotion.get(field) or freeze.get(field) != promotion.get(field):
            errors.append(f"{rule_id}: {field} differs between reviewed receipts, frozen candidate, and promotion metadata")
    if candidate.get("implementer_id") != implementation.get("implementer_id") or not _nonempty(candidate.get("candidate_digest")):
        errors.append(f"{rule_id}: candidate receipt is not bound to the implementer and candidate digest")
    candidate_artifact_path, candidate_artifact_hash = _validate_artifact_ref(candidate.get("candidate_artifact"), base_dir, errors, f"{rule_id}: candidate payload", require_file=True)
    if not _nonempty(freeze.get("candidate_artifact_sha256")) or candidate_artifact_hash != freeze.get("candidate_artifact_sha256") or candidate.get("candidate_artifact_sha256") != candidate_artifact_hash:
        errors.append(f"{rule_id}: candidate payload hash is not bound to the frozen candidate")
    if candidate_artifact_path is not None and candidate_artifact_path.is_file():
        try:
            if _sha256_bytes(candidate_artifact_path.read_bytes()) != candidate_artifact_hash:
                errors.append(f"{rule_id}: candidate payload hash does not match the payload")
        except OSError as exc:
            errors.append(f"{rule_id}: cannot read candidate payload: {exc}")
    if acceptance.get("reviewer_id") != review.get("reviewer_id") or acceptance.get("candidate_digest") != freeze.get("candidate_digest"):
        errors.append(f"{rule_id}: acceptance receipt is not bound to reviewer/frozen candidate")
    if acceptance.get("acceptance_rule") != freeze.get("acceptance_rule"):
        errors.append(f"{rule_id}: acceptance receipt does not bind the frozen acceptance rule")
    evaluator_id = evaluation.get("evaluator_id")
    if not _nonempty(evaluator_id) or (isinstance(evaluator_id, str) and evaluator_id in {implementation.get("implementer_id"), review.get("reviewer_id")}):
        errors.append(f"{rule_id}: held-out evaluator must be identified and independent")
    if evaluator_id != heldout.get("evaluator_id"):
        errors.append(f"{rule_id}: held-out evaluator identity is not consistent between receipt and ledger")
    if candidate.get("candidate_digest") != freeze.get("candidate_digest"):
        errors.append(f"{rule_id}: candidate receipt digest does not match the frozen candidate")
    if evaluation.get("candidate_digest") != freeze.get("candidate_digest") or evaluation.get("acceptance_rule") != freeze.get("acceptance_rule"):
        errors.append(f"{rule_id}: held-out receipt is not bound to the frozen candidate and rule")
    if evaluation.get("passed") is not heldout.get("passed") or evaluation.get("feedback_to_search") is not False:
        errors.append(f"{rule_id}: held-out receipt must bind a feedback-free boolean result")
    if evaluation.get("manifest_hash") != heldout.get("manifest_hash") or evaluation.get("result_digest") != heldout.get("result_digest"):
        errors.append(f"{rule_id}: held-out receipt does not bind manifest/result digests")
    acceptance_metrics = freeze.get("acceptance_metrics")
    observed_metrics = evaluation.get("metrics")
    if not isinstance(acceptance_metrics, list) or not acceptance_metrics or not isinstance(observed_metrics, dict):
        errors.append(f"{rule_id}: held-out receipt needs public metrics and frozen acceptance thresholds")
    else:
        if acceptance.get("acceptance_metrics") != acceptance_metrics or evaluation.get("acceptance_metrics") != acceptance_metrics:
            errors.append(f"{rule_id}: acceptance metrics changed after the reviewed freeze")
        metric_passes: list[bool] = []
        for metric in acceptance_metrics:
            if not isinstance(metric, dict) or not _nonempty(metric.get("name")) or not isinstance(metric.get("direction"), str) or metric.get("direction") not in {"min", "max"} or not _number(metric.get("threshold")):
                errors.append(f"{rule_id}: frozen acceptance metrics need name/direction/numeric threshold")
                continue
            name = str(metric["name"])
            value = observed_metrics.get(name)
            if not _number(value):
                errors.append(f"{rule_id}: held-out public metric {name} is missing or non-numeric")
                continue
            metric_passes.append(value >= metric["threshold"] if metric["direction"] == "min" else value <= metric["threshold"])
        computed_metrics_pass = bool(metric_passes) and all(metric_passes)
        if evaluation.get("metrics_passed") is not computed_metrics_pass or evaluation.get("passed") is not computed_metrics_pass:
            errors.append(f"{rule_id}: held-out result does not pass the frozen numeric acceptance thresholds")
    candidate_at = _parse_time(candidate.get("created_at"))
    acceptance_at = _parse_time(acceptance.get("created_at"))
    frozen_at = _parse_time(freeze.get("frozen_at"))
    evaluated_at = _parse_time(evaluation.get("evaluated_at"))
    if not candidate_at or not acceptance_at or not frozen_at or not evaluated_at:
        errors.append(f"{rule_id}: candidate/acceptance/freeze/evaluation times must be timezone-aware ISO timestamps")
    elif not (candidate_at <= frozen_at and acceptance_at <= frozen_at < evaluated_at):
        errors.append(f"{rule_id}: held-out evaluation must occur after the frozen candidate")
    return by_role


def _validate_rule(rule: Any, index: int, budget: dict[str, Any], development_ids: set[str], heldout_ids: set[str], base_dir: Path | None, errors: list[str]) -> tuple[str, str]:
    if not isinstance(rule, dict):
        errors.append(f"rules[{index}] must be an object")
        return f"<rule-{index}>", f"<lineage-{index}>"
    rule_id = str(rule.get("rule_id", ""))
    lineage_id = str(rule.get("lineage_id", ""))
    status = rule.get("status")
    if not re.fullmatch(r"PTSI-[A-Za-z0-9._-]+", rule_id):
        errors.append(f"rules[{index}] has invalid rule_id")
    if not _nonempty(lineage_id):
        errors.append(f"{rule_id or '<rule>'} lacks lineage_id")
    if not isinstance(status, str) or status not in ALLOWED_STATUSES:
        errors.append(f"{rule_id or '<rule>'} has invalid status {status!r}")
    mechanism_id = rule.get("mechanism_id")
    if not _nonempty(mechanism_id):
        errors.append(f"{rule_id or '<rule>'} lacks one mechanism_id")
    if "mechanism_ids" in rule and (not isinstance(rule["mechanism_ids"], list) or len(rule["mechanism_ids"]) != 1):
        errors.append(f"{rule_id or '<rule>'} must contain one mechanism per lineage")

    _validate_map_reduce(rule, development_ids, heldout_ids, base_dir, errors)
    implementation = rule.get("implementation", {})
    if isinstance(status, str) and status in {"provisional", "promoted"}:
        if not isinstance(implementation, dict):
            errors.append(f"{rule_id}: implementation record required")
            implementation = {}
        if not _nonempty(implementation.get("implementer_id")):
            errors.append(f"{rule_id}: implementation lacks implementer_id")
        if not _nonempty(implementation.get("exit_condition")):
            errors.append(f"{rule_id}: implementation lacks explicit exit_condition")
        iterations = implementation.get("iterations")
        if not isinstance(iterations, int) or isinstance(iterations, bool) or iterations < 1:
            errors.append(f"{rule_id}: implementation iterations must be a positive integer")
        elif isinstance(budget.get("max_iterations_per_lineage"), int) and iterations > budget["max_iterations_per_lineage"]:
            errors.append(f"{rule_id}: implementation exceeds max_iterations_per_lineage")

        review = rule.get("review")
        if not isinstance(review, dict):
            errors.append(f"{rule_id}: independent reviewer record required")
        else:
            reviewer = review.get("reviewer_id")
            if not _nonempty(reviewer) or reviewer == implementation.get("implementer_id"):
                errors.append(f"{rule_id}: reviewer must be distinct from implementer")
            if review.get("decision") != "pass" or not isinstance(review.get("evidence"), list) or not review.get("evidence"):
                errors.append(f"{rule_id}: reviewer must record pass and evidence")
            cycles = review.get("cycles")
            if not isinstance(cycles, int) or isinstance(cycles, bool) or cycles < 1 or (isinstance(budget.get("max_review_cycles_per_lineage"), int) and cycles > budget["max_review_cycles_per_lineage"]):
                errors.append(f"{rule_id}: review cycles exceed or omit max_review_cycles_per_lineage")

        _validate_development_screen(rule.get("development_screen"), rule_id, errors)

    heldout = rule.get("held_out")
    if isinstance(heldout, dict) and heldout.get("available") is True:
        if heldout.get("sealed") is not True or heldout.get("feedback_to_search") is not False:
            errors.append(f"{rule_id}: held-out evaluation must be sealed and feedback-free")
        if "raw_results" in heldout or "raw_trace" in heldout or "repair_advice" in heldout:
            errors.append(f"{rule_id}: raw held-out results/repair advice cannot enter development ledger")
        if not _nonempty(heldout.get("manifest_hash")) or not _nonempty(heldout.get("result_digest")):
            errors.append(f"{rule_id}: held-out record needs manifest_hash and result_digest")
        if not _bool(heldout.get("passed")):
            errors.append(f"{rule_id}: held-out record needs boolean passed")
    if status == "promoted":
        freeze = rule.get("freeze")
        if not isinstance(freeze, dict) or not _nonempty(freeze.get("frozen_at")) or not _nonempty(freeze.get("candidate_digest")) or not _nonempty(freeze.get("acceptance_rule")):
            errors.append(f"{rule_id}: promoted rule needs frozen candidate and acceptance artifacts")
        if not isinstance(heldout, dict) or heldout.get("available") is not True or heldout.get("passed") is not True:
            errors.append(f"{rule_id}: promoted rule needs an independent passing held-out evaluation")
        _validate_receipts(rule, base_dir, errors)
        timeline = rule.get("timeline")
        if not isinstance(timeline, list):
            errors.append(f"{rule_id}: timeline with freeze/evaluation events is required")
        else:
            names = [item.get("event") for item in timeline if isinstance(item, dict)]
            if "candidate_frozen" not in names or "held_out_evaluated" not in names:
                errors.append(f"{rule_id}: timeline must record candidate_frozen before held_out_evaluated")
            else:
                freeze_index = names.index("candidate_frozen")
                evaluation_index = names.index("held_out_evaluated")
                if freeze_index >= evaluation_index:
                    errors.append(f"{rule_id}: timeline places held-out evaluation before freeze")
                freeze_at = _parse_time(timeline[freeze_index].get("at")) if isinstance(timeline[freeze_index], dict) else None
                evaluation_at = _parse_time(timeline[evaluation_index].get("at")) if isinstance(timeline[evaluation_index], dict) else None
                if not freeze_at or not evaluation_at or freeze_at >= evaluation_at:
                    errors.append(f"{rule_id}: timeline timestamps must place held-out evaluation after freeze")
                for item in timeline:
                    if not isinstance(item, dict) or not _parse_time(item.get("at")):
                        errors.append(f"{rule_id}: every timeline event needs a timezone-aware timestamp")
                        break
        promotion = rule.get("promotion")
        if not isinstance(promotion, dict):
            errors.append(f"{rule_id}: promotion metadata required")
        else:
            for field in ("rule_text", "scope", "validation_limits", "rollback"):
                if not _nonempty(promotion.get(field)):
                    errors.append(f"{rule_id}: promotion metadata lacks {field}")
            if not isinstance(promotion.get("provenance"), list) or not promotion.get("provenance"):
                errors.append(f"{rule_id}: promotion metadata lacks provenance")
            if "supersedes" in promotion and not isinstance(promotion.get("supersedes"), list):
                errors.append(f"{rule_id}: supersedes must be a list")
    return rule_id, lineage_id


def validate_ledger(ledger: dict[str, Any], base_dir: Path | None = None) -> list[str]:
    errors: list[str] = []
    if ledger.get("schema_version") != 1:
        errors.append("schema_version must be 1")
    if not _nonempty(ledger.get("case_id")):
        errors.append("case_id is required")
    source = _as_dict(ledger.get("source"), "source", errors)
    if source.get("article") != SOURCE_URL:
        errors.append("source.article must cite the SoL-Pi adaptation source")
    budget = _as_dict(ledger.get("budget"), "budget", errors)
    for field in ("max_lineages", "max_iterations_per_lineage", "max_review_cycles_per_lineage"):
        if not isinstance(budget.get(field), int) or isinstance(budget.get(field), bool) or budget[field] < 1:
            errors.append(f"budget.{field} must be a positive integer")
    if not _nonempty(budget.get("exit_condition")):
        errors.append("budget.exit_condition is required")
    splits = _as_dict(ledger.get("splits"), "splits", errors)
    development = splits.get("development_ids", [])
    heldout = splits.get("held_out_ids", [])
    if not isinstance(development, list) or any(not _nonempty(item) for item in development):
        errors.append("splits.development_ids must be a list of non-empty IDs")
        development = []
    if not isinstance(heldout, list) or any(not _nonempty(item) for item in heldout):
        errors.append("splits.held_out_ids must be a list of non-empty IDs")
        heldout = []
    development_ids = set(map(str, development))
    heldout_ids = set(map(str, heldout))
    if development_ids & heldout_ids:
        errors.append("development and held-out IDs must be disjoint")
    if splits.get("held_out_feedback_to_search") is not False:
        errors.append("splits.held_out_feedback_to_search must be false")
    rules = ledger.get("rules")
    if not isinstance(rules, list):
        errors.append("rules must be a list")
        rules = []
    if isinstance(budget.get("max_lineages"), int) and len(rules) > budget["max_lineages"]:
        errors.append("rules exceed budget.max_lineages")
    seen_rule_ids: set[str] = set()
    lineage_mechanisms: dict[str, str] = {}
    for index, rule in enumerate(rules):
        rule_id, lineage_id = _validate_rule(rule, index, budget, development_ids, heldout_ids, base_dir, errors)
        if rule_id in seen_rule_ids:
            errors.append(f"duplicate rule_id: {rule_id}")
        seen_rule_ids.add(rule_id)
        if lineage_id in lineage_mechanisms and isinstance(rule, dict) and lineage_mechanisms[lineage_id] != str(rule.get("mechanism_id")):
            errors.append(f"lineage {lineage_id} contains more than one mechanism")
        elif lineage_id and isinstance(rule, dict):
            lineage_mechanisms[lineage_id] = str(rule.get("mechanism_id"))
    events = ledger.get("events")
    if not isinstance(events, list):
        errors.append("events must be a list")
    else:
        event_ids: set[str] = set()
        for index, event in enumerate(events):
            if not isinstance(event, dict):
                errors.append(f"events[{index}] must be an object")
                continue
            event_id = event.get("event_id")
            event_key = str(event_id)
            if not _nonempty(event_id) or event_key in event_ids:
                errors.append(f"events[{index}] has missing or duplicate event_id")
            event_ids.add(event_key)
            event_status = event.get("status")
            if not isinstance(event_status, str) or event_status not in EVENT_STATUSES:
                errors.append(f"events[{index}] has invalid status")
            event_rule_id = str(event.get("rule_id"))
            if event_rule_id not in seen_rule_ids and event_rule_id != "case":
                errors.append(f"events[{index}] references unknown rule_id")
    errors.extend(_heldout_leaks(ledger, heldout_ids))
    # The split declaration itself is the sole allowed place for bare held-out IDs outside a rule's
    # sealed held_out record. This catches a common mistake: copying evaluation task names into a
    # proposal or reviewer note.
    return sorted(set(errors))


def _managed_block(text: str) -> tuple[str, str, str]:
    starts = [m.start() for m in re.finditer(re.escape(MARKER_START), text)]
    ends = [m.start() for m in re.finditer(re.escape(MARKER_END), text)]
    if not starts and not ends:
        return text, "", ""
    if len(starts) != 1 or len(ends) != 1 or ends[0] < starts[0]:
        raise LedgerError("AGENTS managed section has missing or duplicate markers")
    start = starts[0]
    end = ends[0] + len(MARKER_END)
    return text[:start], text[start:end], text[end:]


def _render_rule(rule: dict[str, Any]) -> str:
    promotion = rule.get("promotion", {})
    rule_id = str(rule["rule_id"])
    title = str(promotion.get("title") or rule.get("title") or rule_id).strip()
    provenance = promotion.get("provenance", [])
    if not isinstance(provenance, list):
        provenance = [str(provenance)]
    supersedes = promotion.get("supersedes", [])
    if not isinstance(supersedes, list):
        supersedes = [str(supersedes)]
    lines = [
        f"### {rule_id}: {title}",
        "- Status: empirically promoted after independent development and sealed held-out checks.",
        f"- Rule: {promotion.get('rule_text', '').strip()}",
        f"- Provenance: {'; '.join(str(item).strip() for item in provenance if str(item).strip())}",
        f"- Scope: {promotion.get('scope', '').strip()}",
        f"- Validation limits: {promotion.get('validation_limits', '').strip()}",
        f"- Rollback/supersession: {promotion.get('rollback', '').strip()}",
    ]
    if supersedes:
        lines.append(f"- Supersedes: {', '.join(str(item) for item in supersedes)}")
    return "\n".join(lines) + "\n"


def _upsert_managed_rule(text: str, rule: dict[str, Any]) -> str:
    prefix, block, suffix = _managed_block(text)
    entry = _render_rule(rule)
    if not block:
        block = f"{MARKER_START}\n\n{entry}{MARKER_END}"
        combined = prefix.rstrip() + "\n\n" + block + "\n"
        return combined
    headings = list(RULE_HEADING.finditer(block))
    ids = [match.group(1) for match in headings]
    if len(ids) != len(set(ids)):
        raise LedgerError("AGENTS managed section contains duplicate rule IDs")
    if len(ids) >= MAX_MANAGED_RULES and rule["rule_id"] not in ids:
        raise LedgerError(f"AGENTS managed section exceeds {MAX_MANAGED_RULES} rule entries")
    target = str(rule["rule_id"])
    existing_index = ids.index(target) if target in ids else None
    if existing_index is not None:
        start = headings[existing_index].start()
        end = headings[existing_index + 1].start() if existing_index + 1 < len(headings) else block.find(MARKER_END)
        existing = block[start:end].strip() + "\n"
        if existing != entry:
            raise LedgerError(f"managed rule {target} already exists with different content; use a new ID")
        return text
    marker_end = block.find(MARKER_END)
    if marker_end < 0:
        raise LedgerError("AGENTS managed section end marker is missing")
    new_block = block[:marker_end].rstrip() + "\n\n" + entry + block[marker_end:]
    return prefix + new_block + suffix


def append_event(ledger: dict[str, Any], rule_id: str, status: str, evidence_refs: Iterable[str] = (), note: str = "") -> bool:
    if status not in EVENT_STATUSES:
        raise LedgerError(f"invalid event status: {status}")
    events = ledger.setdefault("events", [])
    if not isinstance(events, list):
        raise LedgerError("ledger.events must be a list")
    if any(isinstance(event, dict) and event.get("rule_id") == rule_id and event.get("status") == status for event in events):
        return False
    events.append({
        "event_id": f"{rule_id}-{status}-{len(events) + 1}",
        "rule_id": rule_id,
        "status": status,
        "recorded_at": utc_now(),
        "evidence_refs": [str(ref) for ref in evidence_refs],
        "note": note,
    })
    return True


def _commit_with_recovery_journal(
    ledger_path: Path,
    ledger_before: str,
    ledger_after: str,
    file_changes: list[tuple[Path, str, str]],
    rule_id: str,
) -> None:
    targets = [path.resolve() for path, _, _ in file_changes]
    if len(targets) != len(set(targets)):
        raise LedgerError("promotion targets must be distinct")
    for path, _, _ in file_changes:
        if not path.parent.is_dir():
            raise LedgerError(f"promotion target parent does not exist: {path.parent}")
    changes = [(path, old, new) for path, old, new in file_changes if old != new]
    if not changes:
        return
    journal_path = ledger_path.parent / f"promotion-recovery-{rule_id}.json"
    if journal_path.exists():
        try:
            prior = load_json(journal_path)
        except LedgerError:
            raise LedgerError(f"refusing to reuse unreadable recovery journal: {journal_path}")
        if prior.get("status") == "prepared":
            raise LedgerError(f"unfinished promotion recovery journal requires review: {journal_path}")
    journal = {
        "schema_version": 1,
        "status": "prepared",
        "rule_id": rule_id,
        "prepared_at": utc_now(),
        "files": [
            {
                "path": str(path),
                "old_sha256": _sha256_bytes(old.encode("utf-8")),
                "new_sha256": _sha256_bytes(new.encode("utf-8")),
                "old_content": old,
            }
            for path, old, new in changes
        ],
    }
    write_json_atomic(journal_path, journal)
    mutated: list[tuple[Path, str]] = []
    try:
        for path, old, new in changes:
            _write_text_atomic(path, new)
            mutated.append((path, old))
        journal["status"] = "committed"
        journal["committed_at"] = utc_now()
        write_json_atomic(journal_path, journal)
    except Exception as exc:
        rollback_errors: list[str] = []
        for path, old in reversed(mutated):
            try:
                _write_text_atomic(path, old)
            except Exception as rollback_exc:  # pragma: no cover - requires two simultaneous I/O failures
                rollback_errors.append(f"{path}: {rollback_exc}")
        journal["status"] = "rolled_back" if not rollback_errors else "rollback_incomplete"
        journal["rolled_back_at"] = utc_now()
        journal["error"] = str(exc)
        if rollback_errors:
            journal["rollback_errors"] = rollback_errors
        try:
            write_json_atomic(journal_path, journal)
        except Exception:
            pass
        suffix = f"; rollback errors: {rollback_errors}" if rollback_errors else ""
        raise LedgerError(f"promotion transaction failed and was rolled back; recovery journal: {journal_path}{suffix}") from exc


def promote_rule(ledger_path: Path, rule_id: str, plugin_agents: Path, workspace_agents: Path) -> dict[str, Any]:
    ledger_before = ledger_path.read_text(encoding="utf-8") if ledger_path.exists() else ""
    ledger = load_json(ledger_path)
    errors = validate_ledger(ledger, base_dir=ledger_path.parent)
    if errors:
        raise LedgerError("ledger is not promotable:\n- " + "\n- ".join(errors))
    matches = [rule for rule in ledger.get("rules", []) if isinstance(rule, dict) and rule.get("rule_id") == rule_id]
    if len(matches) != 1:
        raise LedgerError(f"expected one rule with ID {rule_id}, found {len(matches)}")
    rule = matches[0]
    if rule.get("status") != "promoted":
        raise LedgerError(f"rule {rule_id} is {rule.get('status')!r}; only promoted rules may enter AGENTS files")
    # Prepare both policy files and the ledger before mutating any target. Missing workspace AGENTS
    # is created only at the explicit target path; no cache or broad directory is searched.
    plugin_text = plugin_agents.read_text(encoding="utf-8") if plugin_agents.exists() else ""
    workspace_text = workspace_agents.read_text(encoding="utf-8") if workspace_agents.exists() else ""
    new_plugin = _upsert_managed_rule(plugin_text, rule)
    new_workspace = _upsert_managed_rule(workspace_text, rule)
    event_added = append_event(ledger, rule_id, "promoted", evidence_refs=rule.get("promotion", {}).get("provenance", []), note="Consolidated into both canonical AGENTS files.")
    ledger_after = json.dumps(ledger, indent=2, ensure_ascii=False) + "\n" if event_added else ledger_before
    changes = [(plugin_agents, plugin_text, new_plugin), (workspace_agents, workspace_text, new_workspace)]
    if event_added:
        changes.append((ledger_path, ledger_before, ledger_after))
    if all(old == new for _, old, new in changes):
        return {"rule_id": rule_id, "changed": False, "event_added": False, "files": [str(plugin_agents), str(workspace_agents)]}
    _commit_with_recovery_journal(ledger_path, ledger_before, ledger_after, changes, rule_id)
    return {"rule_id": rule_id, "changed": bool(new_plugin != plugin_text or new_workspace != workspace_text), "event_added": event_added, "files": [str(plugin_agents), str(workspace_agents)]}


def init_ledger(case_dir: Path, case_id: str) -> Path:
    path = case_dir / "learning" / "audit-ledger.json"
    if path.exists():
        raise LedgerError(f"refusing to overwrite existing ledger: {path}")
    write_json_atomic(path, default_ledger(case_id))
    return path


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    init = sub.add_parser("init", help="create a case ledger without overwriting it")
    init.add_argument("--case-dir", type=Path, required=True)
    init.add_argument("--case-id", required=True)
    validate = sub.add_parser("validate", help="validate ledger invariants")
    validate.add_argument("--ledger", type=Path, required=True)
    promote = sub.add_parser("promote", help="consolidate one evidenced promoted rule")
    promote.add_argument("--ledger", type=Path, required=True)
    promote.add_argument("--rule-id", required=True)
    promote.add_argument("--plugin-agents", type=Path, required=True)
    promote.add_argument("--workspace-agents", type=Path, required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    try:
        if args.command == "init":
            path = init_ledger(args.case_dir, args.case_id)
            print(path)
            return 0
        ledger = load_json(args.ledger)
        if args.command == "validate":
            errors = validate_ledger(ledger, base_dir=args.ledger.parent)
            if errors:
                print("FAIL: PT self-improvement ledger")
                for error in errors:
                    print(f"- {error}")
                return 1
            print(f"PASS: PT self-improvement ledger: {args.ledger}")
            return 0
        result = promote_rule(args.ledger, args.rule_id, args.plugin_agents, args.workspace_agents)
        print(json.dumps(result, indent=2))
        return 0
    except LedgerError as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
