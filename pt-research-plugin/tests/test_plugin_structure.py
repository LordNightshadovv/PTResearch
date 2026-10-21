from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from validate_plugin import (  # noqa: E402
    CLAUDE_MANIFEST_ALLOWED,
    ENGINEERING_SKILL,
    ENGINEERING_WIRED_SKILLS,
    REQUIRED_SCHEMAS,
    check_claude_manifest,
    check_engineering_integration,
    is_valid_semver,
)


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

    def test_claude_manifest_matches_codex_manifest_and_has_only_supported_fields(self):
        codex = json.loads((ROOT / ".codex-plugin" / "plugin.json").read_text(encoding="utf-8"))
        claude = json.loads((ROOT / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8"))
        self.assertEqual(claude["name"], "pt-research-plugin")
        self.assertEqual(claude["version"], codex["version"])
        self.assertTrue(codex["version"].startswith("0.8.4+codex."))
        self.assertRegex(codex["version"], r"^0\.8\.4\+codex\.\d{14}$")
        self.assertEqual(claude["author"], {"name": codex["author"]["name"]})
        self.assertTrue(claude["keywords"])
        self.assertEqual(claude["skills"], "./skills/")
        self.assertLessEqual(set(claude), CLAUDE_MANIFEST_ALLOWED)
        self.assertNotIn("interface", claude)
        self.assertEqual(check_claude_manifest(ROOT, codex), [])

    def test_claude_manifest_checker_rejects_drift(self):
        codex = json.loads((ROOT / ".codex-plugin" / "plugin.json").read_text(encoding="utf-8"))
        drifted = dict(codex, version="0.0.1")
        self.assertTrue(any("version" in e for e in check_claude_manifest(ROOT, drifted)))

    def test_engineering_skill_is_wired_everywhere_and_policy_is_in_agents(self):
        self.assertEqual(check_engineering_integration(ROOT), [])
        for name in ENGINEERING_WIRED_SKILLS:
            text = (ROOT / "skills" / name / "SKILL.md").read_text(encoding="utf-8")
            self.assertIn(ENGINEERING_SKILL, text)
        agents = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
        self.assertIn("PTENG-001", agents)
        self.assertIn("BEGIN PT-SELF-IMPROVEMENT RULES", agents)
        self.assertLess(agents.index("END PT-ENGINEERING-STANDARDS"), agents.index("BEGIN PT-SELF-IMPROVEMENT RULES"))
        self.assertIn("engineering-standards.schema.json", REQUIRED_SCHEMAS)
        skill = (ROOT / "skills" / ENGINEERING_SKILL / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("proves declaration and structure, never scientific correctness", skill)

    def test_changelog_documents_current_base_version(self):
        base = json.loads((ROOT / ".codex-plugin" / "plugin.json").read_text(encoding="utf-8"))["version"].split("+")[0]
        self.assertIn("## [" + base + "]", (ROOT / "CHANGELOG.md").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
