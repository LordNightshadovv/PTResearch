#!/usr/bin/env python3
"""Small, dependency-free helpers for PT JSON-compatible YAML artifacts."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def load_artifact(path: Path) -> Any:
    """Load the plugin's JSON-compatible YAML subset."""
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ValueError(f"missing artifact: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"{path}: artifacts must be JSON-compatible YAML: {exc}") from exc


def dump_artifact(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def load_schema(plugin_root: Path, name: str) -> dict[str, Any]:
    value = load_artifact(plugin_root / "schemas" / f"{name}.schema.json")
    if not isinstance(value, dict):
        raise ValueError(f"schema {name} is not an object")
    return value


def basic_schema_errors(value: Any, schema: dict[str, Any], location: str = "$") -> list[str]:
    """Validate the schema subset used by this plugin without third-party packages."""
    errors: list[str] = []
    expected = schema.get("type")
    type_map = {
        "object": dict,
        "array": list,
        "string": str,
        "number": (int, float),
        "integer": int,
        "boolean": bool,
        "null": type(None),
    }
    expected_types = expected if isinstance(expected, list) else [expected]
    expected_types = [item for item in expected_types if item in type_map]
    if expected_types:
        matches = False
        for expected_type in expected_types:
            candidate = type_map[expected_type]
            if expected_type in {"number", "integer"} and isinstance(value, bool):
                continue
            if isinstance(value, candidate):
                matches = True
                break
        if not matches:
            label = "/".join(expected_types)
            return [f"{location}: expected {label}"]
    if isinstance(value, dict):
        for key in schema.get("required", []):
            if key not in value:
                errors.append(f"{location}: missing required field {key}")
        properties = schema.get("properties", {})
        for key, subschema in properties.items():
            if key in value and isinstance(subschema, dict):
                errors.extend(basic_schema_errors(value[key], subschema, f"{location}.{key}"))
    if isinstance(value, list) and isinstance(schema.get("items"), dict):
        for index, item in enumerate(value):
            errors.extend(basic_schema_errors(item, schema["items"], f"{location}[{index}]"))
    if isinstance(value, str) and schema.get("minLength", 0) and len(value) < schema["minLength"]:
        errors.append(f"{location}: string is too short")
    if isinstance(value, list) and len(value) < schema.get("minItems", 0):
        errors.append(f"{location}: too few items")
    if "enum" in schema and value not in schema["enum"]:
        errors.append(f"{location}: value is not in enum")
    return errors
