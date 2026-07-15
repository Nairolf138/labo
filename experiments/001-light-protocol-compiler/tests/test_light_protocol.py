"""Behavior tests for the light protocol compiler."""

from pathlib import Path
import json
import subprocess
import sys
import tempfile
import unittest


SRC = Path(__file__).parents[1] / "src"
sys.path.insert(0, str(SRC))

import light_protocol  # noqa: E402
from light_protocol import compile_scene  # noqa: E402


class CompileReportTest(unittest.TestCase):
    def test_reports_unsupported_properties_while_compiling_supported_ones(self) -> None:
        devices = {"desk": {"capabilities": ["brightness"]}}
        scene = {"targets": {"desk": {"brightness": 70, "hue": 30}}}

        report = light_protocol.compile_report(scene, devices)

        self.assertEqual(report["commands"], [{"target": "desk", "brightness": 70}])
        self.assertEqual(report["errors"], [])
        self.assertEqual(
            report["warnings"],
            [
                {
                    "code": "unsupported_property",
                    "target": "desk",
                    "property": "hue",
                    "message": "'desk' does not support 'hue'; property omitted",
                }
            ],
        )

    def test_reports_an_unknown_target_without_blocking_known_targets(self) -> None:
        devices = {"desk": {"capabilities": ["brightness"]}}
        scene = {
            "targets": {
                "missing": {"brightness": 90},
                "desk": {"brightness": 25},
            }
        }

        report = light_protocol.compile_report(scene, devices)

        self.assertEqual(report["commands"], [{"target": "desk", "brightness": 25}])
        self.assertEqual(report["warnings"], [])
        self.assertEqual(
            report["errors"],
            [
                {
                    "code": "unknown_target",
                    "target": "missing",
                    "message": "target 'missing' is not declared in devices",
                }
            ],
        )

    def test_reports_invalid_hue_and_omits_only_its_target_command(self) -> None:
        devices = {
            "stage": {"capabilities": ["hs_color"]},
            "desk": {"capabilities": ["brightness"]},
        }
        scene = {
            "targets": {
                "stage": {"hue": 360, "saturation": 50},
                "desk": {"brightness": 30},
            }
        }

        report = light_protocol.compile_report(scene, devices)

        self.assertEqual(report["commands"], [{"target": "desk", "brightness": 30}])
        self.assertEqual(report["warnings"], [])
        self.assertEqual(
            report["errors"],
            [
                {
                    "code": "value_out_of_range",
                    "target": "stage",
                    "property": "hue",
                    "message": "hue for 'stage' must be at least 0 and less than 360",
                }
            ],
        )

    def test_collects_all_supported_property_range_errors_for_a_target(self) -> None:
        devices = {
            "stage": {
                "capabilities": ["brightness", "color_temperature", "hs_color"],
                "color_temperature_range": [2200, 6500],
            }
        }
        scene = {
            "targets": {
                "stage": {
                    "brightness": True,
                    "color_temperature": 7000,
                    "hue": 120,
                    "saturation": 101,
                }
            }
        }

        report = light_protocol.compile_report(scene, devices)

        self.assertEqual(report["commands"], [])
        self.assertEqual(
            [(error["property"], error["code"]) for error in report["errors"]],
            [
                ("brightness", "value_out_of_range"),
                ("color_temperature", "value_out_of_range"),
                ("saturation", "value_out_of_range"),
            ],
        )
        self.assertIn("between 0 and 100", report["errors"][0]["message"])
        self.assertIn("between 2200 and 6500", report["errors"][1]["message"])
        self.assertIn("between 0 and 100", report["errors"][2]["message"])

    def test_reports_a_malformed_scene_instead_of_raising(self) -> None:
        report = light_protocol.compile_report({"name": "broken"}, {})

        self.assertEqual(report["commands"], [])
        self.assertEqual(report["warnings"], [])
        self.assertEqual(
            report["errors"],
            [
                {
                    "code": "invalid_scene",
                    "path": "targets",
                    "message": "scene must contain an object named 'targets'",
                }
            ],
        )

    def test_reports_an_invalid_device_without_blocking_valid_devices(self) -> None:
        devices = {
            "broken": {"available": True},
            "desk": {"capabilities": ["brightness"]},
        }
        scene = {
            "targets": {
                "broken": {"brightness": 80},
                "desk": {"brightness": 20},
            }
        }

        report = light_protocol.compile_report(scene, devices)

        self.assertEqual(report["commands"], [{"target": "desk", "brightness": 20}])
        self.assertEqual(
            report["errors"],
            [
                {
                    "code": "invalid_device",
                    "target": "broken",
                    "path": "devices.broken.capabilities",
                    "message": "device 'broken' must declare a list of capabilities",
                }
            ],
        )

    def test_explains_why_an_unavailable_target_was_omitted(self) -> None:
        devices = {
            "offline": {"capabilities": ["brightness"], "available": False}
        }
        scene = {"targets": {"offline": {"brightness": 100}}}

        report = light_protocol.compile_report(scene, devices)

        self.assertEqual(report["commands"], [])
        self.assertEqual(report["errors"], [])
        self.assertEqual(
            report["warnings"],
            [
                {
                    "code": "target_unavailable",
                    "target": "offline",
                    "message": "target 'offline' is unavailable; command omitted",
                }
            ],
        )

    def test_reports_a_target_whose_requested_properties_are_not_an_object(self) -> None:
        devices = {"desk": {"capabilities": ["brightness"]}}
        scene = {"targets": {"desk": ["brightness"]}}

        report = light_protocol.compile_report(scene, devices)

        self.assertEqual(report["commands"], [])
        self.assertEqual(
            report["errors"],
            [
                {
                    "code": "invalid_scene",
                    "target": "desk",
                    "path": "targets.desk",
                    "message": "properties requested for 'desk' must be an object",
                }
            ],
        )

    def test_reports_a_malformed_devices_document_instead_of_raising(self) -> None:
        scene = {"targets": {"desk": {"brightness": 50}}}

        report = light_protocol.compile_report(scene, ["not", "an", "object"])

        self.assertEqual(report["commands"], [])
        self.assertEqual(
            report["errors"],
            [
                {
                    "code": "invalid_devices",
                    "path": "devices",
                    "message": "devices must be an object keyed by target name",
                }
            ],
        )

    def test_rejects_an_inverted_color_temperature_range(self) -> None:
        devices = {
            "desk": {
                "capabilities": ["color_temperature"],
                "color_temperature_range": [6500, 2200],
            }
        }
        scene = {"targets": {"desk": {"color_temperature": 3000}}}

        report = light_protocol.compile_report(scene, devices)

        self.assertEqual(report["commands"], [])
        self.assertEqual(report["errors"][0]["code"], "invalid_device")
        self.assertEqual(
            report["errors"][0]["path"], "devices.desk.color_temperature_range"
        )


class CompileSceneTest(unittest.TestCase):
    def test_omits_color_for_a_tunable_white_light(self) -> None:
        devices = {
            "desk": {"capabilities": ["brightness", "color_temperature"]},
        }
        scene = {
            "targets": {
                "desk": {"brightness": 70, "hue": 30, "saturation": 80},
            }
        }

        commands = compile_scene(scene, devices)

        self.assertEqual(commands, [{"target": "desk", "brightness": 70}])

    def test_includes_hs_color_for_a_color_light(self) -> None:
        devices = {
            "stage": {"capabilities": ["brightness", "hs_color"]},
        }
        scene = {
            "targets": {
                "stage": {"brightness": 45, "hue": 210, "saturation": 65},
            }
        }

        commands = compile_scene(scene, devices)

        self.assertEqual(
            commands,
            [{"target": "stage", "brightness": 45, "hue": 210, "saturation": 65}],
        )

    def test_omits_an_unavailable_light(self) -> None:
        devices = {
            "offline": {"capabilities": ["brightness"], "available": False},
        }
        scene = {"targets": {"offline": {"brightness": 100}}}

        commands = compile_scene(scene, devices)

        self.assertEqual(commands, [])

    def test_includes_temperature_for_a_tunable_white_light(self) -> None:
        devices = {
            "reading": {"capabilities": ["brightness", "color_temperature"]},
        }
        scene = {
            "targets": {
                "reading": {"brightness": 80, "color_temperature": 3200},
            }
        }

        commands = compile_scene(scene, devices)

        self.assertEqual(
            commands,
            [{"target": "reading", "brightness": 80, "color_temperature": 3200}],
        )

    def test_rejects_brightness_outside_percent_range(self) -> None:
        devices = {"desk": {"capabilities": ["brightness"]}}
        scene = {"targets": {"desk": {"brightness": 101}}}

        with self.assertRaisesRegex(ValueError, "brightness"):
            compile_scene(scene, devices)


class CommandLineTest(unittest.TestCase):
    def test_compiles_json_files_to_standard_output(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            devices_path = root / "devices.json"
            scene_path = root / "scene.json"
            devices_path.write_text(
                json.dumps({"demo": {"capabilities": ["brightness"]}}),
                encoding="utf-8",
            )
            scene_path.write_text(
                json.dumps({"targets": {"demo": {"brightness": 25}}}),
                encoding="utf-8",
            )

            result = subprocess.run(
                [
                    sys.executable,
                    str(SRC / "main.py"),
                    "--devices",
                    str(devices_path),
                    "--scene",
                    str(scene_path),
                ],
                check=False,
                capture_output=True,
                text=True,
            )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(
            json.loads(result.stdout),
            {
                "commands": [{"target": "demo", "brightness": 25}],
                "warnings": [],
                "errors": [],
            },
        )

    def test_strict_mode_returns_nonzero_when_report_contains_errors(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            devices_path = root / "devices.json"
            scene_path = root / "scene.json"
            devices_path.write_text("{}", encoding="utf-8")
            scene_path.write_text(
                json.dumps({"targets": {"missing": {"brightness": 25}}}),
                encoding="utf-8",
            )

            result = subprocess.run(
                [
                    sys.executable,
                    str(SRC / "main.py"),
                    "--devices",
                    str(devices_path),
                    "--scene",
                    str(scene_path),
                    "--strict",
                ],
                check=False,
                capture_output=True,
                text=True,
            )

        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertEqual(json.loads(result.stdout)["errors"][0]["code"], "unknown_target")


if __name__ == "__main__":
    unittest.main()
