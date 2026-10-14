# Scientific computing and verification checklist

Verification asks "do we solve the chosen equations correctly?" Validation asks "are they the right equations for the experiment?" Keep the two apart, and keep both apart from calibration (fitting parameters). The plugin's evidence lanes (numerical verification, parameter calibration, physical validation) and the claim states in `runnable-simulation-contract.md` still govern what may be claimed.

Pass criteria are written before the run and changed only through a recorded decision.

## A. Numerical accuracy

| Check | How | Pass criterion (declare quantitatively) |
|-------|-----|----------------------------------------|
| Step-size / mesh convergence | Refine h (or mesh) by a constant factor on at least three levels; compute observed order p = log(e1/e2)/log(r) against the exact or Richardson-extrapolated value | p matches the scheme's formal order within a stated band; asymptotic range reached |
| Tolerance study | Tighten `rtol`/`atol` over decades for adaptive solvers | Quantity of interest stable to the required digits; error non-increasing |
| Solver status | Check `success`, event handling, step counts, non-finite values | Failure raises; never plotted silently |
| Conservation checks | Energy, momentum, mass, charge, angular momentum, or a Lyapunov quantity as the physics dictates | Drift below a declared bound; dissipative systems never gain the quantity |
| Stiffness and stability | Compare an explicit and an implicit method, or inspect eigenvalues | No method-dependent qualitative difference |
| Floating-point sensitivity | Compare float32/float64 or perturb inputs by ~1e-12 relative for chaotic or ill-conditioned problems | Sensitivity understood and reported |
| Independent cross-check | Second method, solver, or reduced-order model (a second solver is an escalation under the routing rules) | Agreement within combined numerical errors |

Report numerical error separately from measurement, sampling, calibration, and model-form error.

## B. Physical correctness

- **Dimensional analysis:** every equation dimensionally homogeneous; names carry units; Pint (or exponent-vector) tests assert the dimensions of derived quantities and dimensionless groups.
- **Limiting cases:** each parameter taken to zero/infinity must recover a known simpler result (no damping, small amplitude, large Reynolds number, point source). Encode as tests.
- **Symmetry and invariance:** parity, time reversal, translation, rotation, scaling, and superposition (for linear models) as tests; broken symmetry must have a physical reason.
- **Analytic benchmarks:** at least one closed-form or published reference with tolerance and provenance; cite the source and conditions.
- **Order-of-magnitude and sign checks:** results compared with back-of-envelope estimates.
- **Regime of validity:** state dimensionless groups and the range where each assumption holds; the code warns or refuses outside it.
- **Assumptions registry:** ID, statement, valid-when, violation check, linked test; transparent in the README and reports.

## C. Reproducibility

- **Seeds:** one integer seed in config feeding `numpy.random.default_rng`; seed recorded in metadata; no global random state; parallel streams via `SeedSequence.spawn`.
- **Pinned environment:** committed lockfile; interpreter and library versions recorded; container/recipe when native binaries are involved.
- **Run metadata (provenance):** UTC timestamp, git commit and dirty flag, interpreter, platform, dependency versions, config hash, input file hashes, seed, command line, lockfile hash. Missing facts are recorded as null, never guessed.
- **Deterministic outputs:** canonical serialization (sorted keys, fixed float formatting where relevant); two runs with the same inputs give identical result files; metadata is kept out of the compared payload.
- **Receipts:** keep the command, output, and date for every verification run cited in a claim.

## D. Testability

- Unit tests for each function and validator; property tests for invariants and scaling laws.
- Regression tests with stored reference outputs (small, versioned, with hash) for stable behavior; update only with a changelog entry.
- Convergence and conservation tests are part of the suite, with tolerances sized to the runtime budget.
- Architecture tests keep the core independent of interfaces.
- Coverage is a diagnostic, not a goal; prioritise physics-bearing branches.

## E. Documentation

README with purpose, quickstart, assumptions section, verification status, limitations, and claim ceiling; docs/design-notes; ADRs; docstrings with units and equations; CHANGELOG.

## F. Iterative hypothesis testing and parameter exploration

- Write the hypothesis, the observable, the metric, and the falsifying outcome before running.
- Parameter sweeps: config-driven grids (log-spaced where the physics is multiplicative), one result file per point plus an index, resumable and parallel-safe, seeds per point derived from the base seed.
- Sensitivity: local logarithmic sensitivities d ln f / d ln p, and global methods (Sobol, Morris) when interactions matter; rank parameters by influence on the observable and carry the top ones into the uncertainty budget.
- Identifiability: check that fitted parameters are constrained (Hessian/covariance condition, profile likelihoods, correlation matrix); report degenerate combinations rather than individual values.
- Regime maps: sweep dimensionless groups and mark qualitative regime boundaries (stable/unstable, under/overdamped), so the theory-versus-experiment comparison states where each model applies.
- Model validation loop: predict, measure, compare with stated uncertainties, update the model only through a recorded decision, and re-validate on fresh held-out data.

## G. Pre-handoff gate

1. Quantitative pass criteria exist for each check above that applies, or a written justification says why not.
2. Each check is `implemented`; those cited as passed are `evidenced` with a receipt.
3. Tools not run (ruff, mypy, Pint, hypothesis) are listed as untested.
4. The claim ceiling is stated: declaration, synthetic software evidence, numerical verification, calibration, or physical validation.
