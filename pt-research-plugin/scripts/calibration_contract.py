#!/usr/bin/env python3
"""Semantic gates for parameter calibration and independent validation.

The JSON schema documents the interchange shape.  This module enforces the
parts that a small dependency-free schema checker cannot express: finite
numbers, hash-backed local artifacts, temporal ordering, parameter bounds,
identifiability, and disjoint fit/validation records.  A calibration fit is
never treated as physical validation; the latter requires a separate report
with held-out observations and uncertainty-aware comparison evidence.
"""

from __future__ import annotations

import hashlib
import math
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from artifact_lib import load_artifact


CALIBRATION_PLAN = "calibration_plan.yaml"
CALIBRATION_VERSION = 1
CALIBRATION_STATUSES = {"planned", "not_required", "calibrated", "physically_validated", "failed"}
CALIBRATION_CLAIMS = {
    "calibrated",
    "calibration_complete",
    "parameter_calibrated",
    "parameter_calibration_complete",
    "fit_frozen",
    "fitted",
}
PHYSICAL_CLAIMS = {
    "physically_validated",
    "physical_validation",
    "physical_validation_passed",
    "experimentally_validated",
    "experimentally_compared",
}
NUMERICAL_CLAIMS = {
    "numerically_validated",
    "numerically_verified",
    "numerical_verification",
    "numerical_verification_passed",
}
PLACEHOLDERS = {
    "",
    "pending",
    "not_enabled",
    "not_applicable",
    "not_started",
    "unknown",
    "tbd",
    "to be determined",
}
HASH_RE = re.compile(r"^(?:sha256:)?[0-9a-fA-F]{64}$")


def _objects(value: Any) -> list[dict[str, Any]]:
    return [item for item in value if isinstance(item, dict)] if isinstance(value, list) else []


def _placeholder(value: Any) -> bool:
    return isinstance(value, str) and value.strip().lower() in PLACEHOLDERS


def _text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip()) and not _placeholder(value)


def _finite(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(float(value))


def _positive(value: Any) -> bool:
    return _finite(value) and float(value) > 0


def _hash(value: Any) -> bool:
    return isinstance(value, str) and bool(HASH_RE.fullmatch(value.strip()))


def _timestamp(value: Any) -> datetime | None:
    if not _text(value):
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        return None
    return parsed.astimezone(timezone.utc)


def _same_ids(left: Any, right: Any) -> bool:
    return (
        all(isinstance(item, str) for item in left)
        and all(isinstance(item, str) for item in right)
        and set(left) == set(right)
        if isinstance(left, list) and isinstance(right, list)
        else False
    )


def _duplicates(values: list[Any]) -> set[Any]:
    seen: set[str] = set()
    duplicate: set[str] = set()
    for value in values:
        key = value if isinstance(value, str) else repr(value)
        if key in seen:
            duplicate.add(key)
        seen.add(key)
    return duplicate


def _artifact_path(case_dir: Path, locator: Any, label: str, errors: list[str]) -> Path | None:
    if not _text(locator):
        errors.append(f"{label} must name a frozen case-relative artifact")
        return None
    path = Path(str(locator))
    if path.is_absolute() or ".." in path.parts:
        errors.append(f"{label} must be a case-relative path")
        return None
    resolved = (case_dir / path).resolve()
    try:
        resolved.relative_to(case_dir.resolve())
    except ValueError:
        errors.append(f"{label} escapes the case directory")
        return None
    if not resolved.is_file():
        errors.append(f"{label} does not exist: {locator}")
        return None
    return resolved


def _check_artifact_hash(case_dir: Path, locator: Any, expected: Any, label: str, errors: list[str]) -> bool:
    path = _artifact_path(case_dir, locator, label, errors)
    if path is None:
        return False
    if not _hash(expected):
        errors.append(f"{label} has no SHA-256 hash")
        return False
    actual = hashlib.sha256(path.read_bytes()).hexdigest()
    if actual.lower() != str(expected).lower().removeprefix("sha256:"):
        errors.append(f"{label} hash does not match the frozen artifact")
        return False
    return True


def _load_frozen_fit_content(
    case_dir: Path,
    locator: Any,
    fit: dict[str, Any],
    dataset: dict[str, Any],
    selected_model_id: Any,
    errors: list[str],
) -> bool:
    """Check that the hash-backed fit file carries the declared fit record.

    This is intentionally a local JSON-compatible record rather than an
    optimizer implementation.  It proves that the declared parameter and
    objective values are bound to the frozen bytes; it does not independently
    rerun a solver or establish physical validity.
    """
    path = _artifact_path(case_dir, locator, "fit_result.fit_artifact_locator", errors)
    if path is None:
        return False
    try:
        content = load_artifact(path)
    except ValueError as exc:
        errors.append(f"frozen fit artifact is not a JSON-compatible record: {exc}")
        return False
    if not isinstance(content, dict):
        errors.append("frozen fit artifact must contain an object")
        return False
    ok = True
    if content.get("fit_data_hash") != fit.get("fit_data_hash"):
        errors.append("frozen fit artifact fit_data_hash disagrees with fit_result")
        ok = False
    if content.get("dataset_content_hash") != dataset.get("content_hash"):
        errors.append("frozen fit artifact dataset_content_hash disagrees with the source dataset")
        ok = False
    if not _text(content.get("model_id")):
        errors.append("frozen fit artifact lacks model_id")
        ok = False
    elif _text(selected_model_id) and content.get("model_id") != selected_model_id:
        errors.append("frozen fit artifact model_id disagrees with simulation_spec")
        ok = False
    if content.get("objective_value") != fit.get("objective_value"):
        errors.append("frozen fit artifact objective_value disagrees with fit_result")
        ok = False
    declared_values = _objects(content.get("parameter_values"))
    fit_values = _objects(fit.get("parameter_values"))
    if len(declared_values) != len(fit_values):
        errors.append("frozen fit artifact parameter_values disagree with fit_result")
        ok = False
    else:
        def keyed(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
            return {str(row.get("name")): row for row in rows if _text(row.get("name"))}
        declared_by_name, fit_by_name = keyed(declared_values), keyed(fit_values)
        if set(declared_by_name) != set(fit_by_name):
            errors.append("frozen fit artifact parameter names disagree with fit_result")
            ok = False
        for name, row in fit_by_name.items():
            declared = declared_by_name.get(name, {})
            if declared.get("value") != row.get("value") or declared.get("unit") != row.get("unit"):
                errors.append(f"frozen fit artifact parameter {name} disagrees with fit_result")
                ok = False
    return ok


def _numeric_metric(value: Any, threshold: Any, direction: str, label: str, errors: list[str]) -> bool:
    if not _finite(value) or not _finite(threshold):
        errors.append(f"{label} requires finite criterion_value and acceptance threshold")
        return False
    passed = float(value) <= float(threshold) if direction == "minimize" else float(value) >= float(threshold)
    if not passed:
        errors.append(f"{label} numeric criterion fails: value={value} threshold={threshold} direction={direction}")
    return passed


def _validate_dataset(dataset: dict[str, Any], errors: list[str]) -> dict[str, dict[str, Any]]:
    for field in ("dataset_id", "source", "source_locator", "content_hash", "unit_system"):
        if not _text(dataset.get(field)):
            errors.append(f"calibration dataset lacks concrete {field}")
    if not _hash(dataset.get("content_hash")):
        errors.append("calibration dataset content_hash must be a SHA-256 hash")
    variables = _objects(dataset.get("variables"))
    if not variables:
        errors.append("calibration dataset has no measured variables with units and uncertainty metadata")
    for index, variable in enumerate(variables, start=1):
        for field in ("name", "unit", "uncertainty_status"):
            if not _text(variable.get(field)):
                errors.append(f"calibration dataset variable {index} lacks {field}")
        uncertainty_status = variable.get("uncertainty_status")
        if isinstance(uncertainty_status, str) and uncertainty_status in {"measured", "estimated"}:
            uncertainty = variable.get("uncertainty")
            if not isinstance(uncertainty, dict) or not _positive(uncertainty.get("value")) or not _text(uncertainty.get("unit")):
                errors.append(f"calibration dataset variable {index} lacks a positive uncertainty value and unit")
        elif uncertainty_status == "not_applicable":
            if not _text(variable.get("uncertainty_justification")):
                errors.append(f"calibration dataset variable {index} marks uncertainty not applicable without justification")
        elif uncertainty_status == "missing":
            errors.append(f"calibration dataset variable {index} has missing uncertainty")
        else:
            errors.append(f"calibration dataset variable {index} has unknown uncertainty_status")

    records: dict[str, dict[str, Any]] = {}
    observation_index = dataset.get("observation_index")
    if not isinstance(observation_index, list):
        errors.append("calibration dataset observation_index must be an array")
    for index, record in enumerate(_objects(observation_index), start=1):
        observation_id = record.get("observation_id")
        if not _text(observation_id):
            errors.append(f"calibration observation {index} lacks observation_id")
            continue
        if observation_id in records:
            errors.append(f"calibration observation IDs are duplicated: {observation_id}")
            continue
        for field in ("group_id", "replicate_id"):
            if not _text(record.get(field)):
                errors.append(f"calibration observation {observation_id} lacks {field}")
        records[str(observation_id)] = record
    return records


def _validate_objective(objective: dict[str, Any], errors: list[str]) -> tuple[str, float | None]:
    for field in ("metric", "formula", "predeclared_at"):
        if not _text(objective.get(field)):
            errors.append(f"calibration objective lacks concrete {field}")
    direction = objective.get("direction")
    if not isinstance(direction, str) or direction not in {"minimize", "maximize"}:
        errors.append("calibration objective direction must be minimize or maximize")
        direction = "minimize"
    if not isinstance(objective.get("target_observables"), list) or not objective.get("target_observables"):
        errors.append("calibration objective must name target observables")
    threshold = objective.get("acceptance_threshold")
    if not isinstance(threshold, dict) or not _finite(threshold.get("value")) or not _text(threshold.get("unit")):
        errors.append("calibration objective needs a finite acceptance_threshold value and unit")
        return direction, None
    declared = _timestamp(objective.get("predeclared_at"))
    if declared is None:
        errors.append("calibration objective predeclared_at is not an ISO-8601 timestamp")
    return direction, float(threshold["value"])


def _validate_parameters(parameters: Any, errors: list[str]) -> dict[str, dict[str, Any]]:
    rows = _objects(parameters)
    if not rows:
        errors.append("calibration has no parameter definitions")
    definitions: dict[str, dict[str, Any]] = {}
    for index, parameter in enumerate(rows, start=1):
        name = parameter.get("name")
        if not _text(name):
            errors.append(f"calibration parameter {index} lacks name")
            continue
        name = str(name)
        if name in definitions:
            errors.append(f"calibration parameter names are duplicated: {name}")
        definitions[name] = parameter
        for field in ("unit", "role"):
            if not _text(parameter.get(field)):
                errors.append(f"calibration parameter {name} lacks {field}")
        lower, upper = parameter.get("lower_bound"), parameter.get("upper_bound")
        if not _finite(lower) or not _finite(upper) or float(lower) >= float(upper):
            errors.append(f"calibration parameter {name} has invalid finite bounds")
        identifiability = parameter.get("identifiability")
        if not isinstance(identifiability, dict) or not _text(identifiability.get("method")) or not _text(identifiability.get("status")):
            errors.append(f"calibration parameter {name} lacks identifiability method/status")
        elif identifiability.get("status") == "pass":
            if not _text(identifiability.get("evidence_locator")) or not _finite(identifiability.get("metric")):
                errors.append(f"calibration parameter {name} claims identifiability pass without numeric evidence")
    return definitions


def _validate_split(
    split: dict[str, Any],
    records: dict[str, dict[str, Any]],
    errors: list[str],
    *,
    require_fit: bool = True,
) -> None:
    strategy = split.get("strategy")
    supported = {"predeclared_holdout", "grouped_holdout", "replicate_holdout", "time_holdout"}
    if not require_fit:
        supported.add("external_validation")
    if not isinstance(strategy, str) or strategy not in supported:
        errors.append("calibration split strategy is not a supported held-out strategy")
    fit_ids = split.get("fit_observation_ids")
    validation_ids = split.get("validation_observation_ids")
    if not isinstance(fit_ids, list) or not isinstance(validation_ids, list) or (require_fit and not fit_ids) or not validation_ids:
        errors.append("calibration split needs validation IDs and, when fitting, non-empty fit IDs")
        fit_ids, validation_ids = [], []
    if not all(isinstance(item, str) for item in fit_ids + validation_ids):
        errors.append("calibration split observation IDs must all be strings")
        fit_ids = [item for item in fit_ids if isinstance(item, str)]
        validation_ids = [item for item in validation_ids if isinstance(item, str)]
    for label, ids in (("fit", fit_ids), ("validation", validation_ids)):
        duplicate = _duplicates(ids)
        if duplicate:
            errors.append(f"calibration {label} observation IDs are duplicated: {sorted(duplicate)}")
        unknown = sorted(set(ids) - set(records))
        if unknown:
            errors.append(f"calibration {label} split references unknown observations: {unknown}")
    fit_set, validation_set = set(fit_ids), set(validation_ids)
    for observation_id, record in records.items():
        declared_split = record.get("split")
        if declared_split is not None and (not isinstance(declared_split, str) or declared_split not in {"fit", "validation"}):
            errors.append(f"calibration observation {observation_id} has unknown split label")
        elif declared_split == "fit" and observation_id not in fit_set:
            errors.append(f"calibration observation {observation_id} is indexed as fit but absent from fit_observation_ids")
        elif declared_split == "validation" and observation_id not in validation_set:
            errors.append(f"calibration observation {observation_id} is indexed as validation but absent from validation_observation_ids")
    overlap = sorted(set(fit_ids) & set(validation_ids))
    if overlap:
        errors.append(f"calibration fit and validation observations overlap: {overlap}")

    def ids(field: str) -> set[str]:
        values = split.get(field)
        if not isinstance(values, list):
            errors.append(f"calibration split field {field} must be an array")
            return set()
        if not all(isinstance(item, str) for item in values):
            errors.append(f"calibration split field {field} must contain only strings")
            values = [item for item in values if isinstance(item, str)]
        duplicate = _duplicates(values)
        if duplicate:
            errors.append(f"calibration split field {field} is duplicated: {sorted(duplicate)}")
        return {str(item) for item in values}

    fit_groups, validation_groups = ids("fit_group_ids"), ids("validation_group_ids")
    fit_replicates, validation_replicates = ids("fit_replicate_ids"), ids("validation_replicate_ids")
    if fit_groups & validation_groups:
        errors.append("calibration fit and validation groups overlap")
    if fit_replicates & validation_replicates:
        errors.append("calibration fit and validation replicates overlap")
    expected_fit_groups = {str(records[item].get("group_id")) for item in fit_ids if item in records}
    expected_validation_groups = {str(records[item].get("group_id")) for item in validation_ids if item in records}
    expected_fit_replicates = {str(records[item].get("replicate_id")) for item in fit_ids if item in records}
    expected_validation_replicates = {str(records[item].get("replicate_id")) for item in validation_ids if item in records}
    if fit_groups != expected_fit_groups or validation_groups != expected_validation_groups:
        errors.append("calibration split group IDs do not match the observation index")
    if fit_replicates != expected_fit_replicates or validation_replicates != expected_validation_replicates:
        errors.append("calibration split replicate IDs do not match the observation index")
    for field in ("fit_data_hash", "validation_data_hash"):
        if not _hash(split.get(field)):
            errors.append(f"calibration split {field} must be a SHA-256 hash")
    if _hash(split.get("fit_data_hash")) and str(split.get("fit_data_hash")).lower() == str(split.get("validation_data_hash")).lower():
        errors.append("calibration fit and validation data hashes are identical")


def _validate_residual_summary(summary: Any, label: str, errors: list[str]) -> None:
    if not isinstance(summary, dict):
        errors.append(f"{label} residual_summary must be an object")
        return
    for field in ("n", "rmse", "max_abs", "normalized_rmse"):
        if not _finite(summary.get(field)):
            errors.append(f"{label} residual_summary lacks finite {field}")
    if _finite(summary.get("n")) and float(summary["n"]) < 1:
        errors.append(f"{label} residual_summary n must be positive")
    for field in ("computed_by", "computed_at", "evidence_locator"):
        if not _text(summary.get(field)):
            errors.append(f"{label} residual_summary lacks {field}")


def _validate_numerical_error(value: Any, label: str, errors: list[str]) -> None:
    if not isinstance(value, dict):
        errors.append(f"{label} numerical_error must be an object")
        return
    for field in ("estimate", "tolerance"):
        if not _finite(value.get(field)):
            errors.append(f"{label} numerical_error lacks finite {field}")
    if _finite(value.get("estimate")) and _finite(value.get("tolerance")) and float(value["estimate"]) > float(value["tolerance"]):
        errors.append(f"{label} numerical error exceeds tolerance")
    for field in ("unit", "method", "computed_by", "computed_at"):
        if not _text(value.get(field)):
            errors.append(f"{label} numerical_error lacks {field}")


def _validate_fit_result(
    case_dir: Path,
    fit: dict[str, Any],
    definitions: dict[str, dict[str, Any]],
    objective: dict[str, Any],
    split: dict[str, Any],
    dataset: dict[str, Any],
    selected_model_id: Any,
    errors: list[str],
) -> bool:
    if fit.get("status") == "failed":
        if not _text(fit.get("failure_reason")):
            errors.append("failed calibration fit must record failure_reason")
        return False
    if fit.get("status") != "frozen":
        errors.append("calibration claim requires fit_result.status=frozen")
        return False
    artifact_ok = _check_artifact_hash(case_dir, fit.get("fit_artifact_locator"), fit.get("fit_artifact_hash"), "fit_result.fit_artifact_locator", errors)
    content_ok = _load_frozen_fit_content(case_dir, fit.get("fit_artifact_locator"), fit, dataset, selected_model_id, errors) if artifact_ok else False
    if not _hash(fit.get("fit_data_hash")) or fit.get("fit_data_hash") != split.get("fit_data_hash"):
        errors.append("frozen calibration fit does not identify the declared fit data hash")
    started, frozen, declared = _timestamp(fit.get("fit_started_at")), _timestamp(fit.get("frozen_at")), _timestamp(objective.get("predeclared_at"))
    if started is None or frozen is None:
        errors.append("frozen calibration fit needs aware ISO-8601 fit_started_at and frozen_at")
    elif started > frozen:
        errors.append("calibration fit_started_at is later than frozen_at")
    if declared is not None and started is not None and declared > started:
        errors.append("calibration objective was predeclared after the fit started")
    values = _objects(fit.get("parameter_values"))
    names = [str(row.get("name")) for row in values if _text(row.get("name"))]
    if len(names) != len(set(names)):
        errors.append("frozen calibration parameter values contain duplicate names")
    by_name = {str(row.get("name")): row for row in values if _text(row.get("name"))}
    if set(by_name) != set(definitions):
        errors.append("frozen calibration parameters do not exactly match parameter_definitions")
    for name, definition in definitions.items():
        row = by_name.get(name)
        if row is None:
            continue
        if not _finite(row.get("value")) or not _text(row.get("unit")):
            errors.append(f"frozen calibration parameter {name} lacks finite value and unit")
        elif row.get("unit") != definition.get("unit"):
            errors.append(f"frozen calibration parameter {name} unit disagrees with its definition")
        if _finite(row.get("value")) and (_finite(definition.get("lower_bound")) and float(row["value"]) < float(definition["lower_bound"]) or _finite(definition.get("upper_bound")) and float(row["value"]) > float(definition["upper_bound"])):
            errors.append(f"frozen calibration parameter {name} is outside its declared bounds")
        identifiability = definition.get("identifiability", {})
        if definition.get("role") in {"calibrated", "fit", "free", "estimated"} and identifiability.get("status") != "pass":
            errors.append(f"calibration parameter {name} is not identifiable with status=pass")
    _validate_residual_summary(fit.get("residual_summary"), "fit_result", errors)
    _validate_numerical_error(fit.get("numerical_error"), "fit_result", errors)
    value = fit.get("objective_value")
    threshold = objective.get("acceptance_threshold", {}).get("value") if isinstance(objective.get("acceptance_threshold"), dict) else None
    criterion_ok = _numeric_metric(value, threshold, objective.get("direction", "minimize"), "frozen calibration objective", errors)
    return artifact_ok and content_ok and criterion_ok


def _validate_independent_validation(
    case_dir: Path,
    validation: dict[str, Any],
    plan: dict[str, Any],
    records: dict[str, dict[str, Any]],
    require_pass: bool,
    *,
    has_fitted_parameters: bool = True,
    errors: list[str],
) -> bool:
    status = validation.get("status")
    if status == "failed":
        if not _text(validation.get("failure_reason")):
            errors.append("failed independent validation must record failure_reason")
        if require_pass:
            errors.append("physical validation requires independent_validation.status=passed")
        return False
    if require_pass and status != "passed":
        errors.append("physical validation requires independent_validation.status=passed")
    if status != "passed":
        return False
    split = plan.get("split", {})
    expected_ids = split.get("validation_observation_ids", [])
    if not isinstance(expected_ids, list) or not all(isinstance(item, str) for item in expected_ids):
        errors.append("calibration split validation_observation_ids must be a string array")
        expected_ids = [item for item in expected_ids if isinstance(item, str)] if isinstance(expected_ids, list) else []
    ids = validation.get("observation_ids")
    before = len(errors)
    if not isinstance(ids, list) or not all(isinstance(item, str) for item in ids):
        errors.append("independent validation observation_ids must be a string array")
        ids = [item for item in ids if isinstance(item, str)] if isinstance(ids, list) else []
    if _duplicates(ids):
        errors.append("independent validation observation_ids are duplicated")
    if not _same_ids(ids, expected_ids):
        errors.append("independent validation observation IDs do not match the held-out split")
    unknown = sorted(set(ids or []) - set(records))
    if unknown:
        errors.append(f"independent validation references unknown observations: {unknown}")
    if validation.get("dataset_id") != plan.get("dataset", {}).get("dataset_id"):
        errors.append("independent validation dataset_id does not match the declared dataset")
    if not _hash(validation.get("data_hash")) or validation.get("data_hash") != split.get("validation_data_hash"):
        errors.append("independent validation data_hash does not match the held-out split")
    for field in ("comparison_method", "uncertainty_method", "acceptance_criterion", "performed_at"):
        if not _text(validation.get(field)):
            errors.append(f"independent validation lacks {field}")
    performed = _timestamp(validation.get("performed_at"))
    declared = _timestamp(plan.get("objective", {}).get("predeclared_at"))
    if performed is None:
        errors.append("independent validation performed_at is not an aware ISO-8601 timestamp")
    elif declared is not None and performed < declared:
        errors.append("independent validation predates the predeclared objective")
    for field, expected in (
        ("group_ids", {str(records[item].get("group_id")) for item in ids if item in records}),
        ("replicate_ids", {str(records[item].get("replicate_id")) for item in ids if item in records}),
    ):
        values = validation.get(field)
        if not isinstance(values, list) or not all(isinstance(item, str) for item in values):
            errors.append(f"independent validation {field} must be a string array")
            continue
        if set(values) != expected:
            errors.append(f"independent validation {field} do not match the observation index")
    _validate_residual_summary(validation.get("residual_summary"), "independent_validation", errors)
    _validate_numerical_error(validation.get("numerical_error"), "independent_validation", errors)
    objective = plan.get("objective", {})
    threshold = objective.get("acceptance_threshold", {}).get("value") if isinstance(objective.get("acceptance_threshold"), dict) else None
    criterion_ok = _numeric_metric(validation.get("objective_value"), threshold, objective.get("direction", "minimize"), "independent validation objective", errors)
    fit = plan.get("fit_result", {})
    if not isinstance(fit, dict):
        errors.append("calibration fit_result must be an object")
        fit = {}
    if has_fitted_parameters and _text(fit.get("fit_artifact_hash")) and validation.get("fit_artifact_hash") != fit.get("fit_artifact_hash"):
        errors.append("independent validation does not identify the frozen calibration artifact")
    if not has_fitted_parameters:
        for field in ("frozen_model_artifact_locator", "frozen_model_artifact_hash", "frozen_input_artifact_locator", "frozen_input_artifact_hash"):
            if not _text(validation.get(field)) and not _hash(validation.get(field)):
                errors.append(f"independent validation without fitted parameters lacks {field}")
        if _text(validation.get("frozen_model_artifact_locator")):
            _check_artifact_hash(case_dir, validation.get("frozen_model_artifact_locator"), validation.get("frozen_model_artifact_hash"), "independent_validation.frozen_model_artifact_locator", errors)
        if _text(validation.get("frozen_input_artifact_locator")):
            _check_artifact_hash(case_dir, validation.get("frozen_input_artifact_locator"), validation.get("frozen_input_artifact_hash"), "independent_validation.frozen_input_artifact_locator", errors)
    return criterion_ok and len(errors) == before


def _find_validation_report(case_dir: Path, errors: list[str]) -> dict[str, Any] | None:
    for relative in ("validation_report.yaml", "openfoam/validation_report.yaml", "simulation/validation_report.yaml"):
        path = case_dir / relative
        if not path.is_file():
            continue
        try:
            value = load_artifact(path)
        except ValueError as exc:
            errors.append(str(exc))
            return None
        if not isinstance(value, dict):
            errors.append(f"{relative} must contain an object")
            return None
        return value
    return None


def _validate_report_section(
    case_dir: Path,
    section: Any,
    label: str,
    errors: list[str],
    *,
    require_independent: bool = False,
    expected_dataset_id: str | None = None,
    expected_data_hash: str | None = None,
    expected_observation_ids: list[str] | None = None,
    expected_value: float | None = None,
    expected_threshold: float | None = None,
    expected_fit_artifact_hash: str | None = None,
    direction: str = "minimize",
    minimum_timestamp: datetime | None = None,
) -> bool:
    if not isinstance(section, dict):
        errors.append(f"validation report lacks {label} section")
        return False
    status = section.get("status")
    if status == "failed":
        if not _text(section.get("failure_reason")):
            errors.append(f"failed {label} must record failure_reason")
        errors.append(f"{label} failed and cannot support the claimed state")
        return False
    if status != "passed":
        errors.append(f"{label} status is not passed")
        return False
    for field in ("criterion_value", "criterion_threshold"):
        if not _finite(section.get(field)):
            errors.append(f"passed {label} lacks finite {field}")
    criterion_ok = _numeric_metric(section.get("criterion_value"), section.get("criterion_threshold"), direction, label, errors)
    for field in ("computed_by", "computed_at", "evidence_locator", "evidence_hash"):
        if not _text(section.get(field)):
            errors.append(f"passed {label} lacks {field}")
    if _text(section.get("evidence_locator")):
        _check_artifact_hash(case_dir, section.get("evidence_locator"), section.get("evidence_hash"), f"{label}.evidence_locator", errors)
    computed_at = _timestamp(section.get("computed_at"))
    if computed_at is None:
        errors.append(f"passed {label} computed_at is not an aware ISO-8601 timestamp")
    elif minimum_timestamp is not None and computed_at < minimum_timestamp:
        errors.append(f"passed {label} computed_at predates its independent validation")
    if expected_value is not None and section.get("criterion_value") != expected_value:
        errors.append(f"{label} criterion_value does not match the declared validation metric")
    if expected_threshold is not None and section.get("criterion_threshold") != expected_threshold:
        errors.append(f"{label} criterion_threshold does not match the predeclared objective")
    if expected_fit_artifact_hash is not None and section.get("fit_artifact_hash") != expected_fit_artifact_hash:
        errors.append(f"{label} fit_artifact_hash does not match the frozen fit")
    if require_independent:
        if not _text(section.get("independent_dataset_id")):
            errors.append(f"passed {label} lacks independent_dataset_id")
        if not _hash(section.get("data_hash")):
            errors.append(f"passed {label} lacks a SHA-256 data_hash")
        if not _text(section.get("uncertainty_method")):
            errors.append(f"passed {label} lacks uncertainty_method")
        ids = section.get("observation_ids")
        if not isinstance(ids, list) or not ids or not all(isinstance(item, str) for item in ids):
            errors.append(f"passed {label} lacks held-out observation_ids")
        if expected_dataset_id is not None and section.get("independent_dataset_id") != expected_dataset_id:
            errors.append(f"passed {label} dataset_id does not match the plan")
        if expected_data_hash is not None and section.get("data_hash") != expected_data_hash:
            errors.append(f"passed {label} data_hash does not match the plan")
        if expected_observation_ids is not None and not _same_ids(ids, expected_observation_ids):
            errors.append(f"passed {label} observation_ids do not match the plan")
        if section.get("independent") is not True:
            errors.append(f"passed {label} must declare independent=true")
    return criterion_ok and not errors


def _claim_tokens(case_dir: Path, loaded: dict[str, Any], handoff: dict[str, Any] | None) -> set[str]:
    tokens: set[str] = set()
    state = loaded.get("project_state.yaml", {})
    if isinstance(state, dict):
        tokens.add(str(state.get("stage", "")).strip().lower())
        tokens.add(str(state.get("software_readiness", "")).strip().lower())
        for claim in _objects(state.get("claims")):
            if claim.get("status") in {"completed", "passed", "accepted", "claimed"}:
                tokens.add(str(claim.get("stage", "")).strip().lower())
    if isinstance(handoff, dict):
        tokens.add(str(handoff.get("highest_state", "")).strip().lower())
        tokens.add(str(handoff.get("software_readiness", "")).strip().lower())
    return {token for token in tokens if token}


def _has_version_one_marker(loaded: dict[str, Any]) -> bool:
    state = loaded.get("project_state.yaml", {})
    if isinstance(state, dict) and state.get("calibration_contract_version") == CALIBRATION_VERSION and not isinstance(state.get("calibration_contract_version"), bool):
        return True
    spec = loaded.get("simulation_spec.yaml", {})
    if isinstance(spec, dict):
        calibration = spec.get("calibration")
        if isinstance(calibration, dict):
            marker = calibration.get("calibration_contract_version", calibration.get("contract_version"))
            if marker == CALIBRATION_VERSION and not isinstance(marker, bool):
                return True
    return False


def validate_calibration_contract(case_dir: Path, loaded: dict[str, Any]) -> list[str]:
    """Return semantic calibration/report errors without changing legacy cases."""
    errors: list[str] = []
    handoff: dict[str, Any] | None = None
    handoff_path = case_dir / "simulation_handoff.yaml"
    if handoff_path.is_file():
        try:
            candidate = load_artifact(handoff_path)
            handoff = candidate if isinstance(candidate, dict) else None
        except ValueError as exc:
            errors.append(str(exc))
    tokens = _claim_tokens(case_dir, loaded, handoff)
    calibration_requested = bool(tokens & CALIBRATION_CLAIMS)
    physical_requested = bool(tokens & PHYSICAL_CLAIMS)
    # Physical validity is downstream of numerical verification.  It must
    # carry both sections even when the state vocabulary uses only the
    # physical alias.
    numerical_requested = bool(tokens & NUMERICAL_CLAIMS) or physical_requested
    version_one_marker = _has_version_one_marker(loaded)
    plan_path = case_dir / CALIBRATION_PLAN
    report = _find_validation_report(case_dir, errors)

    if numerical_requested:
        if report is None:
            errors.append("numerical verification claim requires validation_report.yaml")
        else:
            _validate_report_section(case_dir, report.get("numerical_verification"), "numerical_verification", errors)

    if not plan_path.is_file():
        if calibration_requested or physical_requested or version_one_marker:
            errors.append("advanced calibration/physical claim requires calibration_plan.yaml version 1")
        return errors
    try:
        plan = load_artifact(plan_path)
    except ValueError as exc:
        return errors + [str(exc)]
    if not isinstance(plan, dict):
        return errors + ["calibration_plan.yaml must contain an object"]
    version = plan.get("calibration_contract_version")
    if isinstance(version, bool) or version != CALIBRATION_VERSION:
        if calibration_requested or physical_requested or version_one_marker:
            errors.append("advanced calibration/physical claim requires calibration_contract_version=1")
        elif version != 0 or plan.get("status") not in {"planned", "not_enabled"}:
            errors.append("calibration_plan.yaml has unsupported contract version")
        return errors
    status = plan.get("status")
    if not isinstance(status, str) or status not in CALIBRATION_STATUSES:
        errors.append(f"calibration_plan.yaml has unsupported status: {status}")
        return errors
    # A v1 plan with a physically validated status is itself an advanced
    # claim, even if project_state/handoff has not yet been updated.
    if status == "physically_validated":
        physical_requested = True
        if not numerical_requested:
            numerical_requested = True
            if report is None:
                errors.append("physical validation claim requires validation_report.yaml")
            else:
                _validate_report_section(case_dir, report.get("numerical_verification"), "numerical_verification", errors)
    if status == "planned":
        if calibration_requested or physical_requested:
            errors.append("calibration_plan.yaml is still planned but an advanced claim was requested")
        return errors
    if status == "not_required":
        if not _text(plan.get("not_required_justification")):
            errors.append("calibration status not_required requires not_required_justification")
        definitions = _objects(plan.get("parameter_definitions"))
        if any(row.get("role") in {"calibrated", "fit", "free", "estimated"} for row in definitions):
            errors.append("calibration status not_required cannot include fitted parameter roles")
        if calibration_requested:
            errors.append("calibration claim is incompatible with status not_required")
        if not physical_requested:
            return errors
    if status == "failed":
        fit = plan.get("fit_result", {})
        validation = plan.get("independent_validation", {})
        fit_reason = fit.get("failure_reason") if isinstance(fit, dict) else None
        validation_reason = validation.get("failure_reason") if isinstance(validation, dict) else None
        if not _text(fit_reason) and not _text(validation_reason):
            errors.append("failed calibration plan must record a failure_reason")
        if calibration_requested or physical_requested:
            errors.append("failed calibration/validation result cannot support an advanced claim")
        return errors

    dataset = plan.get("dataset")
    objective = plan.get("objective")
    split = plan.get("split")
    if not isinstance(dataset, dict) or not isinstance(objective, dict) or not isinstance(split, dict):
        return errors + ["calibration plan lacks dataset, objective, or split objects"]
    records = _validate_dataset(dataset, errors)
    direction, threshold = _validate_objective(objective, errors)
    raw_definitions = _objects(plan.get("parameter_definitions"))
    has_fitted_parameters = any(row.get("role") in {"calibrated", "fit", "free", "estimated"} for row in raw_definitions)
    if status == "physically_validated" and not has_fitted_parameters and not _text(plan.get("not_required_justification")):
        errors.append("physical validation without fitted parameters requires not_required_justification")
    definitions = _validate_parameters(raw_definitions, errors) if (status in {"calibrated", "physically_validated"} and has_fitted_parameters) else {}
    _validate_split(split, records, errors, require_fit=has_fitted_parameters)
    fit_passed = not has_fitted_parameters
    if status == "calibrated" and not has_fitted_parameters:
        errors.append("calibration status calibrated requires at least one fitted parameter; use not_required for a fixed model")
        fit_passed = False
    if status in {"calibrated", "physically_validated"} and has_fitted_parameters:
        fit = plan.get("fit_result")
        if not isinstance(fit, dict):
            errors.append("calibration status requires fit_result")
        else:
            before = len(errors)
            selected_model_id = loaded.get("simulation_spec.yaml", {}).get("selected_model_id") if isinstance(loaded.get("simulation_spec.yaml"), dict) else None
            fit_passed = _validate_fit_result(case_dir, fit, definitions, objective, split, dataset, selected_model_id, errors)
            if len(errors) != before:
                fit_passed = False
        if not fit_passed and status == "calibrated":
            errors.append("calibration status calibrated has no independently verified frozen fit")

    if physical_requested or status == "physically_validated":
        if status != "physically_validated" and not (status == "not_required" and not has_fitted_parameters):
            errors.append("physical validation claim requires calibration_plan.yaml status=physically_validated")
        validation = plan.get("independent_validation")
        if not isinstance(validation, dict):
            errors.append("physical validation claim requires independent_validation")
        else:
            _validate_independent_validation(case_dir, validation, plan, records, True, has_fitted_parameters=has_fitted_parameters, errors=errors)
        if report is None:
            errors.append("physical validation claim requires validation_report.yaml")
        else:
            if report.get("status") != "passed":
                errors.append("physical validation claim requires validation_report.status=passed")
            if report.get("accepted_for_scientific_use") is not True:
                errors.append("physical validation claim requires accepted_for_scientific_use=true")
            validation = plan.get("independent_validation", {})
            objective_threshold = objective.get("acceptance_threshold", {}).get("value") if isinstance(objective.get("acceptance_threshold"), dict) else None
            minimum_report_timestamp = _timestamp(validation.get("performed_at")) if isinstance(validation, dict) else None
            if has_fitted_parameters and isinstance(plan.get("fit_result"), dict):
                frozen_at = _timestamp(plan["fit_result"].get("frozen_at"))
                if frozen_at is not None and (minimum_report_timestamp is None or frozen_at > minimum_report_timestamp):
                    minimum_report_timestamp = frozen_at
            _validate_report_section(
                case_dir,
                report.get("physical_validation"),
                "physical_validation",
                errors,
                require_independent=True,
                expected_dataset_id=validation.get("dataset_id") if isinstance(validation, dict) else None,
                expected_data_hash=validation.get("data_hash") if isinstance(validation, dict) else None,
                expected_observation_ids=validation.get("observation_ids") if isinstance(validation, dict) else None,
                expected_value=validation.get("objective_value") if isinstance(validation, dict) and _finite(validation.get("objective_value")) else None,
                expected_threshold=objective_threshold if _finite(objective_threshold) else None,
                expected_fit_artifact_hash=(plan.get("fit_result", {}).get("fit_artifact_hash") if has_fitted_parameters and isinstance(plan.get("fit_result"), dict) else None),
                direction=direction,
                minimum_timestamp=minimum_report_timestamp,
            )
    elif calibration_requested and not fit_passed:
        errors.append("calibration claim cannot be supported by a failed or incomplete fit")
    return errors
