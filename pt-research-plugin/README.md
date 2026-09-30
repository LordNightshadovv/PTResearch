# PT Research plugin

## Runnable simulation contract

Scientific readiness and software readiness are separate. A continuing case records
scientific_readiness as scientific_stop, model_selected_not_closed, or model_closed, and
software_readiness as not_applicable, handoff_only, implementation_ready, runnable_synthetic,
runnable_apparatus, executed_unverified, numerically_verified, or experimentally_compared. A
handoff-only package is never a runnable package.

Use the reusable generator to create a route-specific package with executable source/native input,
separated parameter categories, a synthetic example, real system and run gates, a case generator,
machine-readable extraction, equation/code traceability, a three-level verification plan, and
receipts:

    python3 tools/simulation-package/generate_package.py --route python_ode --output /tmp/pt-python-ode
    cd /tmp/pt-python-ode
    bash check_system.sh --mode synthetic
    bash run_gate.sh
    bash run.sh

The synthetic result is software evidence only. It does not establish solver installation,
numerical convergence, apparatus fidelity, or experimental agreement. The allow-partial flag
remains inspection-only and reports handoff-only.

Scientific acceptance is a separate, preregistered evidence lane. Before fitting, execution, or
comparison, freeze the observable, metric/formula, units, threshold, falsifier, data split,
uncertainty method, input/software hashes, and evaluator. Keep calibration fit data separate from
held-out physical-validation data and report measurement, calibration, numerical, sampling, and
model-form uncertainty separately. See
`skills/pt-theoretical-research/references/validation-and-reproducibility.md` and the version-3
contract for the required coverage and claim-ceiling rules.

Calibration and physical-validation claims require `calibration_plan.yaml` with
`calibration_contract_version: 1`. A new scaffold starts with status `planned` and cannot claim a
passed calibration or physical validation; a physical-validation claim additionally requires a
passed held-out comparison and `physical_validation` report. Missing dependencies or data produce
an explicit partial result with blockers and resumption conditions.

Supported generated routes include fourier_optics, elmer_fem, openfoam_continuum, project_chrono,
yade, python_ode, python_optimization, and reduced_order_model.

An installable Codex plugin for auditable IYPT/CYPT research: preserve the prompt, reconstruct the
apparatus, build and compare candidate mechanisms, close equations and parameter mappings, audit
equation lineage and positive/negative evidence, identify regimes, and derive solver requirements
before selecting software. A result may remain unresolved or stop explicitly for insufficient
literature, missing data, or an unresolved mechanism. OpenFOAM is one gated branch, not a keyword
default.

## Architecture

```text
user / AGENTS.md / default prompt
              |
       pt-orchestrator
       /             \
theoretical chain   simulation router
 |  |  |                 |
K-Dense + DeerFlow    physics suitability gate
                         |
       target platform -> native/container package -> solver smoke test
                         |
         OpenFOAM only: design -> Foam-Agent -> mesh gate -> experiment
              |
       schemas + run artifacts + acceptance gates
```

The orchestrator is the only implicitly invocable skill. The other native skills and all upstream specialist bridges require explicit orchestration or an explicit user request. Original upstream content remains under each specialist's `upstream-original/`; runtime research never downloads moving upstream content.

## Included skills

Native: `pt-orchestrator`, `pt-theoretical-research`, `pt-simulation-router`, `pt-simulation-packager`, `pt-openfoam-environment-manager`, and `pt-report-renderer`.

Remote execution is an explicitly orchestrated specialist: `pt-remote-execution`. It connects to a dedicated non-root Linux account through an existing OpenSSH host alias such as `pt-linux`; it never reads private-key contents, passphrases, passwords, tokens, or `~/.codex/auth.json`. See `skills/pt-remote-execution/references/remote-execution.md` for the approval-gated bootstrap and operations workflow.

Vendored specialist bridges: K-Dense literature review; DeerFlow systematic literature review and paper review; AI-CFD-Scientist FoamAgent, mesh gate, experiment, and code modification; and sim-plugin-openfoam. `tools/foam-agent/` preserves the executable Foam-Agent framework separately from its skill bridge.

## Install

Codex plugins are installed from a marketplace. For the default personal marketplace, the local
source is `~/plugins/pt-research-plugin`; after copying a reviewed release there, run:

```text
codex plugin add pt-research-plugin@personal
```

The default personal marketplace is discovered implicitly; do not add it with
`codex plugin marketplace add`. Restart Codex or begin a new session after installation so bundled
skill metadata is discovered. This repository deliberately does not modify the user's personal
marketplace as a build side effect.

For an existing local plugin update, use the Plugin Creator helpers instead of hand-editing the
marketplace or incrementing the base semantic version merely to refresh the cache:

```text
python3 /Users/vold/.codex/skills/.system/plugin-creator/scripts/read_marketplace_name.py
python3 /Users/vold/.codex/skills/.system/plugin-creator/scripts/update_plugin_cachebuster.py ~/plugins/pt-research-plugin
codex plugin add pt-research-plugin@personal
```

The cachebuster preserves the base version and replaces only its `+codex.*` suffix. Start a new
Codex task after reinstalling so the updated skills are loaded. Keep the workspace source and the
marketplace source distinct until the reviewed release has been synchronized deliberately.

To use the repository directly during development, keep `AGENTS.md` in scope and ask: “Use PT Research to investigate this exact IYPT prompt …”. The normal selector is `$pt-orchestrator`. For inspection/debugging only, explicitly select a specialist such as `$upstream-cfd-mesh-gate`; its result is not integrated or accepted until the orchestrator validates its returned artifacts.

## Dependencies and capability levels

The dependency policy declares Python 3.10+ for scaffolding, validation, provenance, calibration
checks, and tests. The baseline suite was observed passing under Python 3.9.6, but that runtime is
outside the supported policy. Standard-library-only checks work without network access. Literature
searches require accessible search/browsing channels and paper text for equation-level audits.

All six numerical runtimes are optional and are managed through a locked official-source runtime layer. Before case design, inspect the selected solver and reuse it only if the installed version matches the lock:

```text
python3 tools/solver-runtime/solver_runtime.py inspect --solver OpenFOAM --output runs/CASE/dependency_report.json
```

If it is missing, the current-computer installer runs only with explicit authority: `python3 tools/solver-runtime/solver_runtime.py install --solver OpenFOAM --authorized`. A package for another computer carries a target-specific official-source installer or container recipe rather than a bundled solver binary. Offline materials are generated separately by OS, CPU architecture, and GPU backend; anything not legally redistributable is listed as an official download to obtain separately.

Missing tools force reduced-capability mode: theory, routing, or design review may continue, but no generated, executed, converged, or scientifically accepted case is claimed. A package cannot claim to be runnable until a matching smoke receipt proves the locked solver on its declared target OS/architecture/GPU backend. System-level installation and smoke execution always require the user's approval.

Before any substantial package or run, the orchestrator records whether to run on the current computer or package for another one, OS/architecture, GPU backend/memory and container permission. Native installation is preferred; a macOS launcher for a Linux container is labelled containerized Linux, never native macOS. Each package includes beginner-facing commands, platform limits, pinned versions, an official smoke test and retained logs. Render the retained research artifacts into a human report with `python3 tools/report-renderer/render_research_report.py runs/CASE --output runs/CASE/reports/research-report.pdf`.

## Durable run artifacts

Create a case without overwriting prior work:

```text
python3 scripts/scaffold_research_case.py my-case --prompt 'Exact official prompt text'
```

The result under `runs/my-case/` contains contract-version-3 prompt/apparatus records, positive and
negative claim evidence, complete equation-lineage records, a mandatory candidate-comparison table,
dimensionless regime analysis, four-way parameter classifications, a physics-first solver chain,
an experiment-to-simulation validation chain, justified stopping criteria, reports, dependency
records, timeline, and final handoff. Files use a JSON-compatible YAML subset so they remain
deterministically validated with the Python standard library. Existing v1/v2 cases remain readable
until explicitly migrated.

## Validate and test

```text
python3 scripts/validate_plugin.py
python3 scripts/validate_artifacts.py tests/fixtures/pinhole-sunglasses
python3 scripts/validate_deep_theory.py /path/to/consolidated-report-root
python3 -m unittest discover -s tests -v
```

The deep-theory and version-2/version-3 artifact validators require a standalone `theory-model.tex`,
apparatus fidelity, candidate comparison, structured equation provenance and symbol
registries, a mathematical mechanism chain, equation-generated predictions, conclusion deductions,
and a compiled PDF. They hard-reject apparatus contradictions, open mechanisms, unmapped controls,
unverified/fabricated locators, context-only quantitative laws, unsupported simulation states,
undefined forcing, generic placeholders, unsupported prediction tables, solver-first routing,
unclassified parameters, incomplete validation mappings, and raw local paths.

The official plugin and skill validators should also be run in an environment with PyYAML available. Provenance gates are independent:

```text
python3 scripts/verify_upstream_integrity.py .
python3 scripts/check_licenses.py
```

## Updating pinned upstream sources

`scripts/fetch_upstream_skills.py` and `scripts/refresh_upstream_skills.py` fetch only exact commits into a staging directory and refuse to overwrite this plugin. Review upstream diffs, licenses, security-sensitive commands, and bridge compatibility manually. Then replace preserved snapshots deliberately, update hardcoded pins and notices, run `verify_upstream_integrity.py --initialize`, and rerun every test. Never update pins during a research run.

## Known limitations

- This release includes installation/container/package integration for every routable primary solver and executable synthetic route templates. External solver execution and route-specific scientific acceptance still require the locked runtime and validation receipts; the portable templates do not imply those external runs occurred.
- Literature completeness depends on available databases and full-text access; unavailable or abstract-only sources remain explicitly labeled.
- Foam-Agent's large dependency stack is vendored but not installed automatically.
- No real OpenFOAM solve is part of the portable test suite; the suite mocks availability and tests refusal, ordering, version separation, and scientific-acceptance contracts.
- Static validators and unit tests establish artifact invariants only. They do not establish
  empirical recursive improvement, physical truth, or generalization of a workflow rule; those
  claims require independently produced, provenance-bound evidence and a sealed evaluation where
  applicable.

See `BUILD_REPORT.md` for the verified build status, `THIRD_PARTY_NOTICES.md` for licensing, and `references/upstream-adaptation-map.md` for every bridge decision.
