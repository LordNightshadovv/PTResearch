# State machine and gates

Each transition requires a validator result and one append-only timeline event.

| Target stage | Required inputs | Required outputs | Allowed next specialists |
|---|---|---|---|
| `prompt_contracted` | exact prompt | `problem_contract.yaml` | `pt-theoretical-research` |
| `literature_discovery` | contract, query map | search log, source registry | K-Dense bridge |
| `literature_screened` | source registry | screening log, synthesis | DeerFlow SLR bridge |
| `evidence_audited` | selected papers | paper cards, evidence matrix | DeerFlow paper-review bridge |
| `candidate_models_selected` | apparatus fidelity, positive/negative evidence matrix, essence/chain, mandatory candidate-comparison table, equation lineage, parameter classes/map, stopping decision | decision log, theory report, closure or justified-stop result | `pt-simulation-router` or handoff |
| `simulation_routed` | closed selected model, dimensionless regime analysis, solver requirements | `simulation_route.yaml` with physics-first selection chain, primary solver, and OpenFOAM classification | `pt-simulation-packager` |
| `simulation_specified` | route, validation targets, chosen platform, preregistered acceptance rule, error budget, coverage matrix, `calibration_plan.yaml` v1 with status `planned` or `not_required` | `simulation_spec.yaml`, experiment-to-simulation validation chain, runtime/package plan, frozen criterion and input manifest | OpenFOAM audit or honest solver-specific handoff |
| `package_implemented` | closed model, route, package template, frozen acceptance/input manifest | executable source/native adapter, separated input schema, generator, extractor, state-aware checks, verification plan, reproducibility receipt plan | synthetic smoke gate |
| `synthetic_smoke_tested` | implementation-ready package, synthetic input | deterministic output, machine-readable results, complete synthetic receipt | case generation or apparatus gate |
| `case_generated` | validated spec, dependencies, implementation package | case manifest and generated case | mesh gate |
| `baseline_executed` | accepted generated case, frozen inputs, predeclared criterion | run results, exact-command receipt, input/output hashes, warnings/errors, and coverage status | mesh/time-step gate |
| `numerically_validated` | converged baseline and machine-readable refinement evidence | `validation_report.yaml.numerical_verification.status: passed`, finite criterion/error evidence, receipts, and numerical uncertainty separate from model-form error | calibration or physical validation |
| `physically_validated` | `numerically_validated`, held-out comparison, `calibration_plan.yaml` v1 status `physically_validated`, disjoint fit/validation IDs/groups/replicates and data hashes | `independent_validation.status: passed`, frozen-fit binding or frozen model/configuration and input binding when no parameters are fitted, uncertainty-aware acceptance, and `validation_report.yaml.physical_validation.status: passed` with independent evidence | parameter study |
| `handoff_complete` | all requested accepted outputs and explicit coverage/claim ceiling | final handoff listing accepted, failed, unavailable, and untested capabilities with provenance | none |

Never move the stage forward when validation fails. Record the attempted transition and failure reason without deleting earlier state.

Stage names are claims, not progress labels. Before accepting a transition, compare
`project_state.yaml`, the simulation handoff, calibration plan, validation report, and receipts;
reject contradictory states such as `physically_validated` with only a synthetic receipt. A
successful subprocess, a populated report, a plausible hash string, or a generic reference
comparison cannot advance a stage. Preserve the failed attempt and lower the claim ceiling.

Numerical validation concerns discretization, solver, benchmark, and refinement evidence. Physical
validation concerns an independent held-out comparison against measured or otherwise justified
reference data. Calibration fits parameters and must never reuse its fit records as physical
validation. Every transition must retain the predeclared criterion, error-budget components,
coverage rows, exact commands, input/output hashes, and evaluator or reviewer identity.

A case may terminate with a justified-stop record after literature screening, evidence audit,
candidate construction, or model comparison. Set no selected solver, preserve unresolved
candidates and evidence gaps, and append the stop plus resumption conditions to `timeline.ndjson`.

If a dependency, dataset, calibration fit, independent evaluator, or validation branch is
unavailable, return a partial state with the highest supported claim ceiling, the blocked artifact,
the exact missing evidence, and the legal resumption condition. Legacy cases without
`calibration_plan.yaml` remain readable but may not claim a new calibration or physical-validation
stage until they explicitly migrate to `calibration_contract_version: 1`.
