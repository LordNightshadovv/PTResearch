# PT Research plugin general revision report

Date: 6 August 2026  
Release: 0.7.0  
Scope: reusable plugin only; the 2027 archive was not regenerated or repaired.

## Outcome

The plugin now adds scientific contract v3 gates for complete equation lineage, a mandatory
five-column alternative-model comparison, positive and negative evidence, dimensionless regime
analysis, four-way parameter metadata, a physics-first solver-selection chain, and an
experiment-to-simulation validation chain. Model selection can end with a justified stop for an
unresolved mechanism, insufficient literature, or missing data. Numerical verification remains
separate from physical validation.

This revision also adds a runnable simulation contract. Scientific and software readiness are
separate; handoff-only plans cannot be called runnable. Continuing numerical routes now require a
real executable/native implementation, separated inputs, a synthetic benchmark, real system and
run gates, machine-readable extraction, equation/code traceability, a concrete verification plan,
and receipts.

The former year-specific 2027 routing table remains absent from the general router. Existing
version-1 and version-2 artifacts remain readable; newly scaffolded cases use contract version 3
and cannot advance through the new validator until their scientific records are complete.

## Changed files and reasons

### Plugin and documentation

- `.codex-plugin/plugin.json` — release 0.7.0 and revised capability description.
- `README.md` — documents the apparatus-first, closure-before-solver workflow, v2 artifacts, and runnable simulation contract.
- `PLUGIN_REVISION_REPORT.md` — this implementation inventory.
- `SCHEMA_MIGRATION.md` — version-1 to version-2 migration guide.
- `validation-logs/2026-07-26-general-revision.log` — retained validation receipts.

### Schemas

- `schemas/apparatus-fidelity.schema.json` — apparatus reconstruction and per-feature match/risk.
- `schemas/equations.schema.json` — six provenance classes, locators, transformations, closure,
  dimensions, limits, and falsifiers.
- `schemas/evidence-matrix.schema.json` — claim importance, source directness, and sufficiency.
- `schemas/parameter-equation-map.schema.json` — control-to-symbol-to-equation-to-observable chain
  and complete symbol metadata.
- `schemas/solver-requirements.schema.json` — physics-derived numerical requirements before route.
- `schemas/simulation-handoff.schema.json` — external-solver adapter semantics, separate
  scientific/software readiness, and legacy/new evidence states.
- `schemas/problem-contract.schema.json` — controlled inputs, ranges, and contract version.
- `schemas/project-state.schema.json` — contract version and evidence IDs for completed claims.
- `schemas/model-registry.schema.json` — candidate kinds, comparison records, retained competitors,
  unresolved outcomes, and single-candidate exception.
- `schemas/source-registry.schema.json` — bibliographic identity and source-directness classes.
- `schemas/simulation-route.schema.json` — link to the solver-requirements artifact, including
  Python/SciPy numerical routes.
- `schemas/simulation-package.schema.json`, `schemas/simulation-parameters.schema.json`, and
  `schemas/run-receipt.schema.json` — executable package, separated inputs, and receipt contracts.

### Deterministic implementation

- `scripts/scientific_contract.py` — new v2 schema and cross-artifact validator. It blocks apparatus
  contradictions, incomplete candidate records, open state variables, unmapped controls,
  missing observables, weak quantitative evidence, missing/unverified/fabricated locators,
  incomplete equation transformations, solver mismatches, unsupported state claims, missing Linux
  adapters, batch omissions, stale coverage, broken shared references, irreproducible predictions,
  and local absolute paths.
- `scripts/validate_artifacts.py` — invokes v2 gates when `contract_version >= 2` while retaining v1
  compatibility.
- `scripts/scaffold_research_case.py` — scaffolds every new case with v2 artifacts and explicit
  unresolved/pending states; accepts the orchestrator-documented `--prompt-file` path as well as
  inline `--prompt` and rejects empty prompts.
- `scripts/validate_plugin.py` — validates the expanded 22-schema set and six locked numerical
  runtimes.

### Orchestration and workflow skills

- `skills/pt-orchestrator/SKILL.md` — apparatus and closure gates, evidence-driven unresolved
  selection, solver requirements, and simulation-state semantics.
- `skills/pt-orchestrator/references/scientific-contract-v2.md` — authoritative reusable contract.
- `skills/pt-orchestrator/references/state-machine.md` — v2 prerequisites at selection/routing.
- `skills/pt-orchestrator/references/specialist-registry.yaml` — new artifacts in specialist I/O.
- `skills/pt-theoretical-research/SKILL.md` — apparatus reconstruction, candidate pool, exact
  provenance, closure, mapping, and nearby report citations.
- `skills/pt-theoretical-research/references/scientific-artifact-templates.md` — concise v2 examples.
- `skills/pt-theoretical-research/references/human-facing-theoretical-pdf.md` — apparatus table and
  nearby equation provenance.
- `skills/pt-theoretical-research/references/latex-theoretical-model.md` — exact locator and
  unavailable-locator behavior.
- `skills/pt-theoretical-research/references/mathematical-audit-checklist.md` — new closure and
  provenance checks.
- `skills/pt-theoretical-research/references/model-card-template.md` — new provenance and comparison
  fields.
- `skills/pt-theoretical-research/references/source-quality-and-search.md` — source directness,
  locator search, and six provenance classes.
- `skills/pt-theoretical-research/references/schemas.md` — v2 directory/artifact map.
- `skills/pt-theoretical-research/references/workflow-details.md` — apparatus gate, candidate pool,
  and closure procedure.
- `skills/pt-simulation-router/SKILL.md` — closure and solver-requirements gate; staged workflows
  only for distinct closed physics.
- `skills/pt-simulation-router/references/2027-solver-routing.md` — removed because reusable routing
  must not encode year-specific conclusions.
- `skills/pt-simulation-packager/SKILL.md` — external-solver adapter semantics, four execution
  modes, state evidence, handoff contents, and no-run truthfulness.
- `skills/pt-report-renderer/SKILL.md` — v2 apparatus and equation-provenance rendering contract.

### Tests

- `tests/test_scientific_contract.py` — 15 positive/negative v2 tests, including every requested
  failure class, a complete adapted equation, an original derivation, an honest unavailable
  locator, an unresolved selection, an external solver reference, and a generated report containing
  an exact locator.
- `tests/test_scaffold_research_case.py` — verifies prompt-file parsing, exact prompt retention, v2
  opt-in, and empty-prompt refusal.
- `tests/test_single_solver_routing.py` — replaces year-specific route counts with general
  closure-before-routing assertions.
- `tests/test_plugin_structure.py` — expects and parses all 22 shared schemas.
- `tests/test_runnable_simulation_contract.py` — generates and executes synthetic packages for
  every supported route, verifies measured-input advancement, and rejects the former handoff
  failure pattern.

## Remaining limitations

## Runnable simulation contract revision

- scripts/runnable_contract.py validates package implementation, state separation, input categories,
  concrete mappings, equation/code traceability, verification plans, and receipts.
- tools/simulation-package/generate_package.py provides executable synthetic templates for optics,
  FEM, OpenFOAM, Chrono, YADE, ODE, optimization, and reduced-order routes.
- schemas/simulation-package.schema.json, schemas/simulation-parameters.schema.json, and
  schemas/run-receipt.schema.json define the manifest, separated inputs, and receipt records.
- The OpenFOAM exporter and solver-runtime package no longer emit echo-only launchers or mark a
  runtime-only platform receipt as a runnable scientific case.
- tests/test_runnable_simulation_contract.py covers the former 2027 handoff failure pattern and
  executes a synthetic example for every supported generated route.

- Locator verification records whether a source-page audit occurred; the validator cannot
  independently determine truth from an inaccessible publication.
- The v2 cross-artifact gate uses the plugin's deterministic JSON-compatible YAML subset.
- Existing v1 cases are not silently rewritten; they require explicit migration before new-stage
  acceptance.
- External solver execution and solver-specific scientific validation still require the locked
  runtime receipt plus route-specific evidence. A generated adapter is not evidence of execution,
  numerical verification, or experimental validation.
- No 2027 archive regeneration was performed in this task.
