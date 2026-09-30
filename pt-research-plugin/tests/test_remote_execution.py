from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REMOTE = ROOT / "skills" / "pt-remote-execution" / "scripts" / "pt_remote.py"
PROGRESS = ROOT / "skills" / "pt-remote-execution" / "scripts"


class RemoteExecutionTests(unittest.TestCase):
    def test_required_remote_contract_files_exist(self):
        required = [
            "SKILL.md", "agents/openai.yaml", "references/remote-execution.md",
            "references/ssh-security.md", "references/progress-contract.md",
            "scripts/pt_remote.py", "templates/config/remote.example.toml",
            "templates/project/status.schema.json", "templates/linux/admin-bootstrap.sh",
        ]
        base = ROOT / "skills" / "pt-remote-execution"
        for relative in required:
            self.assertTrue((base / relative).is_file(), relative)

    def test_config_rejects_secret_fields(self):
        with tempfile.TemporaryDirectory() as directory:
            config = Path(directory) / "remote.toml"
            config.write_text('[remote]\nhost_alias = "pt-linux"\npassword = "no"\n', encoding="utf-8")
            result = subprocess.run([sys.executable, str(REMOTE), "--config", str(config), "doctor"], capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("secret field", result.stderr)

    def test_command_rejects_injection_and_dry_run_does_not_connect(self):
        result = subprocess.run([sys.executable, str(REMOTE), "status", "--host", "bad;host", "--project", "case"], capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        result = subprocess.run([sys.executable, str(REMOTE), "--dry-run", "sync", "--host", "pt-linux", "--project", str(ROOT / "tests" / "fixtures" / "air-vortex-routing")], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("DRY-RUN", result.stdout)

    def test_status_schema_and_indeterminate_progress(self):
        schema = json.loads((ROOT / "skills" / "pt-remote-execution" / "templates" / "project" / "status.schema.json").read_text(encoding="utf-8"))
        self.assertIn("unreachable", schema["properties"]["state"]["enum"])
        sys.path.insert(0, str(PROGRESS))
        from progress.base import estimate
        value = estimate("iterations", 10, None, [])
        self.assertEqual(value.mode, "indeterminate")
        self.assertIsNone(value.progress_percent)
        stable = estimate("iterations", 50, 100, [(i * 10.0, i * 2.0) for i in range(1, 7)])
        self.assertIsNotNone(stable.estimated_remaining_seconds)

    def test_no_sensitive_files_or_host_bypass(self):
        text = REMOTE.read_text(encoding="utf-8")
        self.assertNotIn("StrictHostKeyChecking no", text)
        self.assertNotIn("BEGIN OPENSSH PRIVATE KEY", text)


if __name__ == "__main__":
    unittest.main()
