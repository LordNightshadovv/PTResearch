---
name: pt-orchestrator
description: Authoritative entry point for PT/IYPT/CYPT research and simulation work. Initialize or resume auditable cases, enforce phenomenon-essence and causal-chain rules, route theory and simulation specialists, validate stage artifacts, detect model drift, and control completion claims. Use for any PT research or simulation request; do not bypass it for a specialist unless the user explicitly requests specialist inspection.
---

# PT Orchestrator

Control the workflow; do not perform every specialist task inline. Persist state in artifacts so any later session can resume without conversational memory.

## Start or resume

1. Resolve the workspace root and the writable plugin source before touching a case. Explicitly read
   the workspace `AGENTS.md` and the selected plugin's `AGENTS.md`; a plugin root is not assumed to
   have been auto-loaded, and an immutable marketplace/cache copy is never a writable source.
2. Locate `<workspace-root>/runs/<case-id>/project_state.yaml`. If absent, run from the selected
   plugin root with an absolute workspace runs root:
   `python scripts/scaffold_research_case.py <case-id> --prompt-file <file> --runs-root /absolute/path/to/workspace/runs`.
   Never let the scaffold default create a parallel `runs/` tree inside an installed plugin.
3. Preserve the official prompt exactly in `problem_contract.yaml` before interpretation.
4. Read [specialist-registry.yaml](references/specialist-registry.yaml), [state-machine.md](references/state-machine.md), [dependency-policy.md](references/dependency-policy.md), [scientific contract v2](references/scientific-contract-v2.md), [scientific contract v3](references/scientific-contract-v3.md), and [runnable-simulation-contract.md](references/runnable-simulation-contract.md).
5. Read and validate the case learning ledger at `runs/<case-id>/learning/audit-ledger.json` using
   `pt-self-improvement`. Resume with its active promoted/provisional rules in scope. If the ledger
   is absent, initialize it from the skill template without overwriting another case.
6. Validate available artifacts with `python scripts/validate_artifacts.py <run-dir>` before choosing the next stage.
7. Select only specialists allowed by the current state. Record the invocation, inputs, expected outputs, and dependency mode in `timeline.ndjson`.

## Enforce global scientific rules

- Require a concise phenomenon essence (本质) and an input-to-observable causal chain.
- Reconstruct the actual apparatus before candidate endorsement. Block any model that contradicts
  a decisive open/sealed connection, mask plane, contact/motion geometry, interface, sensor,
  boundary, observable, or experimental range.
- Generate and compare a serious candidate pool before selecting. Permit an unresolved or
  no-justified-candidate outcome; never elevate the first plausible mechanism to truth.
- Require mechanistic closure, exact parameter-to-equation-to-observable mapping, and equation-level
  provenance with verified granular locators or an honest unavailable-locator search record.
- For v3 cases, enforce the complete equation-lineage chain, mandatory comparison table, negative
  evidence review, dimensionless regime analysis, four-way parameter classification,
  physics-first solver-selection chain, and experiment-to-simulation validation chain.
- Prefer complete whole-chain hypotheses; accept components only as a compatible, explicit stack.
- Keep every candidate in `model_registry.yaml`; explain every filtered/non-recommended candidate and residual use.
- Treat a famous theory name as insufficient without causal and regime coverage.
- Treat a simulation framework as a numerical implementation, never as the physical model.
- Require every human-facing theoretical report to stand alone: display and explain the selected model, governing equations, variables and units, assumptions, derivation or justification, parameter provenance, limiting cases, citations, and at least one falsifiable dependent-variable prediction. A solver implements that model; it cannot replace it. If this evidence is not developed, label the document `Preliminary Model Plan`, never `Theoretical Report`.
- For every prompt that reaches the simulation stage, generate a Solver Usage Catalog recording the exact solver/version/origin/repository/license, installation and execution method, modules and numerical algorithms, implemented physical equations, theory-to-solver mapping, inputs, outputs, verification, validation, limitations, and complete citations. Document only software actually used.
- For every batch, generate one Solver-Mechanism Compendium covering each distinct actually used solver once: governing equations, mathematical principles, relevant theorems/identities, discretization, time integration, constraints/coupling, linear/nonlinear solution, stability, convergence, error, batch-specific use, representative equations, and original explanatory diagrams.
- Keep physical theory, prompt-level solver use, and batch-level numerical mechanism separate. The theoretical report explains the phenomenon and prediction; the catalog explains the prompt’s software configuration; the compendium explains numerical machinery. Regenerate the compendium when a new solver, major version, material numerical method, or important module is introduced.
- Require closed physics and a solver-requirements table before naming a primary open-source solver
  and OpenFOAM classification. Prefer built-in physics, then transparent auxiliary relations, then
  lookup tables; use staged multi-solver workflows only when distinct closed models require them.
- Do not simulate until equations, assumptions, parameters, observables, and validation targets are explicit.
- Keep scientific readiness and software readiness separate. Scientific readiness is exactly one of
  `scientific_stop`, `model_selected_not_closed`, or `model_closed`. Software readiness is exactly
  one of `not_applicable`, `handoff_only`, `implementation_ready`, `runnable_synthetic`,
  `runnable_apparatus`, `executed_unverified`, `numerically_verified`, or
  `experimentally_compared`.
- `handoff_only` is an explicit ceiling, never an alias for `runnable_synthetic`. A continuing case
  needs a real source/native implementation, case generator, state-aware gate, result extractor,
  synthetic example, machine-readable verification plan, and receipt before it may claim
  `runnable_synthetic`.
- Require a receipt for every executed command and never infer a later state from file presence,
  a solver name, an installation receipt, or a successful subprocess alone.
- Preserve conflicting evidence, unresolved links, and dependency failures. Never fabricate sources, equations, parameters, or results.
- Accept an explicit justified-stop outcome for unresolved mechanism, insufficient literature, or
  missing data. Record its claim ceiling and resumption conditions; select no solver after stopping.

## Route stages

Use the persistent stage sequence:

```text
initialized → prompt_contracted → literature_discovery → literature_screened
→ evidence_audited → essence_and_chain_proposed → candidate_models_built
→ candidate_models_selected → simulation_routed → simulation_specified
→ package_implemented → synthetic_smoke_tested → case_generated
→ baseline_executed → numerically_validated
→ physically_validated → parameter_study_complete → handoff_complete
```

Theory-only cases may stop after `candidate_models_selected`. Skip a stage only when [state-machine.md](references/state-machine.md) explicitly permits it and record why.

### Theory chain

1. Invoke `pt-theoretical-research` as scientific owner.
2. Let it direct `upstream-kdense-literature-review` for broad retrieval and search logging.
3. Direct `upstream-deerflow-systematic-literature-review` for bounded screening/synthesis.
4. Direct `upstream-deerflow-academic-paper-review` for deep audits.
5. Return to `pt-theoretical-research` for essence, mathematics, registry, and selection.

Before accepting `candidate_models_selected`, require a standalone theoretical report that passes
the deep-model contract in `pt-theoretical-research`. Reject a theory handoff when any causal arrow
from controlled input to terminal observable is only prose, when a forcing or coupling function is
undefined, when the principal prediction is a generic normalized placeholder, or when a calculated
table is not generated from a displayed prompt-specific equation. The report itself must contain
the essential derivation, term meanings, symbol registry, provenance, limits, solver mapping,
calculated prediction, and falsifiable conclusion; internal YAML, code, and registries may support
but never replace that reasoning.

### Simulation chain

1. Invoke `pt-simulation-router` only after apparatus fidelity, evidence sufficiency, model
   comparison, mechanistic closure, and parameter mapping pass. Require its solver-requirements
   table, decision block, and a complete staged/second-solver record when another solver is proposed.
2. Ask the mandated four-way execution choice unless the project already answers it: run locally now if available, produce a Linux/Ubuntu package, produce both, or stop at research before implementation. Record OS, architecture, GPU and container permission for modes that package or run. Do not install, package, generate, or run without the user choice and artifact gate.
3. Invoke `pt-simulation-packager` to prepare the chosen primary solver's native-first or honestly
   containerized package. The package must contain executable implementation, separated inputs,
   a synthetic example, a real system check, a state-aware run gate, a case generator or solver
   native case, machine-readable result extraction, a three-level verification plan, and receipts.
   A solver-runtime smoke receipt alone is not a runnable case receipt.
4. Require a valid `simulation_spec.yaml`, a locked solver version, a runtime probe, and an
   implementation-ready package before case design. If OpenFOAM is primary, invoke
   `pt-openfoam-environment-manager` to probe its distribution, solvers, mesh/post tools, libraries
   and tutorials, then `upstream-sim-plugin-openfoam` for review. If the selected solver is absent,
   install only after explicit user authority on the current computer; for another computer,
   generate an official-source installer or reproducible container recipe.
5. When the approved target is a remote Linux computer, invoke `pt-remote-execution` after the route/specification and target-platform gate. It uses only the user's OpenSSH host alias and agent, plans privileged setup but never performs it without explicit approval, and returns remote runtime/status receipts. A remote start is not accepted until service/process, initialized solver state, writable logs, and an atomic `status.json` are independently observed.
6. Invoke `upstream-cfd-foamagent` only for an OpenFOAM case when Foam-Agent and the correct distribution are available. Invoke its mesh gate, experiment, and custom-code bridges only under their existing gates.
7. For HCIPy, Project Chrono, Elmer FEM, or YADE, stop at the approved package/specification or delegate only to a future solver-specific specialist; do not disguise an unimplemented specialist as execution.
8. Invoke `pt-report-renderer` after theory or simulation handoff only after its theory-package preflight passes. For a simulation-stage case, also invoke `tools/solver-documentation/solver_documents.py` to validate/render the prompt catalog and update/validate/render the batch compendium. It renders human PDFs while preserving the YAML and Markdown artifacts; it must never tell the reader to consult those artifacts for essential theory or numerical mechanism.
9. For a user-requested PowerPoint, invoke `cypt-slide-template` after resolving the deck's content and claim status. The styling skill may be used without advancing a case stage; slide export is not scientific acceptance.

## Detect conflicts and model drift

Compare every specialist output with the selected candidate and `simulation_spec.yaml`. Create a blocking mismatch when a specialist changes governing equations, constitutive behavior, geometry, boundary conditions, phases, solver distribution, or terminal observable without an approved registry decision.

Example:

```yaml
model_mismatch:
  selected_model_requirement: shear_thinning_non_newtonian
  generated_case_assumption: newtonian
  severity: blocking
  action: invoke_upstream-cfd-code-modify_or_change_route
```

Reject the output and return to the responsible stage. Never accept silent simplification that removes the proposed essence.

## Use reduced-capability mode

When an optional dependency is absent, write `dependency_report.yaml`, lower the allowed completion
stage, and forbid unsupported claims. If the selected solver is absent, a complete implementation
may still be tested in synthetic mode; the package must say whether the synthetic path is a
dependency-free reference or an external-solver smoke test. It may not claim production/apparatus
execution, numerical validity, or experimental comparison. A package becomes runnable only after
its synthetic receipt identifies the exact command and outputs; an apparatus claim additionally
requires measured inputs and uncertainty records.

## Close a stage

1. Validate the expected artifacts and cross-file references.
2. Record pass/fail, evidence, dependency mode, and allowed next specialists.
3. Update `project_state.yaml` only after validation passes.
4. Append an immutable event to `timeline.ndjson`.
5. Consider one bounded `pt-self-improvement` opportunity from actual stage evidence. Record a
   proposed, rejected, deferred, or provisional rule when supported; if no meaningful opportunity
   exists, record the no-op reason and do not invent a lesson. Do not run experiments solely to fill
   the learning ledger.
6. At handoff, run the learning skill's consolidation check once. Promote only rules that pass the
   independent reviewer, capability-floor, efficiency, combined-regression, freeze, and sealed
   held-out gates into both canonical AGENTS files. If the canonical plugin source or either AGENTS
   target is unavailable, retain a deferred pending-consolidation record and report the claim ceiling.
7. Report the highest accepted stage, every untested or unavailable capability, and the learning
   ledger's proposed/rejected/deferred/provisional/promoted outcomes.

Do not accept completion because a subprocess returned zero. Acceptance belongs to this orchestrator and its artifact gates.
