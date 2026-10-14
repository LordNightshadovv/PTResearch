# Engineering standards for PT research code

These standards apply to every code-producing PT stage. They are mandatory in scope and proportionate in size: a 50-line prediction script still needs units, a seed, a test, and a recorded command; it does not need a GUI or a plugin architecture.

## 1. Plan and document before implementing

- **Requirements note:** observable(s) and units, controlled inputs and ranges, outputs, accuracy target, runtime budget, target platform, who runs it.
- **Design note:** data flow from config to results, module boundaries, model-form and numerical decisions with the test that guards each, error modes.
- **Assumptions registry:** every modelling assumption with its regime of validity and a check that would reveal violation (kept in the README "Assumptions and validity range" section). An unlisted assumption is a defect.
- **ADR:** stack and structure decision (see [stack-selection-and-adr.md](stack-selection-and-adr.md)).

## 2. Architecture and design

- **Headless core, thin interfaces.** Numerical and physical logic lives in an importable, typed package. CLIs, GUIs, notebooks, and plots call it; they contain no physics.
- **Modularity.** Separate model (equations), solver (numerics), experiment (orchestration), analysis (uncertainty, fit, comparison), I/O (config, provenance), and interface. Dependencies point inward to the core, never back.
- **OOP only where it pays:** abstractions with interchangeable implementations (Model, Solver, Experiment protocols). Use pure functions for stateless numerics and frozen dataclasses for data. Justify the paradigm per module in the ADR; no inheritance for its own sake.
- **Typed interfaces.** Full annotations, `mypy --strict` (or equivalent), `py.typed`, immutable value objects, explicit units in names (`mass_kg`, `t_s`) and in Pint quantities at boundaries.
- **Prefer libraries to reinvention.** Reimplement only with a recorded reason (transparency for a verification stand-in, a missing capability, a measured performance need).

## 3. Implementation hygiene

- **Version control:** one logical change per commit, no generated data or secrets committed, `.gitignore` for outputs and caches, tags for releases, record the commit in run metadata. Do not commit or push without user authority.
- **Linting and formatting:** ruff (check + format) or equivalent, configured in `pyproject.toml`, run in CI.
- **Automated tests:** pytest (+ hypothesis for properties), run in CI on the oldest and newest supported Python.
- **CI-ready:** a workflow file running format, lint, types, tests from a frozen lockfile.
- **Semantic versioning and changelog:** `MAJOR.MINOR.PATCH`; Keep-a-Changelog style. A change to an equation, default parameter, or output schema is user-visible and belongs in the changelog; bump MINOR for new behavior, MAJOR for incompatible output or model changes.
- **Dependencies:** bounded ranges in `pyproject.toml`, exact versions in a committed lockfile (`uv.lock`, `poetry.lock`, `conda-lock`, `Cargo.lock`). Never `pip install` unpinned in a retained environment.
- **Configuration separate from code:** TOML/YAML/JSON validated at the boundary (dataclasses, pydantic, or Hydra if justified). No magic numbers; units in key names; the config hash is recorded per run.
- **Logging:** `logging.getLogger(__name__)` in libraries; handlers configured only at the entry point; log parameters, tolerances, solver status, and warnings, not bulk data.
- **Error handling:** a small exception hierarchy, validation at boundaries, fail fast with actionable messages, no bare `except`, no silent fallback that changes the physics, solver success flags always checked, non-finite results rejected.
- **Determinism:** seeds come from config, use `numpy.random.default_rng(seed)` (no hidden global state), outputs sorted and serialized canonically so reruns are byte-identical; timestamps and host facts go in metadata, not results.

## 4. What the plugin enforces

`engineering_standards.yaml` (schema `engineering-standards`) must declare: project and semantic version; stack ADR with at least two alternatives, paradigm and language justification; interface kind and, for GUI/TUI, thin-layer and accessibility declarations; tooling (linter, formatter, type checker, runner, CI file); dependency lockfile status; configuration path; logging and error-handling approach; a test plan covering unit, dimensional, convergence (when numerical verification is required) and benchmark/limiting-case/conservation tests; numerical verification tolerances and criterion; physical-correctness checks; uncertainty methods with the five separated error sources; experiment-comparison plan; reproducibility metadata fields. See [manifest-contract.md](manifest-contract.md). The validator proves the declaration is complete and consistent and that referenced files exist. It does not run anything.

## 5. Definition of done for a code-producing stage

1. Requirements/design notes and ADR exist.
2. The command that runs the tests is recorded and its output retained as a receipt.
3. Lint, format, and type checks pass, or the tool is recorded as unavailable.
4. The lockfile is committed, or the stage is labeled not reproducible.
5. The assumptions registry, limitations, and claim ceiling are in the README.
6. The manifest validates and the handoff states what was and was not run.
