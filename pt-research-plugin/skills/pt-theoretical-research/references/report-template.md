# Human-facing theoretical report: [problem]

## 1. Title and report status

Give problem number/title, version/date, status (`preliminary`, `exploratory`, `semi-empirical`, or `predictive`), primary theoretical model, and primary solver if any. Use `Preliminary Model Plan`, not `Theoretical Report`, until a quantitative relationship is developed.

## 2. Problem statement

Quote or accurately paraphrase the official prompt.

## 3. Research question and observables

State the focused question. Define every dependent variable with symbol, meaning, SI unit, measurement procedure, expected uncertainty, and direct/derived status. Define each independent variable with symbol, unit, range, status, and why it affects the mechanism.

## 4. Phenomenon and proposed mechanism

Explain input, intermediate process, restoring/dissipative/destabilizing/coupling mechanism, and observable outcome. Distinguish observed facts, source-supported mechanisms, research hypotheses, and tractability assumptions.

## 5. Literature foundation

For each central source, state the mechanism, equation, or parameter it contributes; where it enters the model; and whether the use is copied, adapted, simplified, or newly derived. Use inline citations.

## 6. Assumptions and regime

List assumptions, why each is reasonable, validity range, and likely error or missing behavior.

## 7. Variables and parameters

Include a readable table: symbol, meaning, unit, status, value/range, and source. Mark every numerical value as controlled, measured, literature, fitted, assumed, or calculated.

## 8. Governing equations

Display and number important equations. Define every symbol, identify the physical law, state the validity domain, and label every equation as standard law, literature equation, adapted equation, empirical correlation, fitted model, derived here, or numerical governing equation.

For every equation show `Source -> Original equation -> Assumptions -> Adaptation -> Final model`.
Give source title, authors, exact retrievable locator, transformations, and adaptation justification.
Mark unavailable locator information explicitly with the searches performed.

## 9. Derivation or model construction

Show the path from governing laws to the useful relationship, including balances, approximations, substitutions, and nondimensionalization where useful. Do not hide material steps in YAML, code, or a solver dictionary.

List relevant dimensionless groups, their definitions, parameter sources, values/ranges, and regime
implications. If none apply, justify why.

## 10. Main predicted relationship

Prominently state `Y = f(X_1, X_2, ...; p_1, p_2, ...)`. Explain held controls, signs and form of dependencies, slope/threshold parameters, applicable regime, uncertainty, and what result would falsify the model. Include an explicit holding-fixed trend sentence.

## 11. Limiting cases and sanity checks

Check dimensions and meaningful limits (for example zero forcing, high damping, small angle, or vanishing viscosity). Explain singular or unphysical limits.

## 12. Numerical example or prediction figure

Include a prediction plot, table, dimensionless curve, regime map, or representative calculation. State the equation/model, parameter values, units, and whether values are measured, cited, fitted, or assumed.

## 13. Simulation formulation

Map each theory element to its numerical implementation: governing equation, constitutive law, boundary/initial condition, source/interface law, output, and whether it is solved, prescribed, fitted, or approximated. Name the solver only as an implementation of the physical model.

## 14. Validation plan and current validation

Separate analytical, numerical-convergence, benchmark, and experimental validation. State only checks actually completed; identify planned work clearly.

For each simulation comparison show `Experiment measurement -> Simulation input -> Solver quantity
-> Output metric -> Comparison method`, including uncertainty treatment and acceptance criterion.

## 15. Comparison with experiment

When data exist, show measurements with uncertainty, model predictions, fitted parameters, residual/goodness-of-fit evidence, discrepancies, and possible causes.

## 16. Limitations and competing models

State what the model cannot describe, plausible alternatives, and the discriminating observation or experiment.

Include this table before selection:

| Candidate | Explains | Limitations | Required parameters | Experimental discriminator |
|---|---|---|---|---|

State supporting evidence, opposing evidence or the documented opposing-search outcome, limitations,
and competing interpretations for every serious candidate.

## 17. Conclusions

Summarize the mechanism, main relationship, predicted trends, most important validation result, greatest uncertainty, and next experiment.

If no justified model can be selected, replace the normal conclusion with the stopping status,
rationale, blocking items, allowed claim level, and resumption conditions.

## 18. References

Give complete references and stable identifiers. A title-only list is insufficient.

## Appendix: audit record

Keep a concise provenance note if needed. Do not replace reader-facing theory with raw YAML, internal identifiers, or pointers to registries/case folders.
