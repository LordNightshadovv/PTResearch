# Third-Party Notices

This plugin contains preserved upstream snapshots and one vendored executable framework. PT bridge files are local adaptations; `upstream-original/` directories are unmodified snapshots whose hashes are recorded in `upstream-lock.yaml`.

| Component | Copyright/project | Pinned commit | License evidence |
|---|---|---|---|
| K-Dense literature-review | K-Dense-AI/scientific-agent-skills | `3f825caafe149b7853ec8c4d1dd7f4553ea6b2a5` | MIT; repository `LICENSE` copied into the local specialist |
| DeerFlow systematic-literature-review | bytedance/deer-flow | `0cd55067f39823e7f0950498b5197a8195512481` | MIT; repository `LICENSE` copied into the local specialist |
| DeerFlow academic-paper-review | bytedance/deer-flow | `0cd55067f39823e7f0950498b5197a8195512481` | MIT; repository `LICENSE` copied into the local specialist |
| Four AI-CFD-Scientist skills | csml-rpi/AI-CFD-Scientist | `b7fa924c834ccfd81c67788b7d6b2e3c9ff13514` | MIT as explicitly declared in the pinned repository README under “License and citation”; the repository has no standalone `LICENSE` at this commit. The local license records preserve that provenance and the MIT terms. |
| sim-plugin-openfoam skill | svd-ai-lab/sim-plugin-openfoam | `c53b4f362c9b06c985393a777365a9f48fa00710` | Apache-2.0; repository license copied into the specialist |
| Foam-Agent framework | csml-rpi/Foam-Agent | `cfde3847be548e4264a1455dd77774794e00ee81` | MIT; framework `LICENSE` preserved in `tools/foam-agent/LICENSE` |

The complete source paths, retrieval timestamps, per-file hashes, tree hashes, and reuse classifications are in `upstream-lock.yaml` and each specialist's `SOURCE.yaml`. No license conclusion is inferred from the absence of a file: the AI-CFD record points to its affirmative README declaration.
