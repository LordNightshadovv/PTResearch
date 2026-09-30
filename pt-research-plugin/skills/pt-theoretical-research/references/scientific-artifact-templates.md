# Scientific artifact templates

Use the root JSON schemas as authoritative. These compact examples show intent.

## Apparatus fidelity

```yaml
geometry_topology: "..."
features:
  - apparatus_feature: "cavity is open to atmosphere"
    model_representation: "pressure outlet connected to ambient domain"
    match_status: matched
    justification: "..."
    consequence_if_wrong: "sealed compression would create a spurious restoring force"
    required_measurement_or_source: "apparatus drawing and vent clearance"
observable: "..."
parameter_ranges: [{name: "...", unit: "...", range: "..."}]
```

## Candidate and discriminator

Each non-component candidate records `candidate_kind`, causal mechanism, equation IDs, assumptions
and validity, predicted observables, identifiable parameters, decisive falsifier, feasible
discriminating experiment with `competitor_id` and `predicted_difference`, computational cost,
solver needs, evidence quality, and comparison scores. Separate selected working baseline,
retained competitors, rejected candidates, and unresolved choice.

Add `comparison_table` with one row per serious candidate and the fields `candidate_id`,
`explains`, `limitations`, `required_parameters`, and `experimental_discriminator`. Add a
`selection_rationale_against_alternatives` and a `stopping_decision`.

## Equation provenance

```yaml
id: eq-example
latex: "..."
role: constitutive
provenance_class: adapted_source_equation
source_claims:
  - source_id: S3
    supports: [functional_form, coefficient, validity_range]
    retrieval_status: verified_full_text
    exact_locator: {section: "3.2", pages: "114-116", equation: "Eq. (7)"}
    locator_verification: {status: verified_against_source, evidence: "saved text/page audit"}
    transformation_notes: "..."
derivation_steps: ["..."]
assumptions: ["..."]
dimensional_check: "..."
limiting_cases: ["..."]
falsifier: "..."
symbols: ["..."]
produces: ["requested observable or intermediate state"]
closes_variables: ["history variable, if any"]
transformation_map:
  source_equation: "..."
  source_notation: "..."
  substitutions_or_approximations: ["..."]
  apparatus_specific_changes: ["..."]
  resulting_equation: "..."
  dimensional_check: "..."
  new_assumptions: ["..."]
lineage:
  source_basis:
    - source_id: S3
      source_title: "Verified source title"
      source_authors: ["Author One", "Author Two"]
      exact_locator: {availability: verified, section: "3.2", pages: "114-116", equation: "Eq. (7)"}
  original_equation: "..."
  assumptions: ["..."]
  transformations_made: ["..."]
  final_equation: "..."
  adaptation_justification: "..."
```

For `not_retrieved` or `not_available`, replace the exact locator with `locator_searches` and
`support_limit`. For `original_derivation`, provide at least two nontrivial derivation steps and
`starting_principles`, each with `source_id` and `exact_locator`.

## Parameter mapping

```text
experimental parameter → symbol → equation/term/boundary ID
→ intermediate state → requested observable
```

Register every symbol with meaning, SI unit, one of `controlled`, `measured`, `sourced`, `fitted`,
`calculated`, or `observable`, uncertainty/provenance, admissible range, and history-variable flag.
Also assign exactly one v3 `parameter_class`: `control_variable`, `measured_state_variable`,
`material_constant`, or `hidden_uncertainty_source`.
