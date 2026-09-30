# Runnable simulation contract

Scientific and software readiness are independent records.

## Readiness records

project_state.yaml and simulation_handoff.yaml record both:

- scientific_readiness: scientific_stop, model_selected_not_closed, or model_closed.
- software_readiness: not_applicable, handoff_only, implementation_ready,
  runnable_synthetic, runnable_apparatus, executed_unverified, numerically_verified, or
  experimentally_compared.

handoff_only is retained for unresolved implementation plans and legacy migrations. It never
supports a runnable claim. A continuing route must reach model_closed scientifically and must
contain the implementation layer before package completion.

## Package minimum

linux-simulation/ must contain the equivalent of:

    README.md
    install.sh or environment.yml
    check_system.sh
    run_gate.sh
    parameters.schema.json
    examples/synthetic.json
    src/ or solver-native case/
    generate_case.py or equivalent
    run.sh / Allrun
    extract_results.py or equivalent
    tests/
    numerical-verification.json
    numerical-verification.md
    receipts/
    simulation_package_manifest.json
    parameter-map.json
    equation-lineage.json

The implementation must validate separated inputs, generate a native case or execute a numerical
model, run a deterministic synthetic benchmark, and write machine-readable results. It must fail
clearly for missing dependencies, invalid inputs, absent case generation, and missing evidence.

Input files contain controls, material_properties, geometry, initial_conditions,
boundary_conditions, calibration_parameters, derived_quantities, state_variables, observables,
and uncertainties. Derived/state/output fields are empty in a synthetic input unless a field is
explicitly marked as an imported measured field with provenance.

Each mapping names a concrete destination and implementation file/function. Each implemented
equation records the theory equation ID, source locator, notation conversion, units,
discretization/approximation, and implementation assumptions. Placeholder destinations such as
apparatus-specific input and measured range are invalid.

## Evidence

Every command that executes a package writes a receipt with timestamp, platform, package/solver
version, package revision when available, exact command, input and generated-case hashes, exit
status, runtime, output hashes, warnings, errors, and validation state. runnable_synthetic requires a passed synthetic receipt. runnable_apparatus additionally requires a measured input with provenance/uncertainty and a separate apparatus receipt. numerically_verified
requires an executed and passed machine-readable three-level verification plan. Experimental
comparison requires held-out measurements and uncertainty treatment.

--allow-partial is inspection-only. Its output must say handoff-only and must never satisfy the
runnable package contract.
