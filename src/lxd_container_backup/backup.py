"""Copy LXD container directories using rsync."""

import os
import re
import shutil
import subprocess
import sys
from datetime import datetime

from .config import BackupConfig


def backup_container(config: BackupConfig) -> int:
    """Copy one container directory and return rsync's exit status."""
    name = config.container_name
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]*", name):
        raise ValueError("invalid container name")

    source_path = config.containers_path / name
    if not source_path.is_dir():
        raise FileNotFoundError(f"container directory not found: {source_path}")

    rsync_path = shutil.which("rsync")
    if rsync_path is None:
        raise FileNotFoundError("rsync was not found; install it and try again")

    backup_dir = config.backup_root / name
    source_real = source_path.resolve()
    backup_real = backup_dir.resolve()
    if backup_real == source_real or source_real in backup_real.parents:
        raise ValueError("backup directory must not be inside the source container directory")

    destination_path = backup_dir / datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    destination_path.mkdir(parents=True)
    command = [
        rsync_path,
        "-aHAX",
        "--numeric-ids", "--human-readable", "--info=progress2",
        "--",
        f"{source_path}{os.sep}",
        f"{destination_path}{os.sep}",
    ]
    print(f"Copying {source_path} to {destination_path}")
    result = subprocess.run(command, check=False)
    if result.returncode != 0:
        print(
            f"rsync failed with exit code {result.returncode}; "
            f"the destination may be incomplete: {destination_path}",
            file=sys.stderr,
        )
        return result.returncode
    print(f"Backup completed: {destination_path}")
    return 0
