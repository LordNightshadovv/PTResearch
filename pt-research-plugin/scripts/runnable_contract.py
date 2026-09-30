#!/usr/bin/env python3
"""Validation helpers for the PT runnable-simulation contract.

The scientific contract answers whether a model is ready to implement.  This
module answers the separate software question: whether the case contains a
real implementation, a deterministic synthetic benchmark, machine-readable
outputs, and receipts that support the claimed readiness state.

Artifacts use the repository's JSON-compatible YAML subset so the checks stay
usable on a clean Python installation and on a Linux package recipient's
computer.
"""

from __future__ import annotations

import hashlib
import json
import platform
import re
from pathlib import Path
from typing import Any

from artifact_lib import load_artifact, load_schema, basic_schema_errors


SCIENTIFIC_READINESS_STATES = (
    "scientific_stop",
    "model_selected_not_closed",
    "model_closed",
)

# ``handoff_only`` is deliberately explicit.  It is not a runnable state and
# cannot satisfy a runnable claim.  ``implementation_ready`` means that the
# executable implementation exists but its synthetic smoke test has not yet
# produced a receipt.
SOFTWARE_READINESS_STATES = (
    "not_applicable",
    "handoff_only",
    "implementation_ready",
    "runnable_synthetic",
    "runnable_apparatus",
    "executed_unverified",
    "numerically_verified",
    "experimentally_compared",
)

SOFTWARE_STATE_RANK = {name: index for index, name in enumerate(SOFTWARE_READINESS_STATES)}
RUNNABLE_STATES = {
    "runnable_synthetic",
    "runnable_apparatus",
    "executed_unverified",
    "numerically_verified",
    "experimentally_compared",
}

LEGACY_STATE_TO_SOFTWARE = {
    "solver_selected_only": "handoff_only",
    "installation_package_prepared": "handoff_only",
    "parameter_handoff_validated": "handoff_only",
    "solver_case_generator_prepared": "implementation_ready",
    "solver_native_case_generated": "implementation_ready",
    "smoke_tested": "runnable_synthetic",
    "executed": "executed_unverified",
    "numerically_verified": "numerically_verified",
    "experimentally_validated": "experimentally_compared",
}

PLACEHOLDER_RE = re.compile(
    r"(?:apparatus[- ]specific|measured range|to be determined|solver field to be determined|"
    r"complete (?:an? )?.*case generator|pending(?: route| theory)?|\btbd\b|"
    r"fill in|resolve later|not yet specified|unknown destination)",
    re.IGNORECASE,
)

OUTPUT_FIELD_RE = re.compile(
    r"(?:point.?spread.?function|retinal.?irradiance|pressure.?field|modal.?displacement|"
    r"impact.?time|nondimensional|trajectory|output.?field|result|prediction|solver.?field|"
    r"derived.?state|state.?variable)",
    re.IGNORECASE,
)

REQUIRED_PACKAGE_FILES = (
    "README.md",
    "check_system.sh",
    "run_gate.sh",
    "parameters.schema.json",
    "examples/synthetic.json",
    "generate_case.py",
    "run.sh",
    "extract_results.py",
    "numerical-verification.json",
    "numerical-verification.md",
    "parameter-map.json",
    "equation-lineage.json",
)


def _json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"cannot load {path}: {exc}") from exc


def _objects(value: Any) -> list[dict[str, Any]]:
    return [item for item in value if isinstance(item, dict)] if isinstance(value, list) else []


def _nonempty(value: Any) -> bool:
    return value not in (None, "", [], {})


def _relative_files(package_dir: Path) -> set[str]:
    return {
        path.relative_to(package_dir).as_posix()
        for path in package_dir.rglob("*")
        if path.is_file()
    }


def _find_manifest(package_dir: Path) -> Path | None:
    for name in ("simulation_package_manifest.json", "simulation_package_manifest.yaml", "manifest.json"):
        path = package_dir / name
        if path.is_file():
            return path
    return None


def _load_manifest(package_dir: Path) -> dict[str, Any] | None:
    path = _find_manifest(package_dir)
    if path is None:
        return None
    value = _json(path)
    return value if isinstance(value, dict) else None


def package_dir_for(case_or_package: Path) -> Path:
    """Return a case's package directory or the path when already packaged."""
    candidate = case_or_package / "linux-simulation"
    return candidate if candidate.is_dir() else case_or_package


def _is_echo_only(path: Path) -> bool:
    """Detect shell stubs that only print a message and exit."""
    text = path.read_text(encoding="utf-8", errors="replace")
    commands: list[str] = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or line.startswith("#!"):
            continue
        line = line.split("#", 1)[0].strip()
        if not line:
            continue
        commands.append(line)
    meaningful = re.compile(
        r"(?:command\s+-v|python|python3|test\s|\[\s|if\s|case\s|for\s|while\s|"
        r"mkdir\s|touch\s|uname\s|source\s|\.\s|chmod\s|exec\s|tee\s|"
        r"readlink\s|find\s|hash\s)",
        re.IGNORECASE,
    )
    return not any(meaningful.search(line) for line in commands)


def _unconditional_block(path: Path) -> bool:
    text = path.read_text(encoding="utf-8", errors="replace")
    if not re.search(r"\b(?:if|case|python|python3|test|\[)\b", text):
        return bool(re.search(r"(^|\n)\s*exit\s+[1-9]\d*\s*(?:$|\n)", text))
    return False


def _has_implementation(package_dir: Path, manifest: dict[str, Any] | None) -> bool:
    implementation = package_dir / "src"
    source_files = [
        path for path in implementation.rglob("*")
        if path.is_file() and path.suffix.lower() in {".py", ".cpp", ".cc", ".c", ".cxx", ".f90", ".f", ".cuh", ".h"}
    ] if implementation.is_dir() else []
    native_files = [
        path for path in package_dir.rglob("*")
        if path.is_file() and path.suffix.lower() in {".sif", ".dict", ".foam", ".geo", ".msh", ".cpp", ".cc", ".cxx"}
    ]
    declared = manifest.get("implementation", {}) if isinstance(manifest, dict) else {}
    if isinstance(declared, dict) and declared.get("source_files"):
        return bool(source_files or native_files)
    return bool(source_files or native_files)


def _has_nontrivial_script(path: Path) -> bool:
    if not path.is_file():
        return False
    text = path.read_text(encoding="utf-8", errors="replace")
    stripped = [line.strip() for line in text.splitlines() if line.strip() and not line.strip().startswith("#")]
    if len(stripped) < 3:
        return False
    return not _is_echo_only(path) and not _unconditional_block(path)


def _validate_route_assets(package_dir: Path, manifest: dict[str, Any], errors: list[str]) -> None:
    route = manifest.get("route")
    if route == "openfoam_continuum":
        required = (
            "native/0", "native/constant", "native/system", "native/Allrun", "native/Allclean",
            "native/system/controlDict", "native/system/blockMeshDict", "native/system/fvSchemes",
            "native/system/fvSolution", "native/system/setFieldsDict",
        )
        for relative in required:
            if not (package_dir / relative).exists():
                errors.append(f"OpenFOAM package lacks required native asset: {relative}")
        if (package_dir / "native" / "Allrun").is_file() and not re.search(r"blockMesh|checkMesh|interFoam", (package_dir / "native" / "Allrun").read_text(encoding="utf-8", errors="replace")):
            errors.append("OpenFOAM Allrun lacks mesh, checkMesh, or solver execution commands")
    elif route == "elmer_fem":
        if not list((package_dir / "native").glob("*.sif")):
            errors.append("Elmer FEM package lacks a solver-native .sif file")
        if not (package_dir / "native" / "mesh_generator.py").is_file() or not list((package_dir / "native").glob("*.geo")):
            errors.append("Elmer FEM package lacks a geometry and mesh-generation path")
    elif route == "project_chrono":
        native = list((package_dir / "native").glob("*.py"))
        if not native:
            errors.append("Project Chrono package lacks a native Python/C++ entry point")
        elif "DoStepDynamics" not in "\n".join(path.read_text(encoding="utf-8", errors="replace") for path in native):
            errors.append("Project Chrono package lacks a deterministic integrator/output loop")
    elif route == "yade":
        native = list((package_dir / "native").glob("*.py"))
        if not native:
            errors.append("YADE package lacks a native Python entry point")
        elif "O.engines" not in "\n".join(path.read_text(encoding="utf-8", errors="replace") for path in native):
            errors.append("YADE package lacks contact engine configuration")
    elif route == "fourier_optics":
        native = list((package_dir / "native").glob("*.py"))
        if not native:
            errors.append("HCIPy optics package lacks an importable native optics configuration")
        elif not re.search(r"make_pupil_grid|wavelength", "\n".join(path.read_text(encoding="utf-8", errors="replace") for path in native), re.IGNORECASE):
            errors.append("HCIPy optics package lacks configurable grid and wavelength inputs")


def _import_justified(value: Any) -> bool:
    if isinstance(value, dict):
        if value.get("imported_measured_field") is True and _nonempty(value.get("source")):
            return True
        return bool(value) and all(_import_justified(item) for item in value.values())
    if isinstance(value, list):
        return bool(value) and all(_import_justified(item) for item in value)
    return False


def _walk_keys(value: Any) -> list[str]:
    keys: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            keys.append(str(key))
            keys.extend(_walk_keys(child))
    elif isinstance(value, list):
        for child in value:
            keys.extend(_walk_keys(child))
    return keys


def _validate_input_template(package_dir: Path, errors: list[str]) -> None:
    schema_path = package_dir / "parameters.schema.json"
    example_path = package_dir / "examples" / "synthetic.json"
    if not schema_path.is_file() or not example_path.is_file():
        return
    try:
        schema = _json(schema_path)
        example = _json(example_path)
    except ValueError as exc:
        errors.append(str(exc))
        return
    required = {
        "controls", "material_properties", "geometry", "initial_conditions",
        "boundary_conditions", "calibration_parameters", "derived_quantities",
        "state_variables", "observables", "uncertainties",
    }
    if not isinstance(schema, dict):
        errors.append("parameters.schema.json must be an object")
    elif set(schema.get("required", [])) != required:
        errors.append("parameters.schema.json must require the ten separated input categories")
    if not isinstance(example, dict):
        errors.append("examples/synthetic.json must be an object")
        return
    missing = sorted(required - set(example))
    if missing:
        errors.append(f"synthetic input is missing separated categories: {missing}")
    for category in required:
        value = example.get(category)
        if not isinstance(value, (dict, list)):
            errors.append(f"synthetic input category is not an object/list: {category}")
    for category in ("derived_quantities", "state_variables", "observables"):
        value = example.get(category)
        if _nonempty(value) and not _import_justified(value):
            errors.append(f"required input template contains output-like category {category}; compute it in the implementation")
    output_categories = {"derived_quantities", "state_variables", "observables"}
    for category, value in example.items():
        if category in output_categories and _import_justified(value):
            continue
        for key in _walk_keys(value):
            if OUTPUT_FIELD_RE.search(key):
                errors.append(f"required input template contains obvious output/derived field: {key}")


def _validate_mapping_records(records: Any, errors: list[str], label: str, require_implementation: bool = False) -> None:
    rows = _objects(records)
    if not rows:
        errors.append(f"{label} has no concrete parameter mappings")
        return
    for index, row in enumerate(rows, start=1):
        parameter = row.get("parameter") or row.get("experimental_parameter")
        destination = row.get("destination") or row.get("solver_input")
        if not _nonempty(parameter):
            errors.append(f"{label} mapping {index} lacks a parameter")
        if not _nonempty(destination) or PLACEHOLDER_RE.search(str(destination)):
            errors.append(f"{label} mapping {index} has a placeholder destination")
        if not _nonempty(row.get("destination_kind")):
            errors.append(f"{label} mapping {index} lacks destination_kind")
        if require_implementation:
            if not _nonempty(row.get("implemented_file")):
                errors.append(f"{label} mapping {index} lacks implemented_file")
            if not _nonempty(row.get("implemented_symbol") or row.get("line_or_function")):
                errors.append(f"{label} mapping {index} lacks implemented symbol/function")
            for field in ("equation_id", "units", "notation_conversion", "discretization_or_approximation", "implementation_assumptions"):
                if not _nonempty(row.get(field)):
                    errors.append(f"{label} mapping {index} lacks {field}")


def _validate_equation_trace(package_dir: Path, errors: list[str]) -> None:
    path = package_dir / "equation-lineage.json"
    if not path.is_file():
        errors.append("simulation package lacks equation-lineage.json implementation traceability")
        return
    try:
        root = _json(path)
    except ValueError as exc:
        errors.append(str(exc))
        return
    rows = _objects(root.get("equations") if isinstance(root, dict) else root)
    if not rows:
        errors.append("equation-lineage.json contains no implemented equations")
    required = (
        "equation_id", "source_locator", "implemented_file", "implemented_symbol",
        "notation_conversion", "units", "discretization_or_approximation", "implementation_assumptions",
    )
    for index, row in enumerate(rows, start=1):
        for field in required:
            if not _nonempty(row.get(field)) or PLACEHOLDER_RE.search(str(row.get(field, ""))):
                errors.append(f"equation-lineage record {index} lacks concrete {field}")


def _validate_verification(package_dir: Path, errors: list[str]) -> dict[str, Any] | None:
    path = package_dir / "numerical-verification.json"
    if not path.is_file():
        errors.append("simulation package lacks machine-readable numerical-verification.json")
        return None
    try:
        value = _json(path)
    except ValueError as exc:
        errors.append(str(exc))
        return None
    if not isinstance(value, dict):
        errors.append("numerical-verification.json must be an object")
        return None
    for field in ("refinement_variable", "levels", "observable", "metric", "tolerance", "expected_limiting_behavior", "failure_interpretation", "executed", "status"):
        if field not in value:
            errors.append(f"numerical verification lacks {field}")
    levels = value.get("levels")
    if not isinstance(levels, list) or len(levels) != 3 or any(not isinstance(item, (int, float)) or isinstance(item, bool) for item in levels):
        errors.append("numerical verification must declare exactly three concrete refinement levels")
    if value.get("status") not in {"unexecuted", "failed", "passed"}:
        errors.append("numerical verification has invalid status")
    if value.get("status") == "passed" and value.get("executed") is not True:
        errors.append("numerical verification cannot be passed without execution")
    return value


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    if path.is_file():
        digest.update(path.read_bytes())
    elif path.is_dir():
        for child in sorted(item for item in path.rglob("*") if item.is_file()):
            digest.update(child.relative_to(path).as_posix().encode("utf-8"))
            digest.update(child.read_bytes())
    return digest.hexdigest()


def _receipt_errors(path: Path) -> list[str]:
    try:
        receipt = _json(path)
    except ValueError as exc:
        return [str(exc)]
    if not isinstance(receipt, dict):
        return [f"receipt is not an object: {path.name}"]
    required = {
        "timestamp", "operating_system", "architecture", "package_version", "solver_version", "package_revision", "exact_command",
        "input_file_hash", "generated_case_hash", "exit_status", "runtime_seconds",
        "output_hashes", "warnings", "errors", "validation_state",
    }
    errors = [f"receipt {path.name} lacks {field}" for field in sorted(required - set(receipt))]
    if receipt.get("exit_status") != 0:
        errors.append(f"receipt {path.name} does not record exit_status 0")
    if not isinstance(receipt.get("output_hashes"), (dict, list)):
        errors.append(f"receipt {path.name} output_hashes must be machine-readable")
    return errors


def _validate_receipts(package_dir: Path, software_state: str, errors: list[str]) -> None:
    receipts = package_dir / "receipts"
    if not receipts.is_dir():
        errors.append("simulation package lacks receipts/")
        return
    receipt_files = sorted(receipts.glob("*.json"))
    if software_state in RUNNABLE_STATES and not receipt_files:
        errors.append(f"software readiness {software_state} lacks an execution receipt")
    for path in receipt_files:
        errors.extend(_receipt_errors(path))
    if software_state in RUNNABLE_STATES:
        synthetic = receipts / "synthetic-smoke.json"
        if not synthetic.is_file():
            errors.append("runnable package lacks receipts/synthetic-smoke.json")
        elif synthetic.is_file():
            try:
                value = _json(synthetic)
                if value.get("validation_state") not in {"runnable_synthetic", "runnable_apparatus", "executed_unverified", "numerically_verified", "experimentally_compared"}:
                    errors.append("synthetic smoke receipt has no runnable validation state")
            except ValueError:
                pass
        if software_state == "runnable_apparatus" and not (receipts / "apparatus-run.json").is_file():
            errors.append("runnable_apparatus lacks receipts/apparatus-run.json")


def _manifest_state(manifest: dict[str, Any]) -> tuple[str | None, bool]:
    state = manifest.get("software_readiness")
    if isinstance(state, str) and state in SOFTWARE_READINESS_STATES:
        return state, False
    legacy = manifest.get("highest_state")
    if isinstance(legacy, str) and legacy in LEGACY_STATE_TO_SOFTWARE:
        return LEGACY_STATE_TO_SOFTWARE[legacy], True
    return None, False


def validate_package(package_dir: Path, *, strict: bool = True) -> list[str]:
    """Validate a standalone package directory.

    ``strict=False`` is intentionally handoff-only tolerant: it suppresses
    implementation-absence errors so old pre-run handoffs can be inspected,
    but it never upgrades them to a runnable state.
    """
    errors: list[str] = []
    if not package_dir.is_dir():
        return ["simulation package directory is missing"] if strict else []
    manifest = _load_manifest(package_dir)
    files = _relative_files(package_dir)
    if manifest is None:
        if strict:
            errors.append("simulation package lacks simulation_package_manifest.json")
        return errors
    manifest_errors = basic_schema_errors(manifest, load_schema(Path(__file__).resolve().parents[1], "simulation-package"))
    errors.extend(f"simulation package manifest: {error}" for error in manifest_errors)
    state, legacy_state = _manifest_state(manifest)
    has_implementation = _has_implementation(package_dir, manifest)
    if legacy_state:
        errors.append("simulation package uses legacy highest_state; migrate to scientific_readiness/software_readiness")
    if state is None:
        errors.append("simulation package lacks a valid software_readiness state")
    if not has_implementation:
        if strict:
            errors.append("continuing simulation package has no executable source, solver-native case, or case generator")
        return errors
    for required in REQUIRED_PACKAGE_FILES:
        if required not in files:
            errors.append(f"simulation package missing required file: {required}")
    if "install.sh" not in files and "environment.yml" not in files:
        errors.append("simulation package lacks install.sh or environment.yml")
    if not any(path.startswith("tests/") for path in files):
        errors.append("simulation package lacks tests/")
    source_files = [path for path in (package_dir / "src").rglob("*") if path.is_file()] if (package_dir / "src").is_dir() else []
    if not source_files and not any(path.suffix.lower() in {".sif", ".dict", ".foam", ".geo", ".msh"} for path in package_dir.rglob("*")):
        errors.append("simulation package implementation directory is empty")
    _validate_route_assets(package_dir, manifest, errors)
    check_system = package_dir / "check_system.sh"
    if check_system.is_file() and _is_echo_only(check_system):
        errors.append("check_system.sh is echo-only and performs no dependency or platform checks")
    gate = package_dir / "run_gate.sh"
    if gate.is_file() and _unconditional_block(gate):
        errors.append("run_gate.sh unconditionally blocks instead of checking readiness evidence")
    elif gate.is_file() and not re.search(r"synthetic|apparatus|implementation|receipt|python", gate.read_text(encoding="utf-8", errors="replace"), re.IGNORECASE):
        errors.append("run_gate.sh is not state-aware")
    for name in ("generate_case.py", "run.sh", "extract_results.py"):
        path = package_dir / name
        if path.is_file() and not _has_nontrivial_script(path):
            errors.append(f"{name} is a stub rather than an executable implementation entrypoint")
    _validate_input_template(package_dir, errors)
    _validate_mapping_records(manifest.get("parameter_mapping"), errors, "simulation package", require_implementation=True)
    parameter_map_path = package_dir / "parameter-map.json"
    if parameter_map_path.is_file():
        try:
            parameter_map = _json(parameter_map_path)
            _validate_mapping_records(
                parameter_map.get("mappings") if isinstance(parameter_map, dict) else parameter_map,
                errors,
                "parameter-map.json",
                require_implementation=True,
            )
        except ValueError as exc:
            errors.append(str(exc))
    _validate_equation_trace(package_dir, errors)
    verification = _validate_verification(package_dir, errors)
    if state in RUNNABLE_STATES:
        _validate_receipts(package_dir, state, errors)
        if manifest.get("runnable_claim") is not True:
            errors.append(f"software readiness {state} must set runnable_claim: true")
    elif manifest.get("runnable_claim") is True:
        errors.append("runnable_claim cannot be true before runnable_synthetic")
    if state == "numerically_verified" and (not verification or verification.get("status") != "passed"):
        errors.append("numerically_verified requires passed machine-readable numerical verification")
    if state == "experimentally_compared" and not (package_dir / "experimental-comparison.json").is_file():
        errors.append("experimentally_compared requires experimental-comparison.json")
    return errors


def package_status(package_dir: Path) -> str:
    """Return a truthful package classification for user-facing validators."""
    if not package_dir.is_dir():
        return "handoff-only"
    manifest = _load_manifest(package_dir)
    if not manifest or not _has_implementation(package_dir, manifest):
        return "handoff-only"
    state, _ = _manifest_state(manifest)
    if state in RUNNABLE_STATES and manifest.get("runnable_claim") is True:
        return state
    return state or "implementation-ready"


def validate_case_package(case_dir: Path, core: dict[str, Any], *, strict: bool = True) -> list[str]:
    """Apply package gates to a v2/v3 continuing case."""
    route = core.get("simulation_route.yaml", {}) if isinstance(core, dict) else {}
    handoff = core.get("simulation_handoff.yaml", {}) if isinstance(core, dict) else {}
    if not isinstance(route, dict) or route.get("primary_solver") in {None, "", "No numerical solver"}:
        return []
    decision = core.get("model_registry.yaml", {}) if isinstance(core, dict) else {}
    decision_record = decision.get("stopping_decision", {}) if isinstance(decision, dict) else {}
    if isinstance(decision_record, dict) and decision_record.get("status") != "continue":
        return []
    errors: list[str] = []
    if not isinstance(handoff, dict):
        return ["simulation handoff is not an object"]
    if handoff.get("simulation_contract_version") != 1:
        errors.append("continuing simulation handoff lacks simulation_contract_version: 1")
    scientific_state = handoff.get("scientific_readiness")
    software_state = handoff.get("software_readiness")
    if scientific_state not in SCIENTIFIC_READINESS_STATES:
        errors.append("simulation handoff lacks scientific_readiness: scientific_stop/model_selected_not_closed/model_closed")
    if software_state not in SOFTWARE_READINESS_STATES:
        legacy = handoff.get("highest_state")
        if legacy in LEGACY_STATE_TO_SOFTWARE:
            errors.append("simulation handoff uses legacy highest_state without software_readiness; classify it as handoff_only and migrate")
        else:
            errors.append("simulation handoff lacks software_readiness")
    state_doc = core.get("project_state.yaml", {}) if isinstance(core, dict) else {}
    if isinstance(state_doc, dict):
        if state_doc.get("simulation_contract_version") != 1:
            errors.append("continuing project state lacks simulation_contract_version: 1")
        for field in ("scientific_readiness", "software_readiness"):
            if state_doc.get(field) and handoff.get(field) and state_doc.get(field) != handoff.get(field):
                errors.append(f"project state and simulation handoff disagree on {field}")
        if state_doc.get("software_readiness") in RUNNABLE_STATES and not handoff.get("software_readiness") in RUNNABLE_STATES:
            errors.append("project state claims a runnable software state above the handoff state")
    provisional_route = (
        scientific_state == "model_selected_not_closed"
        and software_state == "runnable_synthetic"
        and handoff.get("implementation_status") == "runnable_provisional"
    )
    if scientific_state != "model_closed" and not provisional_route:
        errors.append(
            "continuing numerical route requires scientific_readiness: model_closed, "
            "or an explicitly labelled runnable_provisional synthetic implementation"
        )
    if software_state == "handoff_only" and strict:
        errors.append("continuing case is handoff-only; executable implementation is required before package completion")
    package_dir = case_dir / "linux-simulation"
    package_errors = validate_package(package_dir, strict=strict)
    if not strict and package_status(package_dir) == "handoff-only":
        package_errors = [error for error in package_errors if "no executable" not in error and "missing required file" not in error and "manifest" not in error]
    errors.extend(package_errors)
    manifest = _load_manifest(package_dir)
    if manifest:
        if manifest.get("primary_solver") not in {route.get("primary_solver"), "", None}:
            errors.append("simulation package primary solver differs from simulation route")
        if manifest.get("model_id") and route.get("selected_model_id") and manifest.get("model_id") != route.get("selected_model_id"):
            errors.append("simulation package model_id differs from simulation route")
        if software_state in SOFTWARE_READINESS_STATES and manifest.get("software_readiness") in SOFTWARE_READINESS_STATES and software_state != manifest.get("software_readiness"):
            errors.append("simulation handoff and package manifest disagree on software_readiness")
        if handoff.get("implementation_status") == "runnable_provisional":
            if manifest.get("implementation_status") != "runnable_provisional":
                errors.append("provisional simulation handoff and package manifest disagree on implementation_status")
            if manifest.get("provisional_model") is not True:
                errors.append("runnable_provisional package must set provisional_model: true")
    _validate_mapping_records(handoff.get("parameter_mapping"), errors, "simulation handoff", require_implementation=False)
    return errors


def receipt_template(*, validation_state: str, command: list[str], input_path: Path | None = None, generated_case: Path | None = None, output_dir: Path | None = None, exit_status: int = 0, runtime_seconds: float = 0.0, warnings: list[str] | None = None, errors: list[str] | None = None, package_version: str = "1", solver_version: str = "not_applicable", package_revision: str = "not_recorded") -> dict[str, Any]:
    """Create the portable receipt shape used by generated packages."""
    output_hashes: dict[str, str] = {}
    if output_dir and output_dir.exists():
        for path in sorted(item for item in output_dir.rglob("*") if item.is_file()):
            output_hashes[path.relative_to(output_dir).as_posix()] = _sha256(path)
    return {
        "timestamp": __import__("datetime").datetime.now(__import__("datetime").timezone.utc).replace(microsecond=0).isoformat(),
        "operating_system": platform.system(),
        "architecture": platform.machine(),
        "package_version": package_version,
        "solver_version": solver_version,
        "package_revision": package_revision,
        "exact_command": command,
        "input_file_hash": _sha256(input_path) if input_path else "not_applicable",
        "generated_case_hash": _sha256(generated_case) if generated_case else "not_applicable",
        "exit_status": exit_status,
        "runtime_seconds": runtime_seconds,
        "output_hashes": output_hashes,
        "warnings": warnings or [],
        "errors": errors or [],
        "validation_state": validation_state,
    }
