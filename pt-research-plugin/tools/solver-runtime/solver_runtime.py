#!/usr/bin/env python3
"""Version-locked, official-source solver runtime operations.

This tool never installs by default.  It can inspect a current host, emit a
target installer, install only after ``--authorized``, and package only after
a tested receipt proves the declared target can run the selected solver.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import platform
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
LOCKS = json.loads((ROOT / "solver-locks.json").read_text(encoding="utf-8"))
TEMPLATES = json.loads((ROOT / "templates.json").read_text(encoding="utf-8"))


def solver_slug(name: str) -> str:
    return name.lower().replace(" ", "-").replace("/", "-")


def target_name() -> str:
    system = platform.system().lower()
    machine = platform.machine().lower()
    arch = "arm64" if machine in {"arm64", "aarch64"} else "x86_64" if machine in {"x86_64", "amd64"} else machine
    if system == "darwin":
        return f"macos-{'apple-silicon' if arch == 'arm64' else 'intel'}-cpu"
    if system == "linux":
        return f"ubuntu-{arch}-cpu"
    return f"{system}-{arch}-cpu"


def solver(name: str) -> dict:
    try:
        return LOCKS["solvers"][name]
    except KeyError as exc:
        raise SystemExit(f"Unknown solver {name!r}; choose one of: {', '.join(LOCKS['solvers'])}") from exc


def command_probe(command: list[str], locked_version: str) -> dict:
    executable = command[0]
    path = shutil.which(executable)
    if not path:
        return {"available": False, "path": None, "version_output": None}
    result = subprocess.run(command, text=True, capture_output=True, timeout=15)
    output = (result.stdout or result.stderr).strip()[:500]
    return {"available": result.returncode == 0, "path": path, "version_output": output, "version_matches_lock": result.returncode == 0 and locked_version.lower() in output.lower()}


def inspect(name: str) -> dict:
    item = solver(name)
    probe = command_probe(item["probe_command"], item["version"])
    return {"solver": name, "locked_version": item["version"], "host_target": target_name(), "probe": probe, "official_source": item["official_source"], "result": "reuse" if probe.get("version_matches_lock") else "install_or_container_required"}


def installer_text(name: str, target: str) -> str:
    item = solver(name)
    if target not in item["targets"]:
        raise SystemExit(f"{name} {item['version']} is not declared for {target}; do not generate an unsupported installer.")
    # Every payload is fetched from a named official project, package channel, or OS repository at execution time.
    common = "#!/usr/bin/env bash\nset -euo pipefail\n"
    if name == "OpenFOAM":
        return common + "# Official OpenFOAM Foundation Ubuntu repository, locked to v14.\nsudo sh -c 'curl -fsSL https://dl.openfoam.org/gpg.key | gpg --dearmor > /usr/share/keyrings/openfoam.gpg'\necho 'deb [signed-by=/usr/share/keyrings/openfoam.gpg] https://dl.openfoam.org/ubuntu $(. /etc/os-release && echo $VERSION_CODENAME) main' | sudo tee /etc/apt/sources.list.d/openfoam.list >/dev/null\nsudo apt-get update\nsudo apt-get install -y openfoam14\necho 'Load the OpenFOAM v14 bashrc, then rerun inspect and the selected smoke test.'\n"
    if name == "HCIPy":
        return common + "python3 -m venv .solver-venv\n. .solver-venv/bin/activate\npython -m pip install --upgrade pip\npython -m pip install 'hcipy==0.7.0'\npython -c 'import hcipy; print(hcipy.__version__)'\n"
    if name == "Project Chrono":
        return common + "# Official Project Chrono source release; build only the approved modules.\ngit clone --depth 1 --branch 10.0.0 https://github.com/projectchrono/chrono.git chrono-10.0.0\ncmake -S chrono-10.0.0 -B chrono-10.0.0/build -DENABLE_MODULE_PYTHON=ON\ncmake --build chrono-10.0.0/build -j\necho 'Set PYTHONPATH to the built pychrono module, then run the smoke test.'\n"
    if name == "Python/SciPy":
        return common + "python3 -m venv .solver-venv\n. .solver-venv/bin/activate\npython -m pip install --upgrade pip\npython -m pip install 'numpy==1.26.4' 'scipy==1.13.1'\npython -c \"import numpy, scipy; print('NumPy', numpy.__version__, 'SciPy', scipy.__version__)\"\n"
    if name == "Elmer FEM":
        return common + "git clone --depth 1 --branch release-9.0 https://github.com/ElmerCSC/elmerfem.git elmerfem-9.0\ncmake -S elmerfem-9.0 -B elmerfem-9.0/build\ncmake --build elmerfem-9.0/build -j\ncmake --install elmerfem-9.0/build --prefix \"$PWD/elmerfem-9.0/install\"\n"
    return common + "sudo apt-get update\nsudo apt-get install -y build-essential cmake git python3-dev libboost-all-dev\ngit clone --depth 1 --branch 2024.02a https://gitlab.com/yade-dev/trunk.git yade-2024.02a\ncmake -S yade-2024.02a -B yade-2024.02a/build\ncmake --build yade-2024.02a/build -j\ncmake --install yade-2024.02a/build --prefix \"$PWD/yade-2024.02a/install\"\n"


def write(path: Path, text: str, executable: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    if executable:
        path.chmod(0o755)


def load_receipt(path: Path, name: str, target: str, gpu_backend: str) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    required = {"solver", "version", "target", "gpu_backend", "passed", "executed_at", "evidence"}
    missing = required - data.keys()
    if missing or data["solver"] != name or data["version"] != solver(name)["version"] or data["target"] != target or data["gpu_backend"] != gpu_backend or data["passed"] is not True or not data["evidence"]:
        raise SystemExit("receipt does not prove the locked solver smoke test on the declared target")
    return data


def package(args: argparse.Namespace) -> None:
    item = solver(args.solver)
    target = args.target
    receipt = load_receipt(args.receipt, args.solver, target, args.gpu_backend)
    output = args.output.resolve()
    if output.exists():
        raise SystemExit(f"refusing to overwrite {output}")
    template = TEMPLATES[item["template"]]
    write(output / "scripts" / "install-solver.sh", installer_text(args.solver, target), True)
    write(output / "scripts" / "check-system.sh", "#!/usr/bin/env bash\nset -euo pipefail\nroot=\"$(cd \"$(dirname \"$0\")/..\" && pwd)\"\nsystem=\"$(uname -s)\"\narch=\"$(uname -m)\"\npython3 -c 'import platform; print(platform.python_version())'\ntest -d \"$root\"\nmkdir -p \"$root/outputs\" \"$root/receipts\"\nprintf '%s\\n' \"system=$system arch=$arch solver=" + args.solver + " version=" + item["version"] + "\"\n", True)
    write(output / "scripts" / "run.sh", f"#!/usr/bin/env bash\nset -euo pipefail\nroot=\"$(cd \"$(dirname \"$0\")/..\" && pwd)\"\ntest -f \"$root/simulation_package_manifest.json\"\nclaim=\"$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))[\"runnable_claim\"])' \"$root/simulation_package_manifest.json\")\"\nif [[ \"$claim\" != \"False\" && \"$claim\" != \"false\" ]]; then echo 'unexpected runtime-only runnable claim' >&2; exit 2; fi\nbash \"$root/scripts/check-system.sh\"\ntest -d \"$root/outputs\"\nprintf '%s\\n' 'Runtime probe package is ready for a separate case adapter; no scientific case is executed by this script.'\n", True)
    write(output / "scripts" / "validate.sh", "#!/usr/bin/env bash\nset -euo pipefail\nroot=\"$(cd \"$(dirname \"$0\")/..\" && pwd)\"\ntest -f \"$root/simulation_package_manifest.json\"\ntest -f \"$root/validated_platform_receipt.json\"\npython3 -c 'import json,sys; r=json.load(open(sys.argv[1])); assert r.get(\"passed\") is True; assert r.get(\"solver\"); assert r.get(\"version\")' \"$root/validated_platform_receipt.json\"\ntest -d \"$root/outputs\"\nprintf '%s\\n' 'Platform smoke evidence is valid; numerical and experimental validation remain unclaimed.'\n", True)
    if target.endswith("-container"):
        dockerfile = (ROOT / "containerfiles" / f"{solver_slug(args.solver)}.Dockerfile").read_text(encoding="utf-8")
        write(output / "Containerfile", dockerfile)
    manifest = {"solver": args.solver, "version": item["version"], "target": target, "gpu_backend": args.gpu_backend, "execution_mode": "container" if target.endswith("-container") else "native", "official_source": item["official_source"], "installer": "scripts/install-solver.sh", "launch": "scripts/run.sh", "template": item["template"], "validated_platform_receipt": receipt, "binaries_included": False, "case_implementation": False, "software_readiness": "handoff_only", "claim_ceiling": "solver_runtime_smoke_only; no case implementation or scientific result claimed", "runnable_claim": False}
    write(output / "simulation_package_manifest.json", json.dumps(manifest, indent=2) + "\n")
    if args.offline:
        write(output / "OFFLINE-MISSING.md", "# Offline materials required\n\nNo solver binary or source archive is bundled by this package. Download the pinned solver material from the official source recorded in `simulation_package_manifest.json` on an online staging computer, verify its licence and checksum, then add it only to this exact OS/architecture/GPU-backend package.\n")
    write(output / "validated_platform_receipt.json", json.dumps(receipt, indent=2) + "\n")
    write(output / "README.md", f"# {args.solver} {item['version']} runtime package\n\nThis package does not redistribute a solver binary and is not a runnable scientific case. The receipt `{args.receipt.name}` proves only that the locked external runtime smoke test passed for `{target}`. Add a route-specific executable case adapter, synthetic benchmark, result extractor, and receipts before claiming `runnable_synthetic`. GPU capability is not inferred; a GPU route requires a separate receipt naming the GPU backend.\n")


def smoke(args: argparse.Namespace) -> int:
    if not args.authorized:
        raise SystemExit("refusing smoke execution: rerun only after user authorization with --authorized")
    if not args.command_to_run:
        raise SystemExit("a smoke-test command is required after --")
    start = time.monotonic()
    result = subprocess.run(args.command_to_run, text=True, capture_output=True)
    runtime_seconds = time.monotonic() - start
    log = args.receipt.with_suffix(".log")
    write(log, "$ " + " ".join(args.command_to_run) + "\n" + result.stdout + result.stderr)
    digest = hashlib.sha256(log.read_bytes()).hexdigest()
    receipt = {"solver": args.solver, "version": solver(args.solver)["version"], "solver_version": solver(args.solver)["version"], "package_revision": "not_recorded", "target": args.target, "gpu_backend": args.gpu_backend, "passed": result.returncode == 0, "executed_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(), "timestamp": datetime.now(timezone.utc).replace(microsecond=0).isoformat(), "operating_system": platform.system(), "architecture": platform.machine(), "exact_command": args.command_to_run, "input_file_hash": "not_applicable", "generated_case_hash": "not_applicable", "exit_status": result.returncode, "runtime_seconds": runtime_seconds, "output_hashes": {log.name: digest}, "warnings": [line for line in result.stderr.splitlines() if "warning" in line.lower()], "errors": result.stderr.splitlines() if result.returncode else [], "validation_state": "solver_runtime_smoke", "evidence": [str(log)]}
    write(args.receipt, json.dumps(receipt, indent=2) + "\n")
    return result.returncode


def main() -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("inspect", "installer"):
        p = sub.add_parser(name); p.add_argument("--solver", required=True, choices=LOCKS["solvers"]); p.add_argument("--target", default=target_name()); p.add_argument("--output", type=Path)
    p = sub.add_parser("install"); p.add_argument("--solver", required=True, choices=LOCKS["solvers"]); p.add_argument("--authorized", action="store_true")
    p = sub.add_parser("package"); p.add_argument("--solver", required=True, choices=LOCKS["solvers"]); p.add_argument("--target", required=True); p.add_argument("--gpu-backend", default="cpu"); p.add_argument("--receipt", type=Path, required=True); p.add_argument("--output", type=Path, required=True); p.add_argument("--offline", action="store_true")
    p = sub.add_parser("smoke"); p.add_argument("--solver", required=True, choices=LOCKS["solvers"]); p.add_argument("--target", default=target_name()); p.add_argument("--gpu-backend", default="cpu"); p.add_argument("--receipt", type=Path, required=True); p.add_argument("--authorized", action="store_true"); p.add_argument("command_to_run", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    if args.command == "inspect":
        payload = inspect(args.solver)
        if args.output: write(args.output, json.dumps(payload, indent=2) + "\n")
        else: print(json.dumps(payload, indent=2))
    elif args.command == "installer":
        text = installer_text(args.solver, args.target)
        if args.output: write(args.output, text, True)
        else: print(text, end="")
    elif args.command == "install":
        if not args.authorized: raise SystemExit("refusing installation: rerun only after user authorization with --authorized")
        script = ROOT / ".generated-install.sh"; write(script, installer_text(args.solver, target_name()), True)
        try: return subprocess.run([str(script)], check=False).returncode
        finally: script.unlink(missing_ok=True)
    elif args.command == "package": package(args)
    else: return smoke(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
