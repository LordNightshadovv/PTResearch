#!/usr/bin/env python3
"""Semantic gates for the PT research-software engineering-standards manifest.

``engineering_standards.yaml`` (JSON-compatible YAML, schema ``engineering-standards``)
declares how research code is engineered: stack decision with alternatives, test plan,
numerical verification, physical-correctness checks, uncertainty treatment, reproducibility
metadata, and interface choice.

SCOPE AND TRUTHFULNESS.  These gates prove that a declaration is complete, internally
consistent, and that the files it points to exist.  They do not run any test, do not measure
numerical accuracy, and do not establish scientific correctness.  ``evidence_status`` is
therefore three-valued: ``planned`` (not written), ``implemented`` (code exists, no claim
that it passes), and ``evidenced`` (a retained receipt file exists at ``evidence``).
"""

from __future__ import annotations

import math
import re
from pathlib import Path
from typing import Any

from artifact_lib import basic_schema_errors, load_artifact, load_schema
from runnable_contract import SOFTWARE_STATE_RANK


ENGINEERING_MANIFEST = "engineering_standards.yaml"
ENGINEERING_VERSION = 1
VALIDATION_SCOPE = "declaration_and_structure_only"

GUI_INTERFACES = {"desktop_gui", "web_ui", "tui_python", "tui_rust"}
ERROR_SOURCES = ("measurement", "calibration", "numerical", "sampling", "model_form")
REQUIRED_METADATA_FIELDS = (
    "timestamp_utc", "git_commit", "python_version", "dependency_versions",
    "config_hash", "seed", "platform", "input_hashes",
)
REQUIRED_TOOLING = ("linter", "formatter", "type_checker", "test_runner", "ci_config_path")
PLACEHOLDERS = {"", "pending", "tbd", "todo", "to be determined", "n/a", "none", "unknown", "not_started"}

SEMVER_RE = re.compile(
    r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)"
    r"(?:-[0-9A-Za-z.-]+)?(?:\+[0-9A-Za-z.-]+)?$"
)

# Software-readiness thresholds that make the manifest mandatory under contract version 1.
_IMPLEMENTATION_RANK = SOFTWARE_STATE_RANK["implementation_ready"]
_EXECUTED_RANK = SOFTWARE_STATE_RANK["executed_unverified"]
_NUMERICAL_RANK = SOFTWARE_STATE_RANK["numerically_verified"]
_COMPARED_RANK = SOFTWARE_STATE_RANK["experimentally_compared"]


def is_valid_semver(value: Any) -> bool:
    return isinstance(value, str) and bool(SEMVER_RE.fullmatch(value))


def _text(value: Any, minimum: int = 1) -> bool:
    return isinstance(value, str) and len(value.strip()) >= minimum and value.strip().lower() not in PLACEHOLDERS


def _objects(value: Any) -> list[dict[str, Any]]:
    return [item for item in value if isinstance(item, dict)] if isinstance(value, list) else []


def _positive(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value) and value > 0


def _path_exists(root: Path | None, relative: Any) -> bool:
    """True when ``relative`` (ignoring any ``#anchor``) is a safe path that exists under root."""
    if root is None:
        return True
    if not isinstance(relative, str) or not relative:
        return False
    candidate = Path(relative.split("#", 1)[0])
    if candidate.is_absolute() or ".." in candidate.parts:
        return False
    return (root / candidate).exists()


def _check_path(errors: list[str], root: Path | None, label: str, relative: Any) -> None:
    if not _text(relative):
        errors.append(f"{label} must name a project-relative path")
    elif not _path_exists(root, relative):
        errors.append(f"{label} does not exist under the project root or is not a safe relative path: {relative}")


def _validate_project(m: dict[str, Any], root: Path | None, errors: list[str]) -> None:
    project = m.get("project")
    if not isinstance(project, dict):
        errors.append("project record is required")
        return
    if not _text(project.get("name")):
        errors.append("project.name is required")
    if not is_valid_semver(project.get("version")):
        errors.append("project.version must be a valid semantic version")
    if project.get("versioning") != "semantic":
        errors.append("project.versioning must be 'semantic'")
    _check_path(errors, root, "project.changelog", project.get("changelog"))
    _check_path(errors, root, "project.design_notes", project.get("design_notes"))
    if not _text(project.get("requires_python")):
        errors.append("project.requires_python must declare the supported interpreter range")


def _validate_stack(m: dict[str, Any], root: Path | None, errors: list[str]) -> None:
    stack = m.get("stack_decision")
    if not isinstance(stack, dict):
        errors.append("stack_decision (ADR) record is required")
        return
    _check_path(errors, root, "stack_decision.adr_path", stack.get("adr_path"))
    language = stack.get("language") if isinstance(stack.get("language"), dict) else {}
    if not _text(language.get("name")):
        errors.append("stack_decision.language.name is required")
    if not _text(language.get("justification"), 20):
        errors.append("stack_decision.language.justification must give a technical-merit reason (>= 20 characters)")
    paradigm = stack.get("paradigm") if isinstance(stack.get("paradigm"), dict) else {}
    if paradigm.get("style") not in {"oop", "functional", "procedural", "mixed"}:
        errors.append("stack_decision.paradigm.style must be oop, functional, procedural, or mixed")
    if not _text(paradigm.get("justification"), 20):
        errors.append("stack_decision.paradigm.justification must justify the paradigm (>= 20 characters)")
    selected = _objects(stack.get("selected"))
    if not selected:
        errors.append("stack_decision.selected must list at least one chosen component")
    for item in selected:
        if not (_text(item.get("name")) and _text(item.get("role")) and _text(item.get("rationale"))):
            errors.append("each selected stack component needs name, role, and rationale")
    alternatives = _objects(stack.get("alternatives_considered"))
    if len(alternatives) < 2:
        errors.append("stack_decision.alternatives_considered must record at least two alternatives")
    for item in alternatives:
        if not (_text(item.get("name")) and _text(item.get("rejected_because"), 10)):
            errors.append("each alternative needs a name and a concrete rejected_because reason")
    for item in _objects(stack.get("reinvention_exceptions")):
        if not (_text(item.get("capability")) and _text(item.get("why_not_library"), 20)):
            errors.append("each reinvention exception needs a capability and a why_not_library reason")


def _validate_interface(m: dict[str, Any], root: Path | None, errors: list[str]) -> None:
    interface = m.get("interface")
    if not isinstance(interface, dict):
        errors.append("interface record is required")
        return
    primary = interface.get("primary")
    if primary not in {"library_only", "cli", "desktop_gui", "web_ui", "tui_python", "tui_rust", "notebook"}:
        errors.append("interface.primary is not a recognized interface kind")
        return
    if not _text(interface.get("justification"), 20):
        errors.append("interface.justification must explain the choice (>= 20 characters)")
    if interface.get("headless_core") is not True:
        errors.append("interface.headless_core must be true: the scientific core must run and be tested without any UI")
    if primary not in GUI_INTERFACES:
        return
    if interface.get("thin_layer") is not True:
        errors.append("a GUI/TUI must be declared a thin_layer over the headless core")
    _check_path(errors, root, "interface.gui_layer_path", interface.get("gui_layer_path"))
    if not _text(interface.get("usability_rationale"), 20):
        errors.append("a GUI/TUI needs usability_rationale: how it improves usability, accessibility, or research efficiency")
    access = interface.get("accessibility") if isinstance(interface.get("accessibility"), dict) else {}
    flags = ("keyboard_operable", "non_color_encoding", "text_alternatives", "scalable_text_or_contrast")
    for flag in flags:
        if not isinstance(access.get(flag), bool):
            errors.append(f"interface.accessibility.{flag} must be declared true or false")
    if not _text(access.get("notes")):
        errors.append("interface.accessibility.notes is required for a GUI/TUI")
    if any(access.get(flag) is False for flag in flags) and not _text(access.get("limitations")):
        errors.append("interface.accessibility.limitations must explain every accessibility flag declared false")
    if primary == "tui_rust":
        if str(interface.get("implementation_language", "")).strip().lower() != "rust":
            errors.append("interface.implementation_language must be 'Rust' for tui_rust")
        if not _text(interface.get("rust_rationale"), 30):
            errors.append("tui_rust needs rust_rationale stating the performance/reliability requirement; Rust is an option, not a default")


def _validate_tooling(m: dict[str, Any], root: Path | None, errors: list[str]) -> None:
    tooling = m.get("quality_tooling")
    if not isinstance(tooling, dict):
        errors.append("quality_tooling record is required")
        return
    for key in REQUIRED_TOOLING:
        if not _text(tooling.get(key)):
            errors.append(f"quality_tooling.{key} is required")
    _check_path(errors, root, "quality_tooling.ci_config_path", tooling.get("ci_config_path"))
    deps = m.get("dependency_management")
    if not isinstance(deps, dict):
        errors.append("dependency_management record is required")
    else:
        for key in ("tool", "lockfile", "pinning_policy"):
            if not _text(deps.get(key)):
                errors.append(f"dependency_management.{key} is required")
        _check_path(errors, root, "dependency_management.manifest_path", deps.get("manifest_path"))
        status = deps.get("lockfile_status")
        if status not in {"committed", "pending_generation"}:
            errors.append("dependency_management.lockfile_status must be committed or pending_generation")
        elif status == "committed":
            _check_path(errors, root, "dependency_management.lockfile", deps.get("lockfile"))
    config = m.get("configuration")
    if not isinstance(config, dict):
        errors.append("configuration record is required")
    else:
        _check_path(errors, root, "configuration.config_path", config.get("config_path"))
        if config.get("separated_from_code") is not True:
            errors.append("configuration.separated_from_code must be true")
        if not _text(config.get("validation")):
            errors.append("configuration.validation must say how configuration is validated")
    logging_record = m.get("logging_and_error_handling")
    if not isinstance(logging_record, dict) or not (
        _text(logging_record.get("logging")) and _text(logging_record.get("error_handling"))
    ):
        errors.append("logging_and_error_handling must declare both logging and error_handling")


def _validate_numerical(m: dict[str, Any], errors: list[str]) -> bool:
    record = m.get("numerical_verification")
    if not isinstance(record, dict):
        errors.append("numerical_verification record is required")
        return False
    required = record.get("required")
    if not isinstance(required, bool):
        errors.append("numerical_verification.required must be true or false")
        return False
    if not required:
        if not _text(record.get("justification_if_not_required"), 20):
            errors.append("numerical_verification not required: give a scientific justification (>= 20 characters)")
        return False
    if not record.get("methods"):
        errors.append("numerical_verification.methods must name at least one method")
    tolerances = record.get("tolerances")
    if not isinstance(tolerances, dict) or not tolerances or not all(_positive(v) for v in tolerances.values()):
        errors.append("numerical_verification.tolerances must be a non-empty map of positive finite numbers")
    if not _text(record.get("convergence_criterion"), 10):
        errors.append("numerical_verification.convergence_criterion must state a quantitative pass criterion")
    return True


def _validate_physics(m: dict[str, Any], root: Path | None, errors: list[str]) -> bool:
    record = m.get("physical_correctness")
    if not isinstance(record, dict):
        errors.append("physical_correctness record is required")
        return False
    policy = record.get("units_policy")
    if policy not in {"pint", "manual_dimension_vectors", "nondimensionalized_with_documented_scales", "none_with_justification"}:
        errors.append("physical_correctness.units_policy is not a recognized policy")
    elif policy == "none_with_justification" and not _text(record.get("units_justification"), 20):
        errors.append("units_policy none_with_justification needs units_justification")
    if not _text(record.get("dimensional_analysis"), 10):
        errors.append("physical_correctness.dimensional_analysis must summarize the dimensional check")
    if not record.get("limiting_cases"):
        errors.append("physical_correctness.limiting_cases must list at least one limiting case")
    if not record.get("symmetry_checks") and not _text(record.get("symmetry_justification"), 20):
        errors.append("physical_correctness needs symmetry_checks or a symmetry_justification")
    if not record.get("analytic_benchmarks") and not _text(record.get("no_benchmark_justification"), 20):
        errors.append("physical_correctness needs analytic_benchmarks or a no_benchmark_justification")
    _check_path(errors, root, "physical_correctness.assumptions_registry", record.get("assumptions_registry"))
    return policy not in {None, "none_with_justification"}


def _validate_tests(m: dict[str, Any], root: Path | None, numerical_required: bool, units_used: bool, errors: list[str]) -> set[str]:
    plan = m.get("test_plan")
    tests = _objects(plan.get("tests")) if isinstance(plan, dict) else []
    if not tests:
        errors.append("test_plan.tests must list at least one test")
        return set()
    kinds: set[str] = set()
    ids: set[str] = set()
    for test in tests:
        test_id = test.get("id")
        if test_id in ids:
            errors.append(f"duplicate test id: {test_id}")
        ids.add(test_id)
        kinds.add(str(test.get("kind")))
        if test.get("evidence_status") != "planned":
            _check_path(errors, root, f"test {test_id} path", test.get("path"))
        if test.get("evidence_status") == "evidenced":
            _check_path(errors, root, f"test {test_id} evidence", test.get("evidence"))
    if "unit" not in kinds:
        errors.append("test_plan must include a 'unit' test")
    if numerical_required:
        if "convergence" not in kinds:
            errors.append("test_plan must include a 'convergence' test when numerical verification is required")
        if not kinds & {"analytic_benchmark", "limiting_case", "conservation"}:
            errors.append("test_plan must include an analytic_benchmark, limiting_case, or conservation test")
    if units_used and "dimensional" not in kinds:
        errors.append("test_plan must include a 'dimensional' test when a units policy is declared")
    return kinds


def _validate_uncertainty(m: dict[str, Any], errors: list[str]) -> None:
    record = m.get("uncertainty_treatment")
    if not isinstance(record, dict):
        errors.append("uncertainty_treatment record is required")
        return
    methods = record.get("methods") if isinstance(record.get("methods"), list) else []
    if not methods:
        errors.append("uncertainty_treatment.methods must be non-empty")
    if "none_with_justification" in methods and not _text(record.get("justification"), 20):
        errors.append("uncertainty_treatment none_with_justification needs a scientific justification")
    sources = record.get("error_sources")
    if not isinstance(sources, dict):
        errors.append("uncertainty_treatment.error_sources must separate " + ", ".join(ERROR_SOURCES))
        return
    for source in ERROR_SOURCES:
        if not _text(sources.get(source), 5):
            errors.append(f"uncertainty_treatment.error_sources.{source} must state a treatment or 'not_applicable: reason'")


def _validate_comparison(m: dict[str, Any], errors: list[str]) -> None:
    record = m.get("experiment_comparison")
    if not isinstance(record, dict):
        errors.append("experiment_comparison record is required")
        return
    planned = record.get("planned")
    if not isinstance(planned, bool):
        errors.append("experiment_comparison.planned must be true or false")
    elif planned:
        if not record.get("metrics"):
            errors.append("experiment_comparison.metrics must name goodness-of-fit metrics")
        if record.get("overlay_with_error_bars") is not True:
            errors.append("experiment_comparison.overlay_with_error_bars must be true when a comparison is planned")
        if not _text(record.get("fit_validation_separation"), 20):
            errors.append("experiment_comparison.fit_validation_separation must describe disjoint fit and held-out data")
    elif not _text(record.get("justification_if_not_planned"), 20):
        errors.append("experiment_comparison not planned: give a justification")


def _validate_reproducibility(m: dict[str, Any], root: Path | None, errors: list[str]) -> None:
    record = m.get("reproducibility")
    if not isinstance(record, dict):
        errors.append("reproducibility record is required")
        return
    if not _text(record.get("seed_policy"), 10):
        errors.append("reproducibility.seed_policy is required")
    if not isinstance(record.get("deterministic_outputs"), bool):
        errors.append("reproducibility.deterministic_outputs must be true or false")
    _check_path(errors, root, "reproducibility.run_metadata_writer", record.get("run_metadata_writer"))
    fields = record.get("run_metadata_fields") if isinstance(record.get("run_metadata_fields"), list) else []
    missing = [field for field in REQUIRED_METADATA_FIELDS if field not in fields]
    if missing:
        errors.append(f"reproducibility.run_metadata_fields lacks required fields: {missing}")
    if not _text(record.get("environment_lock")):
        errors.append("reproducibility.environment_lock is required")
    docs = m.get("documentation")
    if not isinstance(docs, dict):
        errors.append("documentation record is required")
        return
    _check_path(errors, root, "documentation.readme", docs.get("readme"))
    _check_path(errors, root, "documentation.verification_plan", docs.get("verification_plan"))
    if docs.get("assumptions_section") is not True:
        errors.append("documentation.assumptions_section must be true: keep a transparent assumptions registry")


def validate_engineering_manifest(manifest: Any, root: Path | None = None) -> list[str]:
    """Return semantic errors for a manifest. ``root`` enables referenced-file existence checks."""
    if not isinstance(manifest, dict):
        return ["engineering manifest must be an object"]
    plugin_root = Path(__file__).resolve().parents[1]
    errors = [f"engineering manifest: {e}" for e in basic_schema_errors(manifest, load_schema(plugin_root, "engineering-standards"))]
    if errors:
        return errors
    status = manifest["status"]
    if status == "not_started":
        return []
    if status == "not_applicable":
        if not _text(manifest.get("not_applicable_justification"), 20):
            errors.append("engineering manifest: status not_applicable needs not_applicable_justification (>= 20 characters)")
        return errors
    ceiling = manifest["claim_ceiling"]
    if not _text(ceiling, 10):
        errors.append("claim_ceiling must state what the declaration does and does not establish")
    _validate_project(manifest, root, errors)
    _validate_stack(manifest, root, errors)
    _validate_interface(manifest, root, errors)
    _validate_tooling(manifest, root, errors)
    numerical_required = _validate_numerical(manifest, errors)
    units_used = _validate_physics(manifest, root, errors)
    _validate_tests(manifest, root, numerical_required, units_used, errors)
    _validate_uncertainty(manifest, errors)
    _validate_comparison(manifest, errors)
    _validate_reproducibility(manifest, root, errors)
    return [f"engineering manifest: {e}" for e in errors]


def _evidenced(record: Any, root: Path | None) -> bool:
    return (
        isinstance(record, dict)
        and record.get("evidence_status") == "evidenced"
        and _text(record.get("evidence"))
        and _path_exists(root, record.get("evidence"))
    )


def validate_engineering_contract(case_dir: Path, loaded: dict[str, Any]) -> list[str]:
    """Case-level gate.

    Opt-in per case, like the other versioned contracts: it applies when ``project_state.yaml``
    sets ``engineering_contract_version`` to 1 or when an ``engineering_standards.yaml`` exists.
    Legacy cases remain valid and are simply not claimed to follow the engineering standards.
    """
    state = loaded.get("project_state.yaml", {})
    state = state if isinstance(state, dict) else {}
    manifest_path = case_dir / ENGINEERING_MANIFEST
    versioned = state.get("engineering_contract_version") == ENGINEERING_VERSION
    if not manifest_path.exists():
        return [f"{ENGINEERING_MANIFEST}: required when engineering_contract_version is 1"] if versioned else []
    try:
        manifest = load_artifact(manifest_path)
    except ValueError as exc:
        return [str(exc)]
    project_root = case_dir
    declared_root = manifest.get("project", {}).get("root") if isinstance(manifest, dict) else None
    if isinstance(declared_root, str) and declared_root and not Path(declared_root).is_absolute() and ".." not in Path(declared_root).parts:
        project_root = case_dir / declared_root
    errors = [f"{ENGINEERING_MANIFEST}: {e}" for e in validate_engineering_manifest(manifest, project_root)]
    if not isinstance(manifest, dict) or not versioned:
        return errors
    rank = SOFTWARE_STATE_RANK.get(str(state.get("software_readiness", "not_applicable")), 0)
    status = manifest.get("status")
    if rank >= _IMPLEMENTATION_RANK and status != "declared":
        errors.append(
            f"{ENGINEERING_MANIFEST}: software_readiness {state.get('software_readiness')} requires status 'declared'"
        )
    if status == "declared":
        if rank >= _EXECUTED_RANK:
            deps = manifest.get("dependency_management", {})
            if not isinstance(deps, dict) or deps.get("lockfile_status") != "committed":
                errors.append(f"{ENGINEERING_MANIFEST}: an executed package requires a committed dependency lockfile")
        if rank >= _NUMERICAL_RANK:
            numerical = manifest.get("numerical_verification", {})
            if not (isinstance(numerical, dict) and numerical.get("required") is True and _evidenced(numerical, project_root)):
                errors.append(f"{ENGINEERING_MANIFEST}: numerically_verified requires numerical_verification.required with evidenced receipt")
        if rank >= _COMPARED_RANK:
            if not _evidenced(manifest.get("experiment_comparison"), project_root) or manifest.get("experiment_comparison", {}).get("planned") is not True:
                errors.append(f"{ENGINEERING_MANIFEST}: experimentally_compared requires an evidenced, planned experiment_comparison")
    return errors
