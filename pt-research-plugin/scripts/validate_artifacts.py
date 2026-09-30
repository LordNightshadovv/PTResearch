#!/usr/bin/env python3
"""Validate a PT research case's schemas and cross-artifact scientific contracts."""

from __future__ import annotations

import argparse
from pathlib import Path

from artifact_lib import basic_schema_errors, load_artifact, load_schema
from calibration_contract import validate_calibration_contract
from runnable_contract import package_status
from scientific_contract import validate_v2, validate_v3


ARTIFACT_SCHEMAS = {
    "project_state.yaml": "project-state",
    "problem_contract.yaml": "problem-contract",
    "search_log.yaml": "search-log",
    "source_registry.yaml": "source-registry",
    "essence_and_chain.yaml": "essence-chain",
    "model_registry.yaml": "model-registry",
    "simulation_route.yaml": "simulation-route",
    "simulation_spec.yaml": "simulation-spec",
    "dependency_report.yaml": "dependency-report",
}


def validate(case_dir: Path, require_complete: bool = True) -> list[str]:
    errors: list[str] = []
    plugin_root = Path(__file__).resolve().parents[1]
    loaded: dict[str, object] = {}
    for filename, schema_name in ARTIFACT_SCHEMAS.items():
        path = case_dir / filename
        if not path.exists():
            if require_complete:
                errors.append(f"missing required artifact: {filename}")
            continue
        try:
            value = load_artifact(path)
            loaded[filename] = value
            if require_complete:
                errors.extend(f"{filename}: {e}" for e in basic_schema_errors(value, load_schema(plugin_root, schema_name)))
        except ValueError as exc:
            errors.append(str(exc))

    # Calibration is an explicit versioned contract.  A missing plan keeps a
    # legacy case at its previous claim ceiling, but a plan that is present is
    # always schema-checked, including in partial inspection mode.
    calibration_path = case_dir / "calibration_plan.yaml"
    if calibration_path.exists():
        try:
            calibration = load_artifact(calibration_path)
            loaded["calibration_plan.yaml"] = calibration
            errors.extend(
                f"calibration_plan.yaml: {e}"
                for e in basic_schema_errors(calibration, load_schema(plugin_root, "calibration-plan"))
            )
        except ValueError as exc:
            errors.append(str(exc))

    # A runtime manifest is mandatory for an exported Linux package, but not for
    # theory-only or pre-environment research cases.
    runtime_path = case_dir / "runtime.yaml"
    if runtime_path.exists():
        try:
            runtime = load_artifact(runtime_path)
            errors.extend(f"runtime.yaml: {e}" for e in basic_schema_errors(runtime, load_schema(plugin_root, "runtime")))
        except ValueError as exc:
            errors.append(str(exc))

    contract = loaded.get("problem_contract.yaml", {})
    state = loaded.get("project_state.yaml", {})
    chain = loaded.get("essence_and_chain.yaml", {})
    registry = loaded.get("model_registry.yaml", {})
    route = loaded.get("simulation_route.yaml", {})
    spec = loaded.get("simulation_spec.yaml", {})
    if not all(isinstance(x, dict) for x in (contract, state, chain, registry, route, spec)):
        return errors + ["core artifacts must be objects"]

    errors.extend(validate_calibration_contract(case_dir, loaded))

    exact = contract.get("exact_prompt")
    if not isinstance(exact, str) or not exact.strip():
        errors.append("problem_contract.yaml: exact prompt text is not retained")
    if state.get("exact_prompt") != exact:
        errors.append("project_state.yaml: exact_prompt differs from problem contract")
    if not require_complete:
        return errors

    models = registry.get("candidates", [])
    by_id = {m.get("id"): m for m in models if isinstance(m, dict) and m.get("id")}
    selected = registry.get("selected_candidate_ids", [])
    for model_id in selected:
        if model_id not in by_id:
            errors.append(f"selected candidate is absent from registry: {model_id}")
    for model in models:
        if not isinstance(model, dict):
            continue
        if model.get("status") in {"rejected", "filtered", "component_only"} and not model.get("decision_reason"):
            errors.append(f"rejected/filtered candidate lacks reason: {model.get('id', '<unknown>')}")
        for variable in model.get("variables", []):
            if isinstance(variable, dict) and not variable.get("unit"):
                errors.append(f"model {model.get('id')}: variable {variable.get('symbol')} lacks unit")

    for link in chain.get("causal_chain", []):
        if isinstance(link, dict) and not link.get("model_id") and not link.get("unresolved"):
            errors.append(f"causal-chain link {link.get('id', '<unknown>')} has neither model nor unresolved flag")

    route_model = route.get("selected_model_id")
    escalation = route.get("second_solver_escalation")
    if not isinstance(escalation, dict) or not isinstance(escalation.get("status"), str) or not isinstance(escalation.get("condition"), str):
        errors.append("simulation route lacks a usable second-solver escalation record")
    elif escalation.get("status") != "not_required":
        required_escalation_fields = {"failed_prediction", "interface_variables", "coupling_type", "validation_plan"}
        missing = sorted(field for field in required_escalation_fields if not escalation.get(field))
        if missing:
            errors.append(f"second-solver escalation record is incomplete: {missing}")
    if selected and route_model not in selected:
        errors.append("simulation route does not refer to a selected model")
    if spec.get("selected_model_id") and spec.get("selected_model_id") != route_model:
        errors.append("simulation spec and route reference different models")
    selected_assumptions = set(by_id.get(route_model, {}).get("assumptions", []))
    generated_assumptions = set(spec.get("assumptions", []))
    prohibited = set(by_id.get(route_model, {}).get("prohibited_assumptions", []))
    conflict = generated_assumptions & prohibited
    if conflict:
        errors.append(f"generated assumptions contradict selected model: {sorted(conflict)}")

    openfoam_manifest = case_dir / "openfoam" / "case_manifest.yaml"
    if openfoam_manifest.exists():
        manifest = load_artifact(openfoam_manifest)
        errors.extend(f"case_manifest.yaml: {e}" for e in basic_schema_errors(manifest, load_schema(plugin_root, "case-manifest")))
        if isinstance(manifest, dict):
            if manifest.get("selected_model_id") != route_model:
                errors.append("generated case references a different physical model")
            case_assumptions = set(manifest.get("assumptions", []))
            if case_assumptions & prohibited:
                errors.append("generated case assumptions contradict selected model")
            if manifest.get("parameter_sweep_started") and not manifest.get("baseline_accepted"):
                errors.append("parameter sweep precedes baseline acceptance")

    deps = loaded.get("dependency_report.yaml", {})
    unavailable = set()
    if isinstance(deps, dict):
        unavailable = {d.get("name") for d in deps.get("dependencies", []) if isinstance(d, dict) and not d.get("available")}
    claims = state.get("claims", [])
    for claim in claims:
        if isinstance(claim, dict) and claim.get("requires_dependency") in unavailable and claim.get("status") == "completed":
            errors.append(f"stage claims unavailable output: {claim.get('stage')}")

    contract_version = max(
        int(contract.get("contract_version", 1) or 1),
        int(state.get("contract_version", 1) or 1),
    )
    if contract_version >= 3:
        errors.extend(validate_v3(case_dir, loaded, plugin_root))
    elif contract_version >= 2:
        errors.extend(validate_v2(case_dir, loaded, plugin_root))

    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("case_dir", type=Path)
    parser.add_argument("--allow-partial", action="store_true")
    args = parser.parse_args()
    errors = validate(args.case_dir.resolve(), not args.allow_partial)
    if errors:
        print("FAIL: artifact validation")
        for error in errors:
            print(f"- {error}")
        return 1
    if args.allow_partial:
        package = args.case_dir.resolve() / "linux-simulation"
        route_path = args.case_dir.resolve() / "simulation_route.yaml"
        if package.is_dir() and route_path.is_file():
            try:
                route = load_artifact(route_path)
            except ValueError:
                route = {}
            if isinstance(route, dict) and route.get("primary_solver") not in {None, "", "No numerical solver"}:
                status = package_status(package)
                if status in {"runnable_synthetic", "runnable_apparatus", "executed_unverified", "numerically_verified", "experimentally_compared"}:
                    print(f"PASS: partial artifact inspection: {args.case_dir.resolve()} (package_status={status})")
                else:
                    print(f"PASS: handoff-only artifact inspection: {args.case_dir.resolve()} (implementation and receipts are unverified)")
                return 0
        print(f"PASS: partial artifact inspection: {args.case_dir.resolve()} (not a runnable package)")
        return 0
    print(f"PASS: artifact contracts and runnable-simulation contract: {args.case_dir.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
