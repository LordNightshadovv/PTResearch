# Validation, calibration, uncertainty, and reproducibility

Use this reference with the version-3 scientific contract whenever a case will make a
calibration, numerical-verification, physical-validation, or parameter-study claim. It is an
operational handoff contract: a plan or a populated field does not mean that the associated
activity happened.

## Pre-register the acceptance rule

Before fitting a parameter, executing a case, or inspecting a result, write a versioned acceptance
plan. The plan must name:

- the candidate model IDs, prompt observables, apparatus branch, parameter/regime coverage, and
  the hypothesis or falsifier being tested;
- the metric, formula, direction, target observable, units, threshold, uncertainty treatment, and
  failure/rejection condition;
- the fit/development and held-out/validation observations, group IDs, and replicate IDs, with
  content hashes and a reason for the split;
- the allowed parameter roles, finite bounds, identifiability method, and which values are fixed,
  measured, fitted, or assumed;
- the software/package revision, solver/runtime version, input manifest, random seeds, and
  evaluator role that will be recorded in the receipt.

Record `predeclared_at` before fitting or execution starts. A later change is a new plan version;
it cannot silently rescue a failed result. A criterion such as “looks close,” a post-hoc threshold,
or a solver exit code is not an acceptance rule.

For calibration or an advanced physical claim, use the versioned `calibration_plan.yaml` contract
with `calibration_contract_version: 1`. A newly scaffolded plan has status `planned` and the claim
ceiling `no_calibration_or_physical_validation_claim`; it must not be described as a passed plan.
Use `not_required` only with a concrete justification and no fitted parameter role. Legacy cases
without a plan remain at their previous ceiling until they explicitly migrate or opt in.

## Keep calibration and validation independent

Calibration estimates parameters from a declared fit split. Physical validation tests the frozen
model and, when parameters are fitted, the frozen fit on a disjoint held-out split. The split must be disjoint by observation,
group, and replicate where those units exist; record both data hashes. Never use a validation
residual to choose a parameter, threshold, model, or repair, then call the same result held out.

For `calibration_plan.yaml` version 1, a `calibrated` claim requires a frozen fit artifact and
matching fit-data hash, bounded parameter values, objective value, residual summary, numerical
error, and identifiable fitted parameters. A `physically_validated` claim additionally requires
`independent_validation.status: passed`, the exact validation IDs/hash and a binding to the frozen
fit artifact or, when no parameters are fitted, the frozen model/configuration and inputs, an
uncertainty-aware comparison and acceptance criterion, and a passed `physical_validation` section
in `validation_report.yaml`. Every failed or incomplete fit/validation remains visible and lowers
the claim ceiling.

## Build an error budget and coverage ledger

Separate these contributors instead of hiding them in one residual:

| Contribution | Required record |
|---|---|
| measurement and repeatability | instrument/procedure, uncertainty and replicate treatment |
| calibration/parameter | fit data, bounds, identifiability, covariance or sensitivity, and fit residual |
| numerical/discretization | mesh, time-step, solver tolerance or sampling refinement and numerical error |
| model form/omitted physics | excluded mechanism, regime boundary, falsifier, and qualitative or quantitative bound |
| sampling/coverage | held-out groups, replicates, parameter ranges, and untested branches |

Give each contribution a method, value or defensible bound, unit, and correlation assumption. State
whether the final interval is a sum, root-sum-square, covariance-aware propagation, bootstrap, or
another justified method. Report residuals beside the budget; an uncertainty interval cannot hide a
systematic model discrepancy. Do not count the same measurement or calibration uncertainty twice.

Maintain a coverage matrix with one row per observable × regime × apparatus branch × parameter
range. Each row records the prediction, data or run IDs, validation type, uncertainty budget,
acceptance criterion, evidence locator/hash, and status (`covered`, `partially_covered`,
`uncovered`, or `blocked`). A few successful runs do not establish coverage of an untested branch.
An uncovered row is a limitation and a resumption condition, not an implicit pass.

## Preserve evidence provenance

Every conclusion, metric, and state transition must point to an addressable source or artifact:
case-relative locator, stable identifier or URL, content hash, and retrieval/execution timestamp.
For a result, retain the exact command, environment and architecture, package/solver revision,
input and output hashes, warnings/errors, and the script or notebook revision that computed the
metric. A human declaration that a check “passed,” a plausible hash string, or a file's presence
without a bound receipt is advisory evidence only.

Keep negative and unavailable evidence in the ledger. A blocked source, missing dependency,
failed mesh level, unresolved parameter, and failed acceptance criterion must retain its reason,
scope, and next legal action. Do not replace it with a summary saying the check was “considered.”

## Use truthful claim ceilings

Use the highest state supported by receipts and the contract, and report every lower or untested
state. Typical boundaries are:

- theory or route artifacts: a working or competing model, never a physical validation result;
- synthetic benchmark: implementation and extractor evidence only;
- solver run: executed/unverified until numerical checks pass;
- numerical verification: refinement/benchmark evidence, not agreement with an apparatus;
- calibrated: a frozen, independently checked fit, not physical validation;
- physically validated: held-out, uncertainty-aware comparison with the predeclared criterion and
  both the calibration and physical-validation artifacts passed.

When a dependency, dataset, or evaluator is unavailable, return a partial artifact with the
highest supported claim ceiling, failed checks, exact blockers, and resumption conditions. Never
advance a stage because a later file exists or because a subprocess returned zero.

## Review before handoff

The reviewer should answer, in order:

1. Was the acceptance rule frozen before the fit/run and bound to the exact inputs?
2. Are candidate alternatives, falsifiers, and negative evidence still represented?
3. Are fit and validation records disjoint and independently evaluated?
4. Can each reported uncertainty and residual be recomputed from retained artifacts?
5. Does the coverage matrix expose every untested observable, regime, and apparatus branch?
6. Does the claimed stage match the strongest available receipt and its limitations?

If any answer is unknown, retain the evidence gap and lower the claim ceiling. This contract
supports reproducibility; it does not by itself establish that a physical model is correct.
