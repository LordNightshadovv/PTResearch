# Model card

```yaml
candidate_id: C1
name: ""
status: selected_primary | selected_alternative | retained_component | filtered | unresolved
candidate_type: whole_chain | component | correction | empirical
provenance: named_theory | literature_integrated | constructed_first_principles | empirical
essence_claim: ""
causal_chain: []
chain_coverage_fraction: 0.0
dominant_link: ""
governing_equations:
  - equation: ""
    equation_type: law | theorem | model_family | constitutive_relation | governing_equation | approximation | empirical_correlation
    provenance_class: verbatim_source_equation | adapted_source_equation | derived_from_cited_principles | original_derivation | empirical_fit_from_data | assumed_placeholder_pending_measurement
    source_claims: []
    derivation_steps: []
    transformation_map: {}
    lineage:
      source_basis: []
      original_equation: ""
      assumptions: []
      transformations_made: []
      final_equation: ""
      adaptation_justification: ""
    variables_and_units: ""
    assumptions: ""
    validity_regime: ""
boundary_conditions: []
initial_conditions: []
free_parameters: []
measurable_parameters: []
latent_or_difficult_parameters: []
dimensionless_groups: []
limiting_cases: []
main_predictions: []
discriminating_predictions: []
validation_evidence: []
contradicting_evidence: []
known_failures: []
equations_unavailable_reason: ""
simulation_method_suggestion: ""
confidence: high | medium | low | unresolved
selection_or_filter_reason: ""
residual_use: ""
reconsideration_condition: ""
```

Also record `candidate_kind`, causal mechanism, governing equation IDs, validity range, predicted
observables, identifiable parameters, decisive falsifier, discriminating experiment,
computational cost, solver needs, evidence quality, apparatus-fidelity result, and comparison
scores. These fields are mandatory in contract-version-2 root cases.

For contract-version-3 root cases, add one five-column `comparison_table` row for every serious
candidate, a supporting/opposing evidence review, a selection rationale against alternatives, and
an explicit continuing or justified-stop decision.

## Compatibility audit for stacks

| Interface | Upstream output [unit] | Downstream input [unit] | Coordinates/sign | Domain | Regime overlap | Boundary compatibility | Result |
|---|---|---|---|---|---|---|---|

## Magnitude check

State the scaling estimate, input values and provenance, expected order of magnitude, observed/required scale, and conclusion. Mark missing inputs rather than guessing.

## Decision score

Record each weighted sub-score and one-sentence rationale. Apply hard gates first; a filtered candidate remains filtered regardless of score.
