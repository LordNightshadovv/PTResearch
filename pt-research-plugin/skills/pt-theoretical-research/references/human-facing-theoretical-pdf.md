# Human-facing theoretical PDF contract

Use this contract before producing or approving a document titled `Theoretical Report`.

## Required theory package

Create these authoritative files under `theory/`:

```text
theory-model.tex
equations.yaml
variables.csv
assumptions.md
mechanism-chain.md
predictions.csv
parameter-provenance.csv
conclusion-deductions.md
literature-notes.md
validation-plan.md
```

Keep the package synchronized with the selected model. It supports the report; it never substitutes for it.

## Required PDF content

Include these reader-facing sections unless genuinely inapplicable:

1. title, problem identity, version/date, status, primary model, and primary solver if any;
2. official problem statement and focused research question;
3. measurable dependent variable(s) and independent variables with symbols, units, measurement/status, range, and role;
4. proposed mechanism, clearly separating observed facts, sourced mechanisms, hypotheses, and tractability assumptions;
5. literature foundation explaining what each important source contributes to an equation, mechanism, or parameter;
6. numbered governing equations with defined symbols, physical origin, validity regime, and
   nearby equation-level provenance; for sourced/adapted items include exact section/page/equation
   locators and transformation, or the honest unavailable-locator search record;
7. derivation or model construction from physical laws to a useful prediction;
8. prominently displayed `Y = f(X; p)` relationship, its predicted trend, controls, slope/threshold parameters, and failure criterion;
9. assumptions, regime limits, dimensional checks, and meaningful limiting cases;
10. a calculated prediction plot, table, scaling law, threshold, or numerical example with units, parameter values, and provenance;
11. simulation formulation mapping theory to equations, constitutive laws, boundary/initial conditions, source/interface laws, outputs, and approximations;
12. validation status and plan, comparison with data where available, competing models, limitations, conclusions, and full references.

For contract v3, visibly include the mandatory five-column candidate comparison, equation-lineage
chain, negative-evidence review, dimensionless regime analysis, four-way parameter classification,
physics-first solver chain, and experiment-to-simulation validation chain. A justified-stop report
must state its claim ceiling and must not imply that a model or solver was selected.

State at least one testable trend explicitly: “Holding ___ fixed, the model predicts that ___ increases/decreases/remains approximately constant with ___ because ___.”

## Evidence and labeling

For each central claim, equation, or parameter, label it as one of: `standard law`, `literature equation`, `adapted equation`, `empirical correlation`, `fitted model`, `derived here`, or `numerical governing equation`. State fitting data, method, uncertainty, and validity range for fitted values. Distinguish theoretical predictions, numerical results, fitted relationships, and experimental observations.

## Rejection rules

Reject a PDF if it omits a useful quantitative relationship, hides equations in code/YAML, lists sources without explaining their contribution, uses a solver name in place of the model, leaves symbols/units undefined, or tells the reader to consult an internal artifact for essential theory. If only the model-identification gate has passed, title the output `Preliminary Model Plan`, not `Theoretical Report`.

Also reject a PDF that lacks a reader-facing apparatus-fidelity table or puts provenance only in
the references section. Every apparatus row must show the feature, representation, match status,
justification, consequence if wrong, and required measurement/source.

Hard-reject undefined forcing/coupling functions, generic normalized placeholder predictions,
generic term explanations not tied to the apparatus, unsupported synthetic trend tables, and
conclusions without equation-linked prompt-specific deductions. Require every causal-chain arrow
to have a mathematical link and every displayed symbol to appear in the variable registry.

## Publication QA

Use a PDF workflow that renders equations rather than showing raw LaTex. Render every page to images and inspect equations, symbols, tables, figures, captions, headers/footers, page breaks, and references. Reject clipped text, broken glyphs, empty/provenance-only pages, placeholders, raw YAML, and unexplained internal identifiers.
