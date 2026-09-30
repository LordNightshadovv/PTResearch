# PT Research plugin build report

Build date: 2026-08-06  
Plugin version: 0.7.0  
Status: runnable-simulation contract implementation added; no external solver or experiment was run.

## Implemented

- One Codex plugin with a validated `.codex-plugin/plugin.json`.
- Contract v3 equation lineage, alternative comparison, negative evidence, dimensionless regime,
  parameter class, physics-first routing, simulation-validation, and justified-stop gates.
- Seven PT-native skills, including the authoritative orchestrator, theoretical synthesis, routing,
  packaging, remote execution, environment management, and report rendering.
- Eight explicit-only upstream specialist bridges with exact pinned snapshots, bridge notes, patch records, licenses, source metadata, and integrity hashes.
- Complete vendored Foam-Agent tracked tree plus a separate guarded PT wrapper.
- Twenty-two shared JSON Schemas, durable v3 case scaffolding, v1/v2 compatibility,
  cross-artifact validation, provenance/license gates, update staging, OpenFOAM probing, and
  case-model drift protection.
- Required Pinhole sunglasses, Singing capacitor, Air vortex, and unavailable-dependency fixtures.
- Separate scientific/software readiness states, explicit handoff-only ceilings, executable package
  templates for every supported route, real system/run gates, separated input schemas, concrete
  solver mappings, equation/code traceability, machine-readable verification plans, and complete
  execution receipts.

## Verification results

| Gate | Result |
|---|---|
| PT plugin validator | PASS |
| Upstream integrity | PASS: 8 specialist snapshots plus Foam-Agent |
| License/notices gate | PASS |
| Portable unit/integration suite | PASS: 80 tests |
| Runnable-simulation contract suite | PASS: 14 tests |
| Contract-v3 focused suite | PASS: 24 tests |
| Three complete artifact fixtures | PASS |
| Version-3 case scaffold smoke test | PASS in a disposable directory with `--allow-partial`; intentionally fails complete validation while empty |
| Official skill `quick_validate.py` | PASS for all 5 revised skills using PyYAML 6.0.2 in a disposable `/private/tmp` target |

## Environment probe

- OpenFOAM: not detected (`WM_PROJECT_DIR`, `simpleFoam`, `pimpleFoam`, `blockMesh`, `checkMesh`, and `wmake` unavailable). No dictionary generation, mesh, solve, convergence, or scientific acceptance was tested.
- Foam-Agent Python stack: `streamlit` detected; `langchain` and `chromadb` absent. Wrapper correctly reports reduced capability and blocks execution.
- Literature search/full text: not exercised as part of deterministic tests; research-time availability must be recorded per case.

## Upstream provenance

Pins and hashes are authoritative in `upstream-lock.yaml`. AI-CFD-Scientist is classified as MIT because the pinned repository README explicitly declares MIT under “License and citation”; there is no standalone repository `LICENSE` at that commit. This distinction is recorded in notices and all four AI-CFD source records.

## Not run

- No upstream setup/install script.
- No real OpenFOAM or Foam-Agent simulation.
- No Docker build, Conda environment creation, HPC submission, system package install, or secret-backed LLM call.
- No live scientific literature review; fixtures are structural/routing examples and explicitly not evidence for a real solution.
- No plugin installation, personal-marketplace update, or installed-cache verification.

## Remaining limitations

The generated routes provide executable synthetic adapters, but external solver execution and
route-specific scientific acceptance still require fresh source retrieval, apparatus-specific
parameterization, experimental/reference data, locked-runtime receipts, and all relevant
numerical/physical validation gates. Locator structure can be validated, but inaccessible
publications cannot be independently verified by the deterministic validator.
