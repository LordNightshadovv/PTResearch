# CYPT Slide Template

An editable 4:3 PowerPoint slide system based mainly on Team Singapore's *Magnetic Gear* deck. It keeps reusable page types for overviews, parameter maps, models, equations, apparatus, graphs, comparisons, and summaries. An optional green conclusion band comes from Team Slovakia's *Wet Scroll* graph page.

## Use it with Codex

Attach a source PowerPoint and ask Codex to **use `$cypt-slide-template`** to restyle it. This skill is set to explicit invocation, so naming it is the reliable way to load it. Codex should map each source slide to a suitable page type, preserve scientific content and citations, and produce a new PPTX. The sample builder below regenerates the starter deck; it does **not** automatically convert an arbitrary PowerPoint.

The starter file is [assets/CYPT_editable_template.pptx](assets/CYPT_editable_template.pptx). The underlying [skill instructions](SKILL.md) tell Codex how to transform a supplied presentation.

## Edit the starter deck

- Most text, colored blocks, diagrams, and callouts are native PowerPoint objects. Apparatus photos are separate images that can be replaced. The two large example graphs are native charts with **illustrative values**; replace their data, labels, and units before presenting. The smaller characterization curves are schematic drawings.
- Edit [assets/template-config.json](assets/template-config.json) to change the event label, title, problem text, and section structure. `sections` controls both the overview and every roadmap footer; `pageSections` assigns each page type to a **zero-based** section index. The builder accepts one to eight sections.
- Edit [assets/singapore-cypt-theme.json](assets/singapore-cypt-theme.json) to change shared colors or the primary font. The Singapore design remains the reference unless you intentionally choose another style.
- A graph conclusion band is optional. Replace its placeholder sentence with a claim supported by the graph, or omit the band.

PowerPoint, WPS Presentation, and Google Slides can edit imported objects, but they do not run the configuration builder. Typing a new section onto the overview slide will **not** update the footers. Change `sections` and `pageSections`, regenerate the PPTX, or update the footer shapes manually. Check charts and fonts after importing into WPS or Google Slides; their native behavior has not been verified for every object.

## Regenerate the starter

From `/Users/vold/Documents/PTResearch`, use the bundled Node runtime and choose a **new** output filename:

```bash
/Users/vold/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node \
  /Users/vold/.codex/skills/cypt-slide-template/scripts/build_template.mjs \
  /Users/vold/.codex/skills/cypt-slide-template/assets/template-config.json \
  /Users/vold/Documents/PTResearch/deliverables/cypt-slide-template/CYPT_custom_v1.pptx
```

The builder reads its bundled assets and validates the exported deck. Codex can locate the current bundled runtime if its path changes. The export is a new file; keep the supplied presentation and prior template revisions intact.

## Equations and evidence

For polished display equations, [LaTeX equations](references/latex-equations.md) documents the Air Vortex method: LaTeX → MathJax SVG → transparent PNG. The placed image can be moved or resized, while changing the mathematics requires editing the LaTeX source and regenerating it. An optional Office Math layer was packaged experimentally but was not proven editable in WPS or PowerPoint.

The retained Magnetic Gear equations, numbers, schematic plots, and sample chart values are layout examples. Verify every equation, measured value, source citation, and uncertainty before using a transformed deck as research evidence.

## What is in this folder

| Path | Purpose |
| --- | --- |
| `SKILL.md` | Agent workflow for converting a presentation |
| `assets/CYPT_editable_template.pptx` | Editable starter deck |
| `assets/template-config.json` | Overview, footer, and example content configuration |
| `assets/singapore-cypt-theme.json` | Shared design tokens |
| `scripts/build_template.mjs` | Starter deck generator and validation |
| `references/style-map.md` | Page types and geometry |
| `references/latex-equations.md` | Equation image workflow and editability limits |
| `references/third-party-skills-review.md` | Security review of linked third-party skills |

The skill is also part of the PT Research plugin. On this computer, the standalone installation belongs at `~/.codex/skills/cypt-slide-template`; `/.codex` would refer to a directory at the filesystem root and is not the Codex user skills location.
