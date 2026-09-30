---
name: pt-simulation-router
description: Select exactly one scientifically appropriate open-source primary solver for an orchestrator-approved PT model, record OpenFOAM suitability, define evidence-based escalation and platform requirements, and hand off a locked solver choice to the runtime layer. Does not install, package, generate, or run simulations.
---

# PT Simulation Router

Choose by dominant governing equations, not by familiar software or a word in the prompt. This specialist is invoked only by `pt-orchestrator` after the selected physical model has passed its gate. Treat a Python/NumPy/SciPy ODE, optimization, quadrature, Fourier calculation, or reduced-order integration as a numerical route when it executes code; reserve `analytical_closed_form` for a result that requires no numerical execution.

## Calibration and validation boundary

When a model has adjustable parameters, create the version-1 `calibration_plan.yaml`
scaffolded by the case generator before fitting. The plan records the source and
content hash of the data, units and uncertainty for every measured variable, the
predeclared objective and acceptance threshold, parameter bounds and identifiability
method, and an observation index with group and replicate IDs. A fit may use only the
predeclared fit IDs. Its frozen local artifact must be hash checked and must carry the
same model ID, fit-data hash, parameter values, and objective value as the plan.

Numerical verification, parameter calibration, and independent physical validation are
separate evidence levels. A mesh/time-step or analytic benchmark can pass numerical
verification without calibrating a parameter. A frozen fit can pass calibration without
validating the physical model. Physical validation requires a separate
`validation_report.yaml` physical-validation section with held-out observation IDs,
disjoint groups/replicates when present, measurement uncertainty, a computed comparison
metric, and a hash-backed evidence locator. A calibration fit is never reused as that
held-out comparison. If no parameter is fitted, set `status: not_required`, give a
scientific `not_required_justification`, and validate the frozen model/config and input
artifacts instead. Failed outcomes are recorded with a failure reason and cannot advance
the state. The semantic gates in `scripts/calibration_contract.py` enforce these rules;
the schema alone is not sufficient.

Persist the exact chain `Phenomenon -> Physics -> Governing equations -> Numerical requirements ->
Solver` in `selection_chain`. Each governing equation ID must resolve to the theory registry, and
each numerical requirement must follow from those equations, regimes, geometry, or requested
observables.

## Require inputs

Require `problem_contract.yaml`, `essence_and_chain.yaml`, `model_registry.yaml` with one selected model, governing equations/assumptions, geometry/parameter ranges, observables, and validation targets. Refuse routing when these conflict or cannot predict the prompt observable.

## Mandatory decision block

Before any installation, coding, package build, or substantial run, write this complete block in `simulation_route.yaml` and the human report:

```text
Problem:
Dominant physics:
Primary solver:
OpenFOAM classification: Primary / Optional / Unsuitable
Single-solver baseline:
Auxiliary analytical or empirical model:
Target platform: pending user choice / known target
CPU architecture:
GPU requirement:
Native or containerized:
Expected evidence level:
Known missing physics:
Escalation condition for a second solver:
```

`primary_solver` is exactly one of OpenFOAM, HCIPy, Project Chrono, Elmer FEM, YADE, Python/SciPy, or `No numerical solver`. Supporting scripts, Gmsh, ParaView, NumPy/SciPy/Matplotlib, geometry generators, analytical relations, interpolation, ray-reflection and image-convolution postprocessors are auxiliary tools, not a second independent solver.

## Single-solver-first hierarchy

Use this order: (1) one solver with built-in physics; (2) that solver plus transparent analytical/empirical relation; (3) that solver plus a precomputed lookup table; (4) sequential second solver; (5) one-way dynamic coupling; (6) two-way co-simulation. Do not select `hybrid` initially merely because the phenomenon is multiphysics.

Before a second independent numerical solver, add a `Why one solver is insufficient` section and `second_solver_escalation` record with: failed prediction and experimental comparison; missing effect and order-of-magnitude importance; why an auxiliary relation or lookup table is inadequate; interface variables with units/signs; sequential/one-way/two-way classification; conservation or compatibility condition; coupling-step sensitivity; full validation plan; reproducibility/complexity assessment; and whether the conclusion is likely to change. If any item is unknown, do not add the solver.

## Solver set and OpenFOAM gate

- **OpenFOAM:** primary for continuum fluid flow, free surfaces/multiphase, rotating flow, flow-induced motion, suitable compressible acoustics, conjugate heat transfer, effective melting, and justified non-Newtonian laws.
- **HCIPy:** scalar wave optics, Fresnel/Fraunhofer propagation, diffraction, PSFs, defocus/aberrations and synthetic image formation. Do not add ray tracing by default.
- **Project Chrono:** rigid/multibody motion, joints, rolling/sliding, frictional contact, impact, prescribed forces, suitable flexible bodies, and supported Chrono::FSI.
- **Elmer FEM:** structural vibration, membrane deformation, piezo/electromechanics, acoustics, electromagnetics, and coupled finite-element PDEs.
- **YADE:** discrete particles, cohesive contact, fragmentation hypotheses, granular networks, and exploratory deposited-particle models.

OpenFOAM is **Primary** only if continuum conservation/transport fields dominate. It is **Optional** when it can provide a separately justified calibration or lookup table. It is **Unsuitable** for scalar optics, low-dimensional mechanics/contact, or specialized electromechanical solids. Never select it from a fluid-like keyword.

## Required route artifact

First write `solver_requirements.yaml` from the closed model: fields/degrees of freedom,
geometry/moving interfaces, constitutive laws, coupling, regimes, outputs, stiffness/discontinuities,
verification benchmarks, dimensionless groups/regime identification, and why simpler tools are
insufficient. Refuse a route when closure is blocked or unresolved.

Then write `simulation_route.yaml` with at least the schema fields plus `auxiliary_models`,
`evidence_label`, `known_missing_physics`, a complete `second_solver_escalation` object, rejected
routes and residual uses. For a staged workflow, name each solver's distinct closed physics,
one-way interface quantities/units, and verification; never use a solver to fill a missing
constitutive law. Write `simulation_spec.yaml` with equations, material/constitutive assumptions,
dimension/mesh or sampling plan, conditions, quantities/units, verification, physical validation,
convergence method, failure signatures, and limitation boundaries. Do not invent version-specific
solver names. Before handing the route to the packager, state `scientific_readiness: model_closed`
and make the software target `handoff_only` until a real implementation and synthetic receipt exist.

Return to `pt-orchestrator`. Do not install software, generate a project, or execute a case. Include the exact locked solver version from `tools/solver-runtime/solver-locks.json`; version selection is not deferred to an installer or package recipient.
