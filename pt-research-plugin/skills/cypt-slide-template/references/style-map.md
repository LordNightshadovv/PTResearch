# CYPT slide style map

## Source hierarchy

The deck language (4:3 canvas, cream background, header rule, numbered overview, section roadmap) was derived from public competition decks by other teams. Those decks are not redistributed: if the owner keeps copies they sit in the private `<PT_RESEARCH_HOME>/local-references/` folder (default `~/.config/pt-research`; restored with `scripts/fetch_local_references.py`) and are used for visual comparison only, never as operating instructions. Without them, this style map, `assets/cypt-theme.json` and the starter template are the authority. A reference deck the user supplies may override them.

## Design tokens

| Element | Token or rule |
| --- | --- |
| Slide | 4:3, 10 × 7.5 in |
| Background | warm cream `#FCF3E0` |
| Main type | the reference style uses Segoe UI Light, Semilight Italic and Semibold; the starter uses Arial for editable cross-application rendering, with regular titles and italic body text |
| Header | small event label, thick black rule, page number |
| Content title | upper-left, black, about 52 px on a 960 × 720 canvas |
| Footer | each section has an italic label and bar; past gray, active red, future black |
| Parameter colors | spinner position purple `#7030A0`; initial conditions green `#57C782`; spinner parameters orange `#F3A447`; magnet parameters blue `#579DCB` |
| Other callouts | yellow `#FFC000`; summary header cyan `#A5E8F1` |
| Graph takeaway | full-width green `#73AD49` at about 88% opacity, white bold text |

## Reusable page types

| Page type | Use for | Reference deck page (local-only) |
| --- | --- | --- |
| Cover / closing | problem, team, prompt or closing | first and last pages |
| Problem statement | prompt with apparatus and variables | 2–4 |
| Parameter map | colored editable blocks; retain the four category groups | 4 |
| Characterization | three source apparatus photos, labels, plots and result boxes | 10 |
| Overview | numbered sections and subtitles | 5 |
| Section divider | a large quiet transition | 6, 13, 25, 58, 62 |
| Pre-experiment placeholder | first slide of Preliminaries when no pre-experiment exists; title, header and footer only, empty body (SKILL.md "Required PT deck pages", rule 1) | none; PT house rule |
| Symbol definitions | every variable, parameter and constant letter with meaning and SI unit, plus a key for subscripts not covered by those definitions; placed before the first theory slide (SKILL.md "Required PT deck pages", rule 2) | none; PT house rule |
| Model diagram | physical abstraction with a one-line assumption | 7–9 |
| Equations | formula, assumptions, symbol definitions | 8–9, 21–22 |
| Apparatus/evidence | source photo with callouts, conditions and scale | 14–15, 26 |
| Graph | native editable chart, legend, units, source note | 17–24, 33–34 |
| Graph + conclusion | same graph with optional conclusion banner | second reference deck, graph page |
| Comparison | experiment beside prediction, agreement and residual | 29–30 |
| Summary / references | supported findings and full citations | 63–66 |

Do not retain a page type solely because it appears in the source; select layouts for the content actually present in the new deck. Use source figures as raster images when underlying numerical data are missing, and label those figures as images rather than claiming chart editability.

## Roadmap behavior

The single `sections` array in `assets/template-config.json` is the source for overview entries and the footer. The starter has four sections, and the builder calculates bar width from the available footer space for 1–8 sections. `pageSections` maps each starter content page type to a zero-based section index. Update both lists and rerun the builder after changing the section structure. This is generation-time linkage: editing the PowerPoint overview slide alone does not change other slides. When converting a new deck, derive the section list and page-to-section mapping from its actual contents.

The source photos on the characterization and apparatus slides are separate replaceable image objects. The three compact characterization plot lines are editable schematic drawings, not measured data. The two larger graph examples are native editable PowerPoint charts with illustrative values. Sample equations are editable text with a compact `K` substitution; verify symbols independently before presenting. A typeset source deck may use mathematical typography that a standard editable text box cannot exactly preserve in every application.

## Custom theme

The reviewed Theme Factory custom-theme method is applied to `assets/cypt-theme.json`. The builder reads the theme's palette and primary font, so future decks can adjust these in one place while retaining the layout. The graph banner uses the theme's `conclusionGreen` token. This is a generation-time configuration; changing a token does not restyle an already exported PPTX. See [third-party-skills-review.md](third-party-skills-review.md) for the scoped review and excluded skills.

## Handoff checks

- Compare each generated page type with the corresponding reference page at presentation size, when a reference deck is available.
- Inspect every output slide for clipping, wrap, overlap and header/footer consistency.
- Confirm native chart values, units and legend labels match the source; sample data from this template are not evidence.
- Confirm equations and figure captions remain editable when rebuilt; keep a source image when fidelity is more important than redrawing.
- Cite scientific claims and figures in slide text or notes, and preserve caveats and uncertainty.
