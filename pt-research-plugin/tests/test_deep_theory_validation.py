from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("deep_validator", ROOT / "scripts" / "validate_deep_theory.py")
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(MODULE)


class DeepTheoryValidationTests(unittest.TestCase):
    def test_generic_normalized_prediction_is_rejected(self) -> None:
        pattern = MODULE.REJECT[0][0]
        self.assertIsNotNone(pattern.search(r"\frac{Y}{Y_0}=F\!\left(\frac{X}{X_0}\right)"))

    def test_undefined_voltage_force_is_rejected(self) -> None:
        pattern = MODULE.REJECT[1][0]
        self.assertIsNotNone(pattern.search("M q'' + C q' + K q = F(V)"))
        self.assertIsNone(pattern.search("F(V)=kV"))

    def test_local_paths_are_rejected(self) -> None:
        pattern = MODULE.REJECT[-1][0]
        self.assertIsNotNone(pattern.search("/Users/example/report.yaml"))


if __name__ == "__main__":
    unittest.main()
