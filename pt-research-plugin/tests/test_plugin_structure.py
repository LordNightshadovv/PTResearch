from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from validate_plugin import REQUIRED_SCHEMAS, is_valid_semver  # noqa: E402


class PluginStructureTests(unittest.TestCase):
    def test_pt_validator(self):
        result = subprocess.run([sys.executable, str(ROOT / "scripts" / "validate_plugin.py")], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_commander_is_only_implicit_skill(self):
        for skill in (ROOT / "skills").iterdir():
            if not skill.is_dir():
                continue
            policy = (skill / "agents" / "openai.yaml").read_text(encoding="utf-8")
            self.assertIn("allow_implicit_invocation: " + ("true" if skill.name == "pt-orchestrator" else "false"), policy)
        agents = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
        self.assertLess(agents.find("pt-orchestrator"), agents.find("specialist"))

    def test_registry_names_all_specialists(self):
        registry = (ROOT / "skills" / "pt-orchestrator" / "references" / "specialist-registry.yaml").read_text(encoding="utf-8")
        for skill in (ROOT / "skills").iterdir():
            if skill.is_dir() and skill.name != "pt-orchestrator":
                self.assertIn(skill.name + ":", registry)

    def test_manifest_and_all_schemas_parse(self):
        json.loads((ROOT / ".codex-plugin" / "plugin.json").read_text(encoding="utf-8"))
        schemas = list((ROOT / "schemas").glob("*.schema.json"))
        self.assertTrue(REQUIRED_SCHEMAS.issubset({schema.name for schema in schemas}))
        for schema in schemas:
            json.loads(schema.read_text(encoding="utf-8"))

    def test_semver_accepts_build_suffix_and_rejects_malformed_versions(self):
        for version in ("0.7.0", "0.7.0+codex.20260831142305", "1.2.3-alpha.1+build.7"):
            self.assertTrue(is_valid_semver(version), version)
        for version in ("0.7", "v0.7.0", "0.7.0.1", "0.7.0+", "0.7.0+codex/"):
            self.assertFalse(is_valid_semver(version), version)


if __name__ == "__main__":
    unittest.main()
