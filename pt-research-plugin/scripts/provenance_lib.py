#!/usr/bin/env python3
"""Shared deterministic provenance helpers for PT vendored sources."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


SOURCES = [
    {
        "local_skill": "upstream-kdense-literature-review",
        "repository": "https://github.com/K-Dense-AI/scientific-agent-skills",
        "commit": "3f825caafe149b7853ec8c4d1dd7f4553ea6b2a5",
        "source_path": "skills/literature-review",
        "license": "MIT",
    },
    {
        "local_skill": "upstream-deerflow-systematic-literature-review",
        "repository": "https://github.com/bytedance/deer-flow",
        "commit": "0cd55067f39823e7f0950498b5197a8195512481",
        "source_path": "skills/public/systematic-literature-review",
        "license": "MIT",
    },
    {
        "local_skill": "upstream-deerflow-academic-paper-review",
        "repository": "https://github.com/bytedance/deer-flow",
        "commit": "0cd55067f39823e7f0950498b5197a8195512481",
        "source_path": "skills/public/academic-paper-review",
        "license": "MIT",
    },
    {
        "local_skill": "upstream-cfd-foamagent",
        "repository": "https://github.com/csml-rpi/AI-CFD-Scientist",
        "commit": "b7fa924c834ccfd81c67788b7d6b2e3c9ff13514",
        "source_path": "cfd-skills/cfd-foamagent",
        "license": "MIT (declared in README; no standalone license file)",
    },
    {
        "local_skill": "upstream-cfd-mesh-gate",
        "repository": "https://github.com/csml-rpi/AI-CFD-Scientist",
        "commit": "b7fa924c834ccfd81c67788b7d6b2e3c9ff13514",
        "source_path": "cfd-skills/cfd-mesh-gate",
        "license": "MIT (declared in README; no standalone license file)",
    },
    {
        "local_skill": "upstream-cfd-experiment",
        "repository": "https://github.com/csml-rpi/AI-CFD-Scientist",
        "commit": "b7fa924c834ccfd81c67788b7d6b2e3c9ff13514",
        "source_path": "cfd-skills/cfd-experiment",
        "license": "MIT (declared in README; no standalone license file)",
    },
    {
        "local_skill": "upstream-cfd-code-modify",
        "repository": "https://github.com/csml-rpi/AI-CFD-Scientist",
        "commit": "b7fa924c834ccfd81c67788b7d6b2e3c9ff13514",
        "source_path": "cfd-skills/cfd-code-modify",
        "license": "MIT (declared in README; no standalone license file)",
    },
    {
        "local_skill": "upstream-sim-plugin-openfoam",
        "repository": "https://github.com/svd-ai-lab/sim-plugin-openfoam",
        "commit": "c53b4f362c9b06c985393a777365a9f48fa00710",
        "source_path": "src/sim_plugin_openfoam/_skills/openfoam",
        "license": "Apache-2.0",
    },
    {
        "local_skill": "tool-foam-agent",
        "repository": "https://github.com/csml-rpi/Foam-Agent",
        "commit": "cfde3847be548e4264a1455dd77774794e00ee81",
        "source_path": ".",
        "license": "MIT",
    },
]


def tree_hash(root: Path, exclude: set[str] | None = None) -> tuple[str, dict[str, str]]:
    exclude = exclude or set()
    file_hashes: dict[str, str] = {}
    digest = hashlib.sha256()
    for path in sorted(p for p in root.rglob("*") if p.is_file()):
        relative = path.relative_to(root).as_posix()
        if relative in exclude or relative.startswith(".git/"):
            continue
        content_hash = hashlib.sha256(path.read_bytes()).hexdigest()
        file_hashes[relative] = content_hash
        digest.update(relative.encode("utf-8"))
        digest.update(b"\0")
        digest.update(content_hash.encode("ascii"))
        digest.update(b"\n")
    return digest.hexdigest(), file_hashes


def snapshot_path(plugin_root: Path, source: dict[str, str]) -> Path:
    if source["local_skill"] == "tool-foam-agent":
        return plugin_root / "tools" / "foam-agent"
    return plugin_root / "skills" / source["local_skill"] / "upstream-original"


def read_json_yaml(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))
