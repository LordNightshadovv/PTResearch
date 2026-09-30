#!/usr/bin/env python3
"""Generate a portable, synthetic-runnable PT simulation package.

The generated package is deliberately solver-adapter shaped: it contains the
native-input surface for the selected route and a dependency-free deterministic
synthetic benchmark.  The benchmark is software evidence, not experimental
evidence and not a claim that the external solver has run.
"""

from __future__ import annotations

import argparse
import json
import os
import stat
import textwrap
from pathlib import Path
from typing import Any


ROUTES: dict[str, dict[str, Any]] = {
    "fourier_optics": {
        "primary_solver": "HCIPy",
        "solver_version": "0.7.0",
        "observable": "airy_radius",
        "units": "m",
        "equation_id": "EQ-FOURIER-AIRY",
        "equation": "r_airy = 1.22 lambda z / D",
        "source_locator": "README.md#equation-eq-fourier-airy",
        "destination_kind": "HCIPy wavelength/grid/propagator inputs",
        "destination": "src/model.py:compute -> wavelength_m, propagation_distance_m, aperture_diameter_m",
        "mapping_parameter": "wavelength_m",
        "native_file": "native/hcipy_config.py",
        "requirements": ["hcipy==0.7.0"],
        "synthetic": {
            "controls": {"wavelength_m": 5.5e-7, "propagation_distance_m": 0.1},
            "material_properties": {},
            "geometry": {"aperture_diameter_m": 0.01},
            "initial_conditions": {},
            "boundary_conditions": {},
            "calibration_parameters": {},
            "derived_quantities": {},
            "state_variables": {},
            "observables": {},
            "uncertainties": {},
            "metadata": {"synthetic": True, "source": "deterministic idealized Airy-limit benchmark"},
        },
    },
    "elmer_fem": {
        "primary_solver": "Elmer FEM",
        "solver_version": "9.0",
        "observable": "tip_displacement",
        "units": "m",
        "equation_id": "EQ-ELMER-BEAM",
        "equation": "delta = F L^3 / (3 E I), I = b t^3 / 12",
        "source_locator": "README.md#equation-eq-elmer-beam",
        "destination_kind": "Elmer SIF body/material/boundary-condition fields",
        "destination": "native/case.sif:Boundary Condition 1 Potential; src/model.py:compute",
        "mapping_parameter": "force_n",
        "native_file": "native/case.sif",
        "requirements": [],
        "synthetic": {
            "controls": {"force_n": 0.01},
            "material_properties": {"youngs_modulus_pa": 2.0e9},
            "geometry": {"length_m": 0.1, "width_m": 0.01, "thickness_m": 0.001},
            "initial_conditions": {},
            "boundary_conditions": {"root": "clamped"},
            "calibration_parameters": {},
            "derived_quantities": {},
            "state_variables": {},
            "observables": {},
            "uncertainties": {},
            "metadata": {"synthetic": True, "source": "deterministic idealized cantilever-limit benchmark"},
        },
    },
    "openfoam_continuum": {
        "primary_solver": "OpenFOAM",
        "solver_version": "14",
        "observable": "vortex_depth",
        "units": "m",
        "equation_id": "EQ-OPENFOAM-VORTEX",
        "equation": "h_vortex = min(H, omega^2 R^2 / (2 g))",
        "source_locator": "README.md#equation-eq-openfoam-vortex",
        "destination_kind": "OpenFOAM dictionary path/field/function object",
        "destination": "native/system/controlDict:application; native/0/U:internalField; src/model.py:compute",
        "mapping_parameter": "rotation_rate_rad_s",
        "native_file": "native/system/controlDict",
        "requirements": [],
        "synthetic": {
            "controls": {"rotation_rate_rad_s": 8.0},
            "material_properties": {"gravity_m_s2": 9.81},
            "geometry": {"radius_m": 0.02, "height_m": 0.08},
            "initial_conditions": {"phase_fraction": 0.5},
            "boundary_conditions": {"free_surface": "atmospheric"},
            "calibration_parameters": {},
            "derived_quantities": {},
            "state_variables": {},
            "observables": {},
            "uncertainties": {},
            "metadata": {"synthetic": True, "source": "deterministic idealized rotating-column benchmark"},
        },
    },
    "project_chrono": {
        "primary_solver": "Project Chrono",
        "solver_version": "10.0.0",
        "observable": "impact_time",
        "units": "s",
        "equation_id": "EQ-CHRONO-FREEFALL",
        "equation": "t_impact = sqrt(2 h / g)",
        "source_locator": "README.md#equation-eq-chrono-freefall",
        "destination_kind": "Project Chrono body/force/integrator/output channel",
        "destination": "native/chrono_case.py:ChBodyEasyBox; src/model.py:compute -> height_m, gravity_m_s2",
        "mapping_parameter": "height_m",
        "native_file": "native/chrono_case.py",
        "requirements": ["pychrono==10.0.0"],
        "synthetic": {
            "controls": {},
            "material_properties": {},
            "geometry": {"height_m": 0.5},
            "initial_conditions": {"vertical_velocity_m_s": 0.0},
            "boundary_conditions": {"contact": "disabled for known-motion benchmark"},
            "calibration_parameters": {},
            "derived_quantities": {},
            "state_variables": {},
            "observables": {},
            "uncertainties": {},
            "metadata": {"synthetic": True, "source": "deterministic no-contact known-motion benchmark"},
        },
    },
    "yade": {
        "primary_solver": "YADE",
        "solver_version": "2024.02a",
        "observable": "contact_force",
        "units": "N",
        "equation_id": "EQ-YADE-HERTZ-LINEAR",
        "equation": "F_n = k delta",
        "source_locator": "README.md#equation-eq-yade-hertz-linear",
        "destination_kind": "YADE body/contact material/force output",
        "destination": "native/two_sphere.py:FrictMat; src/model.py:compute -> overlap_m, stiffness_n_m",
        "mapping_parameter": "overlap_m",
        "native_file": "native/two_sphere.py",
        "requirements": ["yade==2024.02a"],
        "synthetic": {
            "controls": {},
            "material_properties": {"stiffness_n_m": 1000.0},
            "geometry": {"overlap_m": 0.0001},
            "initial_conditions": {},
            "boundary_conditions": {"contact_model": "linear normal contact"},
            "calibration_parameters": {},
            "derived_quantities": {},
            "state_variables": {},
            "observables": {},
            "uncertainties": {},
            "metadata": {"synthetic": True, "source": "deterministic two-particle contact benchmark"},
        },
    },
    "python_ode": {
        "primary_solver": "Python/SciPy",
        "solver_version": "NumPy 1.26.4 SciPy 1.13.1",
        "observable": "decayed_position",
        "units": "m",
        "equation_id": "EQ-PYTHON-ODE-DECAY",
        "equation": "x(T) = x_0 exp(-c T / m)",
        "source_locator": "README.md#equation-eq-python-ode-decay",
        "destination_kind": "ODE state/coefficient/integration option",
        "destination": "src/model.py:compute -> initial_position_m, damping_kg_s, mass_kg, duration_s",
        "mapping_parameter": "initial_position_m",
        "native_file": "src/model.py",
        "requirements": ["numpy==1.26.4", "scipy==1.13.1"],
        "synthetic": {
            "controls": {"duration_s": 1.0},
            "material_properties": {"damping_kg_s": 0.5, "mass_kg": 1.0},
            "geometry": {},
            "initial_conditions": {"initial_position_m": 1.0},
            "boundary_conditions": {},
            "calibration_parameters": {},
            "derived_quantities": {},
            "state_variables": {},
            "observables": {},
            "uncertainties": {},
            "metadata": {"synthetic": True, "source": "deterministic exponential-decay ODE benchmark"},
        },
    },
    "python_optimization": {
        "primary_solver": "Python/SciPy",
        "solver_version": "NumPy 1.26.4 SciPy 1.13.1",
        "observable": "optimal_control",
        "units": "1",
        "equation_id": "EQ-PYTHON-OPTIMUM",
        "equation": "u_star = clip(target / gain, u_min, u_max)",
        "source_locator": "README.md#equation-eq-python-optimum",
        "destination_kind": "optimization objective/bounds/decision variable",
        "destination": "src/model.py:compute -> target, gain, lower_bound, upper_bound",
        "mapping_parameter": "target",
        "native_file": "src/model.py",
        "requirements": ["numpy==1.26.4", "scipy==1.13.1"],
        "synthetic": {
            "controls": {"target": 3.0},
            "material_properties": {"gain": 2.0},
            "geometry": {},
            "initial_conditions": {},
            "boundary_conditions": {"lower_bound": 0.0, "upper_bound": 2.0},
            "calibration_parameters": {},
            "derived_quantities": {},
            "state_variables": {},
            "observables": {},
            "uncertainties": {},
            "metadata": {"synthetic": True, "source": "deterministic bounded optimization benchmark"},
        },
    },
    "reduced_order_model": {
        "primary_solver": "Python/SciPy",
        "solver_version": "NumPy 1.26.4 SciPy 1.13.1",
        "observable": "harmonic_response",
        "units": "m",
        "equation_id": "EQ-REDUCED-HARMONIC",
        "equation": "y = A sin(2 pi f t)",
        "source_locator": "README.md#equation-eq-reduced-harmonic",
        "destination_kind": "reduced-order state/forcing/output channel",
        "destination": "src/model.py:compute -> amplitude_m, frequency_hz, time_s",
        "mapping_parameter": "amplitude_m",
        "native_file": "src/model.py",
        "requirements": ["numpy==1.26.4", "scipy==1.13.1"],
        "synthetic": {
            "controls": {"amplitude_m": 0.01, "frequency_hz": 2.0, "time_s": 0.125},
            "material_properties": {},
            "geometry": {},
            "initial_conditions": {},
            "boundary_conditions": {},
            "calibration_parameters": {},
            "derived_quantities": {},
            "state_variables": {},
            "observables": {},
            "uncertainties": {},
            "metadata": {"synthetic": True, "source": "deterministic harmonic reduced-order benchmark"},
        },
    },
}


def _write(path: Path, text: str, executable: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    if executable:
        path.chmod(path.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)


def _write_json(path: Path, value: Any) -> None:
    _write(path, json.dumps(value, indent=2, ensure_ascii=False) + "\n")


def _model_source(route: str, config: dict[str, Any]) -> str:
    return textwrap.dedent(
        f"""
        \"\"\"Deterministic synthetic implementation for the {route} route.\"\"\"
        from __future__ import annotations

        import math
        from typing import Any

        ROUTE = {route!r}
        OBSERVABLE = {config['observable']!r}
        UNITS = {config['units']!r}
        EQUATION_ID = {config['equation_id']!r}


        def number(data: dict[str, Any], category: str, name: str, default: float = 0.0) -> float:
            value = data.get(category, {{}}).get(name, default)
            if isinstance(value, dict):
                value = value.get("value", default)
            return float(value)


        def compute(data: dict[str, Any]) -> dict[str, Any]:
            if ROUTE == "fourier_optics":
                wavelength = number(data, "controls", "wavelength_m")
                distance = number(data, "controls", "propagation_distance_m")
                diameter = number(data, "geometry", "aperture_diameter_m")
                value = 1.22 * wavelength * distance / diameter
            elif ROUTE == "elmer_fem":
                force = number(data, "controls", "force_n")
                young = number(data, "material_properties", "youngs_modulus_pa")
                length = number(data, "geometry", "length_m")
                width = number(data, "geometry", "width_m")
                thickness = number(data, "geometry", "thickness_m")
                inertia = width * thickness ** 3 / 12.0
                value = force * length ** 3 / (3.0 * young * inertia)
            elif ROUTE == "openfoam_continuum":
                omega = number(data, "controls", "rotation_rate_rad_s")
                radius = number(data, "geometry", "radius_m")
                height = number(data, "geometry", "height_m")
                gravity = number(data, "material_properties", "gravity_m_s2", 9.81)
                value = min(height, omega ** 2 * radius ** 2 / (2.0 * gravity))
            elif ROUTE == "project_chrono":
                height = number(data, "geometry", "height_m")
                gravity = 9.81
                value = math.sqrt(2.0 * height / gravity)
            elif ROUTE == "yade":
                overlap = number(data, "geometry", "overlap_m")
                stiffness = number(data, "material_properties", "stiffness_n_m")
                value = stiffness * overlap
            elif ROUTE == "python_ode":
                position = number(data, "initial_conditions", "initial_position_m")
                damping = number(data, "material_properties", "damping_kg_s")
                mass = number(data, "material_properties", "mass_kg")
                duration = number(data, "controls", "duration_s")
                value = position * math.exp(-damping * duration / mass)
            elif ROUTE == "python_optimization":
                target = number(data, "controls", "target")
                gain = number(data, "material_properties", "gain", 1.0)
                lower = number(data, "boundary_conditions", "lower_bound")
                upper = number(data, "boundary_conditions", "upper_bound")
                value = min(upper, max(lower, target / gain))
            elif ROUTE == "reduced_order_model":
                amplitude = number(data, "controls", "amplitude_m")
                frequency = number(data, "controls", "frequency_hz")
                time = number(data, "controls", "time_s")
                value = amplitude * math.sin(2.0 * math.pi * frequency * time)
            else:
                raise ValueError(f"unsupported synthetic route: {{ROUTE}}")
            if not math.isfinite(value):
                raise ValueError("synthetic model produced a non-finite observable")
            return {{
                "observable": OBSERVABLE,
                "value": value,
                "unit": UNITS,
                "equation_id": EQUATION_ID,
                "route": ROUTE,
                "synthetic": bool(data.get("metadata", {{}}).get("synthetic", False)),
            }}
        """
    ).lstrip()


def _generate_case_source(route: str, config: dict[str, Any]) -> str:
    return textwrap.dedent(
        f"""
        #!/usr/bin/env python3
        \"\"\"Map separated inputs into a deterministic/native case directory.\"\"\"
        from __future__ import annotations

        import argparse
        import hashlib
        import json
        from pathlib import Path
        from typing import Any

        ROUTE = {route!r}
        NATIVE_FILE = {config['native_file']!r}


        def load_input(path: Path) -> dict[str, Any]:
            value = json.loads(path.read_text(encoding="utf-8"))
            if not isinstance(value, dict):
                raise ValueError("input must be an object")
            required = {{"controls", "material_properties", "geometry", "initial_conditions", "boundary_conditions", "calibration_parameters", "derived_quantities", "state_variables", "observables", "uncertainties"}}
            missing = required - set(value)
            if missing:
                raise ValueError(f"missing input categories: {{sorted(missing)}}")
            metadata = value.get("metadata", {{}})
            if not isinstance(metadata, dict):
                raise ValueError("input metadata must be an object")
            if metadata.get("synthetic") is not True and not (metadata.get("measured") is True and metadata.get("provenance")):
                raise ValueError("input must be clearly labelled synthetic or measured with provenance")
            return value


        def generate_case(input_path: Path, output_dir: Path) -> Path:
            data = load_input(input_path)
            native = output_dir / NATIVE_FILE
            native.parent.mkdir(parents=True, exist_ok=True)
            native.write_text("route: " + ROUTE + "\\nparameter_source: " + str(input_path.name) + "\\n", encoding="utf-8")
            digest = hashlib.sha256(input_path.read_bytes()).hexdigest()
            input_metadata = data.get("metadata", {{}})
            metadata = {{"route": ROUTE, "input_file_hash": digest, "synthetic": bool(input_metadata.get("synthetic", False)), "measured": bool(input_metadata.get("measured", False)), "provenance": input_metadata.get("provenance"), "derived_quantities": {{"input_hash_prefix": digest[:12]}}}}
            (output_dir / "case-metadata.json").write_text(json.dumps(metadata, indent=2) + "\\n", encoding="utf-8")
            return output_dir


        if __name__ == "__main__":
            parser = argparse.ArgumentParser()
            parser.add_argument("--input", type=Path, required=True)
            parser.add_argument("--output", type=Path, default=Path("generated-case"))
            args = parser.parse_args()
            generate_case(args.input, args.output)
            print(args.output)
        """
    ).lstrip()


def _extractor_source() -> str:
    return textwrap.dedent(
        """
        #!/usr/bin/env python3
        from __future__ import annotations

        import argparse
        import json
        import math
        from pathlib import Path
        from typing import Any


        def extract_results(raw_path: Path, output_path: Path) -> dict[str, Any]:
            value = json.loads(raw_path.read_text(encoding="utf-8"))
            observable = value.get("observable")
            result = value.get("value")
            if not isinstance(observable, str) or not isinstance(result, (int, float)) or not math.isfinite(float(result)):
                raise ValueError("raw output lacks a finite machine-readable observable")
            output = {"observable": observable, "value": float(result), "unit": value.get("unit", "1"), "equation_id": value.get("equation_id"), "synthetic": bool(value.get("synthetic")), "validation_state": "runnable_synthetic"}
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(json.dumps(output, indent=2) + "\\n", encoding="utf-8")
            return output


        if __name__ == "__main__":
            parser = argparse.ArgumentParser()
            parser.add_argument("--raw", type=Path, default=Path("outputs/raw.json"))
            parser.add_argument("--output", type=Path, default=Path("outputs/results.json"))
            args = parser.parse_args()
            print(json.dumps(extract_results(args.raw, args.output), indent=2))
        """
    ).lstrip()


def _model_runner_source() -> str:
    return textwrap.dedent(
        """
        #!/usr/bin/env python3
        from __future__ import annotations

        import argparse
        import json
        import sys
        from pathlib import Path

        sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
        from src.model import compute


        if __name__ == "__main__":
            parser = argparse.ArgumentParser()
            parser.add_argument("--input", type=Path, required=True)
            parser.add_argument("--output", type=Path, default=Path("outputs/raw.json"))
            args = parser.parse_args()
            result = compute(json.loads(args.input.read_text(encoding="utf-8")))
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(json.dumps(result, indent=2) + "\\n", encoding="utf-8")
            print(json.dumps(result, indent=2))
        """
    ).lstrip()


def _route_test_source(route: str) -> str:
    checks = {
        "fourier_optics": "zero = json.loads(json.dumps(data)); zero['controls']['wavelength_m'] = 0.0; assert compute(zero)['value'] == 0.0",
        "elmer_fem": "scaled = json.loads(json.dumps(data)); scaled['controls']['force_n'] *= 2.0; assert abs(compute(scaled)['value'] - 2.0 * baseline['value']) < 1e-15",
        "openfoam_continuum": "zero = json.loads(json.dumps(data)); zero['controls']['rotation_rate_rad_s'] = 0.0; assert compute(zero)['value'] == 0.0",
        "project_chrono": "zero = json.loads(json.dumps(data)); zero['geometry']['height_m'] = 0.0; assert compute(zero)['value'] == 0.0",
        "yade": "zero = json.loads(json.dumps(data)); zero['geometry']['overlap_m'] = 0.0; assert compute(zero)['value'] == 0.0",
        "python_ode": "zero = json.loads(json.dumps(data)); zero['controls']['duration_s'] = 0.0; assert abs(compute(zero)['value'] - data['initial_conditions']['initial_position_m']) < 1e-15",
        "python_optimization": "bounded = json.loads(json.dumps(data)); bounded['controls']['target'] = 100.0; assert compute(bounded)['value'] == data['boundary_conditions']['upper_bound']",
        "reduced_order_model": "zero = json.loads(json.dumps(data)); zero['controls']['time_s'] = 0.0; assert abs(compute(zero)['value']) < 1e-15",
    }
    return textwrap.dedent(
        f"""
        import json
        import math
        import sys
        from pathlib import Path

        sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
        from src.model import compute

        data = json.loads((Path(__file__).resolve().parents[1] / "examples" / "synthetic.json").read_text(encoding="utf-8"))
        baseline = compute(data)
        assert math.isfinite(baseline["value"])
        {checks[route]}
        """
    ).lstrip()


def _pipeline_source() -> str:
    return textwrap.dedent(
        """
        #!/usr/bin/env python3
        from __future__ import annotations

        import argparse
        import json
        import sys
        from pathlib import Path

        ROOT = Path(__file__).resolve().parents[1]
        sys.path.insert(0, str(ROOT))
        sys.path.insert(0, str(ROOT / "src"))
        from generate_case import generate_case
        from src.model import compute
        from extract_results import extract_results


        if __name__ == "__main__":
            parser = argparse.ArgumentParser()
            parser.add_argument("--input", type=Path, required=True)
            parser.add_argument("--generated-case", type=Path, default=Path("generated-case"))
            parser.add_argument("--output-dir", type=Path, default=Path("outputs"))
            args = parser.parse_args()
            data = json.loads(args.input.read_text(encoding="utf-8"))
            generate_case(args.input, args.generated_case)
            args.output_dir.mkdir(parents=True, exist_ok=True)
            raw = args.output_dir / "raw.json"
            raw.write_text(json.dumps(compute(data), indent=2) + "\\n", encoding="utf-8")
            extract_results(raw, args.output_dir / "results.json")
            print(args.output_dir / "results.json")
        """
    ).lstrip()


def _check_system_source(config: dict[str, Any]) -> str:
    return textwrap.dedent(
        f"""
        #!/usr/bin/env python3
        from __future__ import annotations

        import argparse
        import importlib.util
        import json
        import os
        import platform
        import shutil
        from pathlib import Path

        SOLVER = {config['primary_solver']!r}

        def main() -> int:
            parser = argparse.ArgumentParser()
            parser.add_argument("--mode", choices=("synthetic", "apparatus", "production"), default="synthetic")
            args = parser.parse_args()
            root = Path(__file__).resolve().parents[1]
            output = root / "outputs"
            output.mkdir(parents=True, exist_ok=True)
            probe = {{"mode": args.mode, "operating_system": platform.system(), "architecture": platform.machine(), "python": platform.python_version(), "solver": SOLVER, "optional_accelerator": bool(os.environ.get("CUDA_VISIBLE_DEVICES"))}}
            if args.mode == "production":
                if SOLVER == "HCIPy" and importlib.util.find_spec("hcipy") is None:
                    raise SystemExit("missing dependency: import hcipy failed")
                if SOLVER == "Python/SciPy" and (importlib.util.find_spec("numpy") is None or importlib.util.find_spec("scipy") is None):
                    raise SystemExit("missing dependency: import numpy and scipy failed")
                if SOLVER == "Project Chrono" and importlib.util.find_spec("pychrono") is None:
                    raise SystemExit("missing dependency: import pychrono failed")
                if SOLVER in {{"OpenFOAM", "Elmer FEM", "YADE"}}:
                    executable = {{"OpenFOAM": "blockMesh", "Elmer FEM": "ElmerSolver", "YADE": "yade"}}[SOLVER]
                    if shutil.which(executable) is None:
                        raise SystemExit(f"missing executable: {{executable}}")
            print(json.dumps(probe, indent=2))
            return 0

        if __name__ == "__main__":
            raise SystemExit(main())
        """
    ).lstrip()


def _gate_source() -> str:
    return textwrap.dedent(
        """
        #!/usr/bin/env python3
        from __future__ import annotations

        import argparse
        import json
        from pathlib import Path

        CATEGORIES = {"controls", "material_properties", "geometry", "initial_conditions", "boundary_conditions", "calibration_parameters", "derived_quantities", "state_variables", "observables", "uncertainties"}

        def main() -> int:
            parser = argparse.ArgumentParser()
            parser.add_argument("--manifest", type=Path, required=True)
            parser.add_argument("--mode", choices=("synthetic", "apparatus", "production"), default="synthetic")
            parser.add_argument("--input", type=Path, default=Path("examples/synthetic.json"))
            parser.add_argument("--require-state")
            args = parser.parse_args()
            manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
            state = manifest.get("software_readiness")
            if state == "handoff_only":
                raise SystemExit("BLOCKED: missing implementation; this package is handoff-only")
            root = args.manifest.resolve().parent
            if not (root / "src").is_dir() or not any((root / "src").rglob("*.py")):
                raise SystemExit("BLOCKED: missing implementation source")
            if args.mode == "production" and not (root / "generated-case" / "case-metadata.json").is_file():
                raise SystemExit("BLOCKED: missing case generation evidence")
            if args.require_state and state != args.require_state:
                raise SystemExit(f"BLOCKED: required state {args.require_state}, current state {state}")
            if args.require_state == "runnable_synthetic" and not (root / "receipts" / "synthetic-smoke.json").is_file():
                raise SystemExit("BLOCKED: missing synthetic smoke receipt")
            data = json.loads(args.input.read_text(encoding="utf-8"))
            missing = CATEGORIES - set(data)
            if missing:
                raise SystemExit(f"BLOCKED: invalid input, missing categories {sorted(missing)}")
            if args.mode == "synthetic":
                if data.get("metadata", {}).get("synthetic") is not True:
                    raise SystemExit("BLOCKED: synthetic mode requires metadata.synthetic=true")
                print("ALLOW: synthetic benchmark; no apparatus evidence is claimed")
            elif args.mode == "apparatus":
                if data.get("metadata", {}).get("synthetic") is True:
                    raise SystemExit("BLOCKED: apparatus mode received synthetic values")
                metadata = data.get("metadata", {})
                if not isinstance(metadata, dict) or metadata.get("measured") is not True or not metadata.get("provenance"):
                    raise SystemExit("BLOCKED: apparatus execution requires metadata.measured=true and metadata.provenance")
                if not data.get("uncertainties"):
                    raise SystemExit("BLOCKED: apparatus execution requires measured inputs and uncertainty records")
                if not (root / "receipts" / "synthetic-smoke.json").is_file():
                    raise SystemExit("BLOCKED: apparatus execution requires a passed synthetic smoke receipt first")
                print("ALLOW: apparatus input structurally present; experimental validity remains untested")
            else:
                if state not in {"runnable_apparatus", "executed_unverified", "numerically_verified", "experimentally_compared"}:
                    raise SystemExit("BLOCKED: production execution requires runnable_apparatus or a later evidenced state")
                print("ALLOW: production execution gate passed for the recorded evidence state")
            return 0

        if __name__ == "__main__":
            raise SystemExit(main())
        """
    ).lstrip()


def _receipt_runner_source() -> str:
    return textwrap.dedent(
        """
        #!/usr/bin/env python3
        from __future__ import annotations

        import argparse
        import hashlib
        import json
        import platform
        import subprocess
        import sys
        import time
        from datetime import datetime, timezone
        from pathlib import Path

        def digest(path: Path) -> str:
            h = hashlib.sha256()
            if path.is_file():
                h.update(path.read_bytes())
            elif path.is_dir():
                for child in sorted(item for item in path.rglob("*") if item.is_file()):
                    h.update(child.relative_to(path).as_posix().encode())
                    h.update(child.read_bytes())
            return h.hexdigest()

        def main() -> int:
            parser = argparse.ArgumentParser()
            parser.add_argument("--receipt", type=Path, required=True)
            parser.add_argument("--input", type=Path)
            parser.add_argument("--generated-case", type=Path)
            parser.add_argument("--output-dir", type=Path)
            parser.add_argument("--validation-state", required=True)
            parser.add_argument("--package-version", default="1")
            parser.add_argument("command", nargs=argparse.REMAINDER)
            args = parser.parse_args()
            command = list(args.command)
            if command and command[0] == "--":
                command = command[1:]
            if not command:
                raise SystemExit("exact command required after --")
            start = time.monotonic()
            result = subprocess.run(command, text=True, capture_output=True)
            runtime = time.monotonic() - start
            output_hashes = {}
            if args.output_dir and args.output_dir.exists():
                for child in sorted(item for item in args.output_dir.rglob("*") if item.is_file()):
                    output_hashes[child.relative_to(args.output_dir).as_posix()] = digest(child)
            manifest_path = Path(__file__).resolve().parents[1] / "simulation_package_manifest.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.is_file() else {}
            receipt = {
                "timestamp": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
                "operating_system": platform.system(),
                "architecture": platform.machine(),
                "package_version": args.package_version,
                "solver_version": manifest.get("solver_version", "not_applicable"),
                "package_revision": manifest.get("package_revision", "not_recorded"),
                "exact_command": command,
                "input_file_hash": digest(args.input) if args.input else "not_applicable",
                "generated_case_hash": digest(args.generated_case) if args.generated_case else "not_applicable",
                "exit_status": result.returncode,
                "runtime_seconds": runtime,
                "output_hashes": output_hashes,
                "warnings": [line for line in result.stderr.splitlines() if "warning" in line.lower()],
                "errors": result.stderr.splitlines() if result.returncode else [],
                "validation_state": args.validation_state,
            }
            args.receipt.parent.mkdir(parents=True, exist_ok=True)
            args.receipt.write_text(json.dumps(receipt, indent=2) + "\\n", encoding="utf-8")
            sys.stdout.write(result.stdout)
            sys.stderr.write(result.stderr)
            return result.returncode

        if __name__ == "__main__":
            raise SystemExit(main())
        """
    ).lstrip()


def _update_state_source() -> str:
    return textwrap.dedent(
        """
        #!/usr/bin/env python3
        from __future__ import annotations
        import argparse
        import json
        from pathlib import Path

        parser = argparse.ArgumentParser()
        parser.add_argument("--state", choices=("runnable_synthetic", "runnable_apparatus"), required=True)
        parser.add_argument("--receipt", type=Path, required=True)
        args = parser.parse_args()
        manifest_path = Path(__file__).resolve().parents[1] / "simulation_package_manifest.json"
        receipt = args.receipt
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        evidence = json.loads(receipt.read_text(encoding="utf-8"))
        if evidence.get("exit_status") != 0 or evidence.get("validation_state") != args.state:
            raise SystemExit("cannot mark package runnable: the requested receipt is not passed")
        if args.state == "runnable_apparatus" and not (manifest_path.parent / "receipts" / "synthetic-smoke.json").is_file():
            raise SystemExit("cannot mark package runnable_apparatus before synthetic smoke evidence exists")
        manifest["software_readiness"] = args.state
        manifest["claim_ceiling"] = (
            "runnable_synthetic_only; no apparatus or scientific validation claimed"
            if args.state == "runnable_synthetic"
            else "runnable_apparatus_input_only; no numerical verification or experimental comparison claimed"
        )
        manifest["runnable_claim"] = True
        manifest_path.write_text(json.dumps(manifest, indent=2) + "\\n", encoding="utf-8")
        print(args.state)
        """
    ).lstrip()


def _shell_scripts() -> dict[str, str]:
    return {
        "check_system.sh": "#!/usr/bin/env bash\nset -euo pipefail\nroot=\"$(cd \"$(dirname \"$0\")\" && pwd)\"\ncd \"$root\"\npython3 scripts/check_system.py \"$@\"\n",
        "run_gate.sh": "#!/usr/bin/env bash\nset -euo pipefail\nroot=\"$(cd \"$(dirname \"$0\")\" && pwd)\"\ncd \"$root\"\nmode=synthetic\nif [[ \"${1:-}\" == \"--apparatus\" ]]; then mode=apparatus; fi\npython3 scripts/run_gate.py --manifest simulation_package_manifest.json --mode \"$mode\" --input \"${2:-examples/synthetic.json}\"\n",
        "run.sh": "#!/usr/bin/env bash\nset -euo pipefail\nroot=\"$(cd \"$(dirname \"$0\")\" && pwd)\"\ncd \"$root\"\nmode=synthetic\ninput=examples/synthetic.json\nreceipt=receipts/synthetic-smoke.json\nvalidation_state=runnable_synthetic\nif [[ \"${1:-}\" == \"--apparatus\" ]]; then mode=apparatus; input=\"${2:?provide a measured input file}\"; receipt=receipts/apparatus-run.json; validation_state=runnable_apparatus; fi\nbash check_system.sh --mode \"$mode\"\nif [[ \"$mode\" == \"apparatus\" ]]; then bash run_gate.sh --apparatus \"$input\"; else bash run_gate.sh \"\" \"$input\"; fi\npython3 scripts/execute_with_receipt.py --receipt \"$receipt\" --input \"$input\" --generated-case generated-case --output-dir outputs --validation-state \"$validation_state\" --package-version 1 -- python3 scripts/run_pipeline.py --input \"$input\" --generated-case generated-case --output-dir outputs\npython3 scripts/update_readiness.py --state \"$validation_state\" --receipt \"$receipt\"\npython3 extract_results.py --raw outputs/raw.json --output outputs/results.json\n",
        "install.sh": "#!/usr/bin/env bash\nset -euo pipefail\npython3 -m venv .venv\n. .venv/bin/activate\npython -m pip install -r requirements.txt\n",
    }


def _native_assets(route: str, config: dict[str, Any]) -> dict[str, str]:
    if route == "openfoam_continuum":
        return {
            "native/0/U": "dimensions [0 1 -1 0 0 0 0];\ninternalField uniform (0 0 0);\nboundaryField { walls { type wall; value uniform (0 0 0); } inlet { type fixedValue; value uniform (0 0 0); } outlet { type zeroGradient; } }\n",
            "native/0/p": "dimensions [1 -1 -2 0 0 0 0];\ninternalField uniform 0;\nboundaryField { walls { type zeroGradient; } inlet { type zeroGradient; } outlet { type fixedValue; value uniform 0; } }\n",
            "native/constant/transportProperties": "transportModel Newtonian;\nnu [0 2 -1 0 0 0 0] 1e-06;\n",
            "native/constant/g": "dimensions [0 1 -2 0 0 0 0];\nvalue (0 0 -9.81);\n",
            "native/system/controlDict": "application interFoam;\nstartFrom startTime;\nstartTime 0;\nendAt endTime;\nendTime 0.1;\ndeltaT 0.001;\nwriteControl timeStep;\nwriteInterval 100;\nfunctions { fieldAverage1 { type fieldAverage; libs (\"libfieldFunctionObjects.so\"); fields (U p); } }\n",
            "native/system/fvSchemes": "ddtSchemes { default Euler; }\ngradSchemes { default Gauss linear; }\ndivSchemes { default none; div(phi,U) Gauss upwind; }\nlaplacianSchemes { default Gauss linear corrected; }\ninterpolationSchemes { default linear; }\nsnGradSchemes { default corrected; }\n",
            "native/system/fvSolution": "solvers { p { solver GAMG; tolerance 1e-07; relTol 0; } U { solver smoothSolver; tolerance 1e-08; relTol 0; smoother symGaussSeidel; } }\nPIMPLE { nOuterCorrectors 1; nCorrectors 2; }\n",
            "native/system/blockMeshDict": "convertToMeters 1;\nvertices ((0 0 0) (1 0 0) (1 1 0) (0 1 0) (0 0 0.1) (1 0 0.1) (1 1 0.1) (0 1 0.1));\nblocks ((hex (0 1 2 3 4 5 6 7) (10 10 1) simpleGrading (1 1 1)));\nedges ();\nboundary { walls { type wall; faces ((0 1 5 4) (1 2 6 5) (2 3 7 6) (3 0 4 7)); } inlet { type patch; faces ((0 4 7 3)); } outlet { type patch; faces ((1 2 6 5)); } }\nmergePatchPairs ();\n",
            "native/system/setFieldsDict": "defaultFieldValues (volScalarFieldValue alpha.water 1);\nregions ();\n",
            "native/Allrun": "#!/usr/bin/env bash\nset -euo pipefail\ncase_dir=\"$(cd \"$(dirname \"$0\")\" && pwd)/..\"\ncommand -v blockMesh\ncommand -v checkMesh\ncommand -v interFoam\nblockMesh -case \"$case_dir\"\ncheckMesh -case \"$case_dir\"\ninterFoam -case \"$case_dir\"\n",
            "native/Allclean": "#!/usr/bin/env bash\nset -euo pipefail\nrm -rf processor* log.*\n",
        }
    if route == "elmer_fem":
        return {
            "native/case.sif": "Header\n  CHECK KEYWORDS Warn\nEnd\n\nSimulation\n  Max Output Level = 3\n  Simulation Type = Steady state\n  Coordinate System = Cartesian 2D\n  Mesh DB = \"mesh\" \"beam\"\nEnd\n\nConstants\n  Gravity(4) = 0 0 -9.81 0\nEnd\n\nBody 1\n  Name = \"beam\"\n  Equation = 1\n  Material = 1\nEnd\n\nMaterial 1\n  Name = \"synthetic elastic beam\"\n  Youngs Modulus = 2.0e9\n  Poisson Ratio = 0.3\n  Density = 1000\nEnd\n\nEquation 1\n  Name = \"linear elasticity\"\n  Active Solvers(1) = 1\nEnd\n\nSolver 1\n  Equation = Linear Elasticity\n  Procedure = \"StressSolve\" \"StressSolver\"\n  Variable = Displacement\n  Calculate Stresses = True\n  Steady State Convergence Tolerance = 1.0e-8\nEnd\n\nBoundary Condition 1\n  Name = \"clamped root\"\n  Target Boundaries(1) = 1\n  Displacement 1 = 0\n  Displacement 2 = 0\nEnd\n\n! Synthetic beam mapping: see src/model.py and equation-lineage.json\n",
            "native/beam.geo": "Point(1) = {0, 0, 0, 0.01};\nPoint(2) = {0.1, 0, 0, 0.01};\nPoint(3) = {0.1, 0.01, 0, 0.01};\nPoint(4) = {0, 0.01, 0, 0.01};\nLine(1) = {1, 2};\nLine(2) = {2, 3};\nLine(3) = {3, 4};\nLine(4) = {4, 1};\nLine Loop(1) = {1, 2, 3, 4};\nPlane Surface(1) = {1};\n",
            "native/mesh_generator.py": "from pathlib import Path\n\n\ndef write_mesh_instructions(output=Path('mesh')):\n    output.mkdir(parents=True, exist_ok=True)\n    (output / 'README.txt').write_text('Run Gmsh on native/beam.geo, then ElmerGrid, before ElmerSolver.\\n', encoding='utf-8')\n\n\nif __name__ == '__main__':\n    write_mesh_instructions()\n",
        }
    if route == "project_chrono":
        return {"native/chrono_case.py": "import pychrono as chrono\n\n\ndef build_system():\n    system = chrono.ChSystemNSC()\n    body = chrono.ChBodyEasyBox(0.1, 0.1, 0.1, 1000)\n    body.SetPos(chrono.ChVector3d(0, 0.5, 0))\n    body.SetBodyFixed(False)\n    system.AddBody(body)\n    # Contact material, gravity, integrator, and output channel remain explicit route inputs.\n    system.SetGravitationalAcceleration(chrono.ChVector3d(0, -9.81, 0))\n    return system, body\n\n\ndef run_known_motion(output_path='chrono-output.csv'):\n    system, body = build_system()\n    with open(output_path, 'w', encoding='utf-8') as stream:\n        stream.write('time_s,position_y_m\\n')\n        for index in range(11):\n            time_s = index * 0.01\n            stream.write(f'{time_s},{body.GetPos().y}\\n')\n            system.DoStepDynamics(0.01)\n\n\nif __name__ == '__main__':\n    run_known_motion()\n"}
    if route == "yade":
        return {"native/two_sphere.py": "from yade import O, FrictMat, ForceResetter, NewtonIntegrator, utils, sphere\n\n\ndef build_contact_scene():\n    material = FrictMat(young=1.0e5, poisson=0.25, frictionAngle=0.1)\n    O.materials.append(material)\n    O.bodies.append([sphere((0, 0, 0), 0.01, material=material), sphere((0, 0, 0.0199), 0.01, material=material)])\n    O.engines = [ForceResetter(), NewtonIntegrator(gravity=(0, 0, -9.81), damping=0.2)]\n    O.dt = utils.PWaveTimeStep() * 0.2\n    return O\n\n\nif __name__ == '__main__':\n    build_contact_scene()\n    O.run(100, wait=True)\n"}
    if route == "fourier_optics":
        return {"native/hcipy_config.py": "from hcipy import FraunhoferPropagator, Wavefront, make_circular_aperture, make_pupil_grid\n\nwavelength_m = 5.5e-7\ngrid = make_pupil_grid(128, 1.0)\naperture = make_circular_aperture(1.0)(grid)\npropagator = FraunhoferPropagator(grid, focal_length=1.0)\nwavefront = Wavefront(aperture, wavelength=wavelength_m)\n\n# The package implementation records scalar limits; this native surface is the configurable array path.\n"}
    return {}


def generate_package(route: str, output: Path, model_id: str | None = None) -> Path:
    if route not in ROUTES:
        raise ValueError(f"unsupported route {route!r}; choose one of: {', '.join(sorted(ROUTES))}")
    if output.exists():
        raise ValueError(f"refusing to overwrite package: {output}")
    config = ROUTES[route]
    output.mkdir(parents=True)
    (output / "src").mkdir()
    (output / "scripts").mkdir()
    (output / "examples").mkdir()
    (output / "tests").mkdir()
    (output / "receipts").mkdir()
    (output / "outputs").mkdir()
    (output / "generated-case").mkdir()
    _write(output / "src" / "__init__.py", "")
    _write(output / "src" / "model.py", _model_source(route, config))
    _write(output / "generate_case.py", _generate_case_source(route, config), True)
    _write(output / "extract_results.py", _extractor_source(), True)
    _write(output / "scripts" / "run_model.py", _model_runner_source(), True)
    _write(output / "scripts" / "run_pipeline.py", _pipeline_source(), True)
    _write(output / "scripts" / "check_system.py", _check_system_source(config), True)
    _write(output / "scripts" / "run_gate.py", _gate_source(), True)
    _write(output / "scripts" / "execute_with_receipt.py", _receipt_runner_source(), True)
    _write(output / "scripts" / "update_readiness.py", _update_state_source(), True)
    for name, contents in _shell_scripts().items():
        _write(output / name, contents, True)
    for relative, contents in _native_assets(route, config).items():
        _write(output / relative, contents, relative.endswith((".sh", ".py")))
    synthetic = json.loads(json.dumps(config["synthetic"]))
    synthetic["metadata"]["route"] = route
    synthetic["metadata"]["case_id"] = model_id or f"synthetic-{route}"
    _write_json(output / "examples" / "synthetic.json", synthetic)
    _write_json(output / "parameters.schema.json", {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "title": f"Separated inputs for {route}",
        "type": "object",
        "required": ["controls", "material_properties", "geometry", "initial_conditions", "boundary_conditions", "calibration_parameters", "derived_quantities", "state_variables", "observables", "uncertainties"],
        "properties": {name: {"type": "object"} for name in ("controls", "material_properties", "geometry", "initial_conditions", "boundary_conditions", "calibration_parameters", "derived_quantities", "state_variables", "observables", "uncertainties")},
        "additionalProperties": False,
    })
    mapping = {
        "parameter": config["mapping_parameter"],
        "destination_kind": config["destination_kind"],
        "destination": config["destination"],
        "equation_id": config["equation_id"],
        "implemented_file": "src/model.py",
        "implemented_symbol": "compute",
        "units": config["units"],
        "notation_conversion": "input category names are converted to named Python variables in number()",
        "discretization_or_approximation": "deterministic idealized benchmark; no experimental calibration is inferred",
        "implementation_assumptions": ["synthetic input is physically plausible but not experimental evidence"],
    }
    _write_json(output / "parameter-map.json", {"mappings": [mapping]})
    _write_json(output / "equation-lineage.json", {"equations": [{
        "equation_id": config["equation_id"],
        "source_locator": config["source_locator"],
        "original_equation": config["equation"],
        "assumptions": ["deterministic idealized synthetic benchmark", "route-specific production calibration remains separate"],
        "adaptation": "map separated package inputs to the synthetic implementation variables",
        "final_equation": config["equation"],
        "implemented_file": "src/model.py",
        "implemented_symbol": "compute",
        "notation_conversion": mapping["notation_conversion"],
        "units": config["units"],
        "discretization_or_approximation": mapping["discretization_or_approximation"],
        "implementation_assumptions": mapping["implementation_assumptions"],
    }]})
    _write_json(output / "numerical-verification.json", {
        "refinement_variable": "synthetic step or sampling scale",
        "levels": [1.0, 0.5, 0.25],
        "observable": config["observable"],
        "metric": "absolute difference from the closed-form synthetic limit",
        "tolerance": 1e-9,
        "expected_limiting_behavior": f"{config['equation_id']} approaches the displayed synthetic equation as the numerical scale is refined",
        "failure_interpretation": "implementation, unit conversion, or numerical approximation is inconsistent; do not infer experimental model failure",
        "executed": False,
        "status": "unexecuted",
        "receipt": None,
    })
    _write(output / "numerical-verification.md", f"# Numerical verification\n\nThe machine-readable plan is in `numerical-verification.json`. Three concrete levels are `{1.0}`, `{0.5}`, and `{0.25}`. It is unexecuted until a receipt records the command and outputs. A synthetic pass tests implementation and limiting behavior only; it is not experimental validation.\n")
    _write(output / "tests" / "test_synthetic.py", "from pathlib import Path\nimport json\nimport sys\nsys.path.insert(0, str(Path(__file__).resolve().parents[1]))\nfrom src.model import compute\ndata = json.loads((Path(__file__).resolve().parents[1] / 'examples' / 'synthetic.json').read_text())\nresult = compute(data)\nassert result['synthetic'] is True\nassert result['value'] == result['value']\n")
    _write(output / "tests" / "test_route_contract.py", _route_test_source(route))
    requirements = ["# Install only after reviewing the target and granting explicit authority."] + [f"{item}" for item in config["requirements"]]
    _write(output / "requirements.txt", "\n".join(requirements) + "\n")
    _write(output / "environment.yml", "name: pt-simulation-package\ndependencies:\n  - python>=3.9\n" + "".join(f"  - {item}\n" for item in config["requirements"]))
    _write(output / "receipts" / ".gitkeep", "")
    manifest = {
        "package_version": 1,
        "simulation_contract_version": 1,
        "route": route,
        "model_id": model_id or f"synthetic-{route}",
        "primary_solver": config["primary_solver"],
        "solver_version": config["solver_version"],
        "package_revision": "not_recorded",
        "scientific_readiness": "model_closed",
        "software_readiness": "implementation_ready",
        "implementation": {"source_files": ["src/model.py"], "solver_native_files": [config["native_file"]] if config["native_file"].startswith("native/") else [], "case_generator": "generate_case.py", "result_extractor": "extract_results.py"},
        "entrypoints": {"check_system": "check_system.sh", "run_gate": "run_gate.sh", "generate_case": "generate_case.py", "run": "run.sh", "extract_results": "extract_results.py"},
        "input_schema": "parameters.schema.json",
        "synthetic_example": "examples/synthetic.json",
        "numerical_verification": "numerical-verification.json",
        "parameter_mapping": [mapping],
        "claim_ceiling": "implementation_ready_only; no execution or scientific validation claimed",
        "runnable_claim": False,
        "receipts": "receipts/",
    }
    _write_json(output / "simulation_package_manifest.json", manifest)
    _write(output / "README.md", f"""# PT simulation package: `{route}`

This package contains a real route adapter, a deterministic synthetic benchmark, a case generator, machine-readable output extraction, and state-aware gates. The synthetic values are physically plausible test inputs only; they are not measurements and do not establish a scientific model or experimental validity.

## Current claim ceiling

`implementation_ready`: the implementation layer exists. It is not called runnable until `receipts/synthetic-smoke.json` is produced by the package command and the manifest is advanced to `runnable_synthetic`.

## Synthetic smoke test

```bash
bash check_system.sh --mode synthetic
bash run_gate.sh
bash run.sh
cat outputs/results.json
cat receipts/synthetic-smoke.json
```

The package records the operating system, architecture, exact command, input hash, generated-case hash, exit status, runtime, output hashes, warnings, errors, and validation state. A successful synthetic receipt proves only that the package executes its idealized benchmark. It does not prove solver installation, numerical convergence, apparatus fidelity, or experimental agreement.

## Production boundary

Use `bash check_system.sh --mode production` only after the locked external runtime has been inspected and explicitly installed on the target. Use `bash run.sh --apparatus <measured-input.json>` only with validated measured inputs and uncertainty records. The state-aware gate blocks apparatus/production claims when those records are absent.

## Equation `{config['equation_id']}`

`{config['equation']}`

The implementation trace is in `equation-lineage.json`; parameter destinations are in `parameter-map.json`. The native route surface is present under `native/` when the selected solver uses one.
""")
    return output


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--route", required=True, choices=sorted(ROUTES))
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--model-id", default=None)
    args = parser.parse_args()
    try:
        path = generate_package(args.route, args.output.resolve(), args.model_id)
    except ValueError as exc:
        parser.error(str(exc))
    print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
