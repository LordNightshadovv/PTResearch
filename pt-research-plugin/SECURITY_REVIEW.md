# Upstream security review

Review date: 2026-07-20. Scope: all eight preserved specialist snapshots and the vendored Foam-Agent tracked tree at the commits in `upstream-lock.yaml`.

No upstream installation script, solver, network client, Docker build, HPC submission, or code-generation workflow was executed during plugin construction. Retrieval used pinned Git commits in disposable staging directories; preserved trees are checked by deterministic hashes.

## Findings and controls

| Surface | Observed behavior | PT control |
|---|---|---|
| K-Dense | Optional OpenRouter credential, network extraction, `curl ... | bash`, package-install suggestions, subprocess PDF/image generation | Bridge never installs packages or reads credentials automatically. Search/tool access is dependency-gated; system changes require approval. |
| DeerFlow SLR | Public arXiv HTTP requests and local scripts | Network failure yields search/dependency records, never fabricated coverage. Only registered sources reach synthesis. |
| AI-CFD experiment | Subprocess solver/mesher calls and deletion of generated variant case directories | Not executed automatically. PT requires an explicit spec, bounded case root, accepted baseline, provenance, and orchestrator gate. |
| sim-plugin-openfoam | Shell/subprocess examples, localhost simulation server, tutorial commands including recursive cleanup | Original instructions are reference-only. Active bridge requires distribution probe, validated spec, sandboxed/bounded case path, and explicit execution authorization. |
| Foam-Agent | LLM/API backends, environment-variable configuration, filesystem case replacement, subprocess/OpenFOAM execution, Docker/Conda installation, HPC submission, optional network clone/update | Framework is inert by default. PT wrapper only reports dependencies unless `--execute` and a spec are supplied. No package/system install, server start, deletion, or HPC job is performed by plugin validation. |

## Residual risks

- Upstream execution paths are powerful and can create/delete cases or launch solvers. Run only inside a case-specific sandbox after reviewing the generated plan and resolved absolute paths.
- Foam-Agent exposes configurable network/LLM backends and may use secrets from its environment. The PT plugin neither stores nor requests those secrets; users must choose and approve any backend.
- The vendored Foam-Agent tree preserves Git LFS pointer files where the pinned Git archive contains pointers; large RAG payload availability must be probed separately.
- Foundation and OpenCFD/ESI cases are not syntax-compatible. The version probe and design gate must pass before dictionary generation.
- Upstream dependency graphs were not installed or exhaustively supply-chain audited. Installation remains an explicit, separately reviewable user action.
