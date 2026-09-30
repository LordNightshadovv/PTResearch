---
name: upstream-cfd-code-modify
description: Build a case-local custom OpenFOAM model only from an approved mathematical specification with units, limits, dependencies, and tests. Explicit-only specialist invoked by pt-orchestrator when installed capabilities cannot represent the selected model; does not invent missing mathematics.
---

# CFD code-modification PT bridge

Read [pt-bridge.md](references/pt-bridge.md), then consult `upstream-original/SKILL.md`. Require `approved_custom_model_spec.yaml` plus a predeclared acceptance/falsifier record. Keep code case-local, record source and artifact hashes, check dimensions/symbols, compile with a bounded repair loop, and run limiting/smoke tests. Separate implementation, numerical, calibration, and model-form error; preserve failed repairs and the baseline diff. Never edit the OpenFOAM installation or compile before `wmake` and distribution compatibility are verified. Return only a case-local implementation receipt; the orchestrator owns stage advancement.
