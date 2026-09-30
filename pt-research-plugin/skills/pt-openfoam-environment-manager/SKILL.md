---
name: pt-openfoam-environment-manager
description: Inspect and prepare an OpenFOAM runtime, discover tutorials, record solver/tool/library availability, and hand off locked official-source installation or tested packages. Use only under pt-orchestrator after an OpenFOAM route is selected; never install or execute without user authority and artifact gates.
---

# PT OpenFOAM Environment Manager

Treat OpenFOAM availability as evidence, never as an assumption. Use `tools/openfoam-runner/probe_openfoam.py` to write `dependency_report.yaml` and `runtime.yaml` before designing or running a case.

## macOS roles

- Use a reference environment to inspect solvers, tutorials, dictionaries, and physical models.
- Use a local testing environment for generated-case syntax, `checkMesh`, and solver-startup failures.
- Use a small-simulation environment only for lightweight debugging or short studies. Recommend Linux export when the mesh, runtime, memory demand, parallelism, or parameter count is material.

## Installation and tutorials

First inspect with `python tools/solver-runtime/solver_runtime.py inspect --solver OpenFOAM --output dependency_report.json`. If the locked version is already available, verify its version and reuse it. If it is absent and the user has authorised execution on the current computer, use `python tools/solver-runtime/solver_runtime.py install --solver OpenFOAM --authorized`, which fetches only from the locked official source; then re-inspect. Without that authority, emit only an installer or container recipe. Locate a comparable validated tutorial before adapting a complex case. Record `openfoam/tutorial_reference.yaml` with solver, original case, adapted purpose, and every modification.

## Execution choice

Ask exactly: “Would you like this simulation to be run immediately on this computer, or would you like a Linux Ubuntu simulation package to run elsewhere?”

For local execution, require the selected solver, mesh tools, post tools, required libraries, a mesh check, solver completion, convergence/timestep evidence where applicable, and a predeclared observable-aware validation criterion. Record exact commands, runtime/version/input/output hashes, warnings, and numerical error separately from calibration/model-form error. Physical validation still requires the version-1 calibration plan and independent held-out report; a solver exit code is not acceptance.

For Linux export, use the shared simulation-package generator (and
`tools/openfoam-runner/export_linux_package.py` when a native case exists) with a matching passed
target receipt. Keep generated scripts editable and require a real implementation, synthetic
benchmark, state-aware gate, machine-readable extractor, and receipts. A platform smoke receipt
proves only the OpenFOAM runtime; do not claim the exported case ran on Linux until its own logs
and validation artifacts return.
