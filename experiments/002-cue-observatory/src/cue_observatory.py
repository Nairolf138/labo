"""Generate a Markdown report from a CSV of lighting cues."""

from __future__ import annotations

import csv
import json
from collections import defaultdict
from datetime import timedelta
from pathlib import Path
from typing import Any


def parse_time(time_str: str) -> timedelta | None:
    """Parse HH:MM:SS time string to timedelta. Returns None if invalid."""
    try:
        parts = time_str.split(":")
        if len(parts) != 3:
            return None
        hours, minutes, seconds = map(int, parts)
        return timedelta(hours=hours, minutes=minutes, seconds=seconds)
    except (ValueError, AttributeError):
        return None


def format_timedelta(td: timedelta) -> str:
    """Format timedelta as HH:MM:SS."""
    total_seconds = int(td.total_seconds())
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"


def parse_csv(csv_path: str) -> tuple[list[dict[str, Any]], list[str]]:
    """Parse CSV file and return list of cue dictionaries with parsed times."""
    cues = []
    warnings = []

    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader):
            cue = {
                "cue": row.get("cue", f"Cue {i + 1}"),
                "time_str": row.get("time", ""),
                "marker": row.get("marker", ""),
                "notes": row.get("notes", ""),
                "time": parse_time(row.get("time", "")),
                "index": i,
            }
            if cue["time"] is None:
                warnings.append(
                    f"Warning: Cue '{cue['cue']}' has invalid time '{cue['time_str']}'; treated as 00:00:00"
                )
                cue["time"] = timedelta(0)
            cues.append(cue)

    # Add time_remaining to each cue (time until next cue)
    sorted_cues = sorted(cues, key=lambda c: c["time"])
    for i, cue in enumerate(sorted_cues):
        if i < len(sorted_cues) - 1:
            next_time = sorted_cues[i + 1]["time"]
            remaining = next_time - cue["time"]
            cue["time_remaining"] = format_timedelta(remaining)
        else:
            # Last cue has no remaining time
            cue["time_remaining"] = "00:00:00"

    # Return sorted cues so time_remaining is preserved
    return sorted_cues, warnings


def analyze_density(cues: list[dict], window_seconds: int = 60) -> list[dict]:
    """Analyze cue density in sliding windows."""
    if not cues:
        return []

    # Sort cues by time
    sorted_cues = sorted(cues, key=lambda c: c["time"])
    max_time = sorted_cues[-1]["time"].total_seconds()
    window = timedelta(seconds=window_seconds)

    density_periods = []
    current_window_start = timedelta(0)

    while current_window_start.total_seconds() <= max_time:
        window_end = current_window_start + window
        cues_in_window = [
            c
            for c in sorted_cues
            if current_window_start <= c["time"] < window_end
        ]

        if cues_in_window:
            density_periods.append(
                {
                    "window_start": format_timedelta(current_window_start),
                    "window_end": format_timedelta(window_end),
                    "cue_count": len(cues_in_window),
                    "cues": [c["cue"] for c in cues_in_window],
                }
            )

        current_window_start += timedelta(seconds=window_seconds // 2)  # 50% overlap

    # Find peak density
    if density_periods:
        max_density = max(d["cue_count"] for d in density_periods)
        for d in density_periods:
            d["is_peak"] = d["cue_count"] == max_density
            d["level"] = "high" if d["cue_count"] >= max_density * 0.7 else "normal"

    return density_periods


def find_simultaneous_cues(cues: list[dict], tolerance: timedelta = timedelta(seconds=1)) -> list[list[dict]]:
    """Find groups of cues that occur at the same time (within tolerance)."""
    if not cues:
        return []

    sorted_cues = sorted(cues, key=lambda c: c["time"])
    groups = []
    current_group = [sorted_cues[0]]

    for cue in sorted_cues[1:]:
        if cue["time"] - current_group[-1]["time"] <= tolerance:
            current_group.append(cue)
        else:
            if len(current_group) > 1:
                groups.append(current_group)
            current_group = [cue]

    if len(current_group) > 1:
        groups.append(current_group)

    return groups


def identify_vigilance_points(cues: list[dict], density_periods: list[dict]) -> list[dict]:
    """Identify vigilance points for a lighting operator."""
    vigilance_points = []

    for cue in cues:
        points = []

        # Check marker type
        marker = cue["marker"].lower()
        if marker in ("start", "end"):
            points.append(f"Key moment: {marker}")
        elif marker == "transition":
            points.append("Transition - verify timing")
        elif marker == "simultaneous":
            points.append("Simultaneous cue - confirm all fire together")

        # Check if applicable

        # Check density
        for dp in density_periods:
            cue_time = cue["time"].total_seconds()
            window_start = sum(int(x) * 60**i for i, x in enumerate(reversed(dp["window_start"].split(":"))))
            window_end = sum(int(x) * 60**i for i, x in enumerate(reversed(dp["window_end"].split(":"))))
            if window_start <= cue_time < window_end and dp.get("is_peak", False):
                points.append(f"High cue density period ({dp['cue_count']} cues/min)")
                break

        # Check if part of simultaneous group
        simultaneous_groups = find_simultaneous_cues(cues)
        for group in simultaneous_groups:
            if cue in group and len(group) > 1:
                other_cues = [c["cue"] for c in group if c != cue]
                points.append(f"Simultaneous with: {', '.join(other_cues)}")
                break

        if points:
            vigilance_points.append(
                {
                    "cue": cue["cue"],
                    "time": format_timedelta(cue["time"]),
                    "points": points,
                }
            )

    return vigilance_points


def generate_markdown_report(
    cues: list[dict],
    warnings: list[str],
    density_periods: list[dict],
    simultaneous_groups: list[list[dict]],
    vigilance_points: list[dict],
) -> str:
    """Generate a Markdown report from analyzed data."""
    lines = []

    # Header
    lines.append("# Cue Observatory Report")
    lines.append("")

    # Summary
    lines.append("## Summary")
    lines.append("")
    total_cues = len(cues)
    if total_cues > 0:
        start_time = min(c["time"] for c in cues)
        end_time = max(c["time"] for c in cues)
        duration = end_time - start_time
        transitions = sum(1 for c in cues if c["marker"].lower() == "transition")
        simultaneous_count = sum(len(g) for g in simultaneous_groups)
    else:
        duration = timedelta(0)
        transitions = 0
        simultaneous_count = 0

    lines.append(f"- **Total cues:** {total_cues}")
    lines.append(f"- **Duration:** {format_timedelta(duration)}")
    lines.append(f"- **Transitions:** {transitions}")
    lines.append(f"- **Simultaneous groups:** {len(simultaneous_groups)}")
    lines.append(f"- **Warnings:** {len(warnings)}")
    lines.append("")

    # Warnings
    if warnings:
        lines.append("## Warnings")
        lines.append("")
        for w in warnings:
            lines.append(f"- {w}")
        lines.append("")

    # Timeline
    lines.append("## Timeline")
    lines.append("")
    lines.append("| Cue | Time | Time Remaining | Marker | Notes |")
    lines.append("|-----|------|----------------|--------|-------|")
    for cue in sorted(cues, key=lambda c: c["time"]):
        time_remaining = cue.get("time_remaining", "N/A")
        lines.append(f"| {cue['cue']} | {format_timedelta(cue['time'])} | {time_remaining} | {cue['marker']} | {cue['notes']} |")
    lines.append("")

    # Density Analysis
    lines.append("## Density Analysis")
    lines.append("")
    if density_periods:
        lines.append("| Window | Cues | Level |")
        lines.append("|--------|------|-------|")
        for dp in density_periods:
            peak_marker = " 🔴" if dp.get("is_peak", False) else ""
            lines.append(f"| {dp['window_start']} – {dp['window_end']} | {dp['cue_count']} | {dp['level']}{peak_marker} |")
    else:
        lines.append("*No cues to analyze.*")
    lines.append("")

    # Simultaneous Cues
    lines.append("## Simultaneous Cues")
    lines.append("")
    if simultaneous_groups:
        for i, group in enumerate(simultaneous_groups, 1):
            lines.append(f"### Group {i}")
            lines.append("")
            lines.append(f"**Time:** {format_timedelta(group[0]['time'])}")
            lines.append("")
            lines.append("| Cue | Marker | Notes |")
            lines.append("|-----|--------|-------|")
            for cue in group:
                lines.append(f"| {cue['cue']} | {cue['marker']} | {cue['notes']} |")
            lines.append("")
            lines.append("⚠️ **Vigilance:** All cues in this group fire simultaneously. Verify all channels.")
            lines.append("")
    else:
        lines.append("*No simultaneous cues detected.*")
        lines.append("")

    # Vigilance Points
    lines.append("## Vigilance Points")
    lines.append("")
    if vigilance_points:
        for vp in vigilance_points:
            lines.append(f"### {vp['cue']} ({vp['time']})")
            lines.append("")
            for point in vp["points"]:
                lines.append(f"- {point}")
            lines.append("")
    else:
        lines.append("*No specific vigilance points identified.*")
        lines.append("")

    return "\n".join(lines)


def generate_json_report(
    cues: list[dict],
    warnings: list[str],
    density_periods: list[dict],
    simultaneous_groups: list[list[dict]],
    vigilance_points: list[dict],
) -> dict:
    """Generate a JSON report from analyzed data."""
    total_cues = len(cues)
    if total_cues > 0:
        start_time = min(c["time"] for c in cues)
        end_time = max(c["time"] for c in cues)
        duration = end_time - start_time
        transitions = sum(1 for c in cues if c["marker"].lower() == "transition")
    else:
        duration = timedelta(0)
        transitions = 0

    return {
        "summary": {
            "total_cues": total_cues,
            "duration": format_timedelta(duration),
            "transitions": transitions,
            "simultaneous_groups": len(simultaneous_groups),
            "warnings": len(warnings),
        },
        "warnings": warnings,
        "timeline": [
            {
                "cue": c["cue"],
                "time": format_timedelta(c["time"]),
                "marker": c["marker"],
                "notes": c["notes"],
                "time_remaining": c.get("time_remaining", "00:00:00"),
            }
            for c in sorted(cues, key=lambda c: c["time"])
        ],
        "density_analysis": density_periods,
        "simultaneous_cues": [
            {
                "time": format_timedelta(g[0]["time"]),
                "cues": [
                    {"cue": c["cue"], "marker": c["marker"], "notes": c["notes"]}
                    for c in g
                ],
            }
            for g in simultaneous_groups
        ],
        "vigilance_points": vigilance_points,
    }


def generate_report(csv_path: str, format: str = "markdown") -> str:
    """Generate a cue observatory report from a CSV file.

    Args:
        csv_path: Path to the CSV file containing cues.
        format: Output format - "markdown" or "json".

    Returns:
        Report as a string (Markdown or JSON).
    """
    cues, warnings = parse_csv(csv_path)
    density_periods = analyze_density(cues)
    simultaneous_groups = find_simultaneous_cues(cues)
    vigilance_points = identify_vigilance_points(cues, density_periods)

    if format == "json":
        report = generate_json_report(
            cues, warnings, density_periods, simultaneous_groups, vigilance_points
        )
        return json.dumps(report, indent=2)
    else:
        return generate_markdown_report(
            cues, warnings, density_periods, simultaneous_groups, vigilance_points
        )


def main() -> int:
    """CLI entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Generate a Cue Observatory report from a CSV file.")
    parser.add_argument("csv", help="Path to CSV file with cues")
    parser.add_argument("--format", choices=["markdown", "json"], default="markdown", help="Output format")
    parser.add_argument("--output", "-o", help="Output file (default: stdout)")
    args = parser.parse_args()

    try:
        report = generate_report(args.csv, format=args.format)
        if args.output:
            Path(args.output).write_text(report, encoding="utf-8")
        else:
            print(report)
        return 0
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(main())