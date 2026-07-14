"""Tests for the experiment scaffolding tool."""

from datetime import date
import importlib.util
from pathlib import Path
import tempfile
import unittest


TOOL_PATH = Path(__file__).parents[1] / "tools" / "new_experiment.py"
SPEC = importlib.util.spec_from_file_location("new_experiment", TOOL_PATH)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class NewExperimentTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        template = self.root / "templates" / "experiment"
        (template / "src").mkdir(parents=True)
        (template / "tests").mkdir()
        (template / "README.md").write_text(
            "# {{ID}} — {{TITLE}}\nDate: {{DATE}}\n", encoding="utf-8"
        )
        (template / "src" / "main.py").write_text("print('ok')\n", encoding="utf-8")

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_creates_next_numbered_experiment(self) -> None:
        (self.root / "experiments" / "000-existing").mkdir(parents=True)
        target = MODULE.create_experiment(
            self.root,
            "new-idea",
            "New Idea",
            today=date(2026, 7, 14),
        )
        self.assertEqual(target.name, "001-new-idea")
        self.assertIn("# 001 — New Idea", (target / "README.md").read_text(encoding="utf-8"))
        self.assertTrue((target / "src" / "main.py").exists())

    def test_dry_run_does_not_write(self) -> None:
        target = MODULE.create_experiment(self.root, "preview", "Preview", dry_run=True)
        self.assertFalse(target.exists())

    def test_rejects_unsafe_slug(self) -> None:
        with self.assertRaises(ValueError):
            MODULE.create_experiment(self.root, "../escape", "Unsafe")


if __name__ == "__main__":
    unittest.main()
