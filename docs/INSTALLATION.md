# Installation and running the backup

This guide explains how to prepare the project, configure it, and run a
container-directory backup. The program uses `rsync` to copy files; it does not
run `lxc export`.

> **Before running a backup:** check the container name, source path, backup
> destination, free space, and permissions in your config. Each successful run
> creates another copy and can use a large amount of disk space.

## 1. Requirements

Run the program on a Linux machine that can access the LXD container directory.
You need:

- Python 3.9 or newer
- `rsync`
- Read access to the container directory and write access to the backup
  destination
- Write access to `/var/log/backup.log` for the application log. On Linux,
  this normally means running the backup with suitable privileges.
- Enough free disk space for another copy of the container

On Ubuntu or Debian, install the system programs with:

```bash
sudo apt update
sudo apt install python3 python3-venv rsync
```

Check they are available:

```bash
python3 --version
rsync --version
```

`requirements.txt` documents these requirements. It intentionally contains no
pip packages: the Python code uses the standard library, and `rsync` must be
installed with the operating system package manager.

## 2. Open the project directory

Open a terminal and go to the directory containing `README.md`, `setup.cfg`,
and `src/`. Replace the example path with where you saved or cloned this
project:

```bash
cd /path/to/backup-code
```

Check that you are in the right place:

```bash
ls
```

You should see files such as `README.md`, `pyproject.toml`, `setup.cfg`, and
the folders `config/`, `docs/`, and `src/`.

## 3. Create and edit your local config

Create `config/backup.env` from the example once. If it already exists, this
command leaves it unchanged:

```bash
if [ ! -f config/backup.env ]; then
    cp config/backup.env.example config/backup.env
fi
```

Open `config/backup.env` in a text editor, for example:

```bash
nano config/backup.env
```

The example settings are:

```dotenv
CONTAINER_NAME=admin---demo-workspaces
LXD_CONTAINERS_PATH=/var/snap/lxd/common/lxd/storage-pools/local/containers
BACKUP_ROOT=/root/sundar/lxd-container-backup
```

- `CONTAINER_NAME` is the name of the container directory to copy.
- `LXD_CONTAINERS_PATH` is the **parent** folder containing container
  directories. The program adds `CONTAINER_NAME` to this path.
- `BACKUP_ROOT` is the parent folder where backup folders are created.

Use plain `KEY=VALUE` lines: do not add quotes or inline comments. Change the
values to match the machine where the program will run. For example, the
source directory for the shown settings is:

```text
/var/snap/lxd/common/lxd/storage-pools/local/containers/admin---demo-workspaces
```

The local `config/backup.env` is ignored by Git because it can contain
machine-specific paths. Share `config/backup.env.example`, not your local
config, unless you intend to share those settings.

## 4. Install the project

A virtual environment is optional but recommended. It keeps this project's
Python installation separate from system Python.

Create and activate one from the project directory:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install the package in editable mode:

```bash
python -m pip install -e .
```

Editable mode makes the `lxd-container-backup` command available in the
activated environment and uses the code in this checkout. When you open a new
terminal, activate the environment again with `source .venv/bin/activate`.
When finished, you can leave it with `deactivate`.

No separate `pip install -r requirements.txt` is needed; that file contains
documentation comments rather than Python package requirements.

## 5. Run the program

First, check that the command is installed and see its options. This does not
start a backup:

```bash
lxd-container-backup --help
```

Then run the backup from the project directory:

```bash
lxd-container-backup --config config/backup.env
```

The `--config` option tells the program which settings file to read. Always
pass it explicitly, especially when using an installed package or running
from another directory.

The command appends timestamped start, success, and failure messages to
`/var/log/backup.log`. The file is created on the first run. If the program
cannot create or write this file, it reports the error and does not start the
backup. `--help` does not create the log.

If you do not want to install the package, run it directly from the source
checkout instead:

```bash
PYTHONPATH=src python3 -m lxd_container_backup --config config/backup.env
```

`PYTHONPATH=src` lets Python find the package under `src/`. This command also
works as a direct check of the source checkout; it does not need the editable
install.

### Permissions

The process needs permission to read the container files and create the
destination. The rsync options also preserve owners, ACLs, and extended
attributes, which may require running with sufficient privileges. Prefer an
account that already has the required access. The default log path under
`/var/log` and the example backup path under `/root` are normally writable
only by root. If root access is required and the editable install is in
`.venv/`, one Linux example is:

```bash
sudo "$PWD/.venv/bin/lxd-container-backup" --config "$PWD/config/backup.env"
```

Only use `sudo` after checking the config values. Running as root gives the
program broad access to the machine.

The log file uses append mode and is not automatically rotated. Check it with:

```bash
sudo tail -n 50 /var/log/backup.log
```

For regular scheduled backups, configure system log rotation so the log does
not grow indefinitely.

## 6. Understand the result

The program prints the source and destination as it runs. A successful run
ends with a message like:

```text
Backup completed: /root/sundar/lxd-container-backup/admin---demo-workspaces/20261125_123000_123456
```

Each run creates a new timestamped folder:

```text
BACKUP_ROOT/CONTAINER_NAME/YYYYMMDD_HHMMSS_microseconds/
```

It does not overwrite an earlier timestamped backup. The folder contains the
contents of the container directory, copied by `rsync`.

If an error occurs, the command prints `Backup failed` and exits with status
`2` for handled setup or configuration errors. If `rsync` itself fails, its
non-zero status is returned and the destination may contain an incomplete
copy. Inspect that folder before deciding what to do with it.

## 7. Common issues

- **`lxd-container-backup: command not found`:** activate `.venv/` in the
  current terminal, reinstall with `python -m pip install -e .`, or use the
  `PYTHONPATH=src` command above.
- **Config file not found:** run from the project directory and check that
  `config/backup.env` exists, or pass the correct config path after
  `--config`.
- **Container directory not found:** check that `LXD_CONTAINERS_PATH` is the
  parent directory and `CONTAINER_NAME` exactly matches a directory under it.
- **`rsync was not found`:** install rsync with the machine's package manager
  and check `rsync --version`.
- **Cannot write `/var/log/backup.log`:** run with an account that can write
  the log file, or arrange appropriate ownership/permissions with the system
  administrator. The backup does not proceed when logging cannot be
  initialized.
- **Permission denied:** confirm the user can read the source and write to
  `BACKUP_ROOT`; preserving ownership and metadata may require root.
- **Not enough space:** check free space on the filesystem containing
  `BACKUP_ROOT` before another run.

## Limitations and data safety

This tool copies the configured container directory only. It does not copy
LXD configuration, snapshots, or storage-pool metadata, and may not be enough
to restore a working LXD container.

Files can change during the copy if the container is running. Databases and
other stateful applications may require application-aware backups. Stop the
container first if a consistent point-in-time filesystem copy is required
and downtime is acceptable. Do not treat a successful `rsync` run as proof
that a live application backup is consistent.

## Share the project

For another developer, share the source project files, including
`src/`, `config/backup.env.example`, packaging files, and `docs/`. Do not
share `.venv/`, generated backups, or your local `config/backup.env`. The
other developer should create their own config, install Python and rsync,
then follow this guide. See [Python learning guide](PYTHON_LEARNING.md) for
the module walkthrough and [Git and version guide](GITHUB_AND_VERSIONING.md)
for GitHub setup and releases. See [Command guide](COMMAND_GUIDE.md) for a
step-by-step explanation of the installed command.
