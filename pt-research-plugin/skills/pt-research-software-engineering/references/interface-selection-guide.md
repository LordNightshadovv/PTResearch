# Interface and GUI selection guide

A scientific tool needs a **headless, testable core** first. An interface is added only where it improves usability, accessibility, or research efficiency (interactive parameter exploration, live plots, instrument control, use by non-programmers). Otherwise a CLI plus saved figures and reports is the right answer.

## Decision procedure

1. Who runs it, how often, and where (laptop, remote Linux over SSH, classroom)?
2. Does interactivity change the science (exploring regimes, tuning fits by eye with residuals, live acquisition)? If not, prefer CLI/config/batch.
3. Pick the lightest interface that meets the need, using the table.
4. Record the choice, rationale, and accessibility notes in the ADR and manifest `interface`.

| Need | Choose | Notes |
|------|--------|-------|
| Batch runs, sweeps, CI, remote servers | CLI + config files | Default; scriptable, diffable, testable |
| Quick interactive exploration, shareable demo, few widgets | Web UI: Streamlit, Panel, or Dash | Fast to build; works in a browser; weaker offline/native control |
| Rich desktop workflow: dockable plots, file dialogs, instrument control, large data | Desktop GUI: PySide6/Qt (matplotlib or pyqtgraph embedding) | Heavier packaging; strongest native accessibility support through Qt |
| Multi-user, remote, or service deployment | FastAPI backend + separate frontend | Core exposed as an API; add auth and versioned schemas |
| Terminal-first, SSH-friendly, keyboard-driven, DOS-style aesthetic | TUI: Python Textual | Rapid development, rich widgets, good with the Python core |
| TUI that must be very fast, single-binary, or highly reliable (long-running monitors, large log streams, simulation dashboards) | TUI: Rust ratatui (+ crossterm) | Only with a documented performance/reliability case; talk to the Python core over a narrow typed interface (files, JSON-lines, sockets); a Rust core is a separate language decision |
| Exploratory analysis and teaching | Notebook, with logic imported from the tested package | Notebooks are views, not the source of truth |

Rust is an option, not a default. A TUI in Python Textual is the normal starting point; move to ratatui only when profiling or reliability requirements justify a second toolchain.

## Required architecture

- **Thin layer:** the interface binds widgets to a toolkit-independent controller (form text in, validated request, call core, view model out). No physics, no numerical logic, no unit conversion rules in widgets.
- **One-way dependency:** interface imports core; core never imports interface or any GUI toolkit (enforced by an AST test in the template).
- **Headless tests:** test the controller and view-model rendering without a display; add a few smoke tests of the real toolkit where feasible.
- **Same results everywhere:** the GUI path and the CLI path produce byte-identical result files for the same config and seed.
- **Long-running work off the UI thread** (workers/processes), with cancellation, progress, and visible failure states.
- **Provenance:** every GUI-launched run writes the same run metadata as the CLI.

## Accessibility and usability

- Full keyboard operation and logical focus order; visible focus.
- Never encode status by color alone; add text, shape, or pattern. Use colorblind-safe palettes (Okabe-Ito) in plots.
- Scalable text, sufficient contrast (WCAG AA targets), no fixed pixel layouts that break at large fonts.
- Text alternatives: data tables, captions, or exportable values for every plot; units on every axis and field.
- Screen-reader friendliness: toolkit accessible names/roles (Qt accessibility, ARIA via web frameworks); in terminals, plain-text output, no information only in cursor position or animation.
- Clear errors in plain language with the offending field and valid range; undo/reset to defaults.
- TUI specifics: respect `NO_COLOR` and terminal size, provide a non-interactive `--plain` output, avoid flicker, support copying values.
- Record unmet items in `interface.accessibility.limitations`; the validator requires an explanation for every flag declared false.

## DOS-style TUI aesthetic

Monospace grid, box-drawing borders, high-contrast two-to-four color palette, menu bar with hotkeys, status line showing units and run state. Keep the look in a theme file; keep behavior identical to the CLI. Accessibility rules above still apply; a retro look must not reduce contrast or keyboard access.

## Manifest fields

`interface.primary` (library_only, cli, desktop_gui, web_ui, tui_python, tui_rust, notebook), `justification`, `headless_core: true`; for GUI/TUI also `thin_layer: true`, `gui_layer_path`, `usability_rationale`, `accessibility` flags with `notes` and `limitations`; for `tui_rust` also `implementation_language: Rust` and a `rust_rationale` stating the performance or reliability requirement.
