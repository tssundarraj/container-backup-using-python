# LXD container directory backup

A small installable Python package that uses `rsync` to copy a configured LXD
container directory, or multiple workspace directories, into timestamped
backup folders. It does not use `lxc export`.

## Quick start

```bash
if [ ! -f config/backup.env ]; then
    cp config/backup.env.example config/backup.env
fi
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e .
lxd-container-backup --config config/backup.env
```

Install Python 3.9+ and `rsync` on the machine that can access the container
directory. Edit `config/backup.env` to choose the container and paths. The
virtual environment is optional; it isolates Python development tools. The
program also writes to `/var/log/backup.log`, so the account running it must
be able to write that file (normally root on Linux).

To back up multiple workspace directories, list them comma-separated in
`CONTAINER_NAMES` in `config/backup.env`. The older single-name
`CONTAINER_NAME` setting remains supported.

See [docs/INSTALLATION.md](docs/INSTALLATION.md) for setup and distribution.
See [docs/COMMAND_GUIDE.md](docs/COMMAND_GUIDE.md) for how the
`lxd-container-backup` command works and how to run it.
See [docs/DAILY_BACKUP_LINUX.md](docs/DAILY_BACKUP_LINUX.md) to schedule
automatic daily backups with systemd or cron.
The [Python developer guide](docs/PYTHON_LEARNING.md) explains each module,
the call flow, how to build the package from scratch, and how to add a module.
See [docs/GITHUB_AND_VERSIONING.md](docs/GITHUB_AND_VERSIONING.md) to publish
the project and manage package versions.

## Files

```text
src/lxd_container_backup/  Config, logging, workspace, rsync, and CLI modules
config/                    Local settings and example
docs/                      Installation, command, scheduling, and learning guides
setup.cfg                   Package metadata and command entry point
pyproject.toml              Build backend
requirements.txt            Runtime notes; no pip packages required
```
