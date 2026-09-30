#!/usr/bin/env python3
"""Validate a finalized IYPT theoretical-research case using stdlib only."""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path


REQUIRED_FILES = (
    "prompt.md",
    "problem_contract.yaml",
    "essence_and_chain.md",
    "search_log.csv",
    "sources.yaml",
    "paper_matrix.csv",
    "model_registry.yaml",
    "candidate_decision_log.md",
    "final_report.md",
    "handoff.md",
)
REQUIRED_THEORY_FILES = (
    "theory/theory-model.md", "theory/equations.md", "theory/variables.csv", "theory/assumptions.md",
    "theory/predictions.csv", "theory/parameter-provenance.csv", "theory/literature-notes.md", "theory/model-validation.md",
)
ALLOWED_STATUSES = {"selected_primary", "selected_alternative", "retained_component", "filtered", "unresolved"}
ALLOWED_OUTCOMES = {
    "single_sufficient_working_model",
    "coupled_model_stack",
    "competing_whole_chain_models",
    "insufficient_evidence_to_select",
}
ALLOWED_ESSENCE = {"well_supported", "provisional", "competing_hypotheses", "unresolved"}
PLACEHOLDER_RE = re.compile(r"\bTODO\b|\[citation needed\]|10\.xxxx|example\.com|<paper-id>|\[problem\]", re.I)


@dataclass
class Candidate:
    candidate_id: str = ""
    fields: dict[str, str] = field(default_factory=dict)
    equations: list[dict[str, str]] = field(default_factory=list)

    def get(self, key: str) -> str:
        return self.fields.get(key, "").strip().strip('"\'')


def scalar(value: str) -> str:
    value = value.strip()
    if value.startswith("#"):
        return ""
    return value.split(" #", 1)[0].strip().strip('"\'')


def parse_registry(text: str) -> tuple[str, list[Candidate]]:
    outcome = ""
    candidates: list[Candidate] = []
    current: Candidate | None = None
    current_equation: dict[str, str] | None = None
    in_equations = False

    for raw in text.splitlines():
        stripped = raw.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if raw.startswith("selection_outcome:"):
            outcome = scalar(raw.split(":", 1)[1])
            continue
        match_candidate = re.match(r"^\s{2}-\s+candidate_id:\s*(.+)$", raw)
        if match_candidate:
            current = Candidate(candidate_id=scalar(match_candidate.group(1)))
            candidates.append(current)
            current_equation = None
            in_equations = False
            continue
        if current is None:
            continue
        if re.match(r"^\s{4}equations:\s*\[\s*\]\s*$", raw):
            current.fields["equations"] = "[]"
            in_equations = False
            continue
        if re.match(r"^\s{4}equations:\s*$", raw):
            in_equations = True
            continue
        equation_start = re.match(r"^\s{6}-\s+(equation|expression):\s*(.*)$", raw)
        if in_equations and equation_start:
            current_equation = {equation_start.group(1): scalar(equation_start.group(2))}
            current.equations.append(current_equation)
            continue
        equation_field = re.match(r"^\s{8}([a-zA-Z0-9_]+):\s*(.*)$", raw)
        if in_equations and current_equation is not None and equation_field:
            current_equation[equation_field.group(1)] = scalar(equation_field.group(2))
            continue
        field_match = re.match(r"^\s{4}([a-zA-Z0-9_]+):\s*(.*)$", raw)
        if field_match:
            in_equations = False
            current_equation = None
            current.fields[field_match.group(1)] = scalar(field_match.group(2))
    return outcome, candidates


def parse_source_blocks(text: str) -> list[dict[str, str]]:
    blocks: list[dict[str, str]] = []
    current: dict[str, str] | None = None
    for raw in text.splitlines():
        start = re.match(r"^\s{2}-\s+paper_id:\s*(.*)$", raw)
        if start:
            current = {"paper_id": scalar(start.group(1))}
            blocks.append(current)
            continue
        field_match = re.match(r"^\s{4}([a-zA-Z0-9_]+):\s*(.*)$", raw)
        if current is not None and field_match:
            current[field_match.group(1)] = scalar(field_match.group(2))
    return blocks


def extract_contract_prompt(contract: str) -> str:
    lines = contract.splitlines()
    for index, line in enumerate(lines):
        match = re.match(r"^exact_prompt:\s*(.*)$", line)
        if not match:
            continue
        marker = match.group(1).strip()
        if marker and marker not in {"|", "|-", "|+", ">", ">-", ">+"}:
            return scalar(marker)
        block: list[str] = []
        for following in lines[index + 1 :]:
            if following.startswith("  "):
                block.append(following[2:])
            elif not following.strip():
                block.append("")
            else:
                break
        return "\n".join(block).strip()
    return ""


def has_matching_exact_prompt(contract: str, prompt: str) -> bool:
    clean_prompt = re.sub(r"^# Official prompt\s*", "", prompt, flags=re.I).strip()
    contract_prompt = extract_contract_prompt(contract).strip()
    return bool(
        clean_prompt
        and contract_prompt
        and not PLACEHOLDER_RE.search(clean_prompt)
        and clean_prompt == contract_prompt
    )


def validate(case_dir: Path) -> list[str]:
    errors: list[str] = []
    for relative in (*REQUIRED_FILES, *REQUIRED_THEORY_FILES):
        if not (case_dir / relative).is_file():
            errors.append(f"missing required file: {relative}")
    if not (case_dir / "papers").is_dir():
        errors.append("missing required directory: papers")
    if errors:
        return errors

    contents = {name: (case_dir / name).read_text(encoding="utf-8") for name in REQUIRED_FILES}
    if not has_matching_exact_prompt(contents["problem_contract.yaml"], contents["prompt.md"]):
        errors.append("exact prompt is missing or differs between prompt.md and problem_contract.yaml")

    essence = contents["essence_and_chain.md"]
    status_match = re.search(r"\*\*Status:\*\*\s*`?([a-z_]+)", essence, re.I)
    if not status_match or status_match.group(1).lower() not in ALLOWED_ESSENCE:
        errors.append("essence status is missing or invalid")
    statement_match = re.search(r"\*\*Statement:\*\*\s*(.+)", essence, re.I)
    if not statement_match or not statement_match.group(1).strip() or PLACEHOLDER_RE.search(statement_match.group(1)):
        errors.append("essence statement is missing")
    if "→" not in essence and "->" not in essence and not re.search(r"^\|\s*L\d+\s*\|", essence, re.M):
        errors.append("at least one causal chain is required")

    outcome, candidates = parse_registry(contents["model_registry.yaml"])
    if outcome not in ALLOWED_OUTCOMES:
        errors.append(f"selection_outcome is missing or invalid: {outcome or '<empty>'}")
    if not candidates:
        errors.append("model registry contains no candidates")
    seen_ids: set[str] = set()
    for candidate in candidates:
        cid = candidate.candidate_id or "<missing-id>"
        if not candidate.candidate_id:
            errors.append("candidate is missing candidate_id")
        elif candidate.candidate_id in seen_ids:
            errors.append(f"duplicate candidate_id: {candidate.candidate_id}")
        seen_ids.add(candidate.candidate_id)
        status = candidate.get("status")
        if status not in ALLOWED_STATUSES:
            errors.append(f"candidate {cid} has missing or invalid status")
        if not candidate.get("name"):
            errors.append(f"candidate {cid} has no name")
        reason = candidate.get("selection_or_filter_reason")
        if status == "filtered" and not reason:
            errors.append(f"filtered candidate {cid} has no selection_or_filter_reason")
        if status.startswith("selected_"):
            unavailable = candidate.get("equations_unavailable_reason")
            if not candidate.equations and not unavailable:
                errors.append(f"selected candidate {cid} has neither equations nor an equations_unavailable_reason")
        for index, equation in enumerate(candidate.equations, 1):
            if not equation.get("provenance_class") or not equation.get("source_or_derivation"):
                errors.append(f"candidate {cid} equation {index} lacks provenance_class or source_or_derivation")

    has_whole_chain = any(c.get("candidate_type") == "whole_chain" for c in candidates)
    if not has_whole_chain and outcome != "insufficient_evidence_to_select":
        errors.append("case needs a whole_chain candidate or insufficient_evidence_to_select outcome")

    report = contents["final_report.md"]
    if not re.search(r"^##+\s+(?:12\.\s*)?Filtered/rejected candidate ledger", report, re.I | re.M):
        errors.append("final report lacks the filtered/rejected candidate ledger section")
    lowered_report = report.lower()
    for candidate in candidates:
        cid = candidate.candidate_id.lower()
        name = candidate.get("name").lower()
        if cid and cid not in lowered_report and name and name not in lowered_report:
            errors.append(f"candidate {candidate.candidate_id} disappears between registry and final report")

    for source in parse_source_blocks(contents["sources.yaml"]):
        sid = source.get("paper_id", "<missing-id>")
        stable_id = source.get("doi_or_stable_id", "")
        if not stable_id:
            errors.append(f"source {sid} must contain a stable identifier or explicit not_available")
        if source.get("identity_verified", "").lower() != "true":
            errors.append(f"source {sid} bibliographic identity is not verified")

    for name, text in contents.items():
        match = PLACEHOLDER_RE.search(text)
        if match:
            errors.append(f"placeholder remains in {name}: {match.group(0)}")
    for paper in sorted((case_dir / "papers").glob("*.md")):
        text = paper.read_text(encoding="utf-8")
        match = PLACEHOLDER_RE.search(text)
        if match:
            errors.append(f"placeholder remains in papers/{paper.name}: {match.group(0)}")
    for relative in REQUIRED_THEORY_FILES:
        text = (case_dir / relative).read_text(encoding="utf-8")
        match = PLACEHOLDER_RE.search(text)
        if match:
            errors.append(f"placeholder remains in {relative}: {match.group(0)}")
    if "=" not in (case_dir / "theory" / "equations.md").read_text(encoding="utf-8"):
        errors.append("theory/equations.md lacks a quantitative relationship")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("case_dir", type=Path)
    args = parser.parse_args()
    try:
        errors = validate(args.case_dir.resolve())
    except (OSError, UnicodeError) as exc:
        print(f"ERROR: could not read case: {exc}", file=sys.stderr)
        return 1
    if errors:
        print(f"FAIL: {len(errors)} validation error(s)")
        for error in errors:
            print(f"- {error}")
        return 1
    print(f"PASS: {args.case_dir.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
