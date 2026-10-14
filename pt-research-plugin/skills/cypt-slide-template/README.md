# CYPT Slide Template

An editable 4:3 PowerPoint slide system in a fixed CYPT house style. It keeps reusable page types for overviews, parameter maps, models, equations, apparatus, graphs, comparisons, and summaries, plus an optional green graph conclusion band. The starter needs no third-party material; optional reference decks stay on the owner's computer (see below).

## Use it with Codex

Attach a source PowerPoint and ask Codex to **use `$cypt-slide-template`** to restyle it. This skill is set to explicit invocation, so naming it is the reliable way to load it. Codex should map each source slide to a suitable page type, preserve scientific content and citations, and produce a new PPTX. The sample builder below regenerates the starter deck; it does **not** automatically convert an arbitrary PowerPoint.

The starter file is [assets/CYPT_editable_template.pptx](assets/CYPT_editable_template.pptx). The underlying [skill instructions](SKILL.md) tell Codex how to transform a supplied presentation.

### Local-only reference material

The decks this style was derived from (Team Singapore "Magnetic Gear" and Team Slovakia "Wet Scroll") are other teams' work, so they are **not** part of the public repository. Private data lives outside the plugin directory so that it survives plugin updates (a marketplace-installed plugin is copied into a cache that is replaced on every update): `PT_RESEARCH_HOME`, default `~/.config/pt-research`.

- `<PT_RESEARCH_HOME>/local.paths.json` – machine paths (template: `local.paths.example.json`);
- `<PT_RESEARCH_HOME>/local-references/*.pdf` – the two source decks, used for visual comparison;
- `<PT_RESEARCH_HOME>/local-references/source-images/` – photos extracted from the Singapore deck (the builder embeds them when present);
- `<PT_RESEARCH_HOME>/local-references/CYPT_editable_template.pptx` and `CYPT_editable_template_reference.pptx` – starter decks with those photos embedded (optional).

`PT_LOCAL_REFERENCES_DIR` overrides the folder; the git-ignored `assets/local-references/` inside the plugin is the last fallback. Settings are looked up in this order: environment variable, `<PT_RESEARCH_HOME>/local.paths.json`, `<plugin-root>/local.paths.json`, `<plugin-root>/.env.local`, default.

To get the decks back on a new machine (or after the folder is lost), run `python3 <plugin-root>/scripts/fetch_local_references.py --check`, then without `--check` to download, or with `--from-dir <backup-folder>` to restore from a local copy. The tool verifies each file against the SHA-256 and size in [references/local-references.manifest.json](references/local-references.manifest.json), keeps only exact matches, and re-extracts `source-images/`. The full agent and user procedure is in the plugin README section "Restoring private CYPT reference decks (not redistributed)". Agents invoked for this skill should run the `--check` preflight first and ask the user before downloading.

Without the folder, the published starter shows labelled photo placeholders, and you can ask for a restyle against any reference deck you supply. Do not commit or redistribute the local references.

## Edit the starter deck

- Most text, colored blocks, diagrams, and callouts are native PowerPoint objects. Apparatus photos are separate images that can be replaced. The two large example graphs are native charts with **illustrative values**; replace their data, labels, and units before presenting. The smaller characterization curves are schematic drawings.
- Edit [assets/template-config.json](assets/template-config.json) to change the event label, title, problem text, and section structure. `sections` controls both the overview and every roadmap footer; `pageSections` assigns each page type to a **zero-based** section index. The builder accepts one to eight sections.
- Edit [assets/cypt-theme.json](assets/cypt-theme.json) to change shared colors or the primary font.
- A graph conclusion band is optional. Replace its placeholder sentence with a claim supported by the graph, or omit the band.

PowerPoint, WPS Presentation, and Google Slides can edit imported objects, but they do not run the configuration builder. Typing a new section onto the overview slide will **not** update the footers. Change `sections` and `pageSections`, regenerate the PPTX, or update the footer shapes manually. Check charts and fonts after importing into WPS or Google Slides; their native behavior has not been verified for every object.

## Regenerate the starter

From your workspace root, run the builder with a Node runtime that provides `@oai/artifact-tool`, and choose a **new** output filename (the output must be inside the workspace):

```bash
export PT_WORKSPACE_ROOT=<workspace>
export RUNTIME_NODE_MODULES=<runtime>/node/node_modules
export RUNTIME_PYTHON=<runtime>/python/bin/python3
export PRESENTATIONS_SKILL=<presentations-skill-dir>   # contains container_tools/
node <plugin-root>/skills/cypt-slide-template/scripts/build_template.mjs \
  <plugin-root>/skills/cypt-slide-template/assets/template-config.json \
  <workspace>/deliverables/cypt-slide-template/CYPT_custom_v1.pptx
```

Instead of exporting variables, you can put the same keys in `<PT_RESEARCH_HOME>/local.paths.json` (copy `local.paths.example.json`; it survives plugin updates). Set `PT_NO_LOCAL_REFERENCES=1` to force placeholder photos even if local references exist. The builder prints which references folder it used.

The builder reads its bundled assets and validates the exported deck. The export is a new file; keep the supplied presentation and prior template revisions intact.

## Equations and evidence

For polished display equations, [LaTeX equations](references/latex-equations.md) documents the Air Vortex method: LaTeX → MathJax SVG → transparent PNG. The placed image can be moved or resized, while changing the mathematics requires editing the LaTeX source and regenerating it. An optional Office Math layer was packaged experimentally but was not proven editable in WPS or PowerPoint.

The sample equations, bracketed values, schematic plots, and sample chart values are layout examples. Verify every equation, measured value, source citation, and uncertainty before using a transformed deck as research evidence.

## What is in this folder

| Path | Purpose |
| --- | --- |
| `SKILL.md` | Agent workflow for converting a presentation |
| `assets/CYPT_editable_template.pptx` | Editable starter deck (photo placeholders) |
| `references/local-references.manifest.json` | Where to obtain the private reference decks and how to verify them (SHA-256, size) |
| `scripts/local_paths.mjs` | Node twin of `scripts/local_paths.py`: settings and local-references lookup |
| `assets/local-references/` | Optional last-fallback, git-ignored location for the private decks (absent in the public repository; prefer `<PT_RESEARCH_HOME>/local-references`) |
| `assets/template-config.json` | Overview, footer, and example content configuration |
| `assets/cypt-theme.json` | Shared design tokens |
| `scripts/build_template.mjs` | Starter deck generator and validation |
| `references/style-map.md` | Page types and geometry |
| `references/latex-equations.md` | Equation image workflow and editability limits |
| `references/third-party-skills-review.md` | Security review of linked third-party skills |

The skill is also part of the PT Research plugin. A standalone installation belongs at `$CODEX_HOME/skills/cypt-slide-template` (by default `~/.codex/skills/cypt-slide-template`).
