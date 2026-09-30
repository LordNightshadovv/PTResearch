---
name: upstream-cfd-experiment
description: Execute an accepted OpenFOAM baseline or controlled parameter matrix and persist per-case outcomes. Explicit-only specialist invoked by pt-orchestrator after baseline and mesh gates; does not infer validity from process completion or change the selected model.
---

# CFD experiment PT bridge

Read [pt-bridge.md](references/pt-bridge.md), then consult `upstream-original/SKILL.md`. Do not start a sweep before baseline acceptance and a frozen experiment matrix with predeclared observables, thresholds, uncertainty method, falsifiers, and coverage rows. Keep parameter provenance, input/output hashes, and split membership; isolate changes and retain every failure. If parameters are fitted, use `calibration_plan.yaml` v1 and keep fit records out of held-out validation. Classify numerical failure, physical invalidity, and scientifically non-informative success separately. A solver exit code alone never establishes validity or acceptance. Return receipts and partial outcomes for orchestrator acceptance.
