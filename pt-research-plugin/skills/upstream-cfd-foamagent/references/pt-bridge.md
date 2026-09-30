# PT bridge

Input: validated `simulation_spec.yaml` and OpenFOAM design review. Probe dependencies before generation. Output a machine-readable case manifest and mismatch ledger. Status may be `dependency_blocked`, `case_generated`, or `solver_completed`; only the orchestrator can advance acceptance.
