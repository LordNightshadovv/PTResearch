# Detailed workflow

Use this reference for every case. Preserve the audit trail when later evidence changes an earlier hypothesis.

## 0. Intake and problem contract

Copy the prompt exactly. Record its source, year, number, and access date if available. Extract:

- action verbs and requested deliverables;
- system boundary;
- controlled inputs and expected observables;
- prompt-defined objectives and constraints;
- apparatus details that are stated, ambiguous, or explicitly excluded;
- preliminary scores from 0 to 3 for explanation, design, optimization, and mechanism-identification emphasis.

Do not add comfort, cost, safety, usability, or manufacturability as mandatory objectives unless the prompt does. Branch on ambiguity when mounting, geometry, materials, drive, environment, or measurement would change the causal chain.

## 1. Provisional essence and hypotheses

Before broad search, answer:

1. What energy or information enters?
2. What converts it into the observed behavior?
3. Which state variables evolve?
4. What controls magnitude, frequency, pattern, threshold, or stability?
5. How does the internal state create the measured observable?
6. Which link is the bottleneck or dominant amplifier?

Write a one-to-three-sentence provisional essence, one main chain, up to three alternatives, uncertain links, and vocabulary questions. Apply the mechanistic necessity test. Label all of this as hypothesis generation.

## 2. Vocabulary map and query tree

Map exact prompt phrases to canonical discipline terms, spelling variants, apparatus names, mechanisms, mathematical frameworks, measurement language, analogous systems, competing mechanisms, and false-positive exclusions.

Execute search layers in this order:

1. **Exact phenomenon:** exact wording and close variants.
2. **Integrated models:** add mechanism, analytical model, coupled model, multiphysics, equivalent source, transfer function, constitutive-to-observable, theory and experiment, full field, or first principles.
3. **Unresolved links:** query input and output quantities for each missing link.
4. **Analogues:** search systems with the same equations or coupling topology; label evidence indirect.
5. **Mathematics and validity:** add derivation, assumptions, boundary conditions, validity, limitation, nonlinear correction, or experimental validation.
6. **Measurement and discrimination:** search parameter measurement and tests that separate candidate mechanisms.
7. **Criticism and failure:** add breakdown, contradiction, alternative mechanism, anomaly, failed model, or regime transition.

For each serious candidate, preserve supporting evidence and actively seek opposing evidence. If no
opposing item is found, record the channels/queries and bounded search outcome rather than claiming
that no contradiction exists.

Prefer short high-signal queries plus filters over long prose queries. Refine when results expose better terminology; record why.

## 3. Bounded search and screening

Set bounds before searching: target breadth, deep-reading count, date/language limits if justified, and a per-layer query budget. Use at least two complementary channels when available. Do not use a single database as a completeness claim.

Aggregate records, deduplicate by DOI/stable ID and then normalized title, and screen against explicit criteria. Retain a source when it supplies a direct mechanism, integrated model, governing derivation, relevant parameter dependence, validation, limitation/alternative, or discriminating measurement. Exclude or downgrade unverifiable identity, unreasoned analogy, methodology-free claims, duplicates, irrelevant results, or regime-mismatched uses.

Record failed and empty searches. Never add irrelevant sources to meet a count.

## 4. Paper extraction

Classify the paper before evaluating it: primary experiment, theoretical/analytical, numerical/modeling, review, thesis, technical report, textbook/monograph, standard, or application note. Read in this order:

1. purpose and claimed contribution;
2. apparatus/materials/regime;
3. governing mathematics and boundary conditions;
4. methods, figures, tables, and results;
5. limitations and conclusions;
6. references worth chasing.

For every important claim record **what**, **where**, **evidence type**, **strength**, **caveat**, and **why it matters to a causal link**. Separate methodological soundness from relevance to the actual apparatus. If only an abstract is accessible, mark `abstract_only` and leave unreported fields unknown.

When parallel extraction is available, batch independent papers with one shared extraction schema. Otherwise process sequentially and update the paper matrix after each source.

## 5. Apparatus gate and candidate construction

Complete `apparatus_fidelity.yaml` before endorsement. Compare each candidate against geometry,
topology, open/sealed/vented connections, deformable/moving parts, masks, contacts, interfaces,
sensors, distances, boundaries, observables, and parameter ranges. A contradiction on a decisive
feature blocks the candidate.

First search for models already spanning input to observable. State every whole-chain candidate as a causal sentence. Record its essence claim, dominant link, component relations, predictions, evidence coverage, and failure regimes.

Build the minimal analytical, serious competitor, limitation-driven higher-fidelity, and useful
empirical-baseline categories where physically defensible. If only one serious formulation exists,
record the search and physics-based exception.

When assembling components, write:

```text
model A → interface quantity [units] → model B → interface quantity [units] → model C
```

Verify coordinate and sign conventions, linear/nonlinear assumptions, time/frequency domains, material/geometry regimes, and boundary conditions. A chain with an incompatible interface is not coherent.

If no named chain exists, derive a candidate from conservation laws, constitutive relations, geometry, symmetry, boundary/initial conditions, and an observation equation. Label it `constructed_first_principles`; cite every borrowed relation; distinguish sourced steps from new reasoning; do not call the assembly established.

## 6. Mathematical and magnitude audit

For every serious candidate:

- name each equation type: law, theorem, theory/model family, constitutive relation, governing equation, approximation, empirical correlation, or numerical method;
- define every symbol and unit;
- classify every symbol as a control variable, measured state variable, material constant, or
  hidden uncertainty source;
- check dimensions term by term and state unresolved dimensional issues;
- derive applicable dimensionless groups, parameter sources, values/ranges, and regime
  implications, or justify why dimensionless analysis is not applicable;
- test zero-input, small/large parameter, low/high frequency, and symmetry limits where meaningful;
- identify boundary and initial conditions;
- list linearization, continuum/discrete, small-angle, thin-body, paraxial, incompressible, quasistatic, coherence, or similar assumptions;
- determine which parameters are measured, estimable, fitted, latent, or unidentifiable;
- estimate orders of magnitude or scaling to test whether the mechanism can create the observed scale;
- confirm that the terminal equation predicts the requested observable.
- map every experimental control to a symbol and equation/term/boundary, intermediate state, and
  terminal observable;
- require an evolution/closure equation for every state/history variable;
- verify exact locators and complete adapted-equation transformations.
- preserve `Source -> Original equation -> Assumptions -> Adaptation -> Final model` for every
  equation, with source title/authors and explicit unavailable-locator records.

Classify the result as explanatory, predictive, descriptive, or a mixture.

## 7. Decision and selection

Apply hard gates in [candidate-decision-rules.md](candidate-decision-rules.md). Then use advisory scoring only to explain tradeoffs. Never silently remove a candidate: filtered whole-chain candidates may remain as components, corrections, limiting cases, or control hypotheses.

Return one outcome and one to three recommended candidates when supported. Compare each selection directly with every filtered candidate. State confidence and the missing evidence most likely to change the decision.

Before selection, render the mandatory table with `Candidate`, `Explains`, `Limitations`, `Required
parameters`, and `Experimental discriminator`.

For multiple objectives, identify aligned and conflicting regimes. Use dominance and Pareto-front reasoning unless a target, constraint, or justified preference supplies scalarization.

## 8. Stopping rule

Stop active search only when:

- prompt and apparatus branches are represented;
- every essential link is supported or explicitly unresolved;
- an integrated model or compatible stack exists, or insufficient evidence is documented;
- major competing mechanisms encountered have registry entries;
- two successive search iterations add no new model family or important correction;
- serious candidates make testable predictions;
- central claims and equations have verified citations.

If the mechanism remains unresolved, literature is insufficient, or indispensable data are
missing, stop without selecting a model. Record the blocking items, allowed claim level, and
specific resumption conditions.

## 9. Handoff boundary

Recommend suitable later simulation families and state required equations, parameters, geometry, boundary conditions, outputs, and validation targets. Recommend discriminating observables and parameter sweeps for later experimental design. Do not execute simulations, choose laboratory hardware, or present a full campaign as part of this skill.
