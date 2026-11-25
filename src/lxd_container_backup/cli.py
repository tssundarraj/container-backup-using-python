"""Command-line entry point for the backup package."""

import argparse
import sys
from pathlib import Path
from typing import Optional, Sequence

from .backup import backup_container
from .config import DEFAULT_CONFIG_PATH, load_config


def main(argv: Optional[Sequence[str]] = None) -> int:
    """Parse command-line options and run one backup."""
    parser = argparse.ArgumentParser(description="Copy an LXD container directory with rsync.")
    parser.add_argument(
        "--config",
        type=Path,
        default=DEFAULT_CONFIG_PATH,
        help=f"settings file (default: {DEFAULT_CONFIG_PATH})",
    )
    args = parser.parse_args(argv)

    try:
        return backup_container(load_config(args.config))
    except (OSError, ValueError) as error:
        print(f"Backup failed: {error}", file=sys.stderr)
        return 2
