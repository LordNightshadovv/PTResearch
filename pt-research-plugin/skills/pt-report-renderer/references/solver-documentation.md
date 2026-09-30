# Solver documentation contract

Use this reference for every simulation-stage prompt and research batch.

## Prompt Solver Usage Catalog

Include: prompt/batch/project identity; solver decision and rejected alternatives; exact primary/secondary solver and supporting libraries actually used; official origin/repository/version/license/citation/runtime; installation, package, platform, smoke-test, and reproduction details; prompt role; modules, equations, laws, conditions, configuration, inputs, outputs, units, and uncertainty; theory-to-solver mapping; separated verification and validation; limitations; and full citations.

State “No second numerical solver was required.” when true. Record actual modules and methods rather than software capabilities. Keep credentials out of all artifacts.

## Batch Solver-Mechanism Compendium

For each distinct actually used solver, explain origin/version/license, prompts/modules, relevant physical equations, mathematical principle/theorem where genuinely relevant, representative discrete equation, spatial discretization, time integration, constraints/coupling, linear/nonlinear solution, stability, convergence/error sources, batch-specific use, verification example, and references. Include an original explanatory diagram when useful. Do not include merely considered software except in an optional appendix.

Use stable cross-reference identifiers such as `solver-openfoam`. Each catalog cites its compendium chapter; each chapter lists every mapped prompt. The batch matrix and inventories must agree.

## Gates

Before finalizing, pass: solver identity; prompt usage; mechanism chapter; cross-reference consistency; and PDF inspection. Render every page to images; reject raw YAML, placeholders, empty sections, broken equations/symbols, unresolved citations, and broken cross-references.
