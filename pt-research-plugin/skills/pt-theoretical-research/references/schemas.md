# Case schemas

Use UTF-8, human-readable Markdown/CSV/YAML, stable IDs, and version-control-friendly ordering.

## Directory

```text
research_cases/<slug>/
├── prompt.md
├── problem_contract.yaml
├── apparatus_fidelity.yaml
├── essence_and_chain.md
├── search_log.csv
├── sources.yaml
├── papers/<paper-id>.md
├── paper_matrix.csv
├── model_registry.yaml
├── parameter_equation_map.yaml
├── theory/equations.yaml
├── evidence_matrix.yaml
├── solver_requirements.yaml
├── simulation_handoff.yaml
├── candidate_decision_log.md
├── final_report.md
└── handoff.md
```

## Problem contract

```yaml
case_slug: ""
source: ""
year: null
problem_number: null
access_date: ""
exact_prompt: |-
  ""
verbs: []
system_boundary: ""
controlled_inputs: []
expected_observables: []
prompt_defined_objectives: []
constraints: []
apparatus_ambiguities: []
excluded_assumptions: []
classification_scores:
  explanation: 0
  design: 0
  optimization: 0
  mechanism_identification: 0
```

## Sources registry

```yaml
sources:
  - paper_id: ""
    title: ""
    authors: []
    year: null
    venue: ""
    doi_or_stable_id: ""
    url: ""
    source_tier: ""
    access_level: ""
    identity_verified: false
    inclusion_reason: ""
```

If no stable identifier exists, state `not_available` and record the identity-verification method. Never fabricate an identifier.

## Model registry

```yaml
selection_outcome: insufficient_evidence_to_select
candidates:
  - candidate_id: C1
    name: ""
    status: unresolved
    candidate_type: whole_chain
    provenance: constructed_first_principles
    chain_links: []
    equations: []
    equations_unavailable_reason: "evidence not yet retrieved"
    selection_or_filter_reason: ""
```

Allowed statuses and outcomes are defined in [model-card-template.md](model-card-template.md). Every candidate mentioned in notes or report must occur here, and every registry candidate must be named in the final report.

## Paper matrix columns

```text
paper_id,title,source_tier,directness,access_level,causal_links,model_families,validation,limitations,relevance
```

## Finalization convention

Draft scaffolds contain `TODO` markers and intentionally fail validation. Before finalization, replace all placeholders, set an explicit selection outcome, verify central citations/equations, and ensure every registry candidate appears by ID or exact name in the report.

The root plugin schemas are authoritative for contract version 3. Version-2 and legacy standalone
layouts remain readable under their original contracts, but migrate them atomically before
claiming v3 compliance or advancing under v3 gates.
