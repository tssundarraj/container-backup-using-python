"""Load and validate backup settings."""

from dataclasses import dataclass
from pathlib import Path

REQUIRED_SETTINGS = {"CONTAINER_NAME", "LXD_CONTAINERS_PATH", "BACKUP_ROOT"}
DEFAULT_CONFIG_PATH = (
    Path(__file__).resolve().parents[2] / "config" / "backup.env"
)


@dataclass(frozen=True)
class BackupConfig:
    """Settings needed to copy one container directory."""

    container_name: str
    containers_path: Path
    backup_root: Path


def load_config(config_path: Path) -> BackupConfig:
    """Read a KEY=VALUE config file and return validated backup settings."""
    settings = {}
    for line_number, raw_line in enumerate(
        config_path.read_text(encoding="utf-8").splitlines(), start=1
    ):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue

        key, separator, value = line.partition("=")
        key, value = key.strip(), value.strip()
        if not separator or not value:
            raise ValueError(f"{config_path}:{line_number}: expected non-empty KEY=VALUE")
        if key not in REQUIRED_SETTINGS:
            raise ValueError(f"{config_path}:{line_number}: unknown setting {key!r}")
        if key in settings:
            raise ValueError(f"{config_path}:{line_number}: duplicate setting {key!r}")
        settings[key] = value

    missing = REQUIRED_SETTINGS - settings.keys()
    if missing:
        raise ValueError(f"{config_path}: missing setting(s): {', '.join(sorted(missing))}")

    return BackupConfig(
        container_name=settings["CONTAINER_NAME"],
        containers_path=Path(settings["LXD_CONTAINERS_PATH"]).expanduser(),
        backup_root=Path(settings["BACKUP_ROOT"]).expanduser(),
    )
