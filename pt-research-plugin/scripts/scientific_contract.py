#!/usr/bin/env python3
"""Cross-artifact gates for the version-2 and version-3 PT scientific contracts."""

from __future__ import annotations

import csv
import re
from pathlib import Path
from typing import Any

from artifact_lib import basic_schema_errors, load_artifact, load_schema
from runnable_contract import validate_case_package


V2_ARTIFACTS = {
    "apparatus_fidelity.yaml": "apparatus-fidelity",
    "evidence_matrix.yaml": "evidence-matrix",
    "solver_requirements.yaml": "solver-requirements",
    "simulation_handoff.yaml": "simulation-handoff",
    "parameter_equation_map.yaml": "parameter-equation-map",
    "theory/equations.yaml": "equations",
}
STOP_STATUSES = {
    "stop_unresolved_mechanism",
    "stop_insufficient_literature",
    "stop_missing_data",
}
SIMULATION_STATES = (
    "solver_selected_only",
    "installation_package_prepared",
    "parameter_handoff_validated",
    "solver_case_generator_prepared",
    "solver_native_case_generated",
    "smoke_tested",
    "executed",
    "numerically_verified",
    "experimentally_validated",
)
EVIDENCE_REQUIRED_FROM = SIMULATION_STATES.index("smoke_tested")
ABSOLUTE_PATH = re.compile(r"(?:^|[\s\"'])(?:/Users/|/home/|[A-Z]:\\\\Users\\\\)")


def _objects(items: Any) -> list[dict[str, Any]]:
    return [item for item in items if isinstance(item, dict)] if isinstance(items, list) else []


def _load_required(case_dir: Path, plugin_root: Path) -> tuple[dict[str, Any], list[str]]:
    loaded: dict[str, Any] = {}
    errors: list[str] = []
    for relative, schema_name in V2_ARTIFACTS.items():
        path = case_dir / relative
        if not path.is_file():
            errors.append(f"missing version-2 artifact: {relative}")
            continue
        try:
            value = load_artifact(path)
            loaded[relative] = value
            errors.extend(f"{relative}: {error}" for error in basic_schema_errors(value, load_schema(plugin_root, schema_name)))
        except ValueError as exc:
            errors.append(str(exc))
    return loaded, errors


def _stopping_decision(core: dict[str, Any]) -> dict[str, Any]:
    registry = core.get("model_registry.yaml", {})
    decision = registry.get("stopping_decision", {}) if isinstance(registry, dict) else {}
    return decision if isinstance(decision, dict) else {}


def _validate_equation_lineage(
    equations: list[dict[str, Any]],
    sources: dict[str, dict[str, Any]],
) -> list[str]:
    errors: list[str] = []
    for equation in equations:
        eq_id = equation.get("id", "?")
        lineage = equation.get("lineage")
        if not isinstance(lineage, dict):
            errors.append(f"equation {eq_id} lacks Source -> Original equation -> Assumptions -> Adaptation -> Final model lineage")
            continue
        for field in ("source_basis", "original_equation", "assumptions", "transformations_made", "final_equation", "adaptation_justification"):
            if field not in lineage or lineage.get(field) in (None, ""):
                errors.append(f"equation {eq_id} lineage lacks {field}")
        bases = _objects(lineage.get("source_basis"))
        if not bases:
            errors.append(f"equation {eq_id} lineage has no source title/author basis")
        for basis in bases:
            source_id = basis.get("source_id")
            source = sources.get(source_id)
            if not source:
                errors.append(f"equation {eq_id} lineage cites unknown source {source_id}")
                continue
            if basis.get("source_title") != source.get("title"):
                errors.append(f"equation {eq_id} lineage source title does not match registry: {source_id}")
            if list(basis.get("source_authors", [])) != list(source.get("authors", [])):
                errors.append(f"equation {eq_id} lineage source authors do not match registry: {source_id}")
            locator = basis.get("exact_locator")
            if not isinstance(locator, dict):
                errors.append(f"equation {eq_id} lineage source {source_id} lacks exact locator record")
                continue
            availability = locator.get("availability")
            granular = any(locator.get(key) for key in ("chapter", "section", "pages", "equation", "figure", "table", "appendix", "url_anchor"))
            if availability == "verified" and not granular:
                errors.append(f"equation {eq_id} verified lineage locator is not retrievable")
            elif availability == "unavailable":
                if not locator.get("unavailable_reason") or not locator.get("searches_performed"):
                    errors.append(f"equation {eq_id} unavailable lineage locator lacks reason and searches")
            elif availability not in {"verified", "unavailable"}:
                errors.append(f"equation {eq_id} lineage locator availability is invalid")
        if lineage.get("final_equation") != equation.get("latex"):
            errors.append(f"equation {eq_id} lineage final_equation differs from the equation actually used")
    return errors


def _validate_justified_stop(case_dir: Path, core: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    registry = core.get("model_registry.yaml", {})
    route = core.get("simulation_route.yaml", {})
    decision = _stopping_decision(core)
    if decision.get("status") not in STOP_STATUSES:
        return ["version-3 stopped case lacks a recognized stopping status"]
    for field in ("rationale", "blocking_items", "allowed_claim_level", "resumption_conditions"):
        if not decision.get(field):
            errors.append(f"justified stop lacks {field}")
    if registry.get("selected_candidate_ids"):
        errors.append("justified stop must not designate a selected model")
    if registry.get("selection_outcome") not in {
        "unresolved", "no_candidate_justified", "competing_whole_chain_models", "insufficient_evidence_to_select"
    }:
        errors.append("justified stop must preserve an unresolved or insufficient-evidence selection outcome")
    if route.get("primary_solver") != "No numerical solver":
        errors.append("justified stop must not select or package a numerical solver")
    if route.get("selected_model_id") not in {"", "none", "unresolved"}:
        errors.append("justified stop route must not retain a selected model ID")
    selection_chain = route.get("selection_chain", {})
    if isinstance(selection_chain, dict) and selection_chain.get("solver") not in {"", "No numerical solver"}:
        errors.append("justified stop retains a solver in the physics-first selection chain")
    handoff_path = case_dir / "simulation_handoff.yaml"
    if handoff_path.is_file():
        handoff = load_artifact(handoff_path)
        if isinstance(handoff, dict) and (
            handoff.get("primary_solver") != "No numerical solver"
            or handoff.get("highest_state") not in {"not_applicable", "solver_selected_only"}
            or handoff.get("software_readiness") not in {None, "not_applicable"}
        ):
            errors.append("justified stop retains a packaged or advanced simulation handoff")
    if (case_dir / "simulation_package_manifest.yaml").exists():
        errors.append("justified stop must not retain a simulation package manifest")
    report_path = case_dir / "reports" / "theoretical-model.tex"
    if report_path.is_file():
        report = report_path.read_text(encoding="utf-8")
        if decision.get("status") not in report or decision.get("allowed_claim_level") not in report:
            errors.append("justified-stop report omits stopping status or allowed claim level")
    return errors


def validate_v2(case_dir: Path, core: dict[str, Any], plugin_root: Path) -> list[str]:
    loaded, errors = _load_required(case_dir, plugin_root)
    if errors:
        return errors

    contract = core.get("problem_contract.yaml", {})
    registry = core.get("model_registry.yaml", {})
    route = core.get("simulation_route.yaml", {})
    state = core.get("project_state.yaml", {})
    sources = core.get("source_registry.yaml", {})
    apparatus = loaded["apparatus_fidelity.yaml"]
    evidence = loaded["evidence_matrix.yaml"]
    requirements = loaded["solver_requirements.yaml"]
    handoff = loaded["simulation_handoff.yaml"]
    mapping = loaded["parameter_equation_map.yaml"]
    equation_root = loaded["theory/equations.yaml"]

    numerical_routes = {"python_ode", "python_optimization", "fourier_optics", "reduced_order_model", "project_chrono", "elmer_fem", "yade", "openfoam_continuum"}
    if route.get("selected_route") in numerical_routes and route.get("primary_solver") == "No numerical solver":
        errors.append("numerical route is mislabeled as No numerical solver")
    if route.get("selected_route") == "analytical_closed_form" and route.get("primary_solver") != "No numerical solver":
        errors.append("analytical_closed_form must not claim a numerical solver")

    features = _objects(apparatus.get("features"))
    contradicted = [f.get("apparatus_feature", "<unknown>") for f in features if f.get("match_status") == "contradicted"]
    if contradicted:
        errors.append(f"apparatus fidelity contradiction blocks model endorsement: {contradicted}")
    for feature in features:
        if feature.get("match_status") in {"approximated", "unknown"} and (
            not feature.get("consequence_if_wrong") or not feature.get("required_measurement_or_source")
        ):
            errors.append(f"apparatus feature lacks risk/measurement record: {feature.get('apparatus_feature')}")

    candidates = _objects(registry.get("candidates"))
    serious = [c for c in candidates if c.get("candidate_kind") != "component"]
    if len(serious) < 2 and not str(registry.get("single_candidate_exception", "")).strip():
        errors.append("candidate pool has fewer than two serious candidates without a physics-based exception")
    candidate_fields = (
        "candidate_kind", "causal_mechanism", "governing_equation_ids", "validity_range",
        "predicted_observables", "identifiable_parameters", "decisive_falsifier",
        "discriminating_experiment", "computational_cost", "solver_needs", "evidence_quality",
    )
    for candidate in serious:
        missing = [field for field in candidate_fields if not candidate.get(field)]
        if missing:
            errors.append(f"candidate {candidate.get('id', '?')} comparison record is incomplete: {missing}")
        if candidate.get("status") == "retained_competitor":
            experiment = candidate.get("discriminating_experiment", {})
            if not isinstance(experiment, dict) or not experiment.get("competitor_id") or not experiment.get("predicted_difference"):
                errors.append(f"retained candidate {candidate.get('id', '?')} lacks a decisive competitor discriminator")
    outcome = registry.get("selection_outcome")
    if outcome in {"unresolved", "no_candidate_justified", "competing_whole_chain_models", "insufficient_evidence_to_select"}:
        if registry.get("selected_candidate_ids"):
            errors.append("unresolved/no-justified selection must not silently designate a final candidate")
    elif not registry.get("selected_candidate_ids"):
        errors.append("selected working outcome lacks selected_candidate_ids")

    equations = _objects(equation_root.get("equations"))
    equation_ids = {eq.get("id") for eq in equations}
    source_by_id = {s.get("id"): s for s in _objects(sources.get("sources"))}
    for equation in equations:
        eq_id = equation.get("id", "?")
        provenance = equation.get("provenance_class")
        claims = _objects(equation.get("source_claims"))
        if provenance in {"verbatim_source_equation", "adapted_source_equation", "derived_from_cited_principles"} and not claims:
            errors.append(f"equation {eq_id} has sourced provenance but no source_claims")
        if provenance == "adapted_source_equation":
            transformation = equation.get("transformation_map")
            required = ("source_equation", "source_notation", "substitutions_or_approximations", "apparatus_specific_changes", "resulting_equation", "dimensional_check", "new_assumptions")
            if not isinstance(transformation, dict) or any(not transformation.get(key) for key in required):
                errors.append(f"adapted equation {eq_id} lacks a complete source-to-report transformation map")
        if provenance == "original_derivation":
            principles = _objects(equation.get("starting_principles"))
            if not principles or any(not p.get("source_id") or not p.get("exact_locator") for p in principles):
                errors.append(f"original derivation {eq_id} lacks cited starting principles with exact locators")
            if len(equation.get("derivation_steps", [])) < 2:
                errors.append(f"original derivation {eq_id} omits nontrivial algebraic steps")
        for claim in claims:
            source_id = claim.get("source_id")
            if source_id not in source_by_id:
                errors.append(f"equation {eq_id} cites unknown source {source_id}")
            status = claim.get("retrieval_status")
            locator = claim.get("exact_locator")
            verification = claim.get("locator_verification", {})
            if status == "verified_full_text":
                granular = isinstance(locator, dict) and any(locator.get(k) for k in ("chapter", "section", "pages", "equation", "appendix", "table", "figure", "url_anchor"))
                if not granular:
                    errors.append(f"equation {eq_id} uses full text but omits a discoverable exact locator")
                if not isinstance(verification, dict) or verification.get("status") != "verified_against_source":
                    errors.append(f"equation {eq_id} exact locator is not verified against the source")
            elif status in {"not_retrieved", "not_available"}:
                if not claim.get("locator_searches") or not claim.get("support_limit"):
                    errors.append(f"equation {eq_id} unavailable locator lacks search record or support limitation")
            else:
                errors.append(f"equation {eq_id} has invalid retrieval_status")
            if isinstance(verification, dict) and verification.get("status") == "unsupported_or_inconsistent":
                errors.append(f"equation {eq_id} contains an unsupported or fabricated locator")
        directness = {source_by_id.get(c.get("source_id"), {}).get("directness") for c in claims}
        if equation.get("role") in {"constitutive", "empirical"} and directness and directness <= {"contextual_only", "official_prompt_only"}:
            errors.append(f"quantitative {equation.get('role')} equation {eq_id} is supported only by contextual/prompt evidence")

    report_path = case_dir / "reports" / "theoretical-model.tex"
    if not report_path.is_file():
        errors.append("missing version-2 human-facing theoretical report")
    else:
        report_text = report_path.read_text(encoding="utf-8")
        for equation in equations:
            eq_id = equation.get("id", "?")
            if rf"\label{{eq:{eq_id}}}" not in report_text:
                errors.append(f"equation {eq_id} is absent from the human-facing report")
            if f"Provenance [{eq_id}]" not in report_text:
                errors.append(f"equation {eq_id} lacks nearby human-facing provenance")
            for claim in _objects(equation.get("source_claims")):
                if claim.get("retrieval_status") == "verified_full_text":
                    locator = claim.get("exact_locator", {})
                    granular_values = [str(locator.get(key)) for key in ("section", "pages", "equation", "appendix", "table", "figure", "url_anchor") if locator.get(key)]
                    if granular_values and not any(value in report_text for value in granular_values):
                        errors.append(f"equation {eq_id} exact locator is absent from the human-facing report")

    controlled = set(contract.get("controlled_inputs", []))
    mappings = _objects(mapping.get("mappings"))
    mapped_controls = {item.get("experimental_parameter") for item in mappings}
    missing_controls = sorted(controlled - mapped_controls)
    if missing_controls:
        errors.append(f"experimental controls absent from equations or boundary conditions: {missing_controls}")
    for item in mappings:
        if item.get("equation_or_boundary_id") not in equation_ids:
            errors.append(f"parameter map references missing equation/boundary: {item.get('equation_or_boundary_id')}")
        if item.get("predicted_observable") not in set(contract.get("primary_observables", [])):
            errors.append(f"parameter map does not terminate in a requested observable: {item.get('predicted_observable')}")
    history = {s.get("symbol") for s in _objects(mapping.get("symbols")) if s.get("history_variable")}
    closed = {symbol for eq in equations for symbol in eq.get("closes_variables", [])}
    if history - closed:
        errors.append(f"history/state variables lack evolution or closure equations: {sorted(history - closed)}")
    produced = {value for eq in equations for value in eq.get("produces", [])}
    observables = set(contract.get("primary_observables", []))
    if not observables <= produced:
        errors.append(f"selected mathematics cannot produce requested observables: {sorted(observables - produced)}")

    for claim in _objects(evidence.get("claims")):
        directness = set(claim.get("directness", []))
        if claim.get("importance") == "central_quantitative" and directness <= {"contextual_only", "official_prompt_only"}:
            errors.append(f"central quantitative claim has context-only evidence: {claim.get('claim_id')}")
        if claim.get("importance", "").startswith("central") and claim.get("status") in {"blocking", "unresolved"}:
            errors.append(f"central evidence claim is not sufficient: {claim.get('claim_id')}")

    if requirements.get("model_closure_status") != "closed":
        # Amendment 05 permits an executable exploratory package for a
        # plausible but not fully closed model.  The package must remain
        # synthetic-only and carry an explicit provisional implementation
        # label; apparatus, predictive and validation claims remain gated.
        unresolved_hold = (
            route.get("primary_solver") == "No numerical solver"
            and handoff.get("scientific_readiness") == "model_selected_not_closed"
            and handoff.get("software_readiness") == "handoff_only"
        )
        provisional_implementation = (
            handoff.get("scientific_readiness") == "model_selected_not_closed"
            and handoff.get("software_readiness") == "runnable_synthetic"
            and handoff.get("implementation_status") == "runnable_provisional"
            and handoff.get("provisional_model") is True
            and (case_dir / "linux-simulation").is_dir()
        )
        if not unresolved_hold and not provisional_implementation:
            errors.append("solver selection is blocked until the physical model is closed")
    if route.get("primary_solver") != handoff.get("primary_solver"):
        errors.append("theory/route solver and simulation handoff solver do not match")
    if route.get("primary_solver") != "No numerical solver" and not (case_dir / "linux-simulation").is_dir():
        errors.append("simulation route lacks linux-simulation adapter directory")
    if handoff.get("solver_distribution") not in {"external_reference", "shared_installer_reference", "embedded_redistributable"}:
        errors.append("simulation package does not declare how the external solver is supplied")
    readme_ref = handoff.get("beginner_readme")
    if isinstance(readme_ref, str) and readme_ref and not (case_dir / readme_ref).is_file():
        errors.append(f"simulation handoff references nonexistent beginner README: {readme_ref}")
    highest = handoff.get("highest_state")
    if highest in SIMULATION_STATES:
        rank = SIMULATION_STATES.index(highest)
        evidence_by_state = {item.get("state"): item for item in _objects(handoff.get("state_evidence"))}
        for required_state in SIMULATION_STATES[EVIDENCE_REQUIRED_FROM:rank + 1]:
            item = evidence_by_state.get(required_state)
            if not item or not item.get("receipt") or not item.get("verified_at"):
                errors.append(f"simulation state {highest} lacks evidence for {required_state}")
    for claim in _objects(state.get("claims")):
        stage = claim.get("stage")
        if claim.get("status") == "completed" and stage in SIMULATION_STATES[EVIDENCE_REQUIRED_FROM:]:
            if not claim.get("evidence_ids"):
                errors.append(f"project state claims {stage} without evidence IDs")

    package_manifest = case_dir / "simulation_package_manifest.yaml"
    if package_manifest.exists():
        package = load_artifact(package_manifest)
        if isinstance(package, dict):
            package_solver = package.get("primary_solver")
            if package_solver and package_solver != route.get("primary_solver"):
                errors.append("theory/package solver mismatch")
            if package.get("solver_embedded") and handoff.get("solver_distribution") == "external_reference":
                errors.append("external solver package contradicts itself by embedding the solver")
            for shared_ref in package.get("shared_files", []):
                if isinstance(shared_ref, str) and not (case_dir / shared_ref).exists():
                    errors.append(f"simulation package references nonexistent shared file: {shared_ref}")

    batch_matrix = case_dir / "data" / "solver-prompt-matrix.csv"
    batch_manifest = case_dir / "batch_manifest.yaml"
    if batch_manifest.exists():
        manifest = load_artifact(batch_manifest)
        text = batch_matrix.read_text(encoding="utf-8") if batch_matrix.exists() else ""
        readme_text = (case_dir / "README.md").read_text(encoding="utf-8") if (case_dir / "README.md").exists() else ""
        for problem in manifest.get("problems", []) if isinstance(manifest, dict) else []:
            if isinstance(problem, str) and problem not in text:
                errors.append(f"problem omitted from batch solver matrix: {problem}")
            if isinstance(problem, str) and readme_text and problem not in readme_text:
                errors.append(f"stale README coverage list omits problem: {problem}")

    predictions_path = case_dir / "theory" / "predictions.csv"
    if predictions_path.exists():
        with predictions_path.open(encoding="utf-8", newline="") as stream:
            for row in csv.DictReader(stream):
                basis = row.get("equation_id") or row.get("prediction_basis", "")
                if not any(str(eq_id) in basis for eq_id in equation_ids):
                    errors.append("prediction is not reproducible from a registered equation")

    for path in case_dir.rglob("*"):
        if path.is_file() and path.suffix.lower() in {".md", ".yaml", ".yml", ".json", ".csv", ".tex"}:
            try:
                text = path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                continue
            if ABSOLUTE_PATH.search(text):
                errors.append(f"local absolute path in artifact: {path.relative_to(case_dir)}")
    package_core = dict(core)
    package_core["simulation_handoff.yaml"] = handoff
    errors.extend(validate_case_package(case_dir, package_core, strict=True))
    return errors


def validate_v3(case_dir: Path, core: dict[str, Any], plugin_root: Path) -> list[str]:
    """Validate v3 additions while retaining v2 behavior for completed continuing cases."""
    decision = _stopping_decision(core)
    stopped = decision.get("status") in STOP_STATUSES
    if stopped:
        errors = _validate_justified_stop(case_dir, core)
        equation_path = case_dir / "theory" / "equations.yaml"
        if equation_path.is_file():
            equation_root = load_artifact(equation_path)
            equations = _objects(equation_root.get("equations")) if isinstance(equation_root, dict) else []
            sources_root = core.get("source_registry.yaml", {})
            sources = {s.get("id"): s for s in _objects(sources_root.get("sources"))}
            if equations:
                errors.extend(_validate_equation_lineage(equations, sources))
        return errors

    errors = validate_v2(case_dir, core, plugin_root)
    if errors:
        return errors
    registry = core.get("model_registry.yaml", {})
    route = core.get("simulation_route.yaml", {})
    sources_root = core.get("source_registry.yaml", {})
    sources = {s.get("id"): s for s in _objects(sources_root.get("sources"))}
    loaded, load_errors = _load_required(case_dir, plugin_root)
    if load_errors:
        return errors + load_errors
    evidence = loaded["evidence_matrix.yaml"]
    requirements = loaded["solver_requirements.yaml"]
    handoff = loaded["simulation_handoff.yaml"]
    mapping = loaded["parameter_equation_map.yaml"]
    equations = _objects(loaded["theory/equations.yaml"].get("equations"))

    serious = [c for c in _objects(registry.get("candidates")) if c.get("candidate_kind") != "component"]
    serious_ids = {c.get("id") for c in serious}
    comparison = _objects(registry.get("comparison_table"))
    comparison_ids = {row.get("candidate_id") for row in comparison}
    if comparison_ids != serious_ids:
        errors.append("mandatory comparison table must cover every serious candidate exactly")
    for row in comparison:
        for field in ("explains", "limitations", "required_parameters", "experimental_discriminator"):
            if not row.get(field):
                errors.append(f"candidate comparison {row.get('candidate_id', '?')} lacks {field}")
    if not str(registry.get("selection_rationale_against_alternatives", "")).strip():
        errors.append("model selection lacks rationale against alternatives")

    reviews = _objects(evidence.get("negative_evidence_review"))
    review_ids = {row.get("candidate_id") for row in reviews}
    if review_ids != serious_ids:
        errors.append("negative-evidence review must cover every serious candidate")
    for row in reviews:
        if not row.get("supporting_evidence_ids"):
            errors.append(f"candidate {row.get('candidate_id', '?')} lacks supporting evidence")
        for field in ("opposing_search_outcome", "limitations", "competing_interpretations"):
            if not row.get(field):
                errors.append(f"candidate {row.get('candidate_id', '?')} negative-evidence review lacks {field}")

    errors.extend(_validate_equation_lineage(equations, sources))

    symbol_rows = _objects(mapping.get("symbols"))
    for symbol in symbol_rows:
        if symbol.get("parameter_class") not in {
            "control_variable", "measured_state_variable", "material_constant", "hidden_uncertainty_source"
        }:
            errors.append(f"symbol {symbol.get('symbol', '?')} lacks required parameter classification")

    dimensionless = requirements.get("dimensionless_analysis")
    if not isinstance(dimensionless, dict):
        errors.append("solver requirements lack dimensionless analysis and regime identification")
    elif dimensionless.get("applicability") == "applicable":
        if not _objects(dimensionless.get("groups")):
            errors.append("applicable dimensionless analysis has no dimensionless groups")
        if not dimensionless.get("regime_identification"):
            errors.append("dimensionless analysis does not identify the operating regime")
    elif dimensionless.get("applicability") == "not_applicable":
        if not dimensionless.get("not_applicable_justification"):
            errors.append("dimensionless analysis marked not applicable without justification")
    else:
        errors.append("dimensionless analysis has invalid applicability")

    selection_chain = route.get("selection_chain")
    if not isinstance(selection_chain, dict):
        errors.append("solver route lacks Phenomenon -> Physics -> Governing equations -> Numerical requirements -> Solver chain")
    else:
        required = ("phenomenon", "physics", "governing_equation_ids", "numerical_requirements", "solver")
        missing = [field for field in required if not selection_chain.get(field)]
        if missing:
            errors.append(f"physics-first solver selection chain is incomplete: {missing}")
        if selection_chain.get("solver") != route.get("primary_solver"):
            errors.append("physics-first selection chain names a different solver than the route")
        equation_ids = {eq.get("id") for eq in equations}
        unknown = set(selection_chain.get("governing_equation_ids", [])) - equation_ids
        if unknown:
            errors.append(f"physics-first selection chain references unknown equations: {sorted(unknown)}")

    if route.get("primary_solver") != "No numerical solver":
        validation_chain = _objects(handoff.get("validation_chain"))
        if not validation_chain:
            errors.append("simulation package lacks experiment-to-simulation validation chain")
        for index, link in enumerate(validation_chain, start=1):
            required = (
                "experiment_measurement", "simulation_input", "solver_quantity", "output_metric",
                "comparison_method", "uncertainty_treatment", "acceptance_criterion",
            )
            missing = [field for field in required if not link.get(field)]
            if missing:
                errors.append(f"simulation validation chain link {index} is incomplete: {missing}")

    if decision.get("status") != "continue":
        errors.append("continuing version-3 case must explicitly record stopping_decision.status: continue")

    report_path = case_dir / "reports" / "theoretical-model.tex"
    if report_path.is_file():
        report = report_path.read_text(encoding="utf-8")
        for heading in ("Candidate", "Explains", "Limitations", "Required parameters", "Experimental discriminator"):
            if heading not in report:
                errors.append(f"human-facing report omits mandatory model-comparison column: {heading}")
        if "Source $\\rightarrow$ Original equation $\\rightarrow$ Assumptions $\\rightarrow$ Adaptation $\\rightarrow$ Final model" not in report:
            errors.append("human-facing report omits the equation-lineage chain")
    return errors
