# Technology stack selection and ADR

Choose the stack for the problem, not for familiarity or novelty. Rank by: **reproducibility, reliability, maintainability, modularity, extensibility, performance** (performance only to the measured need). Prefer well-established, documented, tested libraries.

## Default scientific Python stack

| Concern | Prefer | Notes |
|---------|--------|-------|
| Arrays, linear algebra | NumPy, SciPy | Vectorize; avoid Python loops in inner numerics |
| Tabular / labeled data | pandas, xarray | xarray for gridded/multidimensional with named axes and units metadata |
| Symbolic derivation | SymPy | Derive, simplify, and `lambdify`; keep the derivation as a test |
| Units | Pint | Quantities at interfaces; magnitudes inside tight loops; plus dimension-exponent tests |
| Uncertainty | `uncertainties` (analytic propagation), Monte Carlo with seeded `Generator` | Correlated inputs need covariance, not independent sigmas |
| ODE/PDE integration | `scipy.integrate.solve_ivp` (DOP853, Radau, LSODA), `scipy.sparse` + linear solvers | Choose stiff vs non-stiff solver on evidence |
| Optimization / fitting | `scipy.optimize` (`curve_fit`, `least_squares`), lmfit | Report covariance with `absolute_sigma=True` when sigmas are measured |
| Bayesian / MCMC | emcee | Only where posterior shape or parameter degeneracy matters; document priors and convergence diagnostics |
| Plotting | Matplotlib (static, publication), Plotly (interactive) | Always include error bars and axis units |
| Configuration | dataclasses + TOML; pydantic for schemas; Hydra for sweeps/composed configs | Add heavier tools only when the need is demonstrated |
| Testing | pytest, hypothesis, pytest-cov | Property tests for invariants and scaling laws |
| Quality | ruff, mypy | CI gates |
| Environments | uv (or poetry) with committed lockfile; conda-lock for binary stacks | One tool per project |

PT solver routes use the locked solvers in `tools/solver-runtime/solver-locks.json`; the stack here wraps, drives, and analyses them and never replaces the selected solver or physical model.

## Language choice

Python is the default because of ecosystem, speed of iteration, and readable verification. Choose another language only on technical merit and record the evidence:

- **Rust:** hard reliability or performance requirement, long-running or concurrent tools, memory-safe numerics kernels, high-quality terminal apps (ratatui). Needs profiling or a stated reliability requirement as evidence.
- **C/C++/Fortran:** extending an established solver, existing numerical libraries, or hot loops that NumPy/Numba/Cython cannot express; usually exposed via Python bindings.
- **Julia:** differential-equation-heavy workflows where its ecosystem is a clear fit and the team accepts a second toolchain.
- **MATLAB/other:** only when the user mandates it or a lab pipeline depends on it.

"Rust is faster" without a measured bottleneck is not a justification; a performance claim requires a profile. Mixed-language projects keep the interface narrow, typed, and tested at the boundary.

## Paradigm

- OOP for substitutable abstractions (Model, Solver, Experiment, Sensor) and for objects with invariants (validated parameter sets).
- Functional / pure functions for numerics, transforms, and statistics: easy to test and parallelize.
- Procedural for glue, scripts, and entry points.
State the choice per layer in the ADR with the reason; mixed is normal.

## Avoid reinvention (and know when it is justified)

Before writing an integrator, interpolator, optimizer, unit system, or statistics routine, search the established libraries above. Reimplementation is justified only for: (a) a transparent verification stand-in that checks the library, (b) a missing capability, (c) a profiled performance need. Record each in `reinvention_exceptions` in the manifest.

## ADR (stack decision record) template

Store at `docs/adr/NNNN-title.md`. Immutable once accepted; supersede with a new ADR.

```markdown
# ADR NNNN: <decision title>

- Status: proposed | accepted | superseded by ADR NNNN
- Date: YYYY-MM-DD
- Deciders: <names or roles>

## Context
What problem, constraints (accuracy, runtime, platform, team skills, deadline), and quality
attributes drive this decision? Link the requirements/design note.

## Decision
| Concern | Choice | Why |
|---------|--------|-----|
(language, numerics, units, uncertainty, config, tests, quality, environment, paradigm, interface)

## Alternatives considered
| Alternative | Rejected because |
|-------------|------------------|
(at least two, with concrete technical reasons, e.g. measured cost, missing capability, maintenance risk)

## Consequences
Positive, negative, risks, and the verification that guards the decision.
Revisit when: <measurable trigger>.
```

A decision record with fewer than two alternatives, or reasons such as "familiar" or "faster" without evidence, fails review. The manifest's `stack_decision` block mirrors the ADR (selected, alternatives_considered, paradigm, language, reinvention_exceptions) so it can be machine-checked.
