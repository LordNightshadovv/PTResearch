#!/usr/bin/env python3
"""Render a standalone PT theoretical report from a completed theory package."""

from __future__ import annotations

import argparse
import csv
import json
import re
import tempfile
from pathlib import Path
from xml.sax.saxutils import escape


THEORY_FILES = (
    "theory-model.md",
    "equations.md",
    "variables.csv",
    "assumptions.md",
    "predictions.csv",
    "parameter-provenance.csv",
    "literature-notes.md",
    "model-validation.md",
)
PLACEHOLDER = re.compile(r"\b(?:TODO|TBD|Pending)\b|\[citation needed\]", re.I)
POINTER = re.compile(r"see (?:the )?(?:model registry|yaml|case (?:directory|folder)|causal-chain artifact|simulation specification)", re.I)
REQUIRED_HEADINGS = (
    "Research question",
    "Observable",
    "Independent variables",
    "Proposed mechanism",
    "Governing equations",
    "Derivation",
    "Predicted relationship",
    "Simulation formulation",
    "Limitations",
    "References",
)
LATEX_SECTIONS = (
    "Problem and research question", "Observables and variables", "Physical mechanism and model choice",
    "Assumptions and validity range", "Governing equations and derivation", "Main prediction and limiting cases",
    "Theory-to-solver mapping", "Calculated example or prediction", "Limitations and references",
)


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8").strip()


def readable_math(expression: str) -> str:
    """Convert a restricted LaTex display equation to readable PDF text."""
    result = expression.strip()
    for _ in range(12):
        updated = re.sub(r"\\frac\{([^{}]+)\}\{([^{}]+)\}", r"(\1)/(\2)", result)
        updated = re.sub(r"\\sqrt\{([^{}]+)\}", r"sqrt(\1)", updated)
        if updated == result:
            break
        result = updated
    replacements = {
        r"\approx": "approximately", r"\propto": "proportional to", r"\times": "x",
        r"\cdot": "*", r"\leq": "<=", r"\geq": ">=", r"\mathrm": "",
        r"\operatorname": "", r"\left": "", r"\right": "", r"\,": " ",
        r"\quad": " ", r"\lambda": "lambda", r"\mu": "mu", r"\omega": "omega",
        r"\Delta": "Delta", r"\partial": "partial ", r"\dot": "d/dt ",
    }
    for source, replacement in replacements.items():
        result = result.replace(source, replacement)
    result = re.sub(r"_\{([^{}]+)\}", r"_\1", result)
    result = re.sub(r"\^\{([^{}]+)\}", r"^\1", result)
    result = result.replace("{", "(").replace("}", ")")
    if "\\" in result:
        raise ValueError(f"equation contains unsupported LaTex command: {expression!r}")
    return result


def validate_theory_package(case: Path, preliminary: bool = False) -> list[str]:
    """Return actionable errors before a reader-facing PDF is created."""
    theory = case / "theory"
    required = ("theory-model.md", "variables.csv", "assumptions.md") if preliminary else THEORY_FILES
    errors: list[str] = []
    for name in required:
        path = theory / name
        if not path.is_file() or not read(path):
            errors.append(f"missing required theory artifact: theory/{name}")
    if errors:
        return errors

    latex = case / "reports" / "theoretical-model.tex"
    if not latex.is_file():
        errors.append("missing required standalone LaTeX report: reports/theoretical-model.tex")
        return errors
    latex_text = read(latex)
    if PLACEHOLDER.search(latex_text):
        errors.append("reports/theoretical-model.tex contains placeholder text")
    if POINTER.search(latex_text):
        errors.append("reports/theoretical-model.tex points readers to an internal artifact instead of explaining the theory")
    if not preliminary:
        missing_latex = [section for section in LATEX_SECTIONS if f"\\section{{{section}}}" not in latex_text]
        if missing_latex:
            errors.append("reports/theoretical-model.tex lacks required sections: " + ", ".join(missing_latex))
        if "\\begin{equation}" not in latex_text:
            errors.append("reports/theoretical-model.tex needs numbered LaTeX equations")
        if not re.search(r"(?:\\cite|\\autocite|\\textcite)", latex_text):
            errors.append("reports/theoretical-model.tex needs citations beside supported claims or equations")

    model = read(theory / "theory-model.md")
    if PLACEHOLDER.search(model):
        errors.append("theory/theory-model.md contains placeholder text")
    if POINTER.search(model):
        errors.append("theory/theory-model.md points readers to an internal artifact instead of explaining the theory")
    if preliminary:
        return errors

    missing = [heading for heading in REQUIRED_HEADINGS if heading.lower() not in model.lower()]
    if missing:
        errors.append("theory/theory-model.md lacks required sections: " + ", ".join(missing))
    if "holding " not in model.lower() or not re.search(r"predicts that.+(?:increases|decreases|remains)", model, re.I | re.S):
        errors.append("theory/theory-model.md lacks an explicit holding-fixed, testable trend statement")

    equations = read(theory / "equations.md")
    if PLACEHOLDER.search(equations) or POINTER.search(equations):
        errors.append("theory/equations.md contains placeholder or internal-artifact pointer text")
    if equations.count("$$") < 2:
        errors.append("theory/equations.md needs at least one display equation delimited by $$")
    if not re.search(r"(?:standard law|literature equation|adapted equation|empirical correlation|fitted model|derived here|numerical governing equation)", equations, re.I):
        errors.append("theory/equations.md must state the provenance class of the governing equation")

    for filename, required_columns in {
        "variables.csv": {"symbol", "meaning", "unit", "status", "source"},
        "predictions.csv": {"dependent_variable", "independent_variable", "value", "unit", "prediction_basis", "parameter_values", "provenance"},
        "parameter-provenance.csv": {"parameter", "value", "unit", "status", "source_or_method"},
    }.items():
        with (theory / filename).open(encoding="utf-8", newline="") as stream:
            rows = list(csv.DictReader(stream))
            headers = set(rows[0]) if rows else set()
        if not required_columns.issubset(headers):
            errors.append(f"theory/{filename} lacks required columns: {sorted(required_columns - headers)}")
        elif not rows:
            errors.append(f"theory/{filename} needs at least one data row")

    for filename in ("assumptions.md", "literature-notes.md", "model-validation.md"):
        text = read(theory / filename)
        if PLACEHOLDER.search(text) or POINTER.search(text):
            errors.append(f"theory/{filename} contains placeholder or internal-artifact pointer text")
    literature = read(theory / "literature-notes.md")
    if not re.search(r"(?:doi:|https?://|\[[A-Za-z]\d+\])", literature, re.I):
        errors.append("theory/literature-notes.md needs source-specific citations or stable identifiers")
    return errors


def markdown_story(text: str, story: list[object], styles: object, temp: Path) -> None:
    """Render headings, prose, and display equations from constrained Markdown."""
    from reportlab.platypus import Paragraph, Preformatted, Spacer

    blocks = re.split(r"(\$\$.*?\$\$)", text, flags=re.S)
    for block in blocks:
        block = block.strip()
        if not block:
            continue
        if block.startswith("$$") and block.endswith("$$"):
            expression = readable_math(block[2:-2])
            story.extend([Preformatted(expression, styles["Code"]), Spacer(1, 8)])
            continue
        for paragraph in re.split(r"(?m)(?=^#{1,3}\s)|\n\s*\n", block):
            paragraph = paragraph.strip()
            if not paragraph:
                continue
            if paragraph.startswith("### "):
                story.extend([Paragraph(escape(paragraph[4:]), styles["Heading3"]), Spacer(1, 4)])
            elif paragraph.startswith("## "):
                story.extend([Paragraph(escape(paragraph[3:]), styles["Heading2"]), Spacer(1, 6)])
            elif paragraph.startswith("# "):
                story.extend([Paragraph(escape(paragraph[2:]), styles["Heading1"]), Spacer(1, 8)])
            else:
                clean = re.sub(r"^[*-]\s+", "", paragraph, flags=re.M)
                clean = clean.replace("**", "").replace("`", "")
                story.extend([Paragraph(escape(clean).replace("\n", "<br/>"), styles["BodyText"]), Spacer(1, 7)])


def csv_table(path: Path, title: str, story: list[object], styles: object) -> None:
    from reportlab.lib import colors
    from reportlab.platypus import Paragraph, Spacer, Table, TableStyle

    with path.open(encoding="utf-8", newline="") as stream:
        rows = list(csv.reader(stream))
    data = [
        [Paragraph(escape(cell.replace("_", " ") if index == 0 else cell), styles["BodyText"]) for cell in row]
        for index, row in enumerate(rows)
    ]
    story.extend([Paragraph(title, styles["Heading2"]), Table(data, repeatRows=1, hAlign="LEFT", colWidths=[72] * len(rows[0]))])
    story[-1].setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#183a5a")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#8b99a5")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(Spacer(1, 12))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("case_dir", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--preliminary-model-plan", action="store_true")
    args = parser.parse_args()
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.lib.units import mm
        from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer
    except ImportError as exc:
        raise SystemExit("reportlab is required to render the PDF; install it in the rendering environment") from exc

    case = args.case_dir.resolve()
    errors = validate_theory_package(case, args.preliminary_model_plan)
    if errors:
        raise SystemExit("REFUSED: " + "\n- ".join(["theory package is not ready for a human-facing PDF", *errors]))
    problem_path = case / "problem_contract.yaml"
    problem = json.loads(problem_path.read_text(encoding="utf-8")) if problem_path.exists() else {}
    output = args.output.resolve(); output.parent.mkdir(parents=True, exist_ok=True)
    styles = getSampleStyleSheet(); story: list[object] = []
    title = "Preliminary Model Plan" if args.preliminary_model_plan else "PT Theoretical Report"
    story.extend([Paragraph(title, styles["Title"]), Spacer(1, 14)])
    prompt = problem.get("exact_prompt", "Official prompt not recorded.") if isinstance(problem, dict) else "Official prompt not recorded."
    story.extend([Paragraph("Problem statement", styles["Heading2"]), Paragraph(escape(str(prompt)), styles["BodyText"]), Spacer(1, 12)])

    theory = case / "theory"
    with tempfile.TemporaryDirectory(prefix="pt-theory-pdf-") as temp_dir:
        temp = Path(temp_dir)
        markdown_story(read(theory / "theory-model.md"), story, styles, temp)
        if not args.preliminary_model_plan:
            csv_table(theory / "variables.csv", "Variables and parameters", story, styles)
            markdown_story(read(theory / "equations.md"), story, styles, temp)
            markdown_story(read(theory / "assumptions.md"), story, styles, temp)
            csv_table(theory / "predictions.csv", "Prediction evidence", story, styles)
            csv_table(theory / "parameter-provenance.csv", "Parameter provenance", story, styles)
            markdown_story(read(theory / "literature-notes.md"), story, styles, temp)
            markdown_story(read(theory / "model-validation.md"), story, styles, temp)

        def footer(canvas: object, doc: object) -> None:
            canvas.saveState(); canvas.setFont("Helvetica", 8)
            canvas.drawRightString(A4[0] - 15 * mm, 10 * mm, f"Page {doc.page}")
            canvas.restoreState()

        SimpleDocTemplate(str(output), pagesize=A4, title=title, leftMargin=18 * mm, rightMargin=18 * mm, topMargin=17 * mm, bottomMargin=17 * mm).build(story, onFirstPage=footer, onLaterPages=footer)
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
