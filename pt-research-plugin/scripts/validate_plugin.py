#!/usr/bin/env python3
"""Run PT-specific structural, invocation, provenance, and schema gates."""

from __future__ import annotations

import ast
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path


EXPECTED = {
    "pt-orchestrator", "pt-theoretical-research", "pt-simulation-router",
    "pt-openfoam-environment-manager", "pt-simulation-packager", "pt-remote-execution", "pt-report-renderer",
    "pt-self-improvement", "pt-research-software-engineering",
    "upstream-kdense-literature-review", "upstream-deerflow-systematic-literature-review",
    "upstream-deerflow-academic-paper-review", "upstream-cfd-foamagent",
    "upstream-cfd-mesh-gate", "upstream-cfd-experiment", "upstream-cfd-code-modify",
    "upstream-sim-plugin-openfoam",
}

REQUIRED_SCHEMAS = frozenset({
    "apparatus-fidelity.schema.json", "calibration-plan.schema.json", "case-manifest.schema.json", "dependency-report.schema.json",
    "engineering-standards.schema.json",
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


# Fields Claude Code's plugin manifest supports that this plugin may carry.  Codex-only blocks
# such as "interface" are deliberately excluded so the Claude manifest stays minimal.
CLAUDE_MANIFEST_ALLOWED = frozenset({"name", "version", "description", "author", "keywords", "skills", "homepage", "repository", "license"})
CLAUDE_MANIFEST_REQUIRED = ("name", "version", "description", "author", "keywords", "skills")
ENGINEERING_SKILL = "pt-research-software-engineering"
ENGINEERING_REFERENCES = (
    "engineering-standards.md", "stack-selection-and-adr.md", "interface-selection-guide.md",
    "scientific-computing-vv-checklist.md", "uncertainty-and-experiment-comparison.md", "manifest-contract.md",
)
ENGINEERING_WIRED_SKILLS = ("pt-orchestrator", "pt-simulation-packager", "pt-simulation-router")


def check_claude_manifest(root: Path, codex_manifest: dict) -> list[str]:
    """Check .claude-plugin/plugin.json: required fields, no unsupported fields, version parity."""
    path = root / ".claude-plugin" / "plugin.json"
    try:
        manifest = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return [f"invalid Claude Code plugin manifest: {exc}"]
    if not isinstance(manifest, dict):
        return ["Claude Code plugin manifest must be an object"]
    errors: list[str] = []
    for key in CLAUDE_MANIFEST_REQUIRED:
        if key not in manifest:
            errors.append(f"Claude Code manifest missing field: {key}")
    extra = sorted(set(manifest) - CLAUDE_MANIFEST_ALLOWED)
    if extra:
        errors.append(f"Claude Code manifest has unsupported fields: {extra}")
    if manifest.get("name") != root.name or manifest.get("name") != codex_manifest.get("name"):
        errors.append("Claude Code manifest name must match the plugin directory and Codex manifest")
    if manifest.get("version") != codex_manifest.get("version") or not is_valid_semver(manifest.get("version", "")):
        errors.append("Claude Code manifest version must be valid semver and equal the Codex manifest version")
    author = manifest.get("author")
    if not isinstance(author, dict) or not str(author.get("name", "")).strip():
        errors.append("Claude Code manifest author must be an object with a name")
    if not isinstance(manifest.get("keywords"), list) or not manifest.get("keywords"):
        errors.append("Claude Code manifest keywords must be a non-empty list")
    if not str(manifest.get("description", "")).strip():
        errors.append("Claude Code manifest description is required")
    skills = manifest.get("skills")
    if not isinstance(skills, str) or not (root / skills).is_dir():
        errors.append("Claude Code manifest skills must name an existing skills directory")
    return errors


# --- Publication hygiene -------------------------------------------------------------------------
# Absolute home-directory paths identify a person or machine and break on every other computer.
# Files that would be published (tracked, or untracked but not git-ignored) must not contain them.
HOME_PATH_RE = re.compile(r"(?<![A-Za-z0-9_])/(?:Users|home)/([A-Za-z0-9._-]+)(?=[/\s\"'`)\]>,;:]|$)")
# Placeholder or service-account names that are not a real person's home directory.
GENERIC_HOME_USERS = frozenset({
    "example", "user", "username", "you", "yourname", "name", "me", "runner", "ubuntu", "shared",
    "openfoam",   # container user in the Foam-Agent and OpenFOAM images
    "pt-runner",  # documented non-root service account for pt-remote-execution
})
# Exact (relative path, user) exceptions inside hash-locked vendored upstream code that must not be edited.
HOME_PATH_ALLOWLIST = frozenset({
    ("tools/foam-agent/database/script/tutorial_parser.py", "somasn"),
})
# Machine-local files that are git-ignored in the repository; used only when git is unavailable.
LOCAL_ONLY_FILES = frozenset({"local.paths.json", ".env.local", ".DS_Store"})
LOCAL_ONLY_DIRS = frozenset({".git", "__pycache__", "local-references"})
MAX_SCANNED_BYTES = 8 * 1024 * 1024


def published_files(root: Path) -> list[Path]:
    """Return files that would be published from ``root`` (excluding git-ignored local files).

    Uses ``git ls-files --cached --others --exclude-standard`` when ``root`` is in a git work tree, so
    gitignored local configuration is excluded and untracked-but-publishable files are included.
    Without git (for example an installed copy) it walks the tree and skips the known local-only names.
    """

    try:
        result = subprocess.run(
            ["git", "-C", str(root), "ls-files", "-z", "--cached", "--others", "--exclude-standard"],
            capture_output=True, check=False,
        )
    except OSError:
        result = None
    if result is not None and result.returncode == 0 and result.stdout:
        names = [n for n in result.stdout.decode("utf-8", "surrogateescape").split("\0") if n]
        return sorted({root / n for n in names if (root / n).is_file()})
    files: list[Path] = []
    for current, dirs, names in os.walk(root):
        dirs[:] = [d for d in dirs if d not in LOCAL_ONLY_DIRS]
        files.extend(Path(current) / n for n in names if n not in LOCAL_ONLY_FILES)
    return sorted(files)


def check_no_absolute_home_paths(root: Path) -> list[str]:
    """Fail on absolute home paths (``/Users/<name>/``, ``/home/<name>/``) or on tracked local-only folders."""

    errors: list[str] = []
    for path in published_files(root):
        relative = path.relative_to(root).as_posix()
        if "local-references/" in relative:
            errors.append(f"{relative}: local-only reference material must be git-ignored, not published")
            continue
        try:
            if path.stat().st_size > MAX_SCANNED_BYTES:
                continue
            data = path.read_bytes()
        except OSError:
            continue
        if b"\0" in data[:8192]:
            continue  # binary
        text = data.decode("utf-8", "replace")
        for number, line in enumerate(text.splitlines(), start=1):
            for match in HOME_PATH_RE.finditer(line):
                user = match.group(1)
                if user in GENERIC_HOME_USERS or (relative, user) in HOME_PATH_ALLOWLIST:
                    continue
                errors.append(f"{relative}:{number}: absolute home path {match.group(0)} (use <plugin-root>, <workspace>, ~/ or an environment variable)")
    return errors


def check_license(root: Path, codex_manifest: dict) -> list[str]:
    """Check the MIT LICENSE file and that both manifests declare the same SPDX license."""

    errors: list[str] = []
    license_path = root / "LICENSE"
    try:
        text = license_path.read_text(encoding="utf-8")
    except OSError:
        return ["missing LICENSE at the plugin root"]
    if not text.lstrip().startswith("MIT License") or "Copyright (c) 2026 PT Research Team" not in text:
        errors.append("LICENSE must be the MIT License with 'Copyright (c) 2026 PT Research Team'")
    if codex_manifest.get("license") != "MIT":
        errors.append("Codex manifest must declare \"license\": \"MIT\"")
    try:
        claude = json.loads((root / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        claude = {}
    if claude.get("license") != codex_manifest.get("license"):
        errors.append("Claude Code and Codex manifests must declare the same license")
    notices = root / "THIRD_PARTY_NOTICES.md"
    if notices.is_file() and "MIT license" not in notices.read_text(encoding="utf-8") and "MIT License" not in notices.read_text(encoding="utf-8"):
        errors.append("THIRD_PARTY_NOTICES.md must state that the MIT license covers only PT-authored files")
    return errors


def check_marketplaces(root: Path) -> list[str]:
    """When the plugin sits in its marketplace repository, check both marketplace manifests."""

    errors: list[str] = []
    repo = root.parent
    claude_path = repo / ".claude-plugin" / "marketplace.json"
    codex_path = repo / ".agents" / "plugins" / "marketplace.json"
    relative = "./" + root.name
    if claude_path.is_file():
        try:
            data = json.loads(claude_path.read_text(encoding="utf-8"))
            entries = {p.get("name"): p for p in data.get("plugins", [])}
            if data.get("name") != "pt-research":
                errors.append("Claude marketplace name must be pt-research")
            if not str(data.get("owner", {}).get("name", "")).strip():
                errors.append("Claude marketplace needs owner.name")
            if entries.get(root.name, {}).get("source") != relative:
                errors.append(f"Claude marketplace must list {root.name} with source {relative}")
        except (OSError, json.JSONDecodeError, AttributeError) as exc:
            errors.append(f"invalid Claude marketplace manifest: {exc}")
    if codex_path.is_file():
        try:
            data = json.loads(codex_path.read_text(encoding="utf-8"))
            entries = {p.get("name"): p for p in data.get("plugins", [])}
            if data.get("name") != "pt-research" or data.get("interface", {}).get("displayName") != "PT Research":
                errors.append("Codex marketplace must be named pt-research with displayName 'PT Research'")
            source = entries.get(root.name, {}).get("source", {})
            if source.get("source") != "local" or source.get("path") != relative:
                errors.append(f"Codex marketplace must list {root.name} with a local source path {relative}")
        except (OSError, json.JSONDecodeError, AttributeError) as exc:
            errors.append(f"invalid Codex marketplace manifest: {exc}")
    return errors


def check_local_references_manifest(root: Path) -> list[str]:
    """Check the committed manifest that lets users restore the private (not redistributed) reference decks."""

    relative = "skills/cypt-slide-template/references/local-references.manifest.json"
    try:
        data = json.loads((root / relative).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return [f"{relative}: unreadable ({exc})"]
    errors: list[str] = []
    decks = data.get("decks")
    if not isinstance(decks, list) or not decks:
        return [f"{relative}: needs a non-empty decks list"]
    names = set()
    for deck in decks:
        name = deck.get("filename", "")
        if not name or Path(name).name != name or name in names:
            errors.append(f"{relative}: invalid or duplicate filename {name!r}")
        names.add(name)
        if not re.fullmatch(r"[0-9a-f]{64}", str(deck.get("sha256", ""))):
            errors.append(f"{relative}: {name}: sha256 must be 64 lowercase hex digits")
        if not isinstance(deck.get("size"), int) or deck["size"] <= 0:
            errors.append(f"{relative}: {name}: size must be a positive integer")
        urls = [deck.get("source_url", "")] + list(deck.get("alternate_urls", []))
        if not all(str(u).startswith("https://") for u in urls):
            errors.append(f"{relative}: {name}: every source URL must be https")
        for key in ("team", "problem"):
            if not str(deck.get(key, "")).strip() or "\n" in str(deck.get(key)):
                errors.append(f"{relative}: {name}: {key} must be a one-line description")
    for spec in data.get("derived_images", []):
        if spec.get("source_deck") not in names or not re.fullmatch(r"[0-9a-f]{64}", str(spec.get("jpeg_sha256", ""))):
            errors.append(f"{relative}: derived image {spec.get('output')!r} needs a listed source_deck and a jpeg_sha256")
    return errors


def check_engineering_integration(root: Path) -> list[str]:
    """Check the research-software-engineering skill, its wiring, schema, template, and scaffolder.

    This is a structural check.  It generates a scaffold in a temporary directory, parses every
    generated Python file, and validates the generated manifest; it runs no generated tests.
    """
    errors: list[str] = []
    skill = root / "skills" / ENGINEERING_SKILL
    for reference in ENGINEERING_REFERENCES:
        if not (skill / "references" / reference).is_file():
            errors.append(f"{ENGINEERING_SKILL}: missing reference {reference}")
    for name in ENGINEERING_WIRED_SKILLS:
        text = (root / "skills" / name / "SKILL.md").read_text(encoding="utf-8") if (root / "skills" / name / "SKILL.md").exists() else ""
        if ENGINEERING_SKILL not in text:
            errors.append(f"{name}: SKILL.md must route to {ENGINEERING_SKILL}")
    agents = (root / "AGENTS.md").read_text(encoding="utf-8") if (root / "AGENTS.md").exists() else ""
    if "BEGIN PT-ENGINEERING-STANDARDS" not in agents or "END PT-ENGINEERING-STANDARDS" not in agents or ENGINEERING_SKILL not in agents:
        errors.append("AGENTS.md lacks the engineering-standards policy section")
    if "BEGIN PT-SELF-IMPROVEMENT RULES" not in agents:
        errors.append("AGENTS.md lost the self-improvement managed block")
    try:
        from engineering_contract import validate_engineering_manifest
        from artifact_lib import load_artifact
        import scaffold_research_software as scaffold
    except ImportError as exc:  # pragma: no cover - guards a broken install
        return errors + [f"cannot import engineering tooling: {exc}"]
    try:
        with tempfile.TemporaryDirectory() as temp:
            for interface in ("cli", "desktop_gui"):
                project = Path(temp) / f"check-{interface.replace('_', '-')}"
                written = scaffold.scaffold(project, project.name, interface=interface)
                for path in written:
                    if path.suffix == ".py":
                        ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
                manifest_errors = validate_engineering_manifest(load_artifact(project / "engineering_standards.yaml"), project)
                errors.extend(f"scaffold {interface}: {e}" for e in manifest_errors)
    except (OSError, SyntaxError, ValueError, scaffold.ScaffoldError) as exc:
        errors.append(f"research-software scaffold check failed: {exc}")
    return errors


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
        errors.extend(check_claude_manifest(root, manifest))
        errors.extend(check_license(root, manifest))
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

    errors.extend(check_engineering_integration(root))
    errors.extend(check_marketplaces(root))
    errors.extend(check_local_references_manifest(root))
    errors.extend(check_no_absolute_home_paths(root))

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
