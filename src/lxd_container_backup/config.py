"""Load and validate backup settings."""

from dataclasses import dataclass
from pathlib import Path

CONTAINER_SETTINGS = {"CONTAINER_NAME", "CONTAINER_NAMES"}
REQUIRED_PATH_SETTINGS = {"LXD_CONTAINERS_PATH", "BACKUP_ROOT"}
ALLOWED_SETTINGS = CONTAINER_SETTINGS | REQUIRED_PATH_SETTINGS
DEFAULT_CONFIG_PATH = (
    Path(__file__).resolve().parents[2] / "config" / "backup.env"
)


@dataclass(frozen=True)
class BackupConfig:
    """Settings needed to copy one container directory."""

    container_name: str
    containers_path: Path
    backup_root: Path
    container_names: tuple[str, ...] = ()

    @property
    def workspaces(self) -> tuple[str, ...]:
        """Return all configured names, including legacy single-name configs."""
        return self.container_names or (self.container_name,)


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
        if key not in ALLOWED_SETTINGS:
            raise ValueError(f"{config_path}:{line_number}: unknown setting {key!r}")
        if key in settings:
            raise ValueError(f"{config_path}:{line_number}: duplicate setting {key!r}")
        settings[key] = value

    missing = REQUIRED_PATH_SETTINGS - settings.keys()
    if missing:
        raise ValueError(f"{config_path}: missing setting(s): {', '.join(sorted(missing))}")

    has_single_name = "CONTAINER_NAME" in settings
    has_multiple_names = "CONTAINER_NAMES" in settings
    if has_single_name and has_multiple_names:
        raise ValueError(
            f"{config_path}: use either CONTAINER_NAME or CONTAINER_NAMES, not both"
        )
    if not has_single_name and not has_multiple_names:
        raise ValueError(
            f"{config_path}: missing setting: CONTAINER_NAME or CONTAINER_NAMES"
        )

    if has_multiple_names:
        container_names = tuple(
            name.strip() for name in settings["CONTAINER_NAMES"].split(",")
        )
        if any(not name for name in container_names):
            raise ValueError(
                f"{config_path}: CONTAINER_NAMES must contain non-empty comma-separated names"
            )
        if len(set(container_names)) != len(container_names):
            raise ValueError(f"{config_path}: CONTAINER_NAMES contains duplicates")
    else:
        container_names = (settings["CONTAINER_NAME"],)

    return BackupConfig(
        container_name=container_names[0],
        containers_path=Path(settings["LXD_CONTAINERS_PATH"]).expanduser(),
        backup_root=Path(settings["BACKUP_ROOT"]).expanduser(),
        container_names=container_names,
    )
