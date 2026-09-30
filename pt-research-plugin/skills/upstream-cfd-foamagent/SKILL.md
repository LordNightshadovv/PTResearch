---
name: upstream-cfd-foamagent
description: Generate a candidate OpenFOAM case from an orchestrator-validated simulation specification using the pinned Foam-Agent workflow. Explicit-only specialist; does not choose the physical model or route, and cannot claim numerical or physical acceptance.
---

# CFD FoamAgent PT bridge

Read [pt-bridge.md](references/pt-bridge.md), then consult `upstream-original/SKILL.md`. Require `simulation_spec.yaml`, a compatible OpenFOAM probe, a passing design review, and a frozen validation/coverage target. Use `tools/foam-agent/run_foam_agent.py` only after explicit execution approval. Emit a case manifest, mismatch ledger, dependency report, provenance hashes, and generated-case status separately. Preserve unresolved requirements and partial generation. Never simplify the selected physics silently and never call a generated case calibrated, numerically validated, or physically validated.
