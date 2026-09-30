#!/usr/bin/env python3
"""Create a deterministic, human-readable IYPT theoretical-research case."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


def templates(slug: str, prompt: str) -> dict[str, str]:
    exact_prompt = prompt.strip() or "TODO: paste the official prompt verbatim"
    indented_prompt = "\n".join(f"  {line}" for line in exact_prompt.splitlines())
    return {
        "prompt.md": f"# Official prompt\n\n{exact_prompt}\n",
        "problem_contract.yaml": f'''case_slug: "{slug}"
source: "TODO"
year: null
problem_number: null
access_date: "TODO"
exact_prompt: |-
{indented_prompt}
verbs: []
system_boundary: "TODO"
controlled_inputs: []
expected_observables: []
prompt_defined_objectives: []
constraints: []
apparatus_ambiguities: []
excluded_assumptions: []
classification_scores:
  explanation: 0
  design: 0
  optimization: 0
  mechanism_identification: 0
''',
        "essence_and_chain.md": """# Phenomenon essence (本质)

- **Status:** provisional
- **Statement:** TODO
- **Mechanistic necessity test:** TODO

## Main causal chain

TODO: controlled input → coupling → state evolution → selection/amplification → observable generation → measured observable

## Link table

| Link ID | Input [unit] | Model | Output [unit] | Assumptions | Prediction | Evidence | Confidence | Role |
|---|---|---|---|---|---|---|---|---|
| L1 | TODO | TODO | TODO | TODO | TODO | TODO | low | essential |

## Apparatus branches and unresolved links

TODO
""",
        "search_log.csv": "search_id,date,database_or_site,layer,query,filters,result_count,retained_ids,decision_or_refinement,status\n",
        "sources.yaml": "sources: []\n",
        "paper_matrix.csv": "paper_id,title,source_tier,directness,access_level,causal_links,model_families,validation,limitations,relevance\n",
        "model_registry.yaml": """selection_outcome: insufficient_evidence_to_select
candidates:
  - candidate_id: C1
    name: "TODO"
    status: unresolved
    candidate_type: whole_chain
    provenance: constructed_first_principles
    chain_links: []
    equations: []
    equations_unavailable_reason: "evidence not yet retrieved"
    selection_or_filter_reason: "TODO"
""",
        "candidate_decision_log.md": """# Candidate decision log

## Hard-gate results

TODO

## Advisory scores

TODO

## Filtered/rejected candidate ledger

TODO
""",
        "final_report.md": """# Theoretical research report

## 1. Executive summary
TODO

## 2. Official prompt and problem contract
TODO

## 3. Phenomenon essence (本质)
TODO

## 4. Causal-chain diagram and link table
TODO

## 5. Apparatus branches and ambiguities
TODO

## 6. Search strategy and source coverage
TODO

## 7. Literature synthesis by causal link and model family
TODO

## 8. Whole-chain candidate models
TODO

## 9. Component-model mapping
TODO

## 10. Mathematical audit
TODO

## 11. Selected working model(s)
TODO

## 12. Filtered/rejected candidate ledger
TODO

## 13. Competing predictions and discrimination opportunities
TODO

## 14. Research gaps and uncertainty
TODO

## 15. Simulation-method handoff
TODO

## 16. Experimental-observable handoff
TODO

## 17. References
TODO

## 18. Appendices: search log, paper matrix, model registry
TODO
""",
        "handoff.md": """# Later-stage handoff

## Simulation-method handoff
TODO: methods, equations, parameters, geometry, boundary conditions, outputs, and validation targets; do not run simulations here.

## Experimental-observable handoff
TODO: discriminating observables and parameter dependencies; do not design a full campaign here.
""",
        "theory/theory-model.md": "# Theoretical model\n\nTODO\n",
        "theory/equations.md": "# Equations\n\nTODO\n",
        "theory/variables.csv": "symbol,meaning,unit,status,source\n",
        "theory/assumptions.md": "# Assumptions and regime\n\nTODO\n",
        "theory/predictions.csv": "dependent_variable,independent_variable,value,unit,prediction_basis,parameter_values,provenance\n",
        "theory/parameter-provenance.csv": "parameter,value,unit,status,source_or_method\n",
        "theory/literature-notes.md": "# Literature notes\n\nTODO\n",
        "theory/model-validation.md": "# Model validation\n\nTODO\n",
    }


def scaffold(case_dir: Path, prompt: str, force: bool = False) -> tuple[list[Path], list[Path]]:
    case_dir.mkdir(parents=True, exist_ok=True)
    (case_dir / "papers").mkdir(exist_ok=True)
    (case_dir / "theory" / "figures").mkdir(parents=True, exist_ok=True)
    created: list[Path] = []
    skipped: list[Path] = []
    for relative, content in templates(case_dir.name, prompt).items():
        destination = case_dir / relative
        substantive = destination.exists() and destination.stat().st_size > 0
        if substantive and not force:
            skipped.append(destination)
            continue
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(content, encoding="utf-8")
        created.append(destination)
    return created, skipped


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("slug", help="lowercase hyphenated case slug")
    parser.add_argument("--prompt-file", type=Path, help="UTF-8 file containing the exact prompt")
    parser.add_argument("--root", type=Path, default=Path("research_cases"), help="case parent directory")
    parser.add_argument("--force", action="store_true", help="explicitly overwrite existing substantive case files")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    if not SLUG_RE.fullmatch(args.slug):
        print("error: slug must contain lowercase letters/digits separated by single hyphens", file=sys.stderr)
        return 2
    try:
        prompt = args.prompt_file.read_text(encoding="utf-8") if args.prompt_file else ""
        case_dir = args.root.resolve() / args.slug
        created, skipped = scaffold(case_dir, prompt, args.force)
    except (OSError, UnicodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    for path in created:
        print(f"created: {path}")
    for path in skipped:
        print(f"skipped existing substantive file (use --force to overwrite): {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
