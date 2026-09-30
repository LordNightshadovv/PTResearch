#!/usr/bin/env python3
"""Scaffold, validate, build, and render PT solver-use reference artifacts."""

from __future__ import annotations

import argparse
import csv
import json
import re
from datetime import date
from pathlib import Path
from xml.sax.saxutils import escape


PLACEHOLDER = re.compile(r"\b(?:TODO|TBD|Pending)\b", re.I)
CATALOG_HEADINGS = ("Prompt identity", "Solver decision", "Solver identity and origin", "Installation and packaging", "Role in the prompt", "Prompt-specific configuration", "Theory-to-solver mapping", "Inputs and outputs", "Verification and validation", "Prompt-specific limitations", "Reproduction", "References")
COMPENDIUM_HEADINGS = ("Contents", "Version table", "Solver-prompt matrix", "Glossary", "References")

CORE = {
    "openfoam": """## solver-openfoam: OpenFOAM

### Governing physical equations
For the incompressible cases used here, continuity is `div(u) = 0` and momentum is `rho (du/dt + u dot grad(u)) = -grad(p) + div(tau) + rho g + f`. Add phase, heat, acoustic, or constitutive transport only when the prompt inventory records it.

### Mathematical and numerical foundation
The finite-volume method integrates conservation over each control volume. The Gauss divergence theorem converts `integral_V div(F) dV` to the sum of face fluxes `sum_faces F_f dot S_f`. The resulting discrete balance is `a_P phi_P = sum_N a_N phi_N + b`.

### Integration, coupling, and error
Use the recorded SIMPLE, PISO, or PIMPLE pressure-velocity algorithm; do not imply that an unused algorithm was selected. Report Courant number, residuals, conservation, mesh quality, numerical diffusion, interface boundedness, time-step sensitivity, and turbulence/model-form limits.
""",
    "hcipy": """## solver-hcipy: HCIPy

### Governing physical equations
The scalar complex field is `U(x,y) = A(x,y) exp(i phi(x,y))`; intensity is `I = |U|^2`. In the Fraunhofer regime, focal-plane propagation is `U_f(f_x,f_y) proportional_to Fourier{U_p(x,y)}`.

### Mathematical and numerical foundation
The Huygens-Fresnel principle and Fourier transform/convolution theorem motivate pupil-to-focal-plane propagation. FFT sampling approximates the continuous transform; zero padding and grid spacing control aliasing and field-of-view error.

### Integration, coupling, and error
There is no time integrator for a static propagation unless the recorded prompt uses one. Report scalar/paraxial assumptions, omitted polarization, sampling, aliasing, pupil discretization, and comparison with analytic aperture/PSF limits.
""",
    "project-chrono": """## solver-project-chrono: Project Chrono

### Governing physical equations
Rigid-body motion uses `m dv/dt = sum(F)` and `I domega/dt + omega x (I omega) = sum(tau)`. A constrained system is `M(q) q_ddot + C_q^T lambda = Q`, with constraints `C(q,t) = 0`.

### Mathematical and numerical foundation
Generalized coordinates, constraint Jacobians, and Lagrange multipliers determine reaction forces. State the actual penalty, non-smooth, Hertzian, damping, or Coulomb contact model from the inventory.

### Integration, coupling, and error
Report the recorded integrator, constraint stabilization, contact stiffness, time-step sensitivity, friction/restitution calibration, constraint drift, and energy behavior.
""",
    "elmer-fem": """## solver-elmer-fem: Elmer FEM

### Governing physical equations
For a representative PDE, `-div(k grad(u)) = f`. Its weak form is `integral_Omega k grad(u) dot grad(v) = integral_Omega f v + integral_Gamma qbar v`. Finite elements use `u_h(x) = sum_i N_i(x) u_i`, producing `K u = f`.

### Mathematical and numerical foundation
The weak formulation, virtual work, and Galerkin projection turn the PDE into a sparse algebraic system. Add only the elasticity, membrane, acoustic, piezoelectric, or electromagnetic equation actually used.

### Integration, coupling, and error
Report element order, mesh refinement, conditioning, locking, eigenvalue/nonlinear convergence, boundary-condition sensitivity, and the chosen time integration for dynamics.
""",
    "yade": """## solver-yade: YADE

### Governing physical equations
Particle motion uses `m_i x_ddot_i = sum_j F_ij + m_i g` and `I_i omega_dot_i = sum_j tau_ij`. A representative linear contact law is `F_n = k_n delta_n - c_n delta_dot_n`, with `|F_t| <= mu |F_n|` for Coulomb friction.

### Mathematical and numerical foundation
Discrete-element integration resolves particle/contact forces. State the actual cohesive, frictional, damping, and breakage law used; do not assume real fracture, adhesion, or deposition follows automatically.

### Integration, coupling, and error
Report critical time step, stiffness/damping, particle-size sensitivity, calibration, stochastic variation, and force-displacement verification.
""",
}


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def prompt_catalog_template() -> str:
    return "# Solver Usage Catalog\n\n" + "\n\n".join(f"## {heading}\n\nPending." for heading in CATALOG_HEADINGS) + "\n"


def scaffold_prompt(case: Path, batch_id: str) -> None:
    write(case / "reports" / "solver-usage-catalog.md", prompt_catalog_template())
    write(case / "provenance" / "solver-inventory.yaml", json.dumps({"batch_id": batch_id, "solvers": []}, indent=2) + "\n")
    write(case / "provenance" / "installation-record.md", "# Installation record\n\nPending.\n")
    write(case / "provenance" / "software-citations.bib", "% Pending.\n")
    write(case / "provenance" / "licenses.md", "# Software licenses\n\nPending.\n")


def scaffold_batch(batch: Path) -> None:
    write(batch / "reports" / "solver-mechanism-compendium.md", "# Solver-Mechanism Compendium\n\nPending.\n")
    write(batch / "data" / "batch-solver-index.yaml", json.dumps({"batch_id": batch.name, "solvers": []}, indent=2) + "\n")
    write(batch / "data" / "solver-prompt-matrix.csv", "prompt,primary_solver,module,numerical_method,role,evidence_level,chapter_id\n")
    write(batch / "data" / "software-citations.bib", "% Pending.\n")
    (batch / "figures" / "solver-mechanisms").mkdir(parents=True, exist_ok=True)


def validate_prompt(case: Path) -> list[str]:
    errors: list[str] = []
    catalog = case / "reports" / "solver-usage-catalog.md"
    inventory = case / "provenance" / "solver-inventory.yaml"
    for path in (catalog, inventory, case / "provenance" / "installation-record.md", case / "provenance" / "software-citations.bib", case / "provenance" / "licenses.md"):
        if not path.is_file() or not path.read_text(encoding="utf-8").strip(): errors.append(f"missing required prompt artifact: {path}")
    if errors: return errors
    text = catalog.read_text(encoding="utf-8")
    missing = [h for h in CATALOG_HEADINGS if h not in text]
    if missing: errors.append("catalog lacks sections: " + ", ".join(missing))
    if PLACEHOLDER.search(text): errors.append("catalog contains placeholder text")
    if "Batch Solver-Mechanism Compendium" not in text: errors.append("catalog lacks batch-compendium cross-reference")
    try: solvers = load_json(inventory).get("solvers", [])
    except (ValueError, json.JSONDecodeError): return errors + ["solver inventory must be JSON-compatible YAML"]
    actual = [s for s in solvers if isinstance(s, dict) and s.get("actually_used")]
    if not actual: errors.append("solver inventory records no actually used solver")
    for solver in actual:
        for field in ("id", "official_name", "version", "official_homepage", "repository", "license", "citation", "installation_method", "execution_platform", "modules", "physical_equations", "numerical_algorithms", "chapter_id"):
            if not solver.get(field): errors.append(f"actually used solver lacks {field}: {solver.get('id', '<unknown>')}")
    return errors


def build_compendium(batch: Path) -> None:
    index = load_json(batch / "data" / "batch-solver-index.yaml")
    solvers = [s for s in index.get("solvers", []) if isinstance(s, dict) and s.get("actually_used")]
    chapters: list[str] = []
    for solver in solvers:
        identifier = str(solver.get("id", "")).lower().replace(" ", "-")
        foundation = CORE.get(identifier, "## Numerical mechanism\n\nDescribe the governing equations, discretization, integration, stability, convergence, and error sources for this documented solver.")
        chapters.append(f"Solver: {solver.get('official_name')}\n\nVersion: {solver.get('version')}\n\nProject of origin: {solver.get('official_homepage')}\n\nLicense: {solver.get('license')}\n\nNumerical-method family: {solver.get('numerical_method_family')}\n\nPrompts using it: {', '.join(solver.get('prompts', []))}\n\nModules used: {', '.join(solver.get('modules', []))}\n\n{foundation}\n\n### Batch-specific usage and verification\n\n{solver.get('batch_usage', 'Record prompt-specific module, observable, customization, limitation, and a relevant benchmark or analytical comparison.')}\n")
    matrix = (batch / "data" / "solver-prompt-matrix.csv").read_text(encoding="utf-8")
    body = "# Solver-Mechanism Compendium\n\n## Contents\n\n" + "\n".join(f"- {s.get('chapter_id')}" for s in solvers) + "\n\n## Version table\n\n" + "\n".join(f"- {s.get('official_name')} {s.get('version')} ({s.get('license')})" for s in solvers) + "\n\n## Solver-prompt matrix\n\n```text\n" + matrix + "```\n\n" + "\n\n".join(chapters) + "\n\n## Glossary\n\nDefine every batch-specific symbol and numerical term.\n\n## References\n\nSee data/software-citations.bib for complete software and numerical-method references.\n"
    write(batch / "reports" / "solver-mechanism-compendium.md", body)


def validate_batch(batch: Path) -> list[str]:
    errors: list[str] = []
    report = batch / "reports" / "solver-mechanism-compendium.md"; index_path = batch / "data" / "batch-solver-index.yaml"; matrix = batch / "data" / "solver-prompt-matrix.csv"
    for path in (report, index_path, matrix, batch / "data" / "software-citations.bib"):
        if not path.is_file() or not path.read_text(encoding="utf-8").strip(): errors.append(f"missing required batch artifact: {path}")
    if errors: return errors
    text = report.read_text(encoding="utf-8")
    missing = [h for h in COMPENDIUM_HEADINGS if h not in text]
    if missing: errors.append("compendium lacks sections: " + ", ".join(missing))
    if PLACEHOLDER.search(text): errors.append("compendium contains placeholder text")
    index = load_json(index_path); actual = [s for s in index.get("solvers", []) if isinstance(s, dict) and s.get("actually_used")]
    with matrix.open(encoding="utf-8", newline="") as stream:
        rows = list(csv.DictReader(stream))
    for solver in actual:
        if solver.get("chapter_id") not in text: errors.append(f"compendium lacks solver chapter: {solver.get('chapter_id')}")
        if not any(row.get("primary_solver") == solver.get("official_name") for row in rows): errors.append(f"matrix lacks actually used solver: {solver.get('official_name')}")
    return errors


def render(markdown: Path, output: Path) -> None:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer
    styles = getSampleStyleSheet(); story = []
    for block in re.split(r"\n\s*\n", markdown.read_text(encoding="utf-8")):
        block = block.strip()
        if not block: continue
        level = 1 if block.startswith("# ") else 2 if block.startswith("## ") else 3 if block.startswith("### ") else 0
        if level:
            story.extend([Paragraph(escape(block.splitlines()[0][level + 1:]), styles[f"Heading{level}"]), Spacer(1, 6)])
            remainder = "\n".join(block.splitlines()[1:]).strip()
            if remainder: story.extend([Paragraph(escape(remainder).replace("\n", "<br/>"), styles["BodyText"]), Spacer(1, 8)])
        else: story.extend([Paragraph(escape(block).replace("\n", "<br/>"), styles["BodyText"]), Spacer(1, 8)])
    output.parent.mkdir(parents=True, exist_ok=True)
    SimpleDocTemplate(str(output), pagesize=A4, title=markdown.stem).build(story)


def main() -> int:
    parser = argparse.ArgumentParser(); sub = parser.add_subparsers(dest="command", required=True)
    for name in ("scaffold-prompt", "validate-prompt", "scaffold-batch", "build-compendium", "validate-batch"):
        item = sub.add_parser(name); item.add_argument("path", type=Path)
        if name == "scaffold-prompt": item.add_argument("--batch", required=True)
    item = sub.add_parser("render"); item.add_argument("markdown", type=Path); item.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.command == "scaffold-prompt": scaffold_prompt(args.path.resolve(), args.batch)
    elif args.command == "scaffold-batch": scaffold_batch(args.path.resolve())
    elif args.command == "build-compendium": build_compendium(args.path.resolve())
    elif args.command == "render": render(args.markdown.resolve(), args.output.resolve())
    else:
        errors = validate_prompt(args.path.resolve()) if args.command == "validate-prompt" else validate_batch(args.path.resolve())
        if errors:
            print("FAIL:"); print("\n".join(f"- {error}" for error in errors)); return 1
        print("PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
