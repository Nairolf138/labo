"""Checks that every maintained experiment is exercised by CI."""

from pathlib import Path
import unittest


ROOT = Path(__file__).parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "ci.yml"


class CIConfigurationTest(unittest.TestCase):
    def test_ci_runs_tests_for_each_experiment_with_tests(self) -> None:
        workflow = WORKFLOW.read_text(encoding="utf-8")
        experiments = sorted(
            path
            for path in (ROOT / "experiments").iterdir()
            if path.is_dir() and (path / "tests").is_dir()
        )

        for experiment in experiments:
            self.assertIn(
                f"experiments/{experiment.name}/tests",
                workflow,
                f"CI does not run tests for {experiment.name}",
            )


if __name__ == "__main__":
    unittest.main()