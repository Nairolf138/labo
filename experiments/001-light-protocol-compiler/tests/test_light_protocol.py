"""Behavior tests for the light protocol compiler."""

from pathlib import Path
import json
import subprocess
import sys
import tempfile
import unittest


SRC = Path(__file__).parents[1] / "src"
sys.path.insert(0, str(SRC))

from light_protocol import compile_scene  # noqa: E402


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
        self.assertEqual(json.loads(result.stdout), [{"target": "demo", "brightness": 25}])


if __name__ == "__main__":
    unittest.main()
