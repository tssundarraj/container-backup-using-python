# LXD container directory backup

A small installable Python package that uses `rsync` to copy a configured LXD
container directory into a timestamped backup folder. It does not use
`lxc export`.

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
virtual environment is optional; it isolates Python development tools.

See [docs/INSTALLATION.md](docs/INSTALLATION.md) for setup and distribution.
The [Python developer guide](docs/PYTHON_LEARNING.md) explains each module,
the call flow, how to build the package from scratch, and how to add a module.
See [docs/GITHUB_AND_VERSIONING.md](docs/GITHUB_AND_VERSIONING.md) to publish
the project and manage package versions.

## Files

```text
src/lxd_container_backup/  Config, rsync backup, and CLI modules
config/                    Local settings and example
docs/                      Installation and Python learning guides
setup.cfg                   Package metadata and command entry point
pyproject.toml              Build backend
requirements.txt            Runtime notes; no pip packages required
```
