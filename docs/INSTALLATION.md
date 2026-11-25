# Installation and distribution

The package copies a local LXD container directory with `rsync`. Run it on a
machine that can access the source path. This is a filesystem copy, not
`lxc export`.

## Requirements

- Python 3.9 or newer
- `rsync`, installed with your OS package manager
- Permission to read the container files and write to the backup directory.
  Preserving owners, ACLs, and extended attributes may require root.
- Enough free storage for another copy of the container

The Python code uses only the standard library. `requirements.txt` records the
Python version and system requirement for reference; pip cannot install Python
itself or the `rsync` executable. On Ubuntu or Debian:

```bash
sudo apt update
sudo apt install python3 python3-venv rsync
```

## Configure

From the project directory, create the local configuration from the example
once; this command keeps an existing config unchanged:

```bash
if [ ! -f config/backup.env ]; then
    cp config/backup.env.example config/backup.env
fi
```

Edit `config/backup.env`:

```dotenv
CONTAINER_NAME=admin---demo-workspaces
LXD_CONTAINERS_PATH=/var/snap/lxd/common/lxd/storage-pools/local/containers
BACKUP_ROOT=/root/sundar/lxd-container-backup
```

The local config is ignored by Git. Change `CONTAINER_NAME` to select a
different container. These are plain `KEY=VALUE` settings; do not quote them.

## Install for development

A virtual environment is optional, but recommended so project tooling stays
separate from system Python:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e .
```

The editable install lets developers change the modules and run the updated
package immediately. There are no third-party runtime dependencies. To exit
the environment, run `deactivate`.

## Run

From the project directory:

```bash
lxd-container-backup --config config/backup.env
```

You can also run from the source checkout without installing:

```bash
PYTHONPATH=src python3 -m lxd_container_backup --config config/backup.env
```

The CLI accepts another config path with `--config`, which is useful when
installing the package for a system service:

```bash
lxd-container-backup --config /etc/lxd-container-backup/backup.env
```

The command prints the destination on success. Each run creates a new folder:

```text
BACKUP_ROOT/CONTAINER_NAME/YYYYMMDD_HHMMSS_microseconds/
```

If rsync fails, the destination may contain a partial copy. Inspect it before
deciding whether to remove it.

## Share with another developer

Share or clone the project directory, including `pyproject.toml`, `setup.cfg`,
`setup.py`, `src/`, `config/backup.env.example`, and `docs/`. Do not share
your local `config/backup.env` unless its paths and settings are intended for
them. Developers can create their own config, make a virtual environment, and
run `python -m pip install -e .` to work on the modules.

## Limitations

This copies only the configured container directory. It does not copy LXD
configuration, snapshots, or storage-pool metadata, and may not be sufficient
to restore a working LXD container.

Files may change during the copy if the container is running. Databases and
other stateful applications may require application-aware backups. Stop the
container first for a point-in-time filesystem copy if downtime is acceptable.
