---
name: upstream-cfd-mesh-gate
description: Gate OpenFOAM scientific acceptance through observable-aware mesh and transient time-step sensitivity artifacts. Explicit-only specialist invoked by pt-orchestrator after an accepted baseline; does not choose models or treat fixed universal thresholds as truth.
---

# CFD mesh-gate PT bridge

Read [pt-bridge.md](references/pt-bridge.md), then consult `upstream-original/SKILL.md`. Require a generated baseline, validation targets, and a predeclared numerical acceptance criterion bound to the observable and its error budget. Preserve every mesh/time-step level, failed result, input/output hash, and coverage gap. Choose thresholds from observable uncertainty and research purpose; require time-step sensitivity for transient cases. Report numerical/discretization error separately from calibration and model-form error. Return results to the orchestrator; only a passed machine-readable report can support `numerically_validated`, and this gate never establishes physical validation.
