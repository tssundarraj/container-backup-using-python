"""Back up all workspaces configured for the LXD container backup."""

import logging
import sys
from dataclasses import replace

from .backup import backup_container
from .config import BackupConfig

logger = logging.getLogger(__name__)


def backup_workspaces(config: BackupConfig) -> int:
    """Back up every configured workspace and return the first failure status."""
    exit_status = 0
    workspaces = config.workspaces

    for workspace in workspaces:
        workspace_config = replace(
            config,
            container_name=workspace,
            container_names=(workspace,),
        )
        try:
            status = backup_container(workspace_config)
        except (OSError, ValueError) as error:
            logger.error("Backup failed for workspace %s: %s", workspace, error)
            print(f"Backup failed for workspace {workspace}: {error}", file=sys.stderr)
            status = 2

        if status != 0 and exit_status == 0:
            exit_status = status

    if exit_status == 0:
        logger.info("All %d workspace backups completed", len(workspaces))
    else:
        logger.error(
            "One or more workspace backups failed; returning exit status %s",
            exit_status,
        )
    return exit_status
