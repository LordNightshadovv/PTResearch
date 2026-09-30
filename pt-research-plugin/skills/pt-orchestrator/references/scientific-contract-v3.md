# Scientific contract v3

Version 3 extends v2 without reinterpreting completed v2 cases. New cases use
`contract_version: 3`; migrated cases must be revalidated before claiming v3 compliance.

## Required gates

1. **Equation lineage:** every equation records
   `Source -> Original equation -> Assumptions -> Adaptation -> Final model`. Source identity
   includes title and authors. A locator records chapter, section, page, equation, figure, table,
   appendix, or stable anchor when verified. If unavailable, record that fact, why, and the
   searches performed. Never infer a locator.
2. **Model comparison:** compare every serious candidate in a table with `Candidate`, `Explains`,
   `Limitations`, `Required parameters`, and `Experimental discriminator`. State why the selected
   outcome is preferable to each alternative. Do not accept the first plausible explanation.
3. **Physics-first routing:** preserve the chain
   `Phenomenon -> Physics -> Governing equations -> Numerical requirements -> Solver`. A solver
   name is invalid before closure and numerical requirements.
4. **Negative evidence:** for every serious candidate record supporting evidence, opposing
   evidence or an honest opposing-search outcome, limitations, and competing interpretations.
5. **Dimensionless analysis:** identify relevant dimensionless groups, parameter sources, values
   or ranges, and regime implications. If none are applicable, justify that conclusion explicitly.
6. **Parameter metadata:** classify every symbol in the parameter/equation map as exactly one of
   `control_variable`, `measured_state_variable`, `material_constant`, or
   `hidden_uncertainty_source`.
7. **Simulation validation chain:** every numerical package maps
   `Experiment measurement -> Simulation input -> Solver quantity -> Output metric -> Comparison
   method`, including uncertainty treatment and a quantitative acceptance criterion.
8. **Pre-registered acceptance and coverage:** before fitting, execution, or physical comparison,
   freeze the metric/formula, direction, units, threshold, uncertainty method, data split,
   falsifier, failure condition, input/software hashes, and evaluator. Maintain an observable ×
   regime × apparatus-branch coverage matrix; identify every uncovered or blocked row. A post-hoc
   threshold, self-declared boolean, unbound hash, or solver exit code is advisory evidence only.
9. **Calibration and independent validation:** when a case claims calibration or physical
   validation, require `calibration_plan.yaml` with `calibration_contract_version: 1`. Its fit and
   validation observations, groups, replicates, and data hashes must be disjoint. A `calibrated`
   claim requires a frozen fit artifact/hash, bounded identifiable parameters, objective,
   residual summary, and numerical error. A `physically_validated` claim additionally requires
   `independent_validation.status: passed`, a binding to the frozen fit or, when no parameters are
   fitted, the frozen model/configuration and inputs, held-out uncertainty-aware comparison, and a
   passed `physical_validation` section in `validation_report.yaml`. A new
   scaffold's `planned` plan has no calibration or physical-validation claim; `not_required` needs
   justification and cannot contain fitted parameter roles. Legacy cases stay at their prior
   ceiling until explicit migration or opt-in.
10. **Justified stopping:** permit `stop_unresolved_mechanism`, `stop_insufficient_literature`, or
   `stop_missing_data`. Record rationale, blocking items, allowed claim level, and resumption
   conditions. A stopped case selects no solver and makes no final-model claim.

## Completion

A continuing case must record `stopping_decision.status: continue`, pass all v2 and v3 gates, and
retain a pre-registered acceptance/coverage record. A justified-stop case may close without
downstream equations or simulation artifacts only at the claim level named in its stopping record.
Structural completeness never upgrades literature, equation, numerical, calibration, or
experimental evidence. Each accepted state must be consistent with the strongest receipt and
validation report; a later stage string or claim entry cannot promote an earlier artifact.

## Runnable simulation extension

For every continuing numerical route, the simulation handoff must separately record scientific
readiness and software readiness. A documentation-only handoff is classified as handoff_only. A
complete software package requires executable/native implementation, separated inputs, a synthetic
benchmark, real system and run gates, machine-readable extraction, equation/code traceability, a
three-level verification plan, and receipts. runnable_synthetic requires a passed synthetic
receipt; numerically_verified requires executed passed refinement evidence and a pre-registered
numerical criterion; experimental comparison requires held-out measurements, uncertainty, and a
passed independent physical-validation report. A solver-runtime smoke receipt alone cannot satisfy
any case-runnable claim. Report measurement, calibration, numerical, sampling, and model-form
uncertainty separately and retain the exact commands, input/output hashes, software revision,
warnings, failures, and coverage gaps needed to reproduce the metric.
