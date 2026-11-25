"""Command-line entry point for the backup package."""

import argparse
import sys
from pathlib import Path
from typing import Optional, Sequence

from .config import DEFAULT_CONFIG_PATH, load_config
from .logging_config import LOG_FILE, configure_logging
from .workspace_backup import backup_workspaces


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
        logger = configure_logging()
    except OSError as error:
        print(f"Backup failed: cannot write log file {LOG_FILE}: {error}", file=sys.stderr)
        return 2

    logger.info("Backup command started with config %s", args.config)
    try:
        return backup_workspaces(load_config(args.config))
    except (OSError, ValueError) as error:
        logger.error("Backup failed: %s", error)
        print(f"Backup failed: {error}", file=sys.stderr)
        return 2
