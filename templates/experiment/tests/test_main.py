"""Test minimal du squelette d’expérience."""

import importlib.util
from pathlib import Path
import unittest


MODULE_PATH = Path(__file__).parents[1] / "src" / "main.py"
SPEC = importlib.util.spec_from_file_location("experiment_main", MODULE_PATH)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class ExperimentSmokeTest(unittest.TestCase):
    def test_run(self) -> None:
        self.assertEqual(MODULE.run(), "experiment-ready")


if __name__ == "__main__":
    unittest.main()
