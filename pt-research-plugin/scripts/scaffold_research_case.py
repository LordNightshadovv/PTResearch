#!/usr/bin/env python3
"""Create a durable PT case directory without overwriting prior research."""

from __future__ import annotations

import argparse
import re
from datetime import datetime, timezone
from pathlib import Path

from artifact_lib import dump_artifact


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("case_id")
    prompt_group = parser.add_mutually_exclusive_group(required=True)
    prompt_group.add_argument("--prompt")
    prompt_group.add_argument("--prompt-file", type=Path)
    parser.add_argument("--runs-root", type=Path, default=Path("runs"))
    args = parser.parse_args()
    try:
        prompt = args.prompt if args.prompt is not None else args.prompt_file.read_text(encoding="utf-8").strip()
    except (OSError, UnicodeError) as exc:
        parser.error(f"cannot read prompt file: {exc}")
    if not prompt:
        parser.error("official prompt must not be empty")
    if not re.fullmatch(r"[a-z0-9][a-z0-9._-]*", args.case_id):
        parser.error("case_id must be lowercase and filesystem-safe")
    case = (args.runs_root / args.case_id).resolve()
    if case.exists():
        parser.error(f"refusing to overwrite existing case: {case}")
    (case / "paper_cards").mkdir(parents=True)
    (case / "theory" / "figures").mkdir(parents=True)
    (case / "reports").mkdir(parents=True)
    (case / "provenance").mkdir(parents=True)
    (case / "simulation").mkdir(parents=True)
    (case / "openfoam" / "generated_case").mkdir(parents=True)
    (case / "simulation_package" / "shared").mkdir(parents=True)
    now = datetime.now(timezone.utc).isoformat()
    dump_artifact(case / "project_state.yaml", {"contract_version": 3, "simulation_contract_version": 1, "calibration_contract_version": 1, "case_id": args.case_id, "exact_prompt": prompt, "stage": "intake", "updated_at": now, "scientific_readiness": "model_selected_not_closed", "software_readiness": "not_applicable", "claim_ceiling": "research_intake_only", "claims": []})
    dump_artifact(case / "problem_contract.yaml", {"contract_version": 3, "case_id": args.case_id, "exact_prompt": prompt, "primary_observables": [], "controlled_inputs": [], "experimental_parameter_ranges": [], "constraints": [], "apparatus_branches": []})
    for filename, empty in {
        "preliminary_query_map.yaml": {"queries": []}, "search_log.yaml": {"searches": []},
        "source_registry.yaml": {"sources": []}, "selected_papers.yaml": {"paper_ids": []},
        "evidence_matrix.yaml": {"claims": [], "negative_evidence_review": []}, "essence_and_chain.yaml": {"essence": "", "causal_chain": []},
        "apparatus_fidelity.yaml": {"geometry_topology": "", "features": [], "observable": "", "parameter_ranges": []},
        "model_registry.yaml": {
            "selection_outcome": "unresolved", "candidates": [], "selected_candidate_ids": [],
            "single_candidate_exception": "", "comparison_table": [],
            "selection_rationale_against_alternatives": "",
            "stopping_decision": {
                "status": "continue", "rationale": "research is in progress", "blocking_items": [],
                "allowed_claim_level": "no_scientific_conclusion", "resumption_conditions": [],
            },
        },
        "parameter_equation_map.yaml": {"mappings": [], "symbols": []},
        "solver_requirements.yaml": {
            "model_closure_status": "unresolved", "fields_and_degrees_of_freedom": [],
            "geometry_and_moving_interfaces": [], "constitutive_laws": [], "multiphysics_coupling": [],
            "expected_regimes": [], "required_outputs": [], "numerical_challenges": [],
            "verification_benchmarks": [], "simpler_tools_insufficient_because": "pending closed model",
            "dimensionless_analysis": {
                "applicability": "not_applicable", "groups": [],
                "regime_identification": "pending physics analysis",
                "not_applicable_justification": "temporary scaffold value; reassess before routing",
            },
        },
        "simulation_handoff.yaml": {
            "simulation_contract_version": 1, "primary_solver": "No numerical solver", "version_policy": "not applicable until a closed model is selected",
            "solver_distribution": "external_reference", "highest_state": "not_applicable",
            "scientific_readiness": "model_selected_not_closed", "software_readiness": "not_applicable", "claim_ceiling": "research_intake_only",
            "state_evidence": [], "official_installation_source": "not applicable",
            "documentation_locator": "pending route", "parameter_mapping": [],
            "boundary_and_initial_conditions": [], "discretization_plan": "pending route",
            "controls": "pending route", "output_extraction": "pending route",
            "verification_plan": [], "validation_plan": [], "validation_chain": [],
            "beginner_readme": "reports/simulation-handoff-readme.md",
        },
        "simulation_route.yaml": {
            "selected_model_id": "unresolved", "selected_route": "analytical_closed_form", "primary_solver": "No numerical solver",
            "openfoam_classification": "Unsuitable", "single_solver_baseline": "pending theory",
            "second_solver_escalation": {"status": "pending theory", "condition": "pending theory"},
            "governing_physics": [], "required_fields": [], "rationale": "pending theory",
            "selection_chain": {
                "phenomenon": "", "physics": [], "governing_equation_ids": [],
                "numerical_requirements": [], "solver": "No numerical solver",
            },
        },
        "simulation_spec.yaml": {"selected_model_id": "", "route": "undecided", "assumptions": [], "quantities_of_interest": [], "validation_requirements": [], "calibration": {"calibration_contract_version": 1, "plan_ref": "calibration_plan.yaml", "claim_ceiling": "no_calibration_or_physical_validation_claim"}},
        "calibration_plan.yaml": {
            "calibration_contract_version": 1,
            "status": "planned",
            "claim_ceiling": "no_calibration_or_physical_validation_claim",
            "not_required_justification": "",
            "dataset": {
                "dataset_id": "pending_dataset", "source": "pending_source", "source_locator": "pending_locator",
                "content_hash": "pending_hash", "unit_system": "pending_units", "variables": [], "observation_index": [],
            },
            "objective": {
                "metric": "pending_metric", "formula": "pending_formula", "direction": "minimize",
                "predeclared_at": "", "target_observables": [], "acceptance_threshold": {"value": 0, "unit": "pending_unit"},
            },
            "parameter_definitions": [],
            "split": {
                "strategy": "predeclared_holdout", "fit_observation_ids": [], "validation_observation_ids": [],
                "fit_group_ids": [], "validation_group_ids": [], "fit_replicate_ids": [], "validation_replicate_ids": [],
                "fit_data_hash": "", "validation_data_hash": "",
            },
            "fit_result": {
                "status": "not_started", "fit_artifact_locator": "", "fit_artifact_hash": "", "fit_data_hash": "",
                "fit_started_at": "", "frozen_at": "", "parameter_values": [], "objective_value": None,
                "residual_summary": {}, "numerical_error": {},
            },
            "independent_validation": {
                "status": "not_started", "dataset_id": "", "data_hash": "", "fit_artifact_hash": "",
                "observation_ids": [], "group_ids": [], "replicate_ids": [], "comparison_method": "",
                "uncertainty_method": "", "acceptance_criterion": "", "objective_value": None,
                "residual_summary": {}, "numerical_error": {}, "performed_at": "",
            },
        },
        "dependency_report.yaml": {"mode": "not_checked", "dependencies": [], "limitations": []},
        "runtime.yaml": {"runtime": {"operating_system": "not_checked", "architecture": "not_checked", "gpu": "not_checked", "solver": "not_selected", "required_packages": []}, "execution": {"entrypoint": "not_selected", "mode": "not_selected"}, "validation": {"required_checks": ["official_smoke_test", "baseline_limit", "convergence_check"]}},
    }.items():
        dump_artifact(case / filename, empty)
    (case / "timeline.ndjson").write_text("", encoding="utf-8")
    for filename, title in {
        "candidate_decision_log.md": "Candidate decision log", "theoretical_report.md": "Theoretical report", "final_handoff.md": "Final handoff", "research_report.md": "Human research report"
    }.items():
        (case / filename).write_text(f"# {title}\n\nPending.\n", encoding="utf-8")
    for filename, contents in {
        "theory-model.md": """# Theoretical model

## Research question

Pending.

## Observable

Pending.

## Independent variables

Pending.

## Proposed mechanism

Pending.

## Governing equations

Pending.

## Derivation

Pending.

## Predicted relationship

Pending.

## Simulation formulation

Pending.

## Limitations

Pending.

## References

Pending.
""",
        "equations.md": "# Equations\n\nPending.\n",
        "assumptions.md": "# Assumptions and regime\n\nPending.\n",
        "literature-notes.md": "# Literature notes\n\nPending.\n",
        "model-validation.md": "# Model validation\n\nPending.\n",
        "variables.csv": "symbol,meaning,unit,status,parameter_class,source\n",
        "predictions.csv": "dependent_variable,independent_variable,value,unit,prediction_basis,parameter_values,provenance\n",
        "parameter-provenance.csv": "parameter,value,unit,status,source_or_method\n",
        "equations.yaml": "{\n  \"equations\": []\n}\n",
    }.items():
        (case / "theory" / filename).write_text(contents, encoding="utf-8")
    for filename, contents in {
        "solver-usage-catalog.md": "# Solver Usage Catalog\n\nPending simulation-stage solver decision.\n",
        "theoretical-model.tex": r"""\documentclass[11pt]{article}
\usepackage{amsmath,booktabs,siunitx,graphicx}
\title{Theoretical Model: TODO}
\date{\today}
\begin{document}
\maketitle
\section{Problem and research question}
TODO
\section{Observables and variables}
TODO
\section{Physical mechanism and model choice}
TODO
\subsection{Mandatory model comparison}
\begin{tabular}{lllll}
Candidate & Explains & Limitations & Required parameters & Experimental discriminator\\
TODO & TODO & TODO & TODO & TODO
\end{tabular}
\section{Assumptions and validity range}
TODO
\section{Governing equations and derivation}
TODO

\subsection{Equation lineage}
Source $\rightarrow$ Original equation $\rightarrow$ Assumptions $\rightarrow$ Adaptation $\rightarrow$ Final model.
\section{Main prediction and limiting cases}
TODO
\section{Theory-to-solver mapping}
TODO
\section{Calculated example or prediction}
TODO
\section{Limitations and references}
TODO
\end{document}
""",
    }.items():
        (case / "reports" / filename).write_text(contents, encoding="utf-8")
    (case / "reports" / "simulation-handoff-readme.md").write_text(
        "# Simulation handoff\n\nNo solver has been selected or executed.\n", encoding="utf-8"
    )
    for filename, contents in {
        "solver-inventory.yaml": '{"batch_id":"pending","solvers":[]}\n',
        "installation-record.md": "# Installation record\n\nPending simulation-stage solver decision.\n",
        "software-citations.bib": "% Pending simulation-stage solver decision.\n",
        "licenses.md": "# Software licenses\n\nPending simulation-stage solver decision.\n",
    }.items():
        (case / "provenance" / filename).write_text(contents, encoding="utf-8")
    for filename in ("openfoam_design_review.yaml", "case_manifest.yaml", "mesh_validation.yaml", "run_results.yaml"):
        dump_artifact(case / "openfoam" / filename, {"status": "not_started", "limitations": ["This artifact is a scaffold placeholder, not a completed stage."]})
    dump_artifact(case / "openfoam" / "validation_report.yaml", {
        "status": "not_started", "checks": [], "accepted_for_scientific_use": False,
        "numerical_verification": {"status": "not_started"},
        "parameter_calibration": {"status": "not_started"},
        "physical_validation": {"status": "not_started"},
        "limitations": ["This artifact is a scaffold placeholder, not a completed stage."],
    })
    print(case)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
