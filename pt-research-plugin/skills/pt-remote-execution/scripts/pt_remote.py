#!/usr/bin/env python3
"""Alias-only, secret-free remote PT execution helper.

All remote calls use the OS OpenSSH client. This utility intentionally does
not implement key handling, credential storage, host-key bypass, or sudo.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Optional

SAFE_NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,79}$")
FORBIDDEN_CONFIG = {"password", "private_key", "key_passphrase", "token", "tailscale_key", "auth"}
TERMINAL = {"completed", "failed", "cancelled", "unreachable"}


def die(message: str) -> None:
    raise SystemExit(f"ERROR: {message}")


def require_safe_name(value: str, label: str) -> str:
    if not SAFE_NAME.fullmatch(value):
        die(f"invalid {label}; use letters, numbers, dot, underscore, or hyphen")
    return value


def quote_remote(parts: Iterable[str]) -> str:
    return " ".join(shlex.quote(str(part)) for part in parts)


def read_config(path: Optional[Path]) -> dict[str, Any]:
    if path is None:
        return {}
    try:
        import tomllib  # Python 3.11+
    except ImportError:
        tomllib = None
    try:
        raw = path.read_text(encoding="utf-8")
        if tomllib is not None:
            config = tomllib.loads(raw)
        else:
            # The documented config is deliberately flat TOML; keep the
            # fallback narrow rather than adding a configuration dependency.
            config, section = {}, None
            for line in raw.splitlines():
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if line.startswith("[") and line.endswith("]"):
                    section = line[1:-1]
                    config[section] = {}
                    continue
                if section is None or "=" not in line:
                    die("unsupported TOML syntax in remote config")
                key, value = (part.strip() for part in line.split("=", 1))
                config[section][key] = value.strip('"') if value.startswith('"') else int(value)
    except (OSError, ValueError) as exc:
        die(f"cannot read config: {exc}")
    for section in config.values():
        if isinstance(section, dict):
            for key in section:
                if key.lower() in FORBIDDEN_CONFIG or any(word in key.lower() for word in FORBIDDEN_CONFIG):
                    die(f"config must not contain secret field: {key}")
    remote = config.get("remote", {})
    if remote.get("host_alias"):
        require_safe_name(str(remote["host_alias"]), "host alias")
    return config


def setting(args: argparse.Namespace, config: dict[str, Any], key: str, section: str = "remote", default: Any = None) -> Any:
    value = getattr(args, key, None)
    return value if value is not None else config.get(section, {}).get(key, default)


def ssh_config_has_alias(alias: str) -> bool:
    config = Path.home() / ".ssh" / "config"
    if not config.exists():
        return False
    return any(alias in line.split()[1:] for line in config.read_text(encoding="utf-8", errors="replace").splitlines() if line.strip().lower().startswith("host "))


def run(command: list[str], args: argparse.Namespace, *, capture: bool = True) -> subprocess.CompletedProcess[str]:
    if args.dry_run:
        print("DRY-RUN", json.dumps(command))
        return subprocess.CompletedProcess(command, 0, "", "")
    return subprocess.run(command, text=True, capture_output=capture)


def ssh(alias: str, remote_parts: Iterable[str], args: argparse.Namespace) -> subprocess.CompletedProcess[str]:
    require_safe_name(alias, "host alias")
    # `--` stops ssh option parsing; remote command is a safely quoted POSIX command.
    return run(["ssh", "--", alias, quote_remote(remote_parts)], args)


def emit(payload: Any, args: argparse.Namespace, code: int = 0) -> int:
    if args.json:
        print(json.dumps(payload, sort_keys=True))
    elif isinstance(payload, dict):
        for item in payload.get("checks", []):
            print(f"{item['status']}: {item['name']} — {item['action']}")
        if "state" in payload:
            print(f"state: {payload['state']}")
            print(f"progress: {payload.get('progress_percent', 'indeterminate')}")
    else:
        print(payload)
    return code


def health_item(name: str, ok: bool, action: str, blocked: bool = False) -> dict[str, str]:
    return {"name": name, "status": "PASS" if ok else ("BLOCKED" if blocked else "WARNING"), "action": action}


def doctor(args: argparse.Namespace, config: dict[str, Any]) -> int:
    alias = setting(args, config, "host") or setting(args, config, "host_alias")
    if not alias:
        die("--host or remote.host_alias is required")
    require_safe_name(alias, "host alias")
    key = Path.home() / ".ssh" / "pt_simulation_ed25519"
    checks = [
        health_item("SSH alias", ssh_config_has_alias(alias), "Add or correct a named Host block; do not provide a raw address to the plugin.", True),
        health_item("OpenSSH client", shutil.which("ssh") is not None, "Install or restore the operating system OpenSSH client.", True),
        health_item("Dedicated key file", key.exists(), "After approval, generate the dedicated key; never paste it into chat."),
        health_item("Dedicated key permissions", not key.exists() or (key.stat().st_mode & 0o777) == 0o600, "Run chmod 600 on the key."),
        health_item("SSH agent", shutil.which("ssh-add") is not None, "Use macOS ssh-agent and Keychain; do not expose a passphrase."),
    ]
    if key.exists() and not args.dry_run:
        agent = subprocess.run(["ssh-add", "-l"], text=True, capture_output=True)
        checks.append(health_item("Key loaded in agent", agent.returncode == 0, "Run ssh-add --apple-use-keychain on the dedicated key."))
    return emit({"checks": checks}, args, 1 if any(x["status"] == "BLOCKED" for x in checks) else 0)


def probe(args: argparse.Namespace, config: dict[str, Any]) -> int:
    alias = setting(args, config, "host") or setting(args, config, "host_alias")
    username = setting(args, config, "username")
    if not alias:
        die("--host is required")
    remote = ["sh", "-lc", "command -v codex; codex login status; id -un; uname -m; nproc; df -Pk .; systemctl --user --version"]
    result = ssh(alias, remote, args)
    checks = [health_item("remote probe", result.returncode == 0, "Verify alias, host key, key authentication, Codex login, and user service support.", result.returncode == 255)]
    if username and result.returncode == 0:
        actual = result.stdout.splitlines()[2] if len(result.stdout.splitlines()) > 2 else ""
        checks.append(health_item("remote username", actual == username, "Correct the alias User field or remote configuration.", True))
    payload = {"checks": checks, "output": result.stdout.strip() if not args.redacted else "[redacted]"}
    return emit(payload, args, result.returncode)


def bootstrap_plan(args: argparse.Namespace, config: dict[str, Any]) -> int:
    root = Path(__file__).resolve().parents[1] / "templates"
    return emit({"checks": [health_item("administrator bootstrap", False, f"Review, then explicitly approve: {root / 'linux' / 'admin-bootstrap.sh'}"), health_item("user bootstrap", False, f"Run as the dedicated account after approval: {root / 'linux' / 'user-bootstrap.sh'}")]}, args)


def project_remote_dir(config: dict[str, Any], project: str) -> str:
    require_safe_name(project, "project")
    root = str(config.get("remote", {}).get("project_root", "/home/pt-runner/PT-Simulations"))
    if not root.startswith("/") or ".." in Path(root).parts:
        die("remote.project_root must be an absolute contained path")
    return f"{root.rstrip('/')}/{project}"


def make_manifest(project: Path, project_id: str, solver: str) -> dict[str, Any]:
    files = []
    for path in sorted(project.rglob("*")):
        if path.is_file() and not any(part in {".git", ".venv", "__pycache__", ".codex"} for part in path.parts):
            files.append({"path": path.relative_to(project).as_posix(), "sha256": hashlib.sha256(path.read_bytes()).hexdigest()})
    return {"project_id": project_id, "solver": solver, "created_at": datetime.now(timezone.utc).isoformat(), "files": files}


def sync(args: argparse.Namespace, config: dict[str, Any]) -> int:
    alias, source, project = args.host, Path(args.project).resolve(), args.project_id or Path(args.project).name
    require_safe_name(alias, "host alias"); require_safe_name(project, "project")
    if not source.is_dir(): die("--project must be an existing local directory")
    remote_dir = project_remote_dir(config, project)
    manifest = make_manifest(source, project, args.solver or "unknown")
    with tempfile.TemporaryDirectory() as temp:
        manifest_file = Path(temp) / "pt-sync-manifest.json"; manifest_file.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
        excludes = ["--exclude=.git", "--exclude=.venv", "--exclude=__pycache__", "--exclude=.codex", "--exclude=*.key", "--exclude=auth.json"]
        command = ["rsync", "-az", "--partial", *excludes, "-e", "ssh", str(source) + "/", f"{alias}:{remote_dir}/"]
        if shutil.which("rsync") is None: command = ["scp", "-r", str(source), f"{alias}:{remote_dir}"]
        result = run(command, args)
    return emit({"state": "synced" if result.returncode == 0 else "failed", "project_id": project, "manifest": manifest}, args, result.returncode)


def remote_action(args: argparse.Namespace, config: dict[str, Any]) -> int:
    alias, project = args.host, args.project
    require_safe_name(alias, "host alias"); remote_dir = project_remote_dir(config, project)
    action = args.command
    scripts = {"start": "start.sh", "stop": "stop.sh", "resume": "resume.sh", "logs": "logs.sh", "checkpoints": "status.sh", "fetch-results": "fetch-results.sh"}
    if action == "start":
        # A detached user service survives this SSH invocation. The post-start
        # checks intentionally refuse to call a start successful on its exit
        # code alone: a runner must expose service, log, and status evidence.
        unit = "pt-" + project.replace(".", "-")
        script = " && ".join([
            f"cd {shlex.quote(remote_dir)}",
            "mkdir -p run/checkpoints",
            f"systemd-run --user --unit={shlex.quote(unit)} --collect ./start.sh",
            f"systemctl --user is-active --quiet {shlex.quote(unit)}",
            "test -w run/stdout.log",
            "test -s run/status.json",
            "python3 -c 'import json,sys; s=json.load(open(sys.argv[1])); sys.exit(0 if s.get(\"state\") in {\"starting\",\"running\",\"queued\",\"preparing\"} else 1)' run/status.json",
        ])
        result = ssh(alias, ["sh", "-lc", script], args)
        return emit({"state": "starting" if result.returncode == 0 else "failed", "service": unit, "output": result.stdout.strip()}, args, result.returncode)
    if action == "status":
        result = ssh(alias, ["cat", f"{remote_dir}/run/status.json"], args)
        if result.returncode: return emit({"state": "unreachable" if result.returncode == 255 else "unknown", "error": result.stderr.strip()}, args, result.returncode)
        try: status = json.loads(result.stdout)
        except json.JSONDecodeError: die("remote status.json is not valid JSON")
        return emit(status, args)
    if action == "fetch-results":
        destination = Path(setting(args, config, "local_results_root", "transfer", "./results")).expanduser() / project
        command = ["rsync", "-az", "--partial", "-e", "ssh", f"{alias}:{remote_dir}/run/", str(destination)]
        result = run(command, args)
    else:
        extra = [str(args.tail)] if action == "logs" and args.tail else []
        result = ssh(alias, ["sh", f"{remote_dir}/{scripts[action]}", *extra], args)
    return emit({"state": action if result.returncode == 0 else "failed", "output": result.stdout.strip()}, args, result.returncode)


def install_solver(args: argparse.Namespace, config: dict[str, Any]) -> int:
    if not args.authorized: die("install-solver requires --authorized after explicit user approval")
    return emit({"checks": [health_item("solver install", False, "Use the locked official-source installer plan on the remote host; this command intentionally does not grant sudo.")]}, args)


def clean(args: argparse.Namespace, config: dict[str, Any]) -> int:
    if not args.confirm: return emit({"checks": [health_item("clean", False, "Dry run only. Review targets and rerun with --confirm; newest checkpoint is preserved.")]}, args)
    die("remote cleanup requires a project-specific retention manifest; refusing broad deletion")


def notification(args: argparse.Namespace, config: dict[str, Any]) -> int:
    state = args.state or "unknown"
    text = f"PT simulation {args.project}: {state}."
    if state in TERMINAL: text += " Stop repeated status checks."
    return emit(text, args)


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(); p.add_argument("--config", type=Path); p.add_argument("--json", action="store_true"); p.add_argument("--dry-run", action="store_true"); p.add_argument("--redacted", action="store_true")
    subs = p.add_subparsers(dest="command", required=True)
    for name in ("doctor", "bootstrap-plan", "probe"):
        sp = subs.add_parser(name); sp.add_argument("--host")
    sp = subs.add_parser("sync"); sp.add_argument("--host", required=True); sp.add_argument("--project", required=True); sp.add_argument("--project-id"); sp.add_argument("--solver")
    sp = subs.add_parser("install-solver"); sp.add_argument("--host", required=True); sp.add_argument("--solver", required=True); sp.add_argument("--authorized", action="store_true")
    for name in ("start", "stop", "resume", "status", "logs", "checkpoints", "fetch-results", "clean"):
        sp = subs.add_parser(name); sp.add_argument("--host", required=True); sp.add_argument("--project", required=True); sp.add_argument("--tail", type=int); sp.add_argument("--confirm", action="store_true")
    sp = subs.add_parser("render-notification"); sp.add_argument("--project", required=True); sp.add_argument("--state")
    return p


def main() -> int:
    args = parser().parse_args(); config = read_config(args.config)
    actions = {"doctor": doctor, "bootstrap-plan": bootstrap_plan, "probe": probe, "sync": sync, "install-solver": install_solver, "render-notification": notification, "clean": clean}
    return actions.get(args.command, remote_action)(args, config)

if __name__ == "__main__":
    raise SystemExit(main())
