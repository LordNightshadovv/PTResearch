---
name: pt-research-software-engineering
description: Mandatory engineering and scientific-computing standards for any PT/IYPT/CYPT stage that produces or changes code (simulations, models, analysis scripts, fits, GUIs, packages). Requires a stack decision record, test plan, numerical and physical verification, uncertainty treatment, reproducibility metadata, and an interface choice, declared in a machine-checkable engineering_standards.yaml. Invoked by pt-orchestrator, pt-simulation-router, and pt-simulation-packager; validation proves declaration and structure, never scientific correctness.
---

# PT Research Software Engineering

Apply professional, industrial-grade software engineering and rigorous scientific computing to every PT stage that writes code. Use only through `pt-orchestrator` (or when the user explicitly names this skill). It adds engineering and verification obligations; it never changes the selected physical model.

## What counts as code-producing

Any simulation package, solver adapter, model or prediction script, parameter sweep, fit or uncertainty analysis, plotting/report generator, data-processing tool, GUI/TUI/web front end, or notebook that supplies a number, figure, or claim. One-line arithmetic inside a derivation is not code-producing, but a script that generates a prediction table is.

## Workflow

1. **Plan before coding.** Read [engineering-standards.md](references/engineering-standards.md). Write requirements and design notes (observable, inputs, outputs, units, regimes, failure modes) before implementation.
2. **Decide the stack.** Read [stack-selection-and-adr.md](references/stack-selection-and-adr.md). Choose by technical suitability (maintainability, modularity, performance, reliability, extensibility, reproducibility), prefer established libraries over reinvention, and record an ADR with at least two alternatives. Paradigm (OOP, functional, procedural) is justified per module, not applied dogmatically. Language is chosen on technical merit; Rust or C++ is an option, never a default.
3. **Choose the interface.** Read [interface-selection-guide.md](references/interface-selection-guide.md). Default to a headless, tested core with a CLI. Add a desktop GUI, web UI, or TUI (Python Textual, or Rust ratatui where its performance/reliability case is documented) only where it improves usability, accessibility, or research efficiency, as a thin layer over the core, with accessibility considered.
4. **Scaffold.** For a new Python project run `python scripts/scaffold_research_software.py <dir> --name <project> [--interface cli|library_only|desktop_gui|web_ui|tui_python]` from the plugin root. It creates a src-layout project with typed core, config, provenance writer, dimensional/convergence/conservation/uncertainty tests, CI config, ADR and README assumptions section, plus `engineering_standards.yaml`. Standard library only; it installs and runs nothing. For other languages apply the same checklist by hand.
5. **Verify scientifically.** Follow [scientific-computing-vv-checklist.md](references/scientific-computing-vv-checklist.md): convergence and tolerance studies, conservation checks, dimensional analysis, limiting cases, symmetry, analytic benchmarks, a transparent assumptions registry.
6. **Quantify uncertainty and compare with experiment.** Follow [uncertainty-and-experiment-comparison.md](references/uncertainty-and-experiment-comparison.md): error propagation, Monte Carlo, fit uncertainties, residual analysis, sweeps, sensitivity, overlay plots with error bars, goodness-of-fit, regime maps; keep calibration data apart from held-out validation data (see the plugin calibration contract).
7. **Declare and validate.** Fill `engineering_standards.yaml` ([manifest-contract.md](references/manifest-contract.md)) and run `python scripts/validate_engineering_standards.py <project-or-manifest>`. For a PT case, `python scripts/validate_artifacts.py <run-dir>` checks the case copy when `engineering_contract_version: 1`.

## Evidence discipline

- A test that exists is `implemented`; it is `evidenced` only when a retained receipt (command, output, date, commit) exists at the manifest's `evidence` path. Never write "passes" without a receipt.
- Validation of the manifest proves the declaration is complete, consistent, and that referenced files exist. It does not run tests, prove numerical accuracy, or establish physical truth. Say so in handoffs.
- A deterministic synthetic benchmark is software evidence only. Numerical verification, parameter calibration, and physical validation remain the plugin's separate evidence lanes; do not merge them.
- Record every unavailable tool (ruff, mypy, Pint, a lockfile) honestly as untested or `pending_generation`; do not install packages without user authority.

## Stage gates (enforced by the orchestrator)

- `simulation_routed`: stack ADR drafted with alternatives; interface choice recorded.
- `package_implemented`: `engineering_standards.yaml` status `declared`; test plan, tooling, config, logging, and reproducibility declared; files exist.
- `synthetic_smoke_tested` and later: receipts for the commands cited; a committed lockfile before any `executed_unverified` or higher claim.
- `numerically_validated`: numerical-verification receipt evidenced.
- `physically_validated` / `experimentally_compared`: evidenced experiment-comparison with separate fit and held-out data.

Return to `pt-orchestrator` with the manifest status, the receipts available, the tools not run, and the claim ceiling.
