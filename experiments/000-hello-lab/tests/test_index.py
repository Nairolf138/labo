"""Tests de l'expérience Hello Lab."""

import importlib.util
from pathlib import Path
import unittest


MODULE_PATH = Path(__file__).parents[1] / "src" / "index.py"
SPEC = importlib.util.spec_from_file_location("hello_lab", MODULE_PATH)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class HelloLabTest(unittest.TestCase):
    def test_status_message(self) -> None:
        self.assertEqual(MODULE.status_message(), "Nox Lab opérationnel.")


if __name__ == "__main__":
    unittest.main()
