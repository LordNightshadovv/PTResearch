#!/usr/bin/env python3
"""Validate deep PT theory packages and reject generic or unsupported reports."""
from __future__ import annotations

import argparse
import csv
import json
import re
from pathlib import Path

REQUIRED = (
    "theory-model.tex", "equations.yaml", "variables.csv", "assumptions.md",
    "mechanism-chain.md", "predictions.csv", "parameter-provenance.csv",
    "conclusion-deductions.md", "literature-notes.md", "validation-plan.md",
)
SECTIONS = (
    "Problem and research question", "Observables and variables",
    "Physical mechanism and model choice", "Assumptions and validity range",
    "Governing equations and derivation", "Main prediction and limiting cases",
    "Theory-to-solver mapping", "Calculated example or prediction",
    "Model conclusion", "Validation, limitations, and references",
)
REJECT = (
    (re.compile(r"(?:Y\s*/\s*Y_0|\\frac\{Y\}\{Y_0\}).{0,24}=\s*F\s*(?:\\!)*\s*(?:\\left)?\(", re.I), "generic normalized placeholder"),
    (re.compile(r"\bF\s*\(\s*V\s*\)(?!\s*=)"), "undefined forcing function F(V)"),
    (re.compile(r"the terms represent (?:inertia|forcing|damping|transport)", re.I), "generic term explanation"),
    (re.compile(r"\bmodel variable\b", re.I), "undefined variable meaning"),
    (re.compile(r"(?:/Users/|[A-Z]:\\\\Users\\\\)"), "raw local filesystem path"),
)


def table(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as stream:
        return list(csv.DictReader(stream))


def validate(case: Path) -> list[str]:
    errors: list[str] = []
    theory = case / "theory"
    for name in REQUIRED:
        path = theory / name
        if not path.is_file() or not path.read_text(encoding="utf-8").strip():
            errors.append(f"missing or empty theory/{name}")
    report = case / "reports" / "theoretical-model.tex"
    pdf = case / "reports" / "theoretical-model.pdf"
    if not report.is_file():
        errors.append("missing reports/theoretical-model.tex")
    if not pdf.is_file() or not pdf.read_bytes().startswith(b"%PDF-"):
        errors.append("missing or invalid reports/theoretical-model.pdf")
    if errors:
        return errors

    tex = report.read_text(encoding="utf-8")
    for section in SECTIONS:
        if rf"\section{{{section}}}" not in tex:
            errors.append(f"missing report section: {section}")
    if tex.count(r"\begin{equation}") < 3:
        errors.append("report needs at least three numbered causal-link equations")
    for pattern, label in REJECT:
        if pattern.search(tex):
            errors.append(f"report contains {label}")
    for required_phrase in ("Origin and apparatus meaning", "Dimensions, roles, signs, and competition",
                            "Assumptions, dominant limits, and contradiction", "Falsifier:"):
        if tex.count(required_phrase) < 3:
            errors.append(f"each important equation must include: {required_phrase}")
    chain = (theory / "mechanism-chain.md").read_text(encoding="utf-8")
    if chain.count(r"\(\to\)") < 4 and chain.count("→") < 4:
        errors.append("mechanism chain needs controlled input through measurable observable")

    variables = table(theory / "variables.csv")
    registry = {row.get("symbol", "").strip() for row in variables}
    if not variables or "" in registry:
        errors.append("variable registry is empty or has blank symbols")
    for row in variables:
        for field in ("meaning", "unit", "status", "source"):
            if not row.get(field, "").strip():
                errors.append(f"variable {row.get('symbol','?')} lacks {field}")
        if row.get("meaning", "").strip().lower() == "model variable":
            errors.append(f"variable {row.get('symbol','?')} has generic meaning")

    equations = json.loads((theory / "equations.yaml").read_text(encoding="utf-8")).get("equations", [])
    if len(equations) < 3:
        errors.append("equations.yaml needs at least three causal-link equations")
    for eq in equations:
        if not all(eq.get(key) for key in ("id", "latex", "provenance", "falsifier", "symbols")):
            errors.append(f"equation {eq.get('id','?')} lacks provenance, symbols, or falsifier")
        unknown = set(eq.get("symbols", [])) - registry
        if unknown:
            errors.append(f"equation {eq.get('id','?')} has unregistered symbols: {sorted(unknown)}")
        if rf"\label{{eq:{eq.get('id')}}}" not in tex:
            errors.append(f"equation {eq.get('id','?')} missing from report")
    if not equations or not equations[-1].get("prediction_table_generated"):
        errors.append("prediction table is not linked to its implemented equation")

    predictions = table(theory / "predictions.csv")
    if not predictions:
        errors.append("predictions.csv is empty")
    for row in predictions:
        if not row.get("dependent_variable") or not row.get("independent_variable"):
            errors.append("prediction lacks dependent or independent variable")
        if not re.search(r"\bEq\.\s*\d+", row.get("prediction_basis", "")):
            errors.append("prediction row is not generated from a numbered equation")
        if "calculated" not in row.get("provenance", "").lower():
            errors.append("prediction row is not labelled calculated")

    conclusion = (theory / "conclusion-deductions.md").read_text(encoding="utf-8").lower()
    concepts = {
        "direct experimental test": r"\b(?:measure|track|record|scan|map|calibrate|combine|synchronise|synchronize)\b",
        "uncertainty or omitted mechanism": r"\b(?:uncertaint|omission|omitted|limitation|unmodelled)\w*",
        "rejection or replacement condition": r"\b(?:reject|replace)\w*",
    }
    for label, pattern in concepts.items():
        if not re.search(pattern, conclusion):
            errors.append(f"conclusion lacks {label}")
    if not re.search(r"(eq\.|equation|numbered equations)", conclusion):
        errors.append("conclusion claims are not linked to equations")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("path", type=Path, help="one agent-facing case or consolidated root")
    args = parser.parse_args()
    target = args.path.resolve()
    cases = [target] if (target / "theory").is_dir() else sorted(target.glob("[0-9][0-9]-*/agent-facing"))
    if not cases:
        print("FAIL: no theory cases found")
        return 1
    failed = 0
    for case in cases:
        errors = validate(case)
        if errors:
            failed += 1
            print(f"FAIL: {case}")
            for error in errors:
                print(f"- {error}")
        else:
            print(f"PASS: {case}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
