# Scientific contract version 2

Use this contract for every newly scaffolded case. Older version-1 artifacts remain readable, but
advancing or revising them requires migration to version 2.

## Required order and blocking gates

```text
official prompt
→ apparatus reconstruction and fidelity audit
→ evidence matrix and equation-locator search
→ candidate-model pool
→ mechanistic closure and parameter-to-equation map
→ non-prescriptive model comparison
→ solver requirements
→ solver selection
→ external-solver adapter/case package
→ numerical verification
→ physical validation
```

Do not endorse a candidate with an apparatus contradiction, an unclosed state/history variable, an
unmapped control, a missing terminal observable, a central quantitative claim supported only by
contextual evidence, or a fabricated/unverified locator. The selection outcome may be `unresolved`
or `no_candidate_justified`.

## Required artifacts

- `apparatus_fidelity.yaml`: geometry/topology, open/sealed/vented/connected/deformable/moving
  volumes, masks/forces/contacts/interfaces/sensors, distances/orientations/clearances/boundaries,
  observable, parameter ranges, and per-feature model match/risk/measurement.
- `model_registry.yaml`: minimal analytical baseline where defensible, serious competitors,
  higher-fidelity formulation only for a named limitation, useful empirical falsification baseline,
  comparison rubric, retained/rejected ledger, and single-candidate exception when unavoidable.
- `theory/equations.yaml`: every displayed law/correlation/boundary/value with provenance class,
  granular source locator, transformation map or derivation, assumptions, dimensions, limits,
  falsifier, symbols, closure variables, and produced quantities.
- `parameter_equation_map.yaml`: experimental parameter → symbol → equation/term/boundary →
  intermediate state → requested observable; symbol unit/status/range/uncertainty/provenance.
- `evidence_matrix.yaml`: claim importance, source IDs, source directness, and sufficiency status.
- `solver_requirements.yaml`: physics-derived fields, geometry/interfaces, constitutive laws,
  coupling, regimes, outputs, stiffness/discontinuities, benchmarks, and why simpler tools fail.
- `simulation_handoff.yaml`: external solver/version/install/docs, package state, state receipts,
  parameter/input map, conditions, discretization/controls, output extraction, verification,
  validation, and beginner README.

## Equation provenance

Use exactly one class:

- `verbatim_source_equation`
- `adapted_source_equation`
- `derived_from_cited_principles`
- `original_derivation`
- `empirical_fit_from_data`
- `assumed_placeholder_pending_measurement`

For full text, record the most granular available chapter/section/page/equation/appendix/table/
figure/anchor and verification against the source. A homepage or abstract is not an equation
locator. If a locator is unavailable, search a primary/canonical alternative, record searches,
use `not_retrieved` or `not_available`, and state exactly what remains supported only at metadata
or abstract level. Never infer or invent locators.

For an adapted equation, record source equation and notation, substitutions/approximations,
apparatus-specific changes, resulting equation, dimensional check, and new assumptions. For an
original derivation, cite each starting principle with an exact locator and show nontrivial steps.

## Evidence sufficiency and model comparison

Seek, when available: direct apparatus/phenomenon evidence, canonical theory, constitutive/property
data, measurement method, and numerical-method verification. Use source directness values:
`direct_same_apparatus`, `direct_same_mechanism`, `canonical_theory`, `parameter_data`,
`numerical_method`, `contextual_only`, or `official_prompt_only`. Gate by claim importance, not
citation count.

Compare candidates on apparatus fidelity, equation/constitutive closure, identifiability,
observable prediction, limiting cases, direct literature, discriminating experiments,
implementability, uncertainty, and model-form risk. Every retained competitor needs a feasible
discriminator with a predicted difference in scaling, threshold, spectrum, phase, hysteresis,
pattern, transient, limiting behavior, or parameter dependence. Error fitting alone is insufficient
without identifiability and overfitting analysis.

## Simulation package semantics

Treat a Linux package as an adapter/case package paired with independently installed software. It
need not embed the solver. Declare only the highest evidenced state:

1. `solver_selected_only`
2. `installation_package_prepared`
3. `parameter_handoff_validated`
4. `solver_case_generator_prepared`
5. `solver_native_case_generated`
6. `smoke_tested`
7. `executed`
8. `numerically_verified`
9. `experimentally_validated`

Require receipts for every claimed state from `smoke_tested` onward. Keep numerical verification
(limits, benchmarks, conservation/residuals, mesh/time/sampling sensitivity, constraint/energy
checks) separate from physical validation against independent measurements and uncertainty.

The runnable-simulation extension adds separate scientific_readiness and software_readiness fields.
Legacy pre-run states classify as handoff_only. A continuing case needs executable implementation,
separated inputs, a synthetic benchmark, real checks/gates, result extraction, a machine-readable
verification plan, equation/code traceability, and receipts before runnable_synthetic. A solver
runtime smoke receipt alone is not a case-runnable claim.

## Batch and cross-artifact rules

The validator must find every batch problem in the solver matrix, one explicit staged-workflow
explanation for any solver difference, every claimed simulation route paired with its handoff,
consistent symbols/units/equation IDs/observables, no local absolute paths, and no unsupported
installation/generation/execution/convergence/validation claim.
