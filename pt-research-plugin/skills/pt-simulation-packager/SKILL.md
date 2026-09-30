---
name: pt-simulation-packager
description: Create a beginner-friendly reproducible package for an orchestrator-approved single-solver PT simulation on Ubuntu Linux or macOS, with native-versus-container truthfulness and smoke-test evidence. Does not install or execute without user authority.
---

# PT Simulation Packager

Use only through `pt-orchestrator` after a valid single-solver route/specification and a target-platform decision. Read [packaging policy](references/cross-platform-packaging.md) before producing files.

Keep calibration evidence separate from package smoke evidence. If the package exposes a
parameter-fitting path, include the case's version-1 `calibration_plan.yaml` and require its
predeclared objective, units, uncertainty metadata, bounds, identifiability evidence, and
disjoint fit/held-out observation, group, and replicate IDs. A frozen fit is accepted only
when a local hash-backed record agrees with the declared model ID, fit-data hash, parameter
values, residual metric, and numerical-error tolerance. A deterministic synthetic receipt
is numerical/software evidence; it is neither a calibration result nor physical validation.

Set `software_readiness: numerically_verified` only after the machine-readable numerical
verification section passes with a computed metric and receipt. Set
`software_readiness: experimentally_compared` only after a separate
`validation_report.yaml` physical-validation section compares held-out observations with
measurement uncertainty and a quantitative criterion. The calibration fit must not appear
as that held-out comparison. For a model with no fitted parameters, record
`calibration_plan.yaml` with `status: not_required` and a scientific justification, then
hash the frozen model/config and input artifacts used for independent validation. A failed
fit or comparison is a valid recorded outcome but cannot advance the claim state.

When the information is not already recorded, ask the user to choose exactly one execution mode: (1) run locally now if the locked solver is available, (2) produce a Linux/Ubuntu package for execution elsewhere, (3) produce both a local execution plan and a Linux/Ubuntu package, or (4) produce only research artifacts and stop before implementation. For modes 1-3, also record current computer, target OS, CPU architecture, GPU/CUDA/ROCm/HIP/memory, and container permission. Mode 4 must preserve a scientific stop or model-closure handoff and must not claim an implementation or runnable package.

Use `tools/solver-runtime/solver_runtime.py` and its checked-in `solver-locks.json` for every primary solver. First inspect the current computer. If the selected locked version is present, verify and reuse it. If it is absent, only install with `install --authorized` after explicit user authority. For another computer, emit `installer --solver <name> --target <target>` rather than redistributing a binary. For a container target, include the matching checked-in `Containerfile`; call it Linux-in-a-container, never native macOS. A container cannot supply a missing GPU backend.

For an offline request, make a separate package per OS, CPU architecture, and GPU backend. Include only legally redistributable source archives, Python wheels, installers, or container-image archives; otherwise write `OFFLINE-MISSING.md` naming the official files the recipient must obtain. Never include proprietary or license-restricted binaries. Verify current instructions only from official project sites, repositories, package channels, or OS repositories; pin releases, retain logs/tutorials, use checksums where offered, and explain admin privileges before requesting them.

Treat the route-appropriate Linux package as an adapter/case package for externally installed or
separately installable software; embedding the solver is not required. Create
`simulation_handoff.yaml` with separate `scientific_readiness` and `software_readiness`
fields. Use `handoff_only` for documentation-only legacy plans, `implementation_ready` when
the executable implementation exists, `runnable_synthetic` after the deterministic synthetic
benchmark receipt, `runnable_apparatus` after validated measured inputs, `executed_unverified`
after a solver run, `numerically_verified` after passed machine-readable verification, and
`experimentally_compared` after held-out comparison with uncertainty. Never translate
`installation_package_prepared` or `parameter_handoff_validated` into a runnable state.

Create the package only after user authority. A route package must include executable source or
solver-native inputs, a case generator, result extractor, separated input schema, synthetic example,
real system check, state-aware run gate, tests, machine-readable verification plan, equation/code
traceability, and `receipts/`. `package` also requires a passed
`solver_smoke_receipt.json` for the exact solver version, target OS/architecture, and declared GPU
backend; that receipt proves only the external runtime, never the case. It must fail rather than
claim a runnable solver if no receipt exists. Include an official
installation source and granular documentation locator, dependency/architecture checks, environment
activation, official smoke test, apparatus-specific parameter template with units/uncertainty/
provenance/ranges, parameter-to-input map, native inputs or an honestly declared generator,
boundary/initial conditions, discretization and convergence controls, observable extraction,
verification benchmarks, physical-validation plan, and beginner README with copy-paste commands.
Before packaging, require at least one complete validation chain:
`Experiment measurement -> Simulation input -> Solver quantity -> Output metric -> Comparison
method`, with uncertainty treatment and a quantitative acceptance criterion. Reject a generic
“compare with experiment” statement.
Also include PLATFORM.md, launchers, locks, failure/restart assets, machine-readable outputs,
CITATIONS.md, LICENSES.md, and report source. State explicitly that no run occurred unless an
execution receipt exists.

Run and retain the applicable official smoke test before the research case: HCIPy aperture diffraction vs analytic result; Chrono relevant rigid/contact demo plus constraints/energy; Elmer relevant official PDE example plus convergence/export; YADE contact/cohesive example plus time-step stability; OpenFOAM closest tutorial plus mesh/residual/conservation/postprocess checks. Also run the package's deterministic synthetic benchmark. A synthetic receipt tests the implementation surface only; an external smoke test or solver exit is not scientific acceptance.

Return a `runtime.yaml`, `simulation_package_manifest.yaml`, platform record, and dependency report to the orchestrator. State the highest accepted stage and every untested target.

For a user-approved dedicated remote Linux target, do not copy solvers, images, credentials, SSH keys, or generated results into this plugin. Hand the locked solver/package plan to `pt-remote-execution`; it provides alias-only SSH transfer, persistence, status, and retrieval while retaining these packaging and smoke-test gates.
