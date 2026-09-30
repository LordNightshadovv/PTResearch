---
name: pt-report-renderer
description: Render a standalone human-facing PT theoretical PDF from a complete theory package and retained research artifacts. Include equations, variables, derivation, falsifiable predictions, citations, simulation mapping, validation, and limitations. Use under pt-orchestrator after theory gates pass; never replace or flatten the YAML and Markdown source artifacts.
---

# PT Report Renderer

Render from the authoritative case artifacts and the completed `CASE/theory/` package, not conversational recollection. Write and validate `CASE/reports/theoretical-model.tex`, compile it with a real TeX engine to `CASE/reports/theoretical-model.pdf`, and retain the `.tex` source. Use `tools/report-renderer/render_research_report.py` only for the auxiliary presentation workflow, never as a replacement for the LaTeX theoretical-model report.

The renderer's preflight requires a measurable observable, variables/units/statuses, visible equations, derivation/justification, assumptions, source-specific literature notes, parameter provenance, at least one `Y(X)` prediction with a testable trend, and a simulation bridge. It refuses to produce a `Theoretical Report` from a summary that points readers at YAML, registries, or case files. For a Gate-A-only case, invoke it with `--preliminary-model-plan`; that output must be labelled as such and is not a theoretical report.

For contract-version-2 reports, include the apparatus-fidelity table and put equation provenance
beside every displayed equation/correlation/boundary/coefficient/value. Show exact locators and
adaptation steps when retrievable; otherwise show the unavailable-locator search and support limit.
A bibliography entry alone is not equation provenance.

For contract-version-3 reports, also show the five-column candidate comparison table, the complete
equation-lineage chain, supporting and opposing evidence, dimensionless regime identification,
parameter classes, the experiment-to-simulation validation chain, the preregistered acceptance
criterion, error-budget components, and observable/regime coverage status. If research stops, label
the report with the justified-stop reason and claim ceiling; do not format it as a selected-model
report. For calibration or physical-validation claims, show the `calibration_plan.yaml` version,
status, fit/held-out split, frozen-fit binding, uncertainty method, and passed report section; a
rendered status word cannot substitute for those artifacts.

Keep YAML files, Markdown reports, registries, simulation specifications, and validation reports unchanged. The PDF must incorporate the theory in readable prose, equations, tables, and prediction evidence; a solver name is never a substitute for its governing model. Render the PDF to images and visually inspect every page before delivery; report generation does not confer scientific acceptance.

For a continuing simulation case, render the separate scientific/software readiness records and
claim ceiling. Identify whether the package is handoff-only, implementation-ready, runnable on a
synthetic benchmark, runnable with apparatus inputs, executed but unverified, numerically verified,
or experimentally compared. Do not label a README-plus-shell handoff as a runnable simulation
package, and do not turn a synthetic receipt into experimental evidence.

## Simulation-stage solver references

For every simulation-stage prompt, create and validate `reports/solver-usage-catalog.md` and `reports/solver-usage-catalog.pdf`, plus `provenance/solver-inventory.yaml`, installation record, software citations, and license record. For every batch, create/update `reports/solver-mechanism-compendium.md/.pdf`, `data/batch-solver-index.yaml`, `data/solver-prompt-matrix.csv`, and batch software citations. Use `tools/solver-documentation/solver_documents.py` to scaffold, validate, and render these artifacts.

The catalog documents what was actually used for one prompt: exact solver/version/origin/license, install/platform/runtime provenance, modules, algorithms, physical equations, configuration, theory-to-solver mapping, inputs/outputs, verification, validation, limitations, reproduction, and citations. The batch compendium explains each actual solver once: relevant physical equations, numerical formulation/discretization, integration, coupling, linear/nonlinear solve, stability, convergence, errors, prompt usage, verification, and references. Do not call a solver’s numerical algorithm the physical cause; do not duplicate full solver chapters in prompt reports. Read [solver-documentation.md](references/solver-documentation.md) before producing either artifact.
