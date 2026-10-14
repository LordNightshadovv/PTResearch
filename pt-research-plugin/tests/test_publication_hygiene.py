from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import _isolated_home  # noqa: E402,F401  (never read the real ~/.config/pt-research)
import local_paths  # noqa: E402
from validate_plugin import (  # noqa: E402
    check_license,
    check_marketplaces,
    check_no_absolute_home_paths,
    published_files,
)

# Built from parts so this test file itself never contains an absolute home path.
MAC_HOME = "/" + "Users" + "/alice/project/file.txt"
LINUX_HOME = "/" + "home" + "/bob/.cache/tool"


class AbsoluteHomePathGateTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = Path(tempfile.mkdtemp(prefix="pt-hygiene-"))

    def tearDown(self) -> None:
        shutil.rmtree(self.temp)

    def write(self, relative: str, text: str) -> Path:
        path = self.temp / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return path

    def test_real_plugin_tree_is_clean(self) -> None:
        self.assertEqual(check_no_absolute_home_paths(ROOT), [])

    def test_flags_mac_and_linux_home_paths_with_location(self) -> None:
        self.write("docs/a.md", f"line one\nrun {MAC_HOME} now\n")
        self.write("scripts/b.sh", f"cd {LINUX_HOME}\n")
        errors = check_no_absolute_home_paths(self.temp)
        self.assertEqual(len(errors), 2, errors)
        self.assertTrue(any(e.startswith("docs/a.md:2:") for e in errors), errors)
        self.assertTrue(any(e.startswith("scripts/b.sh:1:") for e in errors), errors)

    def test_placeholders_service_accounts_and_regex_fragments_are_allowed(self) -> None:
        self.write("ok.md", "\n".join([
            "use /Users/<name>/x and /home/$USER/y and ~/z and <workspace>/w",
            "container /home/openfoam/Foam-Agent and /home/pt-runner/PT-Simulations",
            "example /Users/example/report.yaml",
            "pattern (?:/Users/|/home/|[A-Z]:)",
        ]))
        self.assertEqual(check_no_absolute_home_paths(self.temp), [])

    def test_binary_files_are_not_scanned(self) -> None:
        (self.temp / "blob.bin").write_bytes(b"\0\1\2" + MAC_HOME.encode())
        self.assertEqual(check_no_absolute_home_paths(self.temp), [])

    def test_known_local_only_files_are_excluded_without_git(self) -> None:
        self.write("local.paths.json", json.dumps({"PT_BUNDLED_PYTHON": MAC_HOME}))
        self.write(".env.local", f"PT_BUNDLED_PYTHON={MAC_HOME}\n")
        self.write("skills/s/assets/local-references/notes.txt", MAC_HOME)
        with mock.patch("validate_plugin.subprocess.run", side_effect=OSError("git unavailable")):
            names = {p.relative_to(self.temp).as_posix() for p in published_files(self.temp)}
            self.assertEqual(names, set())
            self.assertEqual(check_no_absolute_home_paths(self.temp), [])

    @unittest.skipUnless(shutil.which("git"), "git is unavailable")
    def test_git_mode_excludes_ignored_files_and_flags_everything_publishable(self) -> None:
        subprocess.run(["git", "init", "-q"], cwd=self.temp, check=True)
        self.write(".gitignore", "local.paths.json\nlocal-references/\n")
        self.write("local.paths.json", MAC_HOME)
        self.write("assets/local-references/deck.txt", MAC_HOME)
        self.write("untracked_but_publishable.md", MAC_HOME)
        errors = check_no_absolute_home_paths(self.temp)
        self.assertEqual(len(errors), 1, errors)
        self.assertTrue(errors[0].startswith("untracked_but_publishable.md:1:"), errors)

    @unittest.skipUnless(shutil.which("git"), "git is unavailable")
    def test_git_mode_flags_a_published_local_references_folder(self) -> None:
        subprocess.run(["git", "init", "-q"], cwd=self.temp, check=True)
        self.write("assets/local-references/deck.txt", "harmless")
        errors = check_no_absolute_home_paths(self.temp)
        self.assertTrue(any("local-only reference material" in e for e in errors), errors)

    def test_the_plugin_ignores_its_local_files(self) -> None:
        if not shutil.which("git"):
            self.skipTest("git is unavailable")
        for name in ("local.paths.json", ".env.local", "skills/cypt-slide-template/assets/local-references/x.pdf"):
            result = subprocess.run(["git", "-C", str(ROOT), "check-ignore", "-q", name])
            if result.returncode == 128:
                self.skipTest("plugin is not inside a git work tree")
            self.assertEqual(result.returncode, 0, f"{name} must be git-ignored")


class LicenseAndMarketplaceTests(unittest.TestCase):
    def test_license_is_mit_and_manifests_agree(self) -> None:
        codex = json.loads((ROOT / ".codex-plugin" / "plugin.json").read_text(encoding="utf-8"))
        self.assertEqual(check_license(ROOT, codex), [])
        self.assertEqual(codex["license"], "MIT")
        notices = (ROOT / "THIRD_PARTY_NOTICES.md").read_text(encoding="utf-8")
        self.assertIn("covers only the files authored by the PT Research Team", notices)

    def test_license_gate_rejects_missing_or_wrong_license(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            self.assertEqual(check_license(Path(temp), {"license": "MIT"}), ["missing LICENSE at the plugin root"])
            (Path(temp) / "LICENSE").write_text("Apache License", encoding="utf-8")
            errors = check_license(Path(temp), {"license": "Apache-2.0"})
            self.assertTrue(any("MIT License" in e for e in errors), errors)
            self.assertTrue(any("Codex manifest" in e for e in errors), errors)

    def test_marketplaces_are_named_pt_research(self) -> None:
        self.assertEqual(check_marketplaces(ROOT), [])
        repo = ROOT.parent
        claude = repo / ".claude-plugin" / "marketplace.json"
        codex = repo / ".agents" / "plugins" / "marketplace.json"
        if claude.is_file():
            data = json.loads(claude.read_text(encoding="utf-8"))
            self.assertEqual(data["name"], "pt-research")
            self.assertEqual(data["plugins"][0]["source"], "./pt-research-plugin")
        if codex.is_file():
            data = json.loads(codex.read_text(encoding="utf-8"))
            self.assertEqual(data["interface"]["displayName"], "PT Research")
            self.assertEqual(data["plugins"][0]["source"], {"source": "local", "path": "./pt-research-plugin"})


class LocalPathsResolutionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = Path(tempfile.mkdtemp(prefix="pt-localpaths-"))

    def tearDown(self) -> None:
        shutil.rmtree(self.temp)

    def test_environment_beats_json_beats_env_file_beats_default(self) -> None:
        (self.temp / "local.paths.json").write_text(json.dumps({"PT_TEST_KEY": "from-json", "_comment": "x"}), encoding="utf-8")
        self.assertEqual(local_paths.research_home(), _isolated_home.ISOLATED_HOME)
        (self.temp / ".env.local").write_text("PT_TEST_KEY=from-env-file\nPT_OTHER='quoted'\n", encoding="utf-8")
        with mock.patch.dict(os.environ, {}, clear=False):
            os.environ.pop("PT_TEST_KEY", None)
            self.assertEqual(local_paths.resolve("PT_TEST_KEY", "d", self.temp), "from-json")
            self.assertEqual(local_paths.resolve("PT_OTHER", "d", self.temp), "quoted")
            self.assertEqual(local_paths.resolve("PT_MISSING", "d", self.temp), "d")
            self.assertIsNone(local_paths.resolve("_comment", None, self.temp))
            os.environ["PT_TEST_KEY"] = "from-environment"
            self.assertEqual(local_paths.resolve("PT_TEST_KEY", "d", self.temp), "from-environment")

    def test_missing_or_nonexistent_paths_resolve_to_none(self) -> None:
        (self.temp / "local.paths.json").write_text(json.dumps({"PT_TEST_PATH": str(self.temp / "nope")}), encoding="utf-8")
        with mock.patch.dict(os.environ, {}, clear=False):
            os.environ.pop("PT_TEST_PATH", None)
            self.assertIsNone(local_paths.resolve_path("PT_TEST_PATH", self.temp))
            (self.temp / "nope").mkdir()
            self.assertEqual(local_paths.resolve_path("PT_TEST_PATH", self.temp), self.temp / "nope")

    def test_example_config_documents_every_key_used_by_the_code(self) -> None:
        example = json.loads((ROOT / "local.paths.example.json").read_text(encoding="utf-8"))
        for key in ("PT_BUNDLED_PYTHON", "PT_WORKSPACE_ROOT", "PRESENTATIONS_SKILL", "RUNTIME_PYTHON", "RUNTIME_NODE", "RUNTIME_NODE_MODULES"):
            self.assertIn(key, example)

    def test_corrupt_local_config_is_ignored(self) -> None:
        (self.temp / "local.paths.json").write_text("{not json", encoding="utf-8")
        self.assertEqual(local_paths.resolve("PT_NOT_SET_ANYWHERE", "fallback", self.temp), "fallback")


if __name__ == "__main__":
    unittest.main()
