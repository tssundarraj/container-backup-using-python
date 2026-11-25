"""Configure file logging for the backup command."""

import logging
from pathlib import Path

LOG_FILE = Path("/var/log/backup.log")
LOGGER_NAME = "lxd_container_backup"


def configure_logging(log_file: Path = LOG_FILE) -> logging.Logger:
    """Append package log messages to the configured log file."""
    log_file = log_file.resolve()
    log_file.parent.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger(LOGGER_NAME)
    logger.setLevel(logging.INFO)
    logger.propagate = False
    if not any(
        isinstance(handler, logging.FileHandler)
        and Path(handler.baseFilename) == log_file
        for handler in logger.handlers
    ):
        handler = logging.FileHandler(log_file, encoding="utf-8")
        handler.setFormatter(
            logging.Formatter(
                "%(asctime)s %(levelname)s %(name)s: %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
        )
        logger.addHandler(handler)
    return logger
