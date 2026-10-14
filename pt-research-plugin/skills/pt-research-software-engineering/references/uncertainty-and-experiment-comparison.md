# Uncertainty analysis and theory-versus-experiment comparison

Every quantitative claim in a PT report needs a stated uncertainty and a stated comparison method. Separate the sources; do not merge them into one number without showing the components.

## 1. Separate uncertainty sources

| Source | Examples | Treatment |
|--------|----------|-----------|
| Measurement | ruler/timer resolution, sensor noise, repeat scatter | Type A (statistics of repeats) and Type B (resolution, calibration certificates); per-point sigma |
| Calibration (fitted parameters) | fitted stiffness, drag coefficient | Fit covariance (`curve_fit(..., absolute_sigma=True)`), profile likelihood, bootstrap |
| Numerical | discretization, tolerance, integration error | Convergence and tolerance studies; a bound on the quantity of interest |
| Sampling | Monte Carlo or random-initial-condition variability | Seeded runs, report N and the standard error of the mean |
| Model form | omitted physics, wrong closure | Residual structure, competing models, held-out comparison; usually not reducible to a single sigma |

The manifest's `uncertainty_treatment.error_sources` must state a treatment (or "not_applicable: reason") for each of the five.

## 2. Propagation methods

- **Linear (first-order) propagation:** sigma_f^2 = sum (df/dx_i)^2 sigma_i^2 for independent inputs; use the full covariance for correlated inputs. Libraries: `uncertainties`, SymPy derivatives, or central differences. Valid only when f is near-linear across a few sigma.
- **Monte Carlo propagation:** draw inputs from their distributions with a seeded `Generator`, evaluate the model, report mean, standard deviation, and percentile interval; choose N so the standard error of the estimate is small; compare with linear propagation as a check.
- **Fit parameter uncertainties:** weighted least squares with measured sigmas; report parameters, standard errors, correlation matrix, reduced chi-squared, and degrees of freedom. If sigmas are unknown, say the errors are scaled by the residual variance and that chi-squared is then not a test.
- **Bootstrap:** resample residuals or points for non-Gaussian or small-sample cases.
- **MCMC (emcee):** where posteriors are non-Gaussian or parameters are degenerate; justify the priors, report autocorrelation time, acceptance fraction, and convergence diagnostics, and run from several initial states.
- **Sensitivity:** local logarithmic sensitivities for ranking; global (Sobol, Morris) for interactions. Use them to decide which measurements to improve.

## 3. Residual analysis

Plot standardized residuals (data minus model, divided by sigma) against the independent variable and against each controlled parameter. Look for trends, curvature, oscillation, heteroscedasticity, and outliers. A good fit has no structure; structure means model-form error. Report mean, spread, maximum, and lag-1 autocorrelation of the standardized residuals.

## 4. Quantitative theory-versus-experiment comparison

1. **Pre-declare** the observable, units, metric, threshold, and falsifier before looking at held-out data (the plugin's preregistration rules apply).
2. **Split data:** calibration data fit parameters; held-out data validate. Never report held-out agreement computed on data used for fitting. Keep disjoint observation, group, and replicate IDs in `calibration_plan.yaml`.
3. **Metrics:** reduced chi-squared (with the fit's degrees of freedom), RMSE or normalized RMSE, maximum standardized residual, fraction of points within 2 sigma, R-squared only as a descriptive aid (it hides systematic structure), and for model rivalry AIC/BIC or Bayes factors with caveats.
4. **Overlay plots with error bars:** theory curve (with its own uncertainty band when parameters are uncertain), data with 1-sigma bars, residual panel beneath, axis labels with units, color-blind-safe styling, data table or alt text.
5. **Regime maps:** plot the comparison metric or the qualitative regime over the dimensionless-parameter plane; mark where each model's assumptions fail.
6. **Report honestly:** agreement within uncertainty supports but does not prove a model; discrepancy outside combined uncertainty is a finding, reported with its candidate explanations. Never tune uncertainties to force agreement.
7. **Claim ceiling:** an `experimentally_compared` state requires an evidenced comparison on held-out data with measurement uncertainty and a quantitative criterion.

## 5. Implementation map (scaffold)

| Need | Scaffold function |
|------|-------------------|
| Linear propagation | `uncertainty.linear_propagation` |
| Monte Carlo propagation | `uncertainty.monte_carlo_propagation` |
| Weighted fit with covariance | `uncertainty.fit_with_uncertainty` |
| Reduced chi-squared, residual diagnostics | `uncertainty.reduced_chi_squared`, `uncertainty.residual_summary` |
| Sweeps and sensitivity | `uncertainty.parameter_sweep`, `uncertainty.local_sensitivity` |
| Comparison metrics | `comparison.compare` |
| Overlay with error bars and residuals | `plotting.overlay_with_error_bars` (matplotlib extra) |
