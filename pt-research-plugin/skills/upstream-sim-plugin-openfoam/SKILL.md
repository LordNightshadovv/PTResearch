---
name: upstream-sim-plugin-openfoam
description: Audit an orchestrator-approved OpenFOAM simulation specification for solver-family, fields, dictionaries, boundaries, numerics, and distribution compatibility. Explicit-only specialist; does not generate or run cases and does not replace the selected physical model.
---

# sim-plugin-openfoam PT bridge

Read [pt-bridge.md](references/pt-bridge.md), then consult `upstream-original/SKILL.md` and its references. Probe the local distribution before recommending syntax. Do not mix Foundation and OpenCFD/ESI dictionaries. Produce `openfoam_design_review.yaml` with supported, unsupported, mismatched, and unresolved requirements, exact runtime provenance, and validation/coverage implications before case generation. Treat design review as compatibility evidence only; it cannot advance numerical, calibration, or physical-validation stages.
