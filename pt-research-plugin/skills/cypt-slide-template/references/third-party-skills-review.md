# Third-party skill review for CYPT slides

Codex Security scan `5a8a5b2c-627d-49f0-b86b-18c685518e8d` reviewed the downloaded source on 2026-09-29 before active installation or execution. It was a static review; bundled font binaries were inventoried but not parser-audited. The sealed report is at `/Users/vold/.codex/state/plugins/codex-security/scans/cypt-skill-quarantine/unversioned_20260928T164039Z_qc20e_sj/report.md`.

| Skill | CYPT workflow decision | Source-backed result |
| --- | --- | --- |
| [Theme Factory](https://github.com/anthropics/skills/tree/main/skills/theme-factory) | Use its custom-theme method | No finding in its instructions, theme files, or inspected showcase PDF structure. |
| [MiniMax PDF](https://github.com/MiniMax-AI/skills/tree/main/skills/minimax-pdf) | Exclude | Rendering scripts can install unpinned dependencies and inject document fields into browser-rendered HTML. |
| [Canvas Design](https://github.com/anthropics/skills/tree/main/skills/canvas-design) | Exclude | Its instructions claim the user already issued a directive when none is established. An older local copy may exist; do not treat that as approval for CYPT use. |
| [LaTeX Posters](https://github.com/K-Dense-AI/scientific-agent-skills/tree/main/skills/latex-posters) | Exclude | Its standard workflow sends poster prompts and images to an external AI service. |

Do not run or incorporate the excluded skills unless their issues are resolved and the updated versions pass a new scoped review. This decision is specific to the CYPT workflow and does not establish a general safety guarantee for Theme Factory.
