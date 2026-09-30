#!/usr/bin/env python3
"""Read-only OpenFOAM runtime probe; it never installs or runs a solver."""

from __future__ import annotations

import argparse
import json
import os
import platform
import shutil
from pathlib import Path


SOLVERS = ("simpleFoam", "pimpleFoam", "icoFoam", "interFoam", "rhoPimpleFoam")
MESH_TOOLS = ("blockMesh", "snappyHexMesh", "checkMesh", "topoSet")
POST_TOOLS = ("postProcess", "foamToVTK", "paraFoam")
BUILD_TOOLS = ("wmake",)


def _locations(names: tuple[str, ...], search_path: str) -> dict[str, str | None]:
    return {name: shutil.which(name, path=search_path) for name in names}


def probe(path: str | None = None, environ: dict[str, str] | None = None) -> dict:
    env = environ or dict(os.environ)
    search_path = path if path is not None else env.get("PATH", "")
    project = env.get("WM_PROJECT_DIR")
    distribution = "unknown"
    if project:
        lower = project.lower()
        distribution = "openfoam-foundation" if "openfoam-" in lower else "openfoam-openCFD" if "openfoam" in lower else "unknown"
    all_tools = {**_locations(SOLVERS, search_path), **_locations(MESH_TOOLS, search_path), **_locations(POST_TOOLS, search_path), **_locations(BUILD_TOOLS, search_path)}
    tutorial = env.get("FOAM_TUTORIALS") or (str(Path(project) / "tutorials") if project and (Path(project) / "tutorials").is_dir() else None)
    libraries = [entry for entry in env.get("FOAM_USER_LIBBIN", "").split(os.pathsep) if entry]
    available = bool(project and any(all_tools[name] for name in SOLVERS))
    limitations = [] if available else ["OpenFOAM environment is not loaded or no solver is available; no case execution is claimed."]
    return {"mode": "operational" if available else "reduced_capability", "distribution": distribution, "version": env.get("WM_PROJECT_VERSION"), "wm_project_dir": project, "operating_system": platform.system(), "executable_locations": all_tools, "solvers": {key: all_tools[key] for key in SOLVERS}, "mesh_tools": {key: all_tools[key] for key in MESH_TOOLS}, "post_processing_tools": {key: all_tools[key] for key in POST_TOOLS}, "required_libraries": libraries, "tutorial_location": tutorial, "dependencies": [{"name": "OpenFOAM", "available": available, "detail": project or "not detected"}], "limitations": limitations}


def runtime_manifest(report: dict) -> dict:
    solver = next((name for name, location in report["solvers"].items() if location), "not_selected")
    return {"runtime": {"operating_system": report["operating_system"], "openfoam_distribution": report["distribution"], "openfoam_version": report["version"] or "not_detected", "solver": solver, "required_packages": ["OpenFOAM"]}, "execution": {"entrypoint": solver}, "validation": {"required_checks": ["mesh_check", "solver_completion", "convergence_check", "timestep_check_when_applicable", "conservation_check", "physical_validation"]}, "openfoam_environment": {"distribution": report["distribution"], "version": report["version"], "installation_method": "not_detected", "executable_locations": report["executable_locations"], "tutorial_location": report["tutorial_location"]}}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, help="dependency report path")
    parser.add_argument("--runtime-output", type=Path, help="runtime manifest path")
    args = parser.parse_args()
    report = probe()
    text = json.dumps(report, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    if args.runtime_output:
        args.runtime_output.parent.mkdir(parents=True, exist_ok=True)
        args.runtime_output.write_text(json.dumps(runtime_manifest(report), indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
