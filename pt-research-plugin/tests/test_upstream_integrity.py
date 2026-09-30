from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class UpstreamIntegrityTests(unittest.TestCase):
    def test_lock_and_snapshot_hashes(self):
        result = subprocess.run([sys.executable, str(ROOT / "scripts" / "verify_upstream_integrity.py"), str(ROOT)], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_complete_source_metadata(self):
        lock = json.loads((ROOT / "upstream-lock.yaml").read_text(encoding="utf-8"))
        self.assertEqual(len(lock["sources"]), 9)
        for source in lock["sources"]:
            for key in ("repository", "commit", "source_path", "retrieved_at", "license", "reuse_mode", "tree_hash", "file_hashes"):
                self.assertTrue(source.get(key), f"{source['local_skill']} lacks {key}")
            self.assertEqual(len(source["commit"]), 40)

    def test_ai_cfd_mit_declaration_is_recorded(self):
        lock = json.loads((ROOT / "upstream-lock.yaml").read_text(encoding="utf-8"))
        items = [x for x in lock["sources"] if x["repository"].endswith("AI-CFD-Scientist")]
        self.assertEqual(len(items), 4)
        self.assertTrue(all("MIT" in x["license"] and "README" in x["license"] for x in items))
        notices = (ROOT / "THIRD_PARTY_NOTICES.md").read_text(encoding="utf-8")
        self.assertIn("License and citation", notices)


if __name__ == "__main__":
    unittest.main()
