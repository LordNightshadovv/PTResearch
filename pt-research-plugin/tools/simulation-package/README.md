# PT simulation package templates

generate_package.py is the reusable template entrypoint for the supported numerical routes.
Each generated package has the same portable contract:

- a real source module or solver-native input surface;
- separated controls, material properties, geometry, initial/boundary conditions,
  calibration parameters, derived quantities, state variables, observables, and uncertainties;
- a clearly labelled deterministic synthetic example;
- a case generator, state-aware run gate, real system/dependency check, runner, and
  machine-readable result extractor;
- equation-to-code and parameter-to-destination records;
- a machine-readable three-level numerical-verification plan;
- tests and run receipts with input/case/output hashes.

The synthetic implementations are deliberately dependency-light so the plugin test suite can
exercise every route on a clean host. They are implementation/syntax smoke paths, not external
solver executions and not experimental evidence. Production mode remains blocked until the locked
solver/runtime and measured apparatus inputs have their own evidence.

Run `bash run.sh` for the synthetic receipt. After that receipt exists, a measured input may be
run with `bash run.sh --apparatus <measured-input.json>` only when its metadata declares
`measured: true` plus provenance and its input contains uncertainty records; this writes a separate
apparatus receipt and advances only to `runnable_apparatus`.
