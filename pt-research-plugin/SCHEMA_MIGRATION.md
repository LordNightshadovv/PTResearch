# Scientific contract migration

## Compatibility policy

Version-1 cases continue to validate under the legacy artifact contract. New scaffolds set
`contract_version: 2` in `project_state.yaml` and `problem_contract.yaml`. Adding that value to an
older case opts it into all v2 gates; migrate the complete set atomically rather than adding the
version flag alone.

## New required artifacts

| Artifact | Purpose |
|---|---|
| `apparatus_fidelity.yaml` | Reconstruct the apparatus and compare each decisive feature with the model. |
| `evidence_matrix.yaml` | Gate important claims by directness and sufficiency, not citation count. |
| `theory/equations.yaml` | Register every equation, locator, derivation/transformation, closure, and produced quantity. |
| `parameter_equation_map.yaml` | Trace every experimental control through mathematics to a requested observable. |
| `solver_requirements.yaml` | Derive numerical needs from closed physics before choosing software. |
| `simulation_handoff.yaml` | Describe the external-solver adapter and highest evidenced state. |

## Changed fields

- `problem_contract.yaml`: add `contract_version`, `controlled_inputs`, and
  `experimental_parameter_ranges`.
- `project_state.yaml`: add `contract_version`; completed simulation claims add `evidence_ids`.
- `model_registry.yaml`: add `selection_outcome`, candidate kind and complete comparison fields,
  retained-competitor discriminator, and optional `single_candidate_exception`. An unresolved or
  no-justified outcome has no selected IDs.
- `source_registry.yaml`: add verified bibliographic identity and `directness`.
- `simulation_route.yaml`: add `solver_requirements_id`.

## Equation provenance conversion

Map older labels deliberately; do not convert by string replacement when the evidence is unclear:

| Legacy label | V2 destination |
|---|---|
| `source_verbatim_or_equivalent` | `verbatim_source_equation` only after source/locator verification; otherwise unresolved |
| `standard_textbook_relation` | `derived_from_cited_principles` with exact starting-principle locator |
| `derived_in_this_report` | `original_derivation` with cited starting principles and shown steps |
| `empirical_fit` | `empirical_fit_from_data` with dataset, fit method, uncertainty, and range |

An apparatus-specific change to a sourced equation is `adapted_source_equation`, not verbatim.
Complete its transformation map. Use `assumed_placeholder_pending_measurement` only when the report
clearly marks the placeholder and blocks unsupported prediction.

## Migration sequence

1. Preserve the exact prompt and add controlled inputs, observables, and ranges.
2. Reconstruct the apparatus and resolve/block contradicted decisive features.
3. Re-audit sources and exact locators; record unavailable-locator searches honestly.
4. Build the candidate pool and comparison; permit unresolved selection.
5. Convert equations and register symbols, closures, produced quantities, and falsifiers.
6. Complete the parameter-to-equation map and ensure every requested observable is produced.
7. Complete claim evidence and remove context-only support for central quantitative laws.
8. Derive solver requirements; only then update route/specification.
9. Create the external-solver handoff and set only the highest evidenced state.
10. Update the human report with apparatus fidelity and nearby equation provenance.
11. Set both contract versions to 2 and run `scripts/validate_artifacts.py CASE`.

No migration step grants evidence for solver installation, case generation, execution,
verification, or validation.

## Version 2 to version 3

Version-2 cases remain readable under their original contract. New scaffolds set
`contract_version: 3`. To migrate, update both version fields only after completing these records:

1. Add `lineage` to every model equation with source title/authors, exact-locator status, original
   equation, assumptions, transformations, final equation, and adaptation justification.
2. Add `comparison_table`, `selection_rationale_against_alternatives`, and `stopping_decision` to
   `model_registry.yaml`.
3. Add `evidence_direction` to claims and `negative_evidence_review` for every serious candidate.
4. Add `parameter_class` to every symbol in `parameter_equation_map.yaml`.
5. Add `dimensionless_analysis` to `solver_requirements.yaml`, including an explicit justification
   when not applicable.
6. Add the physics-first `selection_chain` to `simulation_route.yaml`.
7. Add `validation_chain` to numerical `simulation_handoff.yaml`.
8. Put the five-column comparison and equation-lineage chain in the reader-facing report.
9. Set both contract versions to 3 and run `scripts/validate_artifacts.py CASE`.

A stopped v3 case uses one of the three justified-stop statuses, has no selected candidate or
solver, states its claim ceiling, and preserves concrete resumption conditions. Migration does not
retroactively validate sources, equations, software, simulations, or experiments.

## Runnable simulation contract revision

This revision does not rewrite the 2027 archive. Every continuing v2/v3 case that selects a
numerical route must migrate its simulation handoff and package records:

1. Add simulation_contract_version: 1, scientific_readiness, software_readiness, and claim_ceiling
   to project_state.yaml and simulation_handoff.yaml.
2. Classify documentation-only old states (solver_selected_only,
   installation_package_prepared, or parameter_handoff_validated) as handoff_only; never map
   them to runnable_synthetic.
3. Replace echo-only check_system.sh and unconditional run_gate.sh with real platform,
   dependency, input, and evidence checks.
4. Add linux-simulation/simulation_package_manifest.json, parameters.schema.json,
   examples/synthetic.json, executable src/ or native case, generate_case.py, run.sh,
   extract_results.py, tests/, numerical-verification.json, parameter-map.json,
   equation-lineage.json, and receipts/.
5. Replace placeholders in parameter mappings with concrete solver fields/functions and add
   implementation file/function, units, notation conversion, discretization, and assumptions.
6. Set runnable_synthetic only after the deterministic synthetic command returns zero and writes a
   complete receipt containing package/solver version, revision, hashes, and validation state.
   Set runnable_apparatus only after a measured input has provenance and uncertainty records and
   a separate apparatus receipt exists. Set numerically_verified only after the three-level plan is actually
   executed and passes. Experimental comparison additionally needs held-out measurements and
   uncertainty.

The validator keeps legacy scientific artifacts readable, but a continuing numerical case cannot
pass the complete runnable-package contract until this migration is complete. Use the allow-partial
flag only to inspect an old handoff; its output explicitly says handoff-only.
