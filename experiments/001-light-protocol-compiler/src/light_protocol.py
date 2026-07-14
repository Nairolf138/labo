"""Compile generic light scenes into capability-safe commands."""

from __future__ import annotations


def compile_scene(scene: dict, devices: dict) -> list[dict]:
    """Return commands containing only properties supported by each target."""
    commands = []
    for target, requested in scene["targets"].items():
        device = devices[target]
        if device.get("available", True) is False:
            continue
        capabilities = device["capabilities"]
        command = {"target": target}
        if "brightness" in capabilities and "brightness" in requested:
            brightness = requested["brightness"]
            valid_number = isinstance(brightness, (int, float)) and not isinstance(
                brightness, bool
            )
            if not valid_number or not 0 <= brightness <= 100:
                raise ValueError(
                    f"brightness for {target!r} must be between 0 and 100"
                )
            command["brightness"] = brightness
        if "color_temperature" in capabilities and "color_temperature" in requested:
            command["color_temperature"] = requested["color_temperature"]
        if "hs_color" in capabilities:
            if "hue" in requested:
                command["hue"] = requested["hue"]
            if "saturation" in requested:
                command["saturation"] = requested["saturation"]
        commands.append(command)
    return commands
