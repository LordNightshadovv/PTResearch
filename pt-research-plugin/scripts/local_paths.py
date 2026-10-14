#!/usr/bin/env python3
"""Resolve machine-specific tool locations and private data without hard-coding any personal path.

Private, machine-specific data must survive plugin updates. A plugin installed from a marketplace is
copied into a cache directory that is replaced on every update, so nothing private may live only
inside the plugin directory. The user-level directory ``PT_RESEARCH_HOME`` (default
``~/.config/pt-research``) is the durable home for it.

Lookup order for a key such as ``PT_BUNDLED_PYTHON``:

1. the environment variable of the same name;
2. ``<PT_RESEARCH_HOME>/local.paths.json`` (user level; survives plugin updates);
3. ``local.paths.json`` in the plugin root (git-ignored; see ``local.paths.example.json``);
4. ``.env.local`` in the plugin root (``KEY=value`` lines, git-ignored);
5. the caller's default (often ``None``, meaning "feature unavailable, skip gracefully").

Local reference decks (``local_references_dir``): ``PT_LOCAL_REFERENCES_DIR`` (an explicit setting
is used exclusively), then ``<PT_RESEARCH_HOME>/local-references``, then the git-ignored
``skills/cypt-slide-template/assets/local-references`` inside the plugin.

``PT_RESEARCH_HOME`` itself comes only from the environment (it locates the file that could
otherwise define it). Only the standard library is used.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
LOCAL_JSON = "local.paths.json"
LOCAL_ENV = ".env.local"
HOME_ENV = "PT_RESEARCH_HOME"
LOCAL_REFERENCES_ENV = "PT_LOCAL_REFERENCES_DIR"
LOCAL_REFERENCES_NAME = "local-references"
PLUGIN_LOCAL_REFERENCES = Path("skills") / "cypt-slide-template" / "assets" / LOCAL_REFERENCES_NAME


def research_home() -> Path:
    """Return the user-level private data directory (it may not exist yet)."""

    value = os.environ.get(HOME_ENV)
    if value and value.strip():
        return Path(value.strip()).expanduser()
    return Path.home() / ".config" / "pt-research"


def _read_local_json(directory: Path) -> dict[str, str]:
    try:
        data = json.loads((directory / LOCAL_JSON).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    if not isinstance(data, dict):
        return {}
    return {k: v for k, v in data.items() if isinstance(v, str) and v.strip() and not k.startswith("_")}


def _read_local_env(root: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    try:
        lines = (root / LOCAL_ENV).read_text(encoding="utf-8").splitlines()
    except OSError:
        return values
    for line in lines:
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        value = value.strip().strip('"').strip("'")
        if value:
            values[key.strip()] = value
    return values


def resolve(key: str, default: str | None = None, root: Path | None = None, home: Path | None = None) -> str | None:
    """Return the configured value for ``key`` or ``default``.

    ``root`` is the plugin root (default: this plugin); ``home`` is the user-level data directory
    (default: ``research_home()``).
    """

    root = root or PLUGIN_ROOT
    home = home if home is not None else research_home()
    value = os.environ.get(key)
    if value and value.strip():
        return value
    for source in (_read_local_json(home), _read_local_json(root), _read_local_env(root)):
        if key in source:
            return source[key]
    return default


def resolve_path(key: str, root: Path | None = None, home: Path | None = None) -> Path | None:
    """Return the configured path for ``key`` only if it exists, else ``None``."""

    value = resolve(key, None, root, home)
    if not value:
        return None
    path = Path(value).expanduser()
    return path if path.exists() else None


def default_local_references_dir(home: Path | None = None) -> Path:
    """Where private reference decks should be restored: the explicit setting, else the user-level folder."""

    explicit = os.environ.get(LOCAL_REFERENCES_ENV)
    if explicit and explicit.strip():
        return Path(explicit.strip()).expanduser()
    return (home if home is not None else research_home()) / LOCAL_REFERENCES_NAME


def local_references_dir(root: Path | None = None, home: Path | None = None) -> Path | None:
    """Return the existing local reference folder to read from, or ``None`` when there is none.

    An explicit ``PT_LOCAL_REFERENCES_DIR`` is used exclusively (``None`` if it does not exist).
    """

    root = root or PLUGIN_ROOT
    explicit = os.environ.get(LOCAL_REFERENCES_ENV)
    if explicit and explicit.strip():
        path = Path(explicit.strip()).expanduser()
        return path if path.is_dir() else None
    for candidate in (
        (home if home is not None else research_home()) / LOCAL_REFERENCES_NAME,
        root / PLUGIN_LOCAL_REFERENCES,
    ):
        if candidate.is_dir():
            return candidate
    return None


if __name__ == "__main__":  # pragma: no cover - convenience CLI
    import sys

    for name in sys.argv[1:]:
        print(resolve(name) or "")
