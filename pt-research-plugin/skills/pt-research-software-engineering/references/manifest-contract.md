# Engineering-standards manifest contract

File: `engineering_standards.yaml` (JSON-compatible YAML). Schema: `schemas/engineering-standards.schema.json`. Semantic gates: `scripts/engineering_contract.py`. CLI: `scripts/validate_engineering_standards.py`.

## What validation proves

- the declaration is complete for its `status`;
- its parts are internally consistent (for example, a GUI declares a headless core, thin layer, and accessibility; a required numerical verification has a convergence test);
- every referenced project file (ADR, changelog, config, CI file, tests, evidence) exists, as a safe relative path.

## What validation does not prove

It runs no test and measures no accuracy. It does not establish that the code is correct, that a test passes, that the physics is right, or that a result is validated. Fields `validation_scope: declaration_and_structure_only` and `claim_ceiling` make this explicit in every manifest.

## Status

| status | Meaning |
|--------|---------|
| `not_started` | no code yet; case scaffold default; passes trivially |
| `declared` | code produced; every section below is complete |
| `not_applicable` | no code is produced; needs `not_applicable_justification` |

## Evidence status

`planned` (not written) < `implemented` (exists; no claim it passes) < `evidenced` (a retained receipt exists at `evidence`, a project-relative file).

## Sections required when `declared`

`project` (name, semantic `version`, `versioning: semantic`, `changelog`, `design_notes`, `requires_python`); `stack_decision` (`adr_path`, `language`, `paradigm`, `selected`, >= 2 `alternatives_considered`, optional `reinvention_exceptions`); `interface`; `quality_tooling` (linter, formatter, type_checker, test_runner, ci_config_path); `dependency_management` (tool, manifest_path, lockfile, `lockfile_status` committed or pending_generation, pinning_policy); `configuration`; `logging_and_error_handling`; `test_plan.tests` (id, kind, path, evidence_status); `numerical_verification` (required, methods, positive tolerances, convergence_criterion, or a justification when not required); `physical_correctness` (units_policy, dimensional_analysis, limiting_cases, symmetry or justification, benchmarks or justification, assumptions_registry); `uncertainty_treatment` (methods, five separated error_sources); `experiment_comparison` (planned with metrics, error-bar overlay and fit/validation separation, or a justification); `reproducibility` (seed_policy, deterministic_outputs, run_metadata_writer, run_metadata_fields including timestamp_utc, git_commit, python_version, dependency_versions, config_hash, seed, platform, input_hashes; environment_lock); `documentation` (readme, assumptions_section true, verification_plan).

Test-plan coverage rules: always a `unit` test; with required numerical verification a `convergence` test plus an `analytic_benchmark`, `limiting_case`, or `conservation` test; with a units policy a `dimensional` test.

## Case integration (PT cases)

A case opts in with `engineering_contract_version: 1` in `project_state.yaml` (new scaffolds do). `validate_artifacts.py` then requires `engineering_standards.yaml` and enforces by software readiness:

| software_readiness | Requirement |
|--------------------|-------------|
| `implementation_ready` or higher | status `declared` |
| `executed_unverified` or higher | `lockfile_status: committed` |
| `numerically_verified` | `numerical_verification.required` with `evidence_status: evidenced` and an existing receipt |
| `experimentally_compared` | `experiment_comparison.planned` with `evidence_status: evidenced` and an existing receipt |

Cases without the version stay valid as legacy and are not claimed to follow these standards. Packages produced by `tools/simulation-package/generate_package.py` predate this contract and carry no manifest; their claim ceiling is unchanged.

## Scaffold

`python scripts/scaffold_research_software.py <dir> --name <project> --interface cli` writes a project whose manifest declares what it contains: tests `implemented` (not evidenced), lockfile `pending_generation`, claim ceiling "declaration and file structure only".
