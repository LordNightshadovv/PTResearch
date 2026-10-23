# PT Research plugin rules

For every PT, IYPT, or CYPT research or simulation task in this plugin, read and follow `skills/pt-orchestrator/SKILL.md` first. The PT orchestrator is the authoritative router and stage supervisor. Do not invoke a specialist independently unless the orchestrator directs it or the user explicitly names that specialist.

- PT artifact contracts override a specialist's default output format when they conflict.
- A specialist may not silently change, simplify, or replace the selected physical model.
- A completed subprocess is not accepted until the orchestrator's stage gate passes.
- A solver exit code is never sufficient evidence of numerical or physical validity.
- A README-plus-shell handoff is never a runnable simulation package. Require a real implementation,
  synthetic benchmark, state-aware checks, machine-readable outputs, verification plan, and
  receipts; keep handoff-only as an explicit claim ceiling.
- Record every stage transition in `project_state.yaml` and append one event to `timeline.ndjson`.
- Workspace layout: a case's ledgers, receipts, reports, theory scripts, provenance, learning ledger and
  `openfoam/` generated cases live in `<workspace-root>/runs/<case-id>/`, named `NN-slug` with the
  two-digit problem number. Heavy solver output that `validate_artifacts.py` does not inspect (particle
  dumps, frames, videos, remote outputs, long logs) goes to `<workspace-root>/data/<case-id>/<run-folder>/`
  and must be cited by a receipt in the case. Human-facing decks and PDFs go to
  `<workspace-root>/deliverables/<case-id>/`; they present a case and never replace its ledgers. Session
  status and dated handoff notes go to `<workspace-root>/handoffs/<case-id>/`, while the case's
  `final_handoff.md` stays in the case. Write nothing inside the plugin directory. When the workspace
  `AGENTS.md` refines these locations, it wins.
- Keep all candidates in `model_registry.yaml`; every filtered candidate needs an evidence-backed reason and residual use.
- If a user explicitly invokes an upstream specialist for inspection or debugging, state that its output has not been integrated or accepted by the PT orchestrator.
- Never run simulation setup, upstream installation, or system package installation without the required artifact gate and user authority.
- Begin every new simulation with exactly one named primary solver. A second independent solver is an escalation, never a default; preserve the insufficiency evidence, interface variables and coupling-validation plan in the route record.
- Before substantial execution or package generation, obtain or reuse the target platform choice. A container is Linux execution on a host, never a native build by another name.
- When using `pt-self-improvement`, explicitly load this file even if the plugin root was not auto-loaded. Keep its learning ledger under the authorized case, bound every lineage and iteration, and treat rules without an isolated held-out evaluation as provisional.
- Private data lives outside the plugin directory, in `PT_RESEARCH_HOME` (default `~/.config/pt-research`), because a marketplace-installed plugin is replaced on every update: `local.paths.json` (machine paths) and `local-references/` (other teams' CYPT decks, never redistributed). Before using `cypt-slide-template`, run `python3 scripts/fetch_local_references.py --check`; if the decks are missing, follow the README section "Restoring private CYPT reference decks (not redistributed)" (ask the user before any network download, verify hashes, never commit the decks).
- At stage close, consider a bounded process-learning opportunity from actual case evidence; record a no-op when none is supported. At handoff, consolidate only independently evidenced transferable rules into the canonical workspace and plugin policy files.

Run structural and unit checks with:

```bash
python3 scripts/validate_plugin.py .
python3 -m unittest discover -s tests -v
```

<!-- BEGIN PT-ENGINEERING-STANDARDS (managed; edit through the engineering skill's reviewed changes) -->

## Mandatory research-software engineering standards (policy PTENG-001)

Any stage that produces or changes code (simulation packages, solver adapters, prediction/analysis/fit scripts, sweeps, GUIs) must follow `skills/pt-research-software-engineering/SKILL.md`, invoked through the orchestrator. Summary:

- Plan before coding: requirements and design notes, an assumptions registry, and a stack decision record (ADR) naming at least two alternatives. Choose technology on technical suitability (maintainability, modularity, performance, reliability, extensibility, reproducibility), prefer established libraries (NumPy, SciPy, SymPy, pandas/xarray, Pint, uncertainties, `solve_ivp`, lmfit/`scipy.optimize`, emcee where justified, Matplotlib/Plotly, pydantic/Hydra, pytest+hypothesis, ruff, mypy, uv/poetry lockfiles) over reinvention, and justify OOP versus functional/procedural style per module. Choose the language on technical merit; Rust is an option, not a default.
- Professional hygiene: version control without committing generated data or secrets, typed interfaces, lint/format/type gates, automated tests, CI-ready configuration, semantic versioning and a changelog, pinned or locked dependencies, structured logging, explicit error handling, configuration separated from code.
- Interface: a headless, tested core first. Add a desktop GUI, web UI, or TUI (Python Textual; Rust ratatui only with a documented performance/reliability case) only where it improves usability, accessibility, or research efficiency, as a thin layer with accessibility considered.
- Scientific rigor: convergence/step-size/tolerance studies, conservation checks, dimensional analysis, limiting cases, symmetry checks, analytic benchmarks; seeds, pinned environments, run metadata, deterministic outputs; sweeps, sensitivity, uncertainty propagation, fit uncertainties, residual analysis, and quantitative theory-versus-experiment comparison with separate fit and held-out data.
- Declare it: `engineering_standards.yaml` (schema `engineering-standards`), scaffolded by `scripts/scaffold_research_software.py` and checked by `scripts/validate_engineering_standards.py` and `scripts/validate_artifacts.py`.
- Truthfulness: validation proves declaration and structure only. It runs no test and proves neither numerical accuracy nor scientific correctness. A check is "passed" only with a retained receipt; unavailable tools are reported as not run, and no readiness state is raised by the manifest alone.

<!-- END PT-ENGINEERING-STANDARDS -->

<!-- BEGIN PT-SELF-IMPROVEMENT RULES (managed; preserve surrounding content) -->

<!-- PTSI-POLICY-001 is an adopted workflow protocol, not an empirical improvement claim. -->
### PTSI-POLICY-001: Bounded evidence-first learning (adopted policy)
- Status: adopted process policy; no measured improvement claim.
- Rule: Use actual in-scope trajectories, map before reduction, one mechanism per lineage, independent review, capability floors, efficiency checks, and sealed held-out evaluation before empirical promotion.
- Provenance: project policy adopted from the SoL-Pi process adaptation; see `skills/pt-self-improvement/references/sol-pi-adaptation.md`.
- Scope: PT research workflow instructions and case ledgers.
- Validation limits: This policy has not itself been shown to improve PT outcomes; it does not create access isolation or change solver/model authority.
- Rollback/supersession: Remove this managed entry and disable the skill's default learning hook if a later reviewed policy supersedes it.

### PTSI-POLICY-002: Source-bound acceptance and separated evidence lanes (adopted policy)
- Status: adopted software/process contract; no empirical improvement claim.
- Rule: Keep canonical-source identity, calibration/runtime readiness, and physical validation as separate evidence lanes; accept learned policy only from the writable canonical source and leave cache or missing calibration evidence pending.
- Provenance: PT plugin upgrade protocol and the bounded self-improvement workflow.
- Scope: plugin installation/source discovery, calibration receipts, and PT case acceptance.
- Validation limits: This records provenance and claim boundaries; it does not prove scientific correctness or create an access-control boundary.
- Rollback/supersession: Supersede with a new PTSI ID after an explicit source/calibration contract review.

<!-- END PT-SELF-IMPROVEMENT RULES -->
