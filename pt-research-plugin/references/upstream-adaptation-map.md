# Upstream adaptation map

| Local skill | Upstream source | Commit | License | Files inspected | Preserved components | PT bridge behavior | Modified/copied content | Rejected upstream assumptions |
|---|---|---|---|---|---|---|---|---|
| `upstream-kdense-literature-review` | K-Dense `skills/literature-review` | `3f825ca…2a5` | MIT | Skill, references, scripts, license | Entire source subtree | Broad retrieval; returns logs and source candidates | New bridge only | No claim of exhaustive coverage when search channels are absent |
| `upstream-deerflow-systematic-literature-review` | DeerFlow `skills/public/systematic-literature-review` | `0cd5506…481` | MIT | Skill and all bundled references | Entire source subtree | Screens and synthesizes the registered corpus | New bridge only | PT native layer reconciles disagreements; report concatenation is not synthesis |
| `upstream-deerflow-academic-paper-review` | DeerFlow `skills/public/academic-paper-review` | `0cd5506…481` | MIT | Skill and license | Entire source subtree | Audits selected papers into persistent paper cards | New bridge only | Abstract-only access cannot support equation-level claims |
| `upstream-cfd-foamagent` | AI-CFD-Scientist `cfd-skills/cfd-foamagent` | `b7fa924…514` | MIT, README declaration | Skill, catalog README, repository README | Exact skill snapshot | Accepts validated simulation spec; calls guarded framework wrapper | New bridge; framework separately vendored | Presence of instructions does not imply executable readiness or scientific acceptance |
| `upstream-cfd-mesh-gate` | AI-CFD-Scientist `cfd-skills/cfd-mesh-gate` | `b7fa924…514` | MIT, README declaration | Skill, catalog README, repository README | Exact skill snapshot | Enforces observable-aware mesh and time-step gates | New bridge only | No universal threshold and no solver-exit-code acceptance |
| `upstream-cfd-experiment` | AI-CFD-Scientist `cfd-skills/cfd-experiment` | `b7fa924…514` | MIT, README declaration | Skill, catalog README, repository README | Exact skill snapshot | Runs baseline-first experiment plans | New bridge only | Sweeps cannot precede accepted baseline and extractable quantities |
| `upstream-cfd-code-modify` | AI-CFD-Scientist `cfd-skills/cfd-code-modify` | `b7fa924…514` | MIT, README declaration | Skill, catalog README, repository README | Exact skill snapshot | Requires complete equations, dimensions, tests, and fallback | New bridge only | No code generation from an incomplete physical specification |
| `upstream-sim-plugin-openfoam` | sim-plugin-openfoam `_skills/openfoam` | `c53b4f3…710` | Apache-2.0 | Skill, references, tests, license | Entire source skill subtree | Design/audit knowledge after a distribution/version probe | New bridge only | Never mix Foundation and OpenCFD syntax |

## Executable framework

`tools/foam-agent/` is a complete tracked snapshot of `csml-rpi/Foam-Agent` at `cfde3847be548e4264a1455dd77774794e00ee81` (MIT). The PT-authored `tools/openfoam-runner/run_foam_agent.py` sits outside that preserved tree. It defaults to a dependency report and requires both `--execute` and a simulation specification before execution.
