#!/usr/bin/env python3
"""Scaffold an industrial-grade research-software project from the PT template.

Standard library only.  Copies ``skills/pt-research-software-engineering/templates/research-project``
into a new directory, substitutes placeholders, and writes ``engineering_standards.yaml``, a
manifest that honestly records what the scaffold provides (tests are ``implemented``, not
``evidenced``; the lockfile is ``pending_generation`` until ``uv lock`` is run).

The scaffold is a starting point.  It does not install dependencies, run tests, or claim that
any physics is correct.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
TEMPLATE_ROOT = PLUGIN_ROOT / "skills" / "pt-research-software-engineering" / "templates" / "research-project"
INTERFACES = ("cli", "library_only", "desktop_gui", "web_ui", "tui_python")
GUI_KINDS = {"desktop_gui", "web_ui", "tui_python"}
PACKAGE_TOKEN = "@@PACKAGE@@"
DEFAULT_DESCRIPTION = "Research software for a physics-tournament investigation."
GUI_ONLY_PARTS = ("gui",)
GUI_ONLY_FILES = {"test_gui_controller.py"}


class ScaffoldError(Exception):
    """Invalid arguments or an unsafe destination."""


def package_name(project_name: str) -> str:
    """Python import name derived from a project name."""
    package = re.sub(r"[^a-z0-9]+", "_", project_name.lower()).strip("_")
    if not package or package[0].isdigit():
        raise ScaffoldError("project name must contain letters and cannot start with a digit")
    return package


def validate_project_name(name: str) -> str:
    if not re.fullmatch(r"[a-z][a-z0-9]*(?:[-_][a-z0-9]+)*", name):
        raise ScaffoldError("project name must be lowercase letters, digits, '-' or '_' and start with a letter")
    return name


def _destination_name(relative: Path, package: str) -> Path:
    parts = []
    for part in relative.parts:
        part = part.replace(PACKAGE_TOKEN, package)
        if part.startswith("dot-"):
            part = "." + part[len("dot-"):]
        parts.append(part)
    result = Path(*parts)
    if result.name.endswith(".tmpl"):
        result = result.with_name(result.name[: -len(".tmpl")])
    return result


def _render(text: str, values: dict[str, str]) -> str:
    for key, value in values.items():
        text = text.replace(f"@@{key}@@", value)
    return text


def build_manifest(project_name: str, package: str, interface: str, description: str) -> dict[str, Any]:
    """Manifest describing the scaffold exactly as generated."""
    gui = interface in GUI_KINDS
    tests: list[dict[str, str]] = [
        {"id": "T-UNIT-CONFIG", "kind": "unit", "path": "tests/test_config.py", "evidence_status": "implemented"},
        {"id": "T-DIM", "kind": "dimensional", "path": "tests/test_units.py", "evidence_status": "implemented"},
        {"id": "T-ANALYTIC", "kind": "analytic_benchmark", "path": "tests/test_analytic_benchmark.py", "evidence_status": "implemented"},
        {"id": "T-CONVERGENCE", "kind": "convergence", "path": "tests/test_convergence.py", "evidence_status": "implemented"},
        {"id": "T-CONSERVATION", "kind": "conservation", "path": "tests/test_conservation.py", "evidence_status": "implemented"},
        {"id": "T-UNCERTAINTY", "kind": "uncertainty", "path": "tests/test_uncertainty.py", "evidence_status": "implemented"},
        {"id": "T-REPRO", "kind": "reproducibility", "path": "tests/test_provenance_and_cli.py", "evidence_status": "implemented"},
        {"id": "T-PROPERTY", "kind": "property", "path": "tests/test_properties.py", "evidence_status": "implemented"},
        {"id": "T-ARCH", "kind": "architecture", "path": "tests/test_architecture.py", "evidence_status": "implemented"},
    ]
    if gui:
        tests.append({"id": "T-GUI-HEADLESS", "kind": "gui_headless", "path": "tests/test_gui_controller.py", "evidence_status": "implemented"})
    interface_record: dict[str, Any] = {
        "primary": interface,
        "justification": (
            "Headless core with a command-line entry point keeps science testable and scriptable; "
            "interactive layers are thin callers of the same functions."
            if not gui
            else "A thin interface layer over the headless core improves interactive exploration; "
            "the toolkit is chosen in an ADR before the stub is replaced."
        ),
        "headless_core": True,
    }
    if gui:
        interface_record.update(
            {
                "thin_layer": True,
                "gui_layer_path": f"src/{package}/gui",
                "usability_rationale": "Interactive parameter exploration and result inspection benefit from a form-based interface; justify and refine in the ADR.",
                "accessibility": {
                    "keyboard_operable": True,
                    "non_color_encoding": True,
                    "text_alternatives": True,
                    "scalable_text_or_contrast": True,
                    "notes": "The toolkit-independent controller renders plain text; the chosen toolkit must preserve keyboard operation, non-color status cues, plot text alternatives, and scalable text.",
                },
            }
        )
    return {
        "engineering_contract_version": 1,
        "status": "declared",
        "validation_scope": "declaration_and_structure_only",
        "claim_ceiling": (
            "Declaration and file structure only: no test has been run or evidenced, no numerical "
            "accuracy or physical correctness is claimed, and the reference model is a demonstration."
        ),
        "project": {
            "name": project_name,
            "root": ".",
            "version": "0.1.0",
            "versioning": "semantic",
            "changelog": "CHANGELOG.md",
            "requires_python": ">=3.10",
            "design_notes": "docs/design-notes.md",
        },
        "stack_decision": {
            "adr_path": "docs/adr/0001-stack-decision.md",
            "language": {
                "name": "Python",
                "justification": "Mature scientific ecosystem (NumPy/SciPy) with fast iteration; heavy compute is delegated to compiled libraries.",
            },
            "paradigm": {
                "style": "mixed",
                "justification": "An abstract Model gives interchangeable models behind one experiment interface; functions and data classes elsewhere avoid needless hierarchy.",
            },
            "selected": [
                {"name": "NumPy/SciPy", "role": "arrays and ODE integration (solve_ivp), optimization", "rationale": "Tested, documented numerical routines instead of custom solvers."},
                {"name": "Pint", "role": "runtime units (optional extra)", "rationale": "Established units library with dimension-exponent tests as a dependency-free fallback."},
                {"name": "pytest + hypothesis", "role": "automated and property-based tests", "rationale": "Standard parametrized and property testing."},
                {"name": "ruff + mypy", "role": "lint, format, static typing", "rationale": "Fast strict gates that run identically in CI."},
                {"name": "uv", "role": "environment and lockfile", "rationale": "Pinned reproducible installs from a committed lockfile."},
            ],
            "alternatives_considered": [
                {"name": "Hand-written integrators for production", "rejected_because": "Re-implements tested SciPy solvers; kept only as a verification stand-in."},
                {"name": "Jupyter-only workflow", "rejected_because": "Weak testing, versioning, and reproducibility guarantees."},
                {"name": "Rust or C++ core", "rejected_because": "No measured performance bottleneck; revisit with profiling evidence."},
            ],
            "reinvention_exceptions": [
                {"capability": "fixed-step RK4 in tests/test_convergence.py", "why_not_library": "Needed as a transparent stand-in for a custom discretization to demonstrate an observed-order study."}
            ],
        },
        "interface": interface_record,
        "quality_tooling": {
            "linter": "ruff check",
            "formatter": "ruff format",
            "type_checker": "mypy --strict",
            "test_runner": "pytest",
            "ci_config_path": ".github/workflows/ci.yml",
            "commands": {"lint": "ruff check .", "format": "ruff format --check .", "typecheck": "mypy", "test": "pytest"},
        },
        "dependency_management": {
            "tool": "uv",
            "manifest_path": "pyproject.toml",
            "lockfile": "uv.lock",
            "lockfile_status": "pending_generation",
            "pinning_policy": "Run `uv lock` and commit uv.lock; CI installs with --frozen; bounded ranges in pyproject.toml.",
        },
        "configuration": {
            "config_path": "config/default.toml",
            "separated_from_code": True,
            "validation": f"{package}.config.parse_config validates types, finiteness, ranges, and enumerations at load time.",
        },
        "logging_and_error_handling": {
            "logging": "Library modules use logging.getLogger(__name__); only the entry point configures handlers.",
            "error_handling": "Expected failures raise ResearchError subclasses mapped to CLI exit codes; no bare except.",
        },
        "test_plan": {"tests": tests},
        "numerical_verification": {
            "required": True,
            "methods": ["step_size_convergence", "tolerance_study", "conservation_check", "analytic_benchmark"],
            "tolerances": {"analytic_abs_error_m": 1e-9, "energy_relative_drift": 1e-8, "observed_order_lower": 3.7},
            "convergence_criterion": "Observed RK4 order within [3.7, 4.5]; error non-increasing as rtol tightens and below 1e-9 m at rtol 1e-10.",
            "evidence_status": "implemented",
        },
        "physical_correctness": {
            "units_policy": "manual_dimension_vectors",
            "dimensional_analysis": "Dimension-exponent registry checked in tests/test_units.py; Pint cross-check when installed.",
            "limiting_cases": ["zero damping reduces to x0*cos(w0*t)"],
            "symmetry_checks": ["odd under (x0, v0) -> (-x0, -v0)", "linear amplitude scaling"],
            "analytic_benchmarks": ["underdamped closed-form solution"],
            "assumptions_registry": "README.md#assumptions-and-validity-range",
        },
        "uncertainty_treatment": {
            "methods": ["error_propagation", "monte_carlo", "fit_covariance", "residual_analysis", "sensitivity_analysis", "parameter_sweep"],
            "error_sources": {
                "measurement": "Provided as per-point sigma to fits and comparisons.",
                "calibration": "Fit covariance from curve_fit with absolute_sigma=True.",
                "numerical": "Tolerance and step-size studies; kept separate from measurement error.",
                "sampling": "Seeded Monte Carlo with reported sample count.",
                "model_form": "Residual structure and held-out comparison; not quantified in the scaffold.",
            },
        },
        "experiment_comparison": {
            "planned": False,
            "justification_if_not_planned": "The scaffold has no experimental data; comparison.py and plotting.py provide metrics and overlays to use when data exist.",
            "evidence_status": "planned",
        },
        "reproducibility": {
            "seed_policy": "A single integer seed in config/default.toml feeds numpy.random.default_rng; no global random state.",
            "deterministic_outputs": True,
            "run_metadata_writer": f"src/{package}/provenance.py",
            "run_metadata_fields": ["timestamp_utc", "git_commit", "git_dirty", "python_version", "dependency_versions", "config_hash", "seed", "platform", "input_hashes", "lockfile_sha256"],
            "environment_lock": "uv.lock (pending generation)",
        },
        "documentation": {
            "readme": "README.md",
            "assumptions_section": True,
            "verification_plan": "docs/verification-plan.md",
        },
    }


def scaffold(
    destination: Path,
    project_name: str,
    *,
    description: str = DEFAULT_DESCRIPTION,
    interface: str = "cli",
    now: datetime | None = None,
) -> list[Path]:
    """Create the project and return the files written.  Refuses a non-empty destination."""
    validate_project_name(project_name)
    if interface not in INTERFACES:
        raise ScaffoldError(f"interface must be one of {INTERFACES}")
    if any(c in description for c in "\r\n\0"):
        raise ScaffoldError("description must be a single line")
    if '"' in description or "\\" in description or "@@" in description:
        raise ScaffoldError("description must not contain quotes, backslashes, or '@@'")
    if not TEMPLATE_ROOT.is_dir():
        raise ScaffoldError(f"template is missing: {TEMPLATE_ROOT}")
    if destination.exists() and (not destination.is_dir() or any(destination.iterdir())):
        raise ScaffoldError(f"refusing to write into a non-empty path: {destination}")
    package = package_name(project_name)
    stamp = (now or datetime.now(timezone.utc)).strftime("%Y-%m-%d")
    values = {"PROJECT_NAME": project_name, "PACKAGE": package, "DESCRIPTION": description, "DATE": stamp}
    include_gui = interface in GUI_KINDS
    written: list[Path] = []
    for source in sorted(TEMPLATE_ROOT.rglob("*")):
        if not source.is_file():
            continue
        relative = source.relative_to(TEMPLATE_ROOT)
        renamed = _destination_name(relative, package)
        if not include_gui and (renamed.name in GUI_ONLY_FILES or any(part == "gui" for part in renamed.parts)):
            continue
        target = destination / renamed
        target.parent.mkdir(parents=True, exist_ok=True)
        text = source.read_text(encoding="utf-8")
        target.write_text(_render(text, values), encoding="utf-8")
        written.append(target)
    manifest_path = destination / "engineering_standards.yaml"
    manifest_path.write_text(
        json.dumps(build_manifest(project_name, package, interface, description), indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    written.append(manifest_path)
    return written


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("destination", type=Path, help="new project directory (must not exist or be empty)")
    parser.add_argument("--name", help="project name (default: destination directory name)")
    parser.add_argument("--description", default=DEFAULT_DESCRIPTION)
    parser.add_argument("--interface", choices=INTERFACES, default="cli", help="primary interface; GUI kinds add a thin gui/ stub")
    args = parser.parse_args(argv)
    destination = args.destination.resolve()
    try:
        written = scaffold(destination, args.name or destination.name, description=args.description, interface=args.interface)
    except ScaffoldError as exc:
        parser.error(str(exc))
    print(destination)
    print(f"wrote {len(written)} files; next: uv lock && uv sync --extra dev --frozen && uv run pytest", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
