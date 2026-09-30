#!/usr/bin/env python3
"""Run PT-specific structural, invocation, provenance, and schema gates."""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path


EXPECTED = {
    "pt-orchestrator", "pt-theoretical-research", "pt-simulation-router",
    "pt-openfoam-environment-manager", "pt-simulation-packager", "pt-remote-execution", "pt-report-renderer",
    "pt-self-improvement",
    "upstream-kdense-literature-review", "upstream-deerflow-systematic-literature-review",
    "upstream-deerflow-academic-paper-review", "upstream-cfd-foamagent",
    "upstream-cfd-mesh-gate", "upstream-cfd-experiment", "upstream-cfd-code-modify",
    "upstream-sim-plugin-openfoam",
}

REQUIRED_SCHEMAS = frozenset({
    "apparatus-fidelity.schema.json", "calibration-plan.schema.json", "case-manifest.schema.json", "dependency-report.schema.json",
    "equations.schema.json", "essence-chain.schema.json", "evidence-matrix.schema.json",
    "model-registry.schema.json", "paper-card.schema.json", "parameter-equation-map.schema.json",
    "problem-contract.schema.json", "project-state.schema.json", "run-receipt.schema.json",
    "runtime.schema.json", "search-log.schema.json", "simulation-handoff.schema.json",
    "simulation-package.schema.json", "simulation-parameters.schema.json", "simulation-route.schema.json",
    "simulation-spec.schema.json", "solver-requirements.schema.json", "source-registry.schema.json",
    "validation-report.schema.json",
})

SEMVER_RE = re.compile(
    r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)"
    r"(?:-((?:0|[1-9A-Za-z-][0-9A-Za-z-]*)(?:\.(?:0|[1-9A-Za-z-][0-9A-Za-z-]*))*))?"
    r"(?:\+((?:0|[1-9A-Za-z-][0-9A-Za-z-]*)(?:\.(?:0|[1-9A-Za-z-][0-9A-Za-z-]*))*))?$"
)


def is_valid_semver(value: object) -> bool:
    """Accept SemVer core with optional prerelease/build metadata."""

    return isinstance(value, str) and bool(SEMVER_RE.fullmatch(value))


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    errors: list[str] = []
    manifest_path = root / ".codex-plugin" / "plugin.json"
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        if manifest.get("name") != root.name:
            errors.append("manifest name must match plugin directory")
        if not is_valid_semver(manifest.get("version", "")):
            errors.append("manifest version is not valid semver")
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(f"invalid plugin manifest: {exc}")

    actual = {p.name for p in (root / "skills").iterdir() if p.is_dir()}
    if EXPECTED - actual:
        errors.append(f"missing skills: {sorted(EXPECTED - actual)}")
    for name in sorted(EXPECTED):
        skill = root / "skills" / name
        text = (skill / "SKILL.md").read_text(encoding="utf-8") if (skill / "SKILL.md").exists() else ""
        match = re.match(r"^---\n(.*?)\n---", text, re.S)
        if not match or not re.search(rf"^name:\s*{re.escape(name)}\s*$", match.group(1), re.M) or not re.search(r"^description:\s*\S", match.group(1), re.M):
            errors.append(f"invalid SKILL.md frontmatter: {name}")
        agent = skill / "agents" / "openai.yaml"
        agent_text = agent.read_text(encoding="utf-8") if agent.exists() else ""
        expected_value = "true" if name == "pt-orchestrator" else "false"
        if not re.search(rf"allow_implicit_invocation:\s*{expected_value}\b", agent_text):
            errors.append(f"wrong invocation policy: {name}")
        if name.startswith("upstream-"):
            for required in ("upstream-original", "SOURCE.yaml", "PATCHES.md", "LICENSE", "references/pt-bridge.md", "references/upstream-notes.md", "tests", "scripts"):
                if not (skill / required).exists():
                    errors.append(f"{name}: missing {required}")

    for schema in (root / "schemas").glob("*.json"):
        try:
            json.loads(schema.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            errors.append(f"invalid schema {schema.name}: {exc}")
    schema_names = {schema.name for schema in (root / "schemas").glob("*.schema.json")}
    missing_schemas = REQUIRED_SCHEMAS - schema_names
    if missing_schemas:
        errors.append(f"missing required shared schemas: {sorted(missing_schemas)}")

    for script in ("verify_upstream_integrity.py", "check_licenses.py"):
        result = subprocess.run([sys.executable, str(root / "scripts" / script), str(root)] if script.startswith("verify") else [sys.executable, str(root / "scripts" / script)], capture_output=True, text=True)
        if result.returncode:
            errors.append(result.stdout.strip() or result.stderr.strip())
    runtime = root / "tools" / "solver-runtime"
    locks = runtime / "solver-locks.json"
    try:
        entries = json.loads(locks.read_text(encoding="utf-8"))["solvers"]
        expected_solvers = {"OpenFOAM", "HCIPy", "Project Chrono", "Elmer FEM", "YADE", "Python/SciPy"}
        if set(entries) != expected_solvers:
            errors.append("solver runtime locks must cover every routable primary solver exactly once")
        for name, item in entries.items():
            dockerfile = runtime / "containerfiles" / f"{name.lower().replace(' ', '-').replace('/', '-')}.Dockerfile"
            if not item.get("version") or not item.get("probe_command") or not str(item.get("official_source", "")).startswith("https://") or not item.get("targets") or not item.get("smoke_test") or not dockerfile.exists():
                errors.append(f"incomplete solver runtime integration: {name}")
        validation_cases = json.loads((runtime / "validation-cases.json").read_text(encoding="utf-8"))
        if set(validation_cases) != expected_solvers:
            errors.append("solver runtime validation cases must cover every routable primary solver exactly once")
    except (OSError, KeyError, json.JSONDecodeError) as exc:
        errors.append(f"invalid solver runtime locks: {exc}")
    if errors:
        print("FAIL: PT plugin validation")
        for error in errors:
            print(f"- {error}")
        return 1
    print(f"PASS: PT plugin structure, policies, schemas, provenance, and licenses: {root}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
