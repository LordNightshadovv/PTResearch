# PT Research plugin

Version 0.8.5. See `CHANGELOG.md`. The plugin ships a Codex manifest (`.codex-plugin/plugin.json`) and a
Claude Code manifest (`.claude-plugin/plugin.json`); Claude Code discovers the skills in `skills/`
automatically, and the validator keeps the two manifests' names and versions identical.

## Research-software engineering standards

Any stage that produces code (simulation packages, solver adapters, prediction/analysis/fit
scripts, sweeps, GUIs) is routed by the orchestrator through `pt-research-software-engineering`.
It requires requirements and design notes, a stack decision record (ADR) naming at least two
alternatives, technology chosen on technical suitability with established libraries (NumPy,
SciPy, Pint, SymPy, pytest/hypothesis, ruff, mypy, uv lockfiles) preferred over reinvention, a
headless typed core with a CLI by default, and a GUI, web UI, or TUI (Python Textual; Rust
ratatui only with a documented case) only where it improves usability or research efficiency, as
a thin accessible layer. It also requires scientific-computing rigor: convergence and tolerance
studies, conservation checks, dimensional analysis, limiting cases, symmetry checks, analytic
benchmarks, seeds, pinned environments, run metadata, deterministic outputs, sweeps, sensitivity
and uncertainty analysis, and quantitative theory-versus-experiment comparison with separate fit
and held-out data. The mandatory summary is policy PTENG-001 in `AGENTS.md`.

Declare the result in `engineering_standards.yaml` (schema
`schemas/engineering-standards.schema.json`):

    python3 scripts/scaffold_research_software.py /path/to/my-model --name my-model --interface cli
    python3 scripts/validate_engineering_standards.py /path/to/my-model
    python3 scripts/validate_artifacts.py runs/CASE      # checks the case copy when engineering_contract_version is 1

The scaffolder uses only the standard library and installs nothing. The generated project's
tests need numpy, scipy, and pytest (with optional Pint, hypothesis, matplotlib); lockfile
creation (`uv lock`), ruff, and mypy are left to the user's environment. Validation proves that
the declaration is complete and consistent and that the referenced files exist. It runs no
test and does not establish numerical accuracy or scientific correctness; a check counts as
passed only when a retained receipt exists, and the manifest alone never raises a software-readiness
claim. Details: `skills/pt-research-software-engineering/references/manifest-contract.md`.

## Runnable simulation contract

Scientific readiness and software readiness are separate. A continuing case records
scientific_readiness as scientific_stop, model_selected_not_closed, or model_closed, and
software_readiness as not_applicable, handoff_only, implementation_ready, runnable_synthetic,
runnable_apparatus, executed_unverified, numerically_verified, or experimentally_compared. A
handoff-only package is never a runnable package.

Use the reusable generator to create a route-specific package with executable source/native input,
separated parameter categories, a synthetic example, real system and run gates, a case generator,
machine-readable extraction, equation/code traceability, a three-level verification plan, and
receipts:

    python3 tools/simulation-package/generate_package.py --route python_ode --output /tmp/pt-python-ode
    cd /tmp/pt-python-ode
    bash check_system.sh --mode synthetic
    bash run_gate.sh
    bash run.sh

The synthetic result is software evidence only. It does not establish solver installation,
numerical convergence, apparatus fidelity, or experimental agreement. The allow-partial flag
remains inspection-only and reports handoff-only.

Scientific acceptance is a separate, preregistered evidence lane. Before fitting, execution, or
comparison, freeze the observable, metric/formula, units, threshold, falsifier, data split,
uncertainty method, input/software hashes, and evaluator. Keep calibration fit data separate from
held-out physical-validation data and report measurement, calibration, numerical, sampling, and
model-form uncertainty separately. See
`skills/pt-theoretical-research/references/validation-and-reproducibility.md` and the version-3
contract for the required coverage and claim-ceiling rules.

Calibration and physical-validation claims require `calibration_plan.yaml` with
`calibration_contract_version: 1`. A new scaffold starts with status `planned` and cannot claim a
passed calibration or physical validation; a physical-validation claim additionally requires a
passed held-out comparison and `physical_validation` report. Missing dependencies or data produce
an explicit partial result with blockers and resumption conditions.

Supported generated routes include fourier_optics, elmer_fem, openfoam_continuum, project_chrono,
yade, python_ode, python_optimization, and reduced_order_model.

An installable Codex plugin for auditable IYPT/CYPT research: preserve the prompt, reconstruct the
apparatus, build and compare candidate mechanisms, close equations and parameter mappings, audit
equation lineage and positive/negative evidence, identify regimes, and derive solver requirements
before selecting software. A result may remain unresolved or stop explicitly for insufficient
literature, missing data, or an unresolved mechanism. OpenFOAM is one gated branch, not a keyword
default.

## Architecture

```text
user / AGENTS.md / default prompt
              |
       pt-orchestrator
       /             \
theoretical chain   simulation router
 |  |  |                 |
K-Dense + DeerFlow    physics suitability gate
                         |
       target platform -> native/container package -> solver smoke test
                         |
         OpenFOAM only: design -> Foam-Agent -> mesh gate -> experiment
              |
       schemas + run artifacts + acceptance gates
```

The orchestrator is the only implicitly invocable skill. The other native skills and all upstream specialist bridges require explicit orchestration or an explicit user request. Original upstream content remains under each specialist's `upstream-original/`; runtime research never downloads moving upstream content.

## Included skills

Native: `pt-orchestrator`, `pt-theoretical-research`, `pt-simulation-router`, `pt-simulation-packager`, `pt-research-software-engineering`, `pt-openfoam-environment-manager`, and `pt-report-renderer`.

Remote execution is an explicitly orchestrated specialist: `pt-remote-execution`. It connects to a dedicated non-root Linux account through an existing OpenSSH host alias such as `pt-linux`; it never reads private-key contents, passphrases, passwords, tokens, or `~/.codex/auth.json`. See `skills/pt-remote-execution/references/remote-execution.md` for the approval-gated bootstrap and operations workflow.

Vendored specialist bridges: K-Dense literature review; DeerFlow systematic literature review and paper review; AI-CFD-Scientist FoamAgent, mesh gate, experiment, and code modification; and sim-plugin-openfoam. `tools/foam-agent/` preserves the executable Foam-Agent framework separately from its skill bridge.

## Install

This repository is a plugin marketplace named `pt-research` (display name "PT Research") for both Claude Code and Codex. The plugin is `pt-research-plugin`.

### Claude Code

```text
/plugin marketplace add LordNightshadovv/PTResearch
/plugin install pt-research-plugin@pt-research
```

The marketplace manifest is `.claude-plugin/marketplace.json` at the repository root; the plugin manifest is `pt-research-plugin/.claude-plugin/plugin.json`. Start a new session after installation so the skills are discovered.

### Codex

Codex discovers repository marketplaces from `.agents/plugins/marketplace.json`, which this repository provides at its root (marketplace `pt-research`, plugin source `./pt-research-plugin`). Add the GitHub repository `LordNightshadovv/PTResearch` as a marketplace with Codex's marketplace command (`codex plugin marketplace add ...`; run `codex plugin marketplace add --help` for the source forms your Codex version accepts, or clone the repository and add the local checkout), then install the plugin from it:

```text
codex plugin add pt-research-plugin@pt-research
```

Restart Codex or begin a new session after installation so bundled skill metadata is discovered.

### Local development and personal marketplaces

Private, machine-specific settings and data live in a **user-level directory that survives plugin updates**: `PT_RESEARCH_HOME` (default `~/.config/pt-research`). A plugin installed from a marketplace is copied into a cache directory that is replaced on every update, so nothing private may live only inside the plugin directory. Use `local.paths.example.json` as the template for `<PT_RESEARCH_HOME>/local.paths.json` when you need machine-specific tool locations (for example a Python with PDF libraries for the renderer tests, or the slide-builder runtime). Lookup order for each key: environment variable, `<PT_RESEARCH_HOME>/local.paths.json`, a git-ignored `local.paths.json` in the plugin directory (convenient in a checkout), a git-ignored `.env.local` in the plugin directory, then the built-in default. Everything is optional: tests and builders skip or stop with a clear message when a tool is unavailable. Optional reference decks for the `cypt-slide-template` skill live in `<PT_RESEARCH_HOME>/local-references` (override with `PT_LOCAL_REFERENCES_DIR`; the git-ignored `skills/cypt-slide-template/assets/local-references/` folder inside the plugin is the last fallback); see the next section. The plugin works without them.

For a private personal marketplace, the local source can be `~/plugins/pt-research-plugin`. After copying a reviewed release there, use the Plugin Creator helpers from your Codex home instead of hand-editing the marketplace or incrementing the base semantic version merely to refresh the cache:

```text
python3 $CODEX_HOME/skills/.system/plugin-creator/scripts/read_marketplace_name.py
python3 $CODEX_HOME/skills/.system/plugin-creator/scripts/update_plugin_cachebuster.py ~/plugins/pt-research-plugin
codex plugin add pt-research-plugin@<personal-marketplace-name>
```

The cachebuster preserves the base version and replaces only its `+codex.*` suffix. Start a new Codex task after reinstalling so the updated skills are loaded. The default personal marketplace is discovered implicitly; do not add it with `codex plugin marketplace add`. Keep the workspace source and any personal-marketplace copy distinct until the reviewed release has been synchronized deliberately.

## Restoring private CYPT reference decks (not redistributed)

**Audience: AI agents and users who need the CYPT style references for the `cypt-slide-template` skill.**

Two other teams' presentations were used as visual style references for the CYPT slide template:

| File name (exact) | Team and problem | Source |
| --- | --- | --- |
| `Magnetic Gear Singapore.pdf` | Team Singapore, Magnetic Gear | Google Drive link in the manifest |
| `Wet Scroll Slovakia.pdf` | Team Slovakia, Wet Scroll | Google Drive link in the manifest |

They are **not redistributed** with this plugin or this repository. They are used only as local style references with the `cypt-slide-template` skill and template, and the plugin works without them (the starter template then uses labelled photo placeholders). The committed manifest `skills/cypt-slide-template/references/local-references.manifest.json` records, for each deck, the exact file name, a one-line team/problem description, the original download link, and the SHA-256 and byte size of the exact file. Never commit, publish, or copy the decks (or anything extracted from them) into the plugin tree.

Steps for an agent (or a user) to restore them. Ask the user before any network download.

1. Check what is present (read-only, writes nothing):

   ```text
   python3 <plugin-root>/scripts/fetch_local_references.py --check
   ```

   It resolves the destination as `PT_LOCAL_REFERENCES_DIR`, else `<PT_RESEARCH_HOME>/local-references` (default `~/.config/pt-research/local-references`) and exits 0 only when both decks match the manifest.
2. If anything is missing or invalid, restore it. With the user's approval to download:

   ```text
   python3 <plugin-root>/scripts/fetch_local_references.py
   ```

   or, from a local backup folder that holds copies of the PDFs (no network):

   ```text
   python3 <plugin-root>/scripts/fetch_local_references.py --from-dir <backup-folder>
   ```

   Use `--dest <folder>` to choose another destination. The tool verifies size and SHA-256 before keeping a file, writes through a temporary file and an atomic rename, never overwrites a verified file, and discards any mismatch (a corrupt existing file is replaced only with `--force`). If downloads are blocked, open the links from the manifest in a browser, save the files under the exact names above in the destination folder, and re-run `--check`.
3. Verify: re-run `--check`; both decks must print `[ok]`. Hash mismatch means the file is not the expected deck; do not use it.
4. Create `<PT_RESEARCH_HOME>/local.paths.json` from `local.paths.example.json` if it does not exist, with the correct machine paths (slide-builder runtime: `PRESENTATIONS_SKILL`, `RUNTIME_PYTHON`, `RUNTIME_NODE_MODULES`, optionally `PT_WORKSPACE_ROOT`). Keep it out of version control; it is never published.
5. Regenerate the derived files:
   - `source-images/p10-image0.png` to `p10-image2.png` and `p14-image0.png`, `p14-image1.png` are the five apparatus photographs embedded in pages 10 and 14 of the Singapore deck. `fetch_local_references.py` re-extracts them automatically after a verified restore (or run it again; it only creates missing files, and `--no-images` skips this). The JPEG streams are verified against SHA-256 values in the manifest; PNG conversion uses Pillow when installed (the PNGs may differ from the original export by decoder rounding, at most a few levels per pixel) and otherwise `.jpg` files are written, which the template builder also accepts.
   - `CYPT_editable_template.pptx` (starter with those photos embedded) and `CYPT_editable_template_reference.pptx` (a copy) are optional conveniences. Rebuild with the builder, writing inside your workspace, then copy the result into the local references folder:

     ```text
     node <plugin-root>/skills/cypt-slide-template/scripts/build_template.mjs \
       <plugin-root>/skills/cypt-slide-template/assets/template-config.json \
       <workspace>/deliverables/cypt-slide-template/CYPT_with_photos.pptx
     cp <workspace>/deliverables/cypt-slide-template/CYPT_with_photos.pptx <local-references>/CYPT_editable_template.pptx
     ```

     The builder prints `local references: <folder>` so you can confirm which folder supplied the photos; set `PT_NO_LOCAL_REFERENCES=1` to build with placeholders instead.
   - An optional `.pptx` conversion of the Singapore PDF may exist on the owner's computer. It is not required, not verified by the manifest, and not downloadable from it.
6. Use the `cypt-slide-template` skill. Treat the decks only as visual references; do not quote or copy their content into outputs.

Both the Python tools and the Node builder use the same lookup order (`scripts/local_paths.py` and `skills/cypt-slide-template/scripts/local_paths.mjs`), and the test suite isolates `HOME` and `PT_RESEARCH_HOME` in temporary directories so it never reads the real `~/.config/pt-research`.

## License

The PT-authored files are released under the [MIT License](LICENSE). Bundled third-party components keep their own licenses; see [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md). The MIT license covers only the PT-authored files, not those components.

To use the repository directly during development, keep `AGENTS.md` in scope and ask: “Use PT Research to investigate this exact IYPT prompt …”. The normal selector is `$pt-orchestrator`. For inspection/debugging only, explicitly select a specialist such as `$upstream-cfd-mesh-gate`; its result is not integrated or accepted until the orchestrator validates its returned artifacts.

## Dependencies and capability levels

The dependency policy declares Python 3.10+ for scaffolding, validation, provenance, calibration
checks, and tests. The baseline suite was observed passing under Python 3.9.6, but that runtime is
outside the supported policy. Standard-library-only checks work without network access. Literature
searches require accessible search/browsing channels and paper text for equation-level audits.

All six numerical runtimes are optional and are managed through a locked official-source runtime layer. Before case design, inspect the selected solver and reuse it only if the installed version matches the lock:

```text
python3 tools/solver-runtime/solver_runtime.py inspect --solver OpenFOAM --output runs/CASE/dependency_report.json
```

If it is missing, the current-computer installer runs only with explicit authority: `python3 tools/solver-runtime/solver_runtime.py install --solver OpenFOAM --authorized`. A package for another computer carries a target-specific official-source installer or container recipe rather than a bundled solver binary. Offline materials are generated separately by OS, CPU architecture, and GPU backend; anything not legally redistributable is listed as an official download to obtain separately.

Missing tools force reduced-capability mode: theory, routing, or design review may continue, but no generated, executed, converged, or scientifically accepted case is claimed. A package cannot claim to be runnable until a matching smoke receipt proves the locked solver on its declared target OS/architecture/GPU backend. System-level installation and smoke execution always require the user's approval.

Before any substantial package or run, the orchestrator records whether to run on the current computer or package for another one, OS/architecture, GPU backend/memory and container permission. Native installation is preferred; a macOS launcher for a Linux container is labelled containerized Linux, never native macOS. Each package includes beginner-facing commands, platform limits, pinned versions, an official smoke test and retained logs. Render the retained research artifacts into a human report with `python3 tools/report-renderer/render_research_report.py runs/CASE --output runs/CASE/reports/research-report.pdf`.

## Durable run artifacts

Create a case without overwriting prior work:

```text
python3 scripts/scaffold_research_case.py my-case --prompt 'Exact official prompt text'
```

The result under `runs/my-case/` contains contract-version-3 prompt/apparatus records, positive and
negative claim evidence, complete equation-lineage records, a mandatory candidate-comparison table,
dimensionless regime analysis, four-way parameter classifications, a physics-first solver chain,
an experiment-to-simulation validation chain, justified stopping criteria, reports, dependency
records, timeline, and final handoff. Files use a JSON-compatible YAML subset so they remain
deterministically validated with the Python standard library. Existing v1/v2 cases remain readable
until explicitly migrated.

## Validate and test

```text
python3 scripts/validate_plugin.py
python3 scripts/fetch_local_references.py --check   # optional: verifies the private CYPT reference decks
python3 scripts/validate_engineering_standards.py /path/to/research-software-project
python3 scripts/validate_artifacts.py tests/fixtures/pinhole-sunglasses
python3 scripts/validate_deep_theory.py /path/to/consolidated-report-root
python3 -m unittest discover -s tests -v
```

The deep-theory and version-2/version-3 artifact validators require a standalone `theory-model.tex`,
apparatus fidelity, candidate comparison, structured equation provenance and symbol
registries, a mathematical mechanism chain, equation-generated predictions, conclusion deductions,
and a compiled PDF. They hard-reject apparatus contradictions, open mechanisms, unmapped controls,
unverified/fabricated locators, context-only quantitative laws, unsupported simulation states,
undefined forcing, generic placeholders, unsupported prediction tables, solver-first routing,
unclassified parameters, incomplete validation mappings, and raw local paths.

The official plugin and skill validators should also be run in an environment with PyYAML available. Provenance gates are independent:

```text
python3 scripts/verify_upstream_integrity.py .
python3 scripts/check_licenses.py
```

## Updating pinned upstream sources

`scripts/fetch_upstream_skills.py` and `scripts/refresh_upstream_skills.py` fetch only exact commits into a staging directory and refuse to overwrite this plugin. Review upstream diffs, licenses, security-sensitive commands, and bridge compatibility manually. Then replace preserved snapshots deliberately, update hardcoded pins and notices, run `verify_upstream_integrity.py --initialize`, and rerun every test. Never update pins during a research run.

## Known limitations

- This release includes installation/container/package integration for every routable primary solver and executable synthetic route templates. External solver execution and route-specific scientific acceptance still require the locked runtime and validation receipts; the portable templates do not imply those external runs occurred.
- Literature completeness depends on available databases and full-text access; unavailable or abstract-only sources remain explicitly labeled.
- Foam-Agent's large dependency stack is vendored but not installed automatically.
- No real OpenFOAM solve is part of the portable test suite; the suite mocks availability and tests refusal, ordering, version separation, and scientific-acceptance contracts.
- The engineering-standards manifest and its validator check declaration and file structure only.
  `generate_package.py` packages do not yet emit a manifest. Ruff, mypy, Pint, and hypothesis are
  declared in the scaffold but are not run by the plugin's own suite; the generated project's tests
  run in the plugin suite only when numpy, scipy, and pytest are importable.
- Static validators and unit tests establish artifact invariants only. They do not establish
  empirical recursive improvement, physical truth, or generalization of a workflow rule; those
  claims require independently produced, provenance-bound evidence and a sealed evaluation where
  applicable.

See `BUILD_REPORT.md` for the verified build status, `THIRD_PARTY_NOTICES.md` for licensing, and `references/upstream-adaptation-map.md` for every bridge decision.
