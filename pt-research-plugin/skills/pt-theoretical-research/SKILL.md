---
name: pt-theoretical-research
description: Build PT artifact records and standalone human-facing theoretical reports for IYPT/CYPT research, including exact prompt contracts, phenomenon essence, causal chains, quantitative models, literature evidence, mathematical audits, model selection, and rejected-candidate ledgers. Normally invoked by pt-orchestrator after case initialization; does not run simulations or select a solver route.
---

# PT Theoretical Research

Build an auditable first-stage physics case that explains the phenomenon from controlled input to measured observable and recommends defensible working models. Preserve uncertainty and negative results. Do not run simulations or design a full experiment.

## Start the case

1. Preserve the official prompt verbatim. Record source, year, problem number, and access date when known.
2. Create or resume the orchestrator-owned run directory. For standalone inspection, use `python scripts/scaffold_case.py <slug> [--prompt-file FILE] [--root DIR]`.
3. Read [workflow-details.md](references/workflow-details.md) completely before researching.
4. Read [source-quality-and-search.md](references/source-quality-and-search.md) before searching or evaluating sources.
5. Use the templates and root plugin schemas; do not invent incompatible status values or omit registry entries.
6. Route broad retrieval, bounded synthesis, and deep-paper audit through the three upstream literature bridges only when the orchestrator registry permits it. Reconcile their outputs; never concatenate reports as synthesis.

When apparatus ambiguity changes the causal chain, create explicit branches. Ask the user only if branching cannot preserve meaningful progress.

## Work in causal order

Execute these phases, revisiting earlier work when evidence changes:

1. **Contract and apparatus:** extract the prompt verbs, system boundary, controlled inputs,
   observables, objectives, constraints, ambiguities, and excluded assumptions. Reconstruct geometry,
   topology, open/sealed/vented/connected/deformable/moving volumes, masks, forces, contacts,
   interfaces, sensors, distances, orientations, clearances, boundaries, parameter ranges, and
   measurement procedure in `apparatus_fidelity.yaml`.
2. **Provisional essence:** state the initiating cause, central coupling/transduction, response controlling the observable, and relevant amplification, suppression, instability, or selection. Mark it `well_supported`, `provisional`, `competing_hypotheses`, or `unresolved`.
3. **Causal hypotheses:** write a main whole-chain hypothesis plus zero to three alternatives. Use input/energy source → coupling/transduction → state/field evolution → amplification/suppression/selection → observable generation → measured observable.
4. **Vocabulary and queries:** translate prompt language into canonical terms, synonyms, apparatus terms, mechanisms, mathematical frameworks, analogies, competing mechanisms, and false-positive exclusions.
5. **Breadth-first survey:** search the exact phenomenon, then integrated whole-chain models, unresolved links, analogous systems, mathematical validity, measurements/discrimination, and criticism/failure. Bound the search and log every query, filter, date, result count, refinement, empty result, inaccessible source, and tool failure.
6. **Structured extraction:** create one paper card per retained source. Classify source and paper type before judging it. Extract claims with what/where/evidence/caveat. Never infer full-text details from an abstract.
7. **Candidate construction:** before selection, build a defensible pool: a minimal analytical
   baseline, a serious competing mechanism/constitutive model, higher fidelity only for a named
   limitation, and an empirical baseline when useful. If physics admits only one, record the
   evidence-based exception. Preserve each candidate's equations, regime, observables,
   identifiability, falsifier, discriminator, cost, solver needs, and evidence quality. For every
   serious candidate, state the observation or metric that would reject it, the acceptance
   threshold for that test, and which competing candidate would become preferable. Complete the
   five-column comparison table before selection.
8. **Mathematical audit and closure:** check dimensions, definitions/units, provenance, boundary and
   initial conditions, limiting cases, signs, regime restrictions, identifiability, magnitude, and
   observable mapping. Block every unclosed history/state variable, verbally described but absent
   coupling, unmapped experimental control, implicit solver coefficient, or reduced model that
   removes a plausible causal degree of freedom. Record relevant dimensionless groups and the
   regime they identify; justify a `not_applicable` decision. Draft the uncertainty/error budget
   and observable × regime × apparatus-branch coverage matrix; distinguish measurement,
   calibration, numerical, sampling, and model-form error.
9. **Decision ledger:** apply hard gates before advisory scores. Keep every candidate in the registry; name and justify every filtered candidate and state its residual use and reconsideration condition.
   Freeze the proposed acceptance rule, falsifier, data split, uncertainty method, and claim
   ceiling before fitting or simulation. A later threshold or model change is a new decision event.
10. **Theory package, LaTeX report, selection, and handoff:** complete the required `theory/` package and `reports/theoretical-model.tex` before asking for a human-facing PDF. The LaTeX source is a standalone detailed theoretical-model section at scientific-paper level, not an equation list or a pointer to internal artifacts. Return exactly one outcome: `single_sufficient_working_model`, `coupled_model_stack`, `competing_whole_chain_models`, or `insufficient_evidence_to_select`.

## Enforce the essence test

Ask: if the proposed central mechanism were removed, would the phenomenon disappear or change fundamentally? If not, classify it as secondary rather than the essence. Do not restate the observation as the essence.

Keep four levels separate:

1. essence statement;
2. whole-chain hypotheses;
3. component models;
4. corrections and secondary effects.

Select primarily at level 2. Never present a component as a complete explanation.

## Search and evidence rules

- Use complementary scholarly channels; use reviews for vocabulary and citation chasing, but prefer primary sources for central claims.
- Verify title, authors, year, and DOI or stable identifier before citation. Record blocked access rather than pretending to have read a source.
- Classify each equation using the six provenance classes in the orchestrator's scientific-contract
  v2 reference. For source/adapted items, search full text for exact equation/page/section locators;
  verify them against the source. For unavailable locators, record alternative searches and the
  exact support limitation. Never invent a locator. For v3, record each equation as
  `Source -> Original equation -> Assumptions -> Adaptation -> Final model`, including source title,
  authors, exact locator status, transformations, final equation, and adaptation justification.
- Distinguish direct quotation, paraphrase, derived result, and hypothesis. Keep quotations short.
- Treat direct-system evidence, component evidence, analogy, and constructed reasoning as different evidence classes.
- Search for supporting and opposing evidence, limitations, anomalies, and competing
  interpretations for every serious candidate. An empty opposing-evidence list requires a logged
  opposing-search outcome; it never means opposition was disproved.
- Do not pad a corpus to a quota. Stop only under the saturation rules in the detailed workflow.
- If web, PDFs, APIs, or subagents are unavailable, work sequentially from accessible sources, log the limitation, preserve unresolved items, and lower confidence.

## Select models transparently

Read [candidate-decision-rules.md](references/candidate-decision-rules.md) before filtering or selection. A score cannot override a hard-gate failure. For multi-objective prompts, preserve prompt-defined objectives; use dominance/Pareto analysis unless the prompt or user supplies a defensible scalarization.

Use these templates:

- [causal-chain-template.md](references/causal-chain-template.md)
- [paper-card-template.md](references/paper-card-template.md)
- [model-card-template.md](references/model-card-template.md)
- [report-template.md](references/report-template.md)
- [schemas.md](references/schemas.md)
- [few-shot-examples.md](references/few-shot-examples.md) for structure only, never as evidence
- [human-facing-theoretical-pdf.md](references/human-facing-theoretical-pdf.md) before producing or approving a human-facing PDF
- [latex-theoretical-model.md](references/latex-theoretical-model.md) before writing or approving `reports/theoretical-model.tex`
- [validation-and-reproducibility.md](references/validation-and-reproducibility.md) before
  registering acceptance criteria, calibration, numerical verification, physical validation, or
  parameter-study claims
- [scientific artifact templates](references/scientific-artifact-templates.md) for apparatus,
  evidence, equation provenance, parameter mapping, and candidate comparison

## Develop the standalone theory before rendering

Create and keep current `theory/theory-model.tex`, `theory/equations.yaml`,
`theory/variables.csv`, `theory/assumptions.md`, `theory/mechanism-chain.md`,
`theory/predictions.csv`, `theory/parameter-provenance.csv`,
`theory/conclusion-deductions.md`, `theory/literature-notes.md`, and
`theory/validation-plan.md`. Compatibility mirrors such as `theory-model.md`,
`equations.md`, or `model-validation.md` may remain, but they do not satisfy the deep-model gate.
These are agent-facing production and provenance artifacts; the PDF must incorporate their
essential content and must never require the reader to open them.

Write `reports/theoretical-model.tex` as the reader-facing source. It must identify the dependent and independent variables, reconstruct the causal mechanism, justify/derive every selected model from applicable laws, number and explain equations, define symbols/units/status/source, distinguish equation provenance, derive a falsifiable `Y=f(X;p)` relationship with fixed-variable trends, discuss limits/dimensions/omitted mechanisms, cite sources at claims and constants, map theory to the selected solver, and include a calculated example/table/plot. Do not write generic placeholders, use “see the retained model,” or make readers consult YAML, code, or registries.

Translate every arrow in the explicit chain
`controlled input → immediate physical response → coupling mechanism → state evolution → measurable observable`
into a displayed equation or a clearly identified constitutive/geometric relation. For every
important equation explain its origin, apparatus-specific applicability, the physical process and
sign of every term, units and dimensions, state/control/parameter/force/flux/field/observable roles,
competing balances, negligible and dominant limits, assumptions, validity range, and a measurement
that would contradict it. Name the actual apparatus, geometry, material, forcing, and observable;
generic balance-language is insufficient.

Place provenance immediately beside every displayed equation, boundary condition, numerical
correlation, threshold, coefficient, and sourced value in the report. Give the source identity and
granular locator, plus the adaptation map when applicable. A references section alone never passes.

Before PDF generation, pass these gates in order:

1. **Model identified:** define measurable dependent variable(s), independent variables, a proposed mechanism, candidate model, and selection reason.
2. **Quantitative relationship developed:** show a governing equation, define symbols and units, state assumptions, give a derivation or physical justification, and derive or compute at least one `Y = f(X; p)` prediction.
3. **Literature support complete:** identify the source, adaptation, or derivation behind every central physical claim, equation, and parameter.
4. **Prediction generated:** provide a calculated curve, table, scaling law, threshold, or numerical example with units, parameter values, and sensitivity/uncertainty.
5. **Simulation bridge complete:** map equations, constitutive laws, boundary/initial conditions, and output observable to the numerical implementation; distinguish solved, prescribed, fitted, and approximated elements.
6. **Conclusion deduction complete:** state the causal mechanism, central relationship, control
   dependences, predicted harmonics/resonances/thresholds/regimes, most direct test, largest
   uncertainty, and explicit rejection condition. Every conclusion claim must point to a displayed
   equation, a generated prediction, or a cited mechanism.
7. **Acceptance and coverage complete:** state the predeclared criterion, error-budget components,
   held-out or unavailable split, coverage rows, and the highest claim ceiling supported by
   retained receipts. If calibration is used, distinguish fit residual from independent validation
   residual and identify the frozen fit artifact.

For each dependent variable give its symbol, definition, SI unit, measurement procedure, uncertainty, and whether it is direct or derived. For each independent variable give its symbol, unit, range, status (`controlled`, `measured`, `literature`, `fitted`, `assumed`, or `calculated`), and mechanism relevance. State a testable trend in the form: “Holding ___ fixed, the model predicts that ___ increases/decreases/remains approximately constant with ___ because ___.”

Also classify every parameter-map symbol as `control_variable`, `measured_state_variable`,
`material_constant`, or `hidden_uncertainty_source`. If the mechanism, literature, or required data
remain inadequate, write a justified stopping decision with blocking items, claim ceiling, and
resumption conditions instead of selecting a model.

## Pre-register acceptance and preserve validation coverage

Before a fit, solver run, or physical comparison, create the acceptance record described in
[validation-and-reproducibility.md](references/validation-and-reproducibility.md). It must bind the
candidate and falsifier to exact observables, units, data splits, uncertainty/error budget,
threshold, input hashes, software revision, and evaluator. Keep failed thresholds, unavailable
sources, and uncovered regimes in the case ledger. Do not turn a generic comparison sentence into
an accepted validation result.

For calibration or physical-validation claims, create `calibration_plan.yaml` with
`calibration_contract_version: 1`. New scaffolds start `planned` and claim no calibration or
physical validation. `calibrated` requires a frozen fit artifact and disjoint fit records;
`physically_validated` requires an independent held-out comparison and a passed physical-validation
report bound to the frozen fit, or to frozen model/configuration and inputs when no parameter is
fitted. Keep the plan at `not_required` only with a concrete justification;
legacy cases without the plan remain at their legacy claim ceiling until explicitly migrated.

Treat reproducibility as an evidence chain: a source or artifact locator, content hash, exact
command, environment/solver revision, input/output hashes, warnings, and metric computation must
be retained. A self-declared `passed: true`, a plausible hash string, or a successful subprocess
does not prove that the corresponding scientific check occurred.

Do not call a document a theoretical report when only the first gate is met. It may be a `Preliminary Model Plan`; do not produce a final theoretical PDF before the quantitative-relationship gate.

## Human-facing PDF rule

A human-facing theoretical report must be a standalone scientific explanation, not a presentation-layer index of internal artifacts. It must visibly display and explain the selected model, equations, variable definitions, assumptions, derivation or justification, parameter provenance, predicted relationships, limiting cases, citations, simulation bridge, validation status, and limitations. Never use “see the model registry,” “see the YAML,” “see the case directory,” or equivalent language in place of that content.

Reject a LaTeX source or PDF whose mathematics only points to other artifacts, whose literature section only lists titles, that names a solver without displaying the physical model, or that has no falsifiable dependent-versus-independent-variable relationship. Render the LaTeX source to PDF with a real TeX engine and inspect every final PDF page; reject clipped text, broken symbols, unrendered commands, empty pages, placeholder sections, and inaccessible tables/figures.

Also reject a report if it:

- says only that terms represent “inertia, forcing, damping, or transport” without mapping each
  actual term to the prompt apparatus;
- leaves a forcing or coupling function such as \(F(V)\) undefined;
- uses a generic normalized function such as
  \(Y/Y_0=F(X/X_0;p/p_0)\) as its principal prediction;
- presents an example table whose values were not generated by a displayed equation;
- leaves any displayed symbol absent from the variable registry;
- concludes with headings or monotonic prose instead of prompt-specific mechanisms and
  falsifiable deductions.

## Validate before finalizing

Run:

```bash
python scripts/validate_case.py research_cases/<slug>
```

Resolve every error. A finalized case must contain the exact prompt, essence status and statement, a causal chain, a complete model registry, provenance for central equations, a selected whole-chain model/stack or explicit insufficient-evidence outcome, a rejected-candidate section, stable identifiers where available, the complete `theory/` package, and no placeholders.

## Prevent these failures

- Do not hunt for one famous theorem and stop.
- Do not create a disconnected equation catalogue.
- Do not inflate a component into a whole-chain model.
- Do not silently reject or delete candidates.
- Do not search only for the first mechanism proposed.
- Do not fabricate citations, metadata, equations, or source contents.
- Do not overreach beyond an abstract.
- Do not force a familiar solver such as OpenFOAM onto the problem.
- Do not add product objectives absent from the prompt.
- Do not invent scalar weights where a Pareto analysis is faithful.
- Do not ignore assumptions, regimes, magnitudes, or apparatus branches.
- Do not force certainty when evidence supports competing hypotheses.
- Do not call a fitted parameter a physical validation result; keep fit and held-out data disjoint.
- Do not report an uncertainty-free residual, post-hoc acceptance threshold, or unbound hash as
  reproducibility evidence.
- Do not promote an uncovered regime or apparatus branch from a nearby successful run.

## Invocation examples

- `Use $pt-theoretical-research to inspect the Singing Capacitor theory stage without running simulations.`
- `Use $pt-theoretical-research to build a causal-chain model registry from this existing problem contract.`
