#!/usr/bin/env python3
"""Compile a synthetic light scene from JSON files."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from light_protocol import compile_report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--devices", required=True, type=Path)
    parser.add_argument("--scene", required=True, type=Path)
    parser.add_argument(
        "--strict",
        action="store_true",
        help="return exit status 2 when compilation reports an error",
    )
    args = parser.parse_args()

    devices = json.loads(args.devices.read_text(encoding="utf-8"))
    scene = json.loads(args.scene.read_text(encoding="utf-8"))
    report = compile_report(scene, devices)
    print(json.dumps(report, indent=2))
    if args.strict and report["errors"]:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
