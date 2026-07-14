#!/usr/bin/env python3
"""Create an isolated, numbered laboratory experiment."""

from __future__ import annotations

import argparse
from datetime import date
from pathlib import Path
import re
import shutil


SLUG_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
NUMBERED_EXPERIMENT = re.compile(r"^(\d{3})-")


def next_identifier(experiments_dir: Path) -> int:
    """Return the next available numeric experiment identifier."""
    identifiers = []
    if experiments_dir.exists():
        for child in experiments_dir.iterdir():
            match = NUMBERED_EXPERIMENT.match(child.name)
            if child.is_dir() and match:
                identifiers.append(int(match.group(1)))
    return max(identifiers, default=-1) + 1


def create_experiment(
    root: Path,
    slug: str,
    title: str,
    *,
    dry_run: bool = False,
    today: date | None = None,
) -> Path:
    """Create an experiment from the repository template and return its path."""
    if not SLUG_PATTERN.fullmatch(slug):
        raise ValueError("slug must use lowercase letters, digits and single hyphens")

    experiments_dir = root / "experiments"
    template_dir = root / "templates" / "experiment"
    if not template_dir.is_dir():
        raise FileNotFoundError(f"template not found: {template_dir}")

    identifier = next_identifier(experiments_dir)
    target = experiments_dir / f"{identifier:03d}-{slug}"
    if target.exists():
        raise FileExistsError(target)
    if dry_run:
        return target

    shutil.copytree(template_dir, target)
    readme = target / "README.md"
    rendered = (
        readme.read_text(encoding="utf-8")
        .replace("{{ID}}", f"{identifier:03d}")
        .replace("{{TITLE}}", title)
        .replace("{{DATE}}", str(today or date.today()))
    )
    readme.write_text(rendered, encoding="utf-8")
    return target


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("slug", help="lowercase slug, for example cue-observatory")
    parser.add_argument("--title", required=True, help="human-readable experiment title")
    parser.add_argument("--dry-run", action="store_true", help="show the future path without writing")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    root = Path(__file__).resolve().parents[1]
    target = create_experiment(root, args.slug, args.title, dry_run=args.dry_run)
    verb = "Would create" if args.dry_run else "Created"
    print(f"{verb}: {target.relative_to(root)}")


if __name__ == "__main__":
    main()
