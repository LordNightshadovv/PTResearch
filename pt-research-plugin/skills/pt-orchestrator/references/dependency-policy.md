# Dependency policy

## Required for every case

- Read/write access to the run directory.
- Python 3.10 or newer for plugin scripts.
- Valid PT artifact inputs for the requested stage.

## Optional capabilities

- Academic web/search tools and full-text PDF access.
- PyYAML and jsonschema for broader YAML/schema support; scripts retain JSON-compatible YAML fallbacks.
- Foam-Agent Python dependencies and a built RAG index.
- A sourced, supported OpenFOAM distribution.
- `wmake` for custom compiled models.
- Rendering and post-processing tools.

## Reduced-capability rules

Write `dependency_report.yaml` whenever an optional dependency is absent. State each missing command/module, affected specialist, allowed outputs, and forbidden claims. Never replace unavailable evidence or execution with invented success.

System package installation, Python dependency installation, RAG-index construction, remote solver access, and real simulation execution require explicit user approval. Dependency checks themselves must be read-only.
