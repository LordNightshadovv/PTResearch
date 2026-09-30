from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "scaffold_research_case.py"


class ScaffoldResearchCaseTests(unittest.TestCase):
    def test_prompt_file_is_preserved_exactly_after_outer_whitespace(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            prompt_file = root / "prompt.txt"
            prompt_file.write_text("\nOfficial line one.\nOfficial line two.\n\n", encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(SCRIPT), "prompt-file-case", "--prompt-file", str(prompt_file), "--runs-root", str(root / "runs")],
                capture_output=True, text=True,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            contract = json.loads((root / "runs" / "prompt-file-case" / "problem_contract.yaml").read_text())
            self.assertEqual(contract["exact_prompt"], "Official line one.\nOfficial line two.")
            self.assertEqual(contract["contract_version"], 3)
            state = json.loads((root / "runs" / "prompt-file-case" / "project_state.yaml").read_text())
            self.assertEqual(state["simulation_contract_version"], 1)
            self.assertEqual(state["software_readiness"], "not_applicable")
            registry = json.loads((root / "runs" / "prompt-file-case" / "model_registry.yaml").read_text())
            self.assertEqual(registry["stopping_decision"]["status"], "continue")
            self.assertIn("comparison_table", registry)
            requirements = json.loads((root / "runs" / "prompt-file-case" / "solver_requirements.yaml").read_text())
            self.assertIn("dimensionless_analysis", requirements)

    def test_empty_prompt_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            result = subprocess.run(
                [sys.executable, str(SCRIPT), "empty", "--prompt", "", "--runs-root", str(Path(temp) / "runs")],
                capture_output=True, text=True,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("must not be empty", result.stderr)


if __name__ == "__main__":
    unittest.main()
