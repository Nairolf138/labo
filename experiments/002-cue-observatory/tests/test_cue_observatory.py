"""Behavior tests for the Cue Observatory."""

from pathlib import Path
import json
import sys
import unittest

SRC = Path(__file__).parents[1] / "src"
sys.path.insert(0, str(SRC))

import cue_observatory  # noqa: E402


class CueObservatoryTest(unittest.TestCase):
    """Tests for the Cue Observatory experiment."""

    def setUp(self) -> None:
        """Create a temporary CSV file for testing."""
        import tempfile

        self.temp_dir = tempfile.mkdtemp()
        self.csv_path = f"{self.temp_dir}/cues.csv"

    def tearDown(self) -> None:
        """Clean up temporary files."""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_generates_markdown_report_from_csv(self) -> None:
        """Generate a Markdown report from a synthetic CSV file."""
        csv_content = """cue,time,marker,notes
Cue 1,00:00:00,start,"Opening cue"
Cue 2,00:05:30,transition,"Fade to blue"
Cue 3,00:05:30,simultaneous,"Cue 3 starts with Cue 2"
Cue 4,00:10:00,transition,"Crossfade to red"
Cue 5,00:15:00,end,"Finale"
"""

        with open(self.csv_path, "w") as f:
            f.write(csv_content)

        report = cue_observatory.generate_report(self.csv_path)

        # Check that report is markdown
        self.assertIn("# Cue Observatory Report", report)
        self.assertIn("## Summary", report)
        self.assertIn("## Timeline", report)
        self.assertIn("## Density Analysis", report)
        self.assertIn("## Simultaneous Cues", report)
        self.assertIn("## Vigilance Points", report)

        # Check summary statistics (markdown format)
        self.assertIn("**Total cues:** 5", report)
        self.assertIn("**Duration:** 00:15:00", report)
        self.assertIn("**Transitions:** 2", report)
        self.assertIn("**Simultaneous groups:** 1", report)

        # Check timeline contains cues
        self.assertIn("Cue 1", report)
        self.assertIn("Cue 5", report)

        # Check simultaneous cues are detected
        self.assertIn("Cue 2", report)
        self.assertIn("Cue 3", report)
        self.assertIn("simultaneous", report.lower())

        # Check vigilance points
        self.assertIn("Vigilance", report)

    def test_handles_empty_csv(self) -> None:
        """Handle empty CSV gracefully."""
        csv_content = "cue,time,marker,notes\n"

        with open(self.csv_path, "w") as f:
            f.write(csv_content)

        report = cue_observatory.generate_report(self.csv_path)
        # Check summary statistics (markdown format)
        self.assertIn("**Total cues:** 0", report)
        self.assertIn("**Duration:** 00:00:00", report)
        self.assertIn("**Transitions:** 0", report)
        self.assertIn("**Simultaneous groups:** 0", report)

    def test_handles_malformed_time(self) -> None:
        """Handle malformed time gracefully with a warning."""
        csv_content = """cue,time,marker,notes
Cue 1,00:00:00,start,"Valid"
Cue 2,invalid-time,transition,"Invalid time"
Cue 3,00:10:00,end,"Valid"
"""

        with open(self.csv_path, "w") as f:
            f.write(csv_content)

        report = cue_observatory.generate_report(self.csv_path)

        self.assertIn("**Total cues:** 3", report)
        self.assertIn("Cue 2", report)
        self.assertTrue("warning" in report.lower() or "invalid" in report.lower())

    def test_detects_high_density_periods(self) -> None:
        """Detect periods with high cue density."""
        csv_content = """cue,time,marker,notes
Cue 1,00:00:00,start,"Start"
Cue 2,00:00:30,transition,"Quick"
Cue 3,00:01:00,transition,"Quick"
Cue 4,00:01:30,transition,"Quick"
Cue 5,00:05:00,end,"Slow"
"""

        with open(self.csv_path, "w") as f:
            f.write(csv_content)

        report = cue_observatory.generate_report(self.csv_path)

        self.assertIn("Density", report)
        self.assertTrue("high" in report.lower() or "peak" in report.lower())

    def test_outputs_json_when_requested(self) -> None:
        """Support JSON output format for machine consumption."""
        csv_content = """cue,time,marker,notes
Cue 1,00:00:00,start,"Start"
Cue 2,00:05:00,end,"End"
"""

        with open(self.csv_path, "w") as f:
            f.write(csv_content)

        report = cue_observatory.generate_report(self.csv_path, format="json")

        data = json.loads(report)
        self.assertIn("summary", data)
        self.assertIn("timeline", data)
        self.assertIn("density_analysis", data)
        self.assertIn("simultaneous_cues", data)
        self.assertIn("vigilance_points", data)
        self.assertEqual(data["summary"]["total_cues"], 2)


if __name__ == "__main__":
    unittest.main()