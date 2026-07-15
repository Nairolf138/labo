"""Compile generic light scenes into capability-safe commands."""

from __future__ import annotations


PROPERTY_CAPABILITIES = {
    "brightness": "brightness",
    "color_temperature": "color_temperature",
    "hue": "hs_color",
    "saturation": "hs_color",
}


def _is_number(value: object) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _range_error(target: str, property_name: str, message: str) -> dict:
    return {
        "code": "value_out_of_range",
        "target": target,
        "property": property_name,
        "message": message,
    }


def _validate_requested_values(
    target: str, requested: dict, device: dict
) -> list[dict]:
    capabilities = device["capabilities"]
    errors = []
    if "brightness" in capabilities and "brightness" in requested:
        value = requested["brightness"]
        if not _is_number(value) or not 0 <= value <= 100:
            errors.append(
                _range_error(
                    target,
                    "brightness",
                    f"brightness for {target!r} must be between 0 and 100",
                )
            )
    if "color_temperature" in capabilities and "color_temperature" in requested:
        value = requested["color_temperature"]
        minimum, maximum = device.get("color_temperature_range", [1000, 10000])
        if not _is_number(value) or not minimum <= value <= maximum:
            errors.append(
                _range_error(
                    target,
                    "color_temperature",
                    f"color_temperature for {target!r} must be between "
                    f"{minimum} and {maximum}",
                )
            )
    if "hs_color" in capabilities and "hue" in requested:
        value = requested["hue"]
        if not _is_number(value) or not 0 <= value < 360:
            errors.append(
                _range_error(
                    target,
                    "hue",
                    f"hue for {target!r} must be at least 0 and less than 360",
                )
            )
    if "hs_color" in capabilities and "saturation" in requested:
        value = requested["saturation"]
        if not _is_number(value) or not 0 <= value <= 100:
            errors.append(
                _range_error(
                    target,
                    "saturation",
                    f"saturation for {target!r} must be between 0 and 100",
                )
            )
    return errors


def _compile_command(target: str, requested: dict, device: dict) -> dict:
    capabilities = device["capabilities"]
    command = {"target": target}
    if "brightness" in capabilities and "brightness" in requested:
        command["brightness"] = requested["brightness"]
    if "color_temperature" in capabilities and "color_temperature" in requested:
        command["color_temperature"] = requested["color_temperature"]
    if "hs_color" in capabilities:
        if "hue" in requested:
            command["hue"] = requested["hue"]
        if "saturation" in requested:
            command["saturation"] = requested["saturation"]
    return command


def compile_report(scene: dict, devices: dict) -> dict:
    """Compile valid targets and return deterministic warnings and errors."""
    if not isinstance(scene, dict) or not isinstance(scene.get("targets"), dict):
        return {
            "commands": [],
            "warnings": [],
            "errors": [
                {
                    "code": "invalid_scene",
                    "path": "targets",
                    "message": "scene must contain an object named 'targets'",
                }
            ],
        }
    if not isinstance(devices, dict):
        return {
            "commands": [],
            "warnings": [],
            "errors": [
                {
                    "code": "invalid_devices",
                    "path": "devices",
                    "message": "devices must be an object keyed by target name",
                }
            ],
        }
    commands = []
    warnings = []
    errors = []
    for target, requested in scene["targets"].items():
        if not isinstance(requested, dict):
            errors.append(
                {
                    "code": "invalid_scene",
                    "target": target,
                    "path": f"targets.{target}",
                    "message": f"properties requested for {target!r} must be an object",
                }
            )
            continue
        if target not in devices:
            errors.append(
                {
                    "code": "unknown_target",
                    "target": target,
                    "message": f"target {target!r} is not declared in devices",
                }
            )
            continue

        device = devices[target]
        if not isinstance(device, dict) or not isinstance(
            device.get("capabilities"), list
        ):
            errors.append(
                {
                    "code": "invalid_device",
                    "target": target,
                    "path": f"devices.{target}.capabilities",
                    "message": f"device {target!r} must declare a list of capabilities",
                }
            )
            continue
        capabilities = device["capabilities"]
        temperature_range = device.get("color_temperature_range", [1000, 10000])
        valid_temperature_range = (
            isinstance(temperature_range, list)
            and len(temperature_range) == 2
            and all(_is_number(value) for value in temperature_range)
            and temperature_range[0] <= temperature_range[1]
        )
        if (
            "color_temperature" in capabilities
            and not valid_temperature_range
        ):
            errors.append(
                {
                    "code": "invalid_device",
                    "target": target,
                    "path": f"devices.{target}.color_temperature_range",
                    "message": (
                        f"device {target!r} must declare an ascending two-number "
                        "color_temperature_range"
                    ),
                }
            )
            continue
        target_errors = _validate_requested_values(target, requested, device)
        errors.extend(target_errors)
        if device.get("available", True) is False:
            warnings.append(
                {
                    "code": "target_unavailable",
                    "target": target,
                    "message": f"target {target!r} is unavailable; command omitted",
                }
            )
        for property_name in requested:
            required = PROPERTY_CAPABILITIES.get(property_name)
            if required not in capabilities:
                warnings.append(
                    {
                        "code": "unsupported_property",
                        "target": target,
                        "property": property_name,
                        "message": (
                            f"{target!r} does not support {property_name!r}; "
                            "property omitted"
                        ),
                    }
                )
        if not target_errors and device.get("available", True) is not False:
            commands.append(_compile_command(target, requested, device))

    return {"commands": commands, "warnings": warnings, "errors": errors}


def compile_scene(scene: dict, devices: dict) -> list[dict]:
    """Return commands containing only properties supported by each target.

    This compatibility API raises on invalid supported values. Use ``compile_report``
    when diagnostics and partial compilation are required.
    """
    commands = []
    for target, requested in scene["targets"].items():
        device = devices[target]
        if device.get("available", True) is False:
            continue
        errors = _validate_requested_values(target, requested, device)
        if errors:
            raise ValueError(errors[0]["message"])
        commands.append(_compile_command(target, requested, device))
    return commands
