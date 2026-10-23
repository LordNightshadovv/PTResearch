# Changelog

All notable changes to the PT Research plugin are recorded here. The plugin follows
[Semantic Versioning](https://semver.org/); the `+codex.<UTC timestamp>` build suffix only
refreshes the Codex plugin cache and carries no compatibility meaning.

## [0.8.5] - 2026-10-23

Workspace layout rules, so agents put each kind of output where its reader expects it.

### Added
- `AGENTS.md`: a workspace-layout rule. Gated artifacts and `openfoam/` generated cases stay in
  `<workspace-root>/runs/<case-id>/` (named `NN-slug`); heavy solver output the validator does not
  inspect goes to `<workspace-root>/data/<case-id>/<run-folder>/` and must be cited by a receipt;
  human-facing decks and PDFs go to `<workspace-root>/deliverables/<case-id>/`; session status and
  dated handoff notes go to `<workspace-root>/handoffs/<case-id>/`.
- `pt-orchestrator` SKILL.md section "Place artifacts where the workspace expects them" with the
  same four locations and the rule that the workspace `AGENTS.md` refines them.
- `cypt-slide-template` SKILL.md: finished decks and build files go under
  `<workspace-root>/deliverables/<case-id>/`, never inside the plugin or the case ledger.

### Changed
- Plugin version 0.8.4 to 0.8.5.

## [0.8.4] - 2026-10-21

Two required pages for PT decks in the CYPT slide template.

### Added
- `cypt-slide-template` SKILL.md section "Required PT deck pages":
  - Rule 1: when no pre-experiment exists, the Preliminaries section opens with an empty, title-only
    pre-experiment placeholder page directly after its divider.
  - Rule 2: before the first theory slide, a symbol-definitions page defines every variable, parameter
    and constant letter used in the deck, with meaning and SI unit, typeset as math, plus a key for
    subscripts whose meaning is not contained in the symbol definitions; an export check confirms
    complete and non-redundant coverage.
- `references/style-map.md`: the two pages added to the reusable page-type table.

### Changed
- Plugin version 0.8.3 to 0.8.4.

## [0.8.3] - 2026-10-14

Fresh-clone fixes: the published repository now passes the validator and the test suite.

### Fixed
- `tools/foam-agent/runs/.gitkeep` and `tools/foam-agent/database/foamgpt/data/.gitkeep` are hash-locked in
  `upstream-lock.yaml` but were excluded by the vendored (and also hash-locked) `tools/foam-agent/.gitignore`,
  so they never reached GitHub and the Foam-Agent integrity check failed in a clone. They are now tracked
  (force-added); the vendored `.gitignore` is unchanged.
- Empty `scripts/` and `tests/` folders that the validator requires for the upstream skills (and
  `skills/pt-self-improvement/tests`) cannot be stored by git; each now holds a `.gitkeep`.
- `test_current_2027_synthetic_package_is_runnable_and_partial_mode_reports_state` depended on the
  owner's private, untracked `deliverables/` workspace. It now skips with a reason when that case is
  absent, and looks in `PT_WORKSPACE_ROOT` (via `scripts/local_paths.py`) before the folder containing
  the plugin.

### Changed
- Plugin version 0.8.2 to 0.8.3.

## [0.8.2] - 2026-10-14

Private data moves to a user-level directory that survives plugin updates, and the private CYPT
reference decks become restorable from a verified manifest.

### Added
- User-level private data directory `PT_RESEARCH_HOME` (default `~/.config/pt-research`). Setting lookup
  order is now: environment variable, `<PT_RESEARCH_HOME>/local.paths.json`, plugin `local.paths.json`,
  plugin `.env.local`, default. The local reference decks resolve as `PT_LOCAL_REFERENCES_DIR` (used
  exclusively when set), `<PT_RESEARCH_HOME>/local-references`, then the git-ignored in-plugin
  `skills/cypt-slide-template/assets/local-references`. Implemented in `scripts/local_paths.py` and, with
  the same order, in `skills/cypt-slide-template/scripts/local_paths.mjs` (used by `build_template.mjs`,
  which now also reads `.env.local` and prints the references folder it used).
- `scripts/fetch_local_references.py` (standard library only): downloads the two private reference decks
  (Team Singapore "Magnetic Gear", Team Slovakia "Wet Scroll") from the links in the new committed
  manifest `skills/cypt-slide-template/references/local-references.manifest.json`, or restores them with
  `--from-dir`; `--check` verifies without writing. SHA-256 and size are verified before a file is kept,
  placement is atomic, a verified file is never overwritten, mismatches are discarded, and Google Drive's
  confirmation page is followed. It also re-extracts the five derived apparatus photos
  (`source-images/`, pages 10 and 14 of the Singapore deck) with a pure-Python PDF reader, using Pillow for
  PNG output when available (otherwise `.jpg`, which the builder accepts).
- README section "Restoring private CYPT reference decks (not redistributed)" with exact agent steps, plus
  pointers in `AGENTS.md` and the `cypt-slide-template` skill (run `--check` first; ask the user before any
  network download).
- `validate_plugin.py` gate `check_local_references_manifest`; offline tests in
  `tests/test_local_references.py` (verification, restore, mismatch rejection, `--check`, Drive
  confirmation handling, image extraction, Python/Node lookup parity). Tests isolate `PT_RESEARCH_HOME`
  (`tests/_isolated_home.py`) and never read the real `~/.config`.

### Changed
- `local.paths.example.json` documents the user-level location and `PT_LOCAL_REFERENCES_DIR`.
- Plugin version 0.8.1 to 0.8.2.

## [0.8.1] - 2026-10-14

Public-distribution preparation: licensing, marketplace metadata, removal of third-party and
personal material from the published tree, and a regression gate for local paths.

### Added
- MIT `LICENSE` (PT-authored files only; third-party components keep their own licenses per
  `THIRD_PARTY_NOTICES.md`) and `"license": "MIT"`, `homepage`, and `repository` in both manifests.
- Repository marketplaces named `pt-research` ("PT Research"): `.claude-plugin/marketplace.json` and
  `.agents/plugins/marketplace.json` at the repository root, both pointing at `./pt-research-plugin`.
- `scripts/local_paths.py`, `local.paths.example.json`, and git-ignored `local.paths.json` /
  `.env.local` for machine-specific tool locations (`PT_BUNDLED_PYTHON`, `PT_WORKSPACE_ROOT`,
  `PRESENTATIONS_SKILL`, `RUNTIME_PYTHON`, `RUNTIME_NODE`, `RUNTIME_NODE_MODULES`). Environment
  variables take precedence.
- `validate_plugin.py` gate `check_no_absolute_home_paths` and unit tests: files that would be
  published may not contain absolute home paths (`/Users/<name>/`, `/home/<name>/`).
- Repository-root and plugin `.gitignore` files covering local configuration and
  `skills/cypt-slide-template/assets/local-references/`.

### Changed
- The `cypt-slide-template` skill no longer ships other teams' slide decks or extracted photographs.
  Reference PDFs, extracted images, and the photo-embedded template copies moved to the git-ignored
  `assets/local-references/` folder (used when present). The published starter template is rebuilt with
  labelled photo placeholders and bracketed sample values; `build_template.mjs` falls back to
  placeholders when the local folder is absent. The theme file is now `assets/cypt-theme.json` (token
  `slovakGreen` renamed `conclusionGreen`).
- Hard-coded personal paths in documentation, logs, tests, and `build_template.mjs` were replaced with
  placeholders or configuration lookups. PDF-renderer tests skip cleanly when no bundled Python is configured.
- README install instructions cover Claude Code and Codex marketplace installation.
- Plugin version 0.8.0 to 0.8.1.

### Notes
- Files removed from the published tree remain in earlier git history until that history is rewritten.

## [0.8.0] - 2026-10-14

Research-software engineering and scientific-computing standards become first-class,
enforced plugin policy.

### Added
- Skill `pt-research-software-engineering` with references for engineering standards,
  stack selection and the ADR template, interface/GUI/TUI selection (including accessibility,
  Python Textual, and Rust ratatui as an option rather than a default), the scientific-computing
  verification checklist, uncertainty analysis, and theory-versus-experiment comparison.
  The orchestrator routes every code-producing stage through it; `pt-simulation-router` hands it
  the stack inputs, and `pt-simulation-packager` requires its declaration before
  `implementation_ready`.
- `engineering_standards.yaml` contract: schema `schemas/engineering-standards.schema.json`,
  semantic gates in `scripts/engineering_contract.py`, CLI `scripts/validate_engineering_standards.py`,
  and a case-level gate in `scripts/validate_artifacts.py` that applies when
  `engineering_contract_version: 1`. Validation proves declaration and structure only; it runs
  no tests and does not establish numerical accuracy or scientific correctness.
- `scripts/scaffold_research_software.py` (standard library only) and the
  `research-project` template: src layout, `pyproject.toml` with ruff/mypy/pytest/coverage,
  typed headless core, TOML config, provenance writer, dimensional, convergence, conservation,
  analytic-benchmark, uncertainty, reproducibility, property, and architecture tests, CI
  workflow, ADR, verification plan, README assumptions section, and an optional thin GUI/TUI stub.
- Policy PTENG-001 in `AGENTS.md` (separate managed block, outside the self-improvement block).
- `.claude-plugin/plugin.json` Claude Code manifest; `validate_plugin.py` checks it, enforces
  version parity with the Codex manifest, and rejects unsupported fields.
- Unit tests for the validator, case integration, scaffolder, and manifest checks.

### Changed
- `scaffold_research_case.py` writes `engineering_contract_version: 1` and a `not_started`
  `engineering_standards.yaml`; the project-state schema accepts the new version field.
- `state-machine.md` and `runnable-simulation-contract.md` document the engineering gate at
  `package_implemented` and the readiness ladder (lockfile at `executed_unverified`, evidenced
  receipts at `numerically_verified` and `experimentally_compared`).
- Plugin version 0.7.0 to 0.8.0.

### Not changed
- Existing cases without `engineering_contract_version` remain valid legacy cases.
- Packages from `tools/simulation-package/generate_package.py` do not yet emit a manifest and keep
  their previous claim ceiling.
