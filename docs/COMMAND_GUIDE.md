# Using the `lxd-container-backup` command

This guide explains what the project's command does and how to run it.

> **Command name:** this project installs `lxd-container-backup` (with a **d**).
> `lxc` is the separate LXD management command; `lxc-container-backup` is not
> the command provided by this Python project.

The command copies a configured container directory using `rsync`. It does
not run `lxc export` and does not create an LXD-native export archive.

## What happens when you run it

The `lxd-container-backup` command is created from the console-script entry in
`setup.cfg`:

```ini
lxd-container-backup = lxd_container_backup.cli:main
```

In plain language, the command works like this:

1. Your terminal finds the installed `lxd-container-backup` program. If you
   installed it in `.venv/`, activate that virtual environment first.
2. The command calls `main()` in `src/lxd_container_backup/cli.py`.
3. The CLI initializes file logging at `/var/log/backup.log`.
4. The CLI reads `--config` to find the settings file.
5. `config.py` reads the workspace names and the required paths.
6. `workspace_backup.py` visits each configured workspace in order.
7. For each one, `backup.py` checks its name and source directory, creates a
   timestamped destination, and runs `rsync`.
8. The program logs each result, continues after an individual failure, and
   returns a non-zero status if any workspace failed.

The copy is a filesystem copy. The source may change while a running
container is being copied, so a successful command does not guarantee an
application-consistent backup.

The log file is opened in append mode, so each run adds new entries rather
than replacing old ones. `--help` exits before logging is initialized and
does not create the file. The log records application start, completion, and
failure messages; rsync's live progress output remains in the terminal.

## Run it from a source checkout

### 1. Install the system requirements

On Ubuntu or Debian:

```bash
sudo apt update
sudo apt install python3 python3-venv rsync
```

Check Python and rsync:

```bash
python3 --version
rsync --version
```

### 2. Open the project directory

Change to the directory containing `setup.cfg`, `pyproject.toml`, and `src/`:

```bash
cd /path/to/backup-code
```

Replace `/path/to/backup-code` with the actual location of this project.

### 3. Create and edit the config

Make a local config from the example if you do not already have one:

```bash
if [ ! -f config/backup.env ]; then
    cp config/backup.env.example config/backup.env
fi
nano config/backup.env
```

Check that the values match the machine where the command will run:

```dotenv
CONTAINER_NAMES=admin---demo-workspaces
LXD_CONTAINERS_PATH=/var/snap/lxd/common/lxd/storage-pools/local/containers
BACKUP_ROOT=/root/sundar/lxd-container-backup
```

Use plain `KEY=VALUE` lines without quotes. Add more workspace directory
names by separating them with commas:

```dotenv
CONTAINER_NAMES=admin---demo-workspaces,admin---team-workspace
```

Spaces around names are ignored. Existing config files using the singular
`CONTAINER_NAME=name` continue to work; do not set both keys. The program
appends each name to `LXD_CONTAINERS_PATH`, which is the parent folder. For
the first example value, the source directory must be:

```text
/var/snap/lxd/common/lxd/storage-pools/local/containers/admin---demo-workspaces
```

### 4. Install and activate the Python package

Create a virtual environment and activate it:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install the project from the current directory:

```bash
python -m pip install -e .
```

The `-e` means editable install: the command uses the code in this checkout.
The project has no third-party runtime Python dependencies; install `rsync`
separately as shown above.

### 5. Check the command, then start the backup

First display the available options. This does **not** start a backup:

```bash
lxd-container-backup --help
```

Then start the backup:

```bash
lxd-container-backup --config config/backup.env
```

The `--config` option supplies the settings file. Pass it explicitly so the
command uses the config you just reviewed. If you open a new terminal later,
go back to the project directory and activate the environment again:

```bash
cd /path/to/backup-code
source .venv/bin/activate
lxd-container-backup --config config/backup.env
```

The command also needs permission to write `/var/log/backup.log`. Because the
example source and destination paths are under system/root directories, it
may need to run with elevated permissions. If needed, use the venv's
executable explicitly:

```bash
sudo "$PWD/.venv/bin/lxd-container-backup" --config "$PWD/config/backup.env"
```

Each workspace gets a new directory under:

```text
BACKUP_ROOT/WORKSPACE_NAME/YYYYMMDD_HHMMSS_microseconds/
```

For the example config, a destination might look like:

```text
/root/sundar/lxd-container-backup/admin---demo-workspaces/20261125_123000_123456/
```

It does not overwrite previous timestamped backup directories. Check the
printed destination and confirm it contains the expected files. If one
workspace fails, the command continues with the remaining names and returns
a non-zero exit status after the batch.

View the latest log entries with:

```bash
sudo tail -n 50 /var/log/backup.log
```

The log is not automatically rotated. Configure system log rotation if the
program will run regularly.

## Run without installing the command

From the project root, you can invoke the package directly:

```bash
PYTHONPATH=src python3 -m lxd_container_backup --config config/backup.env
```

`PYTHONPATH=src` tells Python to find the package under `src/`. This is useful
for a quick checkout run or while learning how the modules work. It still
requires Python, `rsync`, a valid config, and filesystem permissions.

## What `--help` means

```bash
lxd-container-backup --help
```

`--help` is provided by Python's `argparse` module. It prints command usage
and exits without loading the config or starting `rsync`. The current CLI
options are:

- `--help`: show usage and exit.
- `--config PATH`: use the specified settings file.

Workspace names are configured in `config/backup.env`; they are not currently
command-line options.

## Errors and exit status

- **Command not found:** activate `.venv/` in the same terminal, or install
  the package with `python -m pip install -e .` while that environment is
  active.
- **Config not found or invalid:** confirm the path after `--config` and
  check that `LXD_CONTAINERS_PATH` and `BACKUP_ROOT` are present, along with
  exactly one of `CONTAINER_NAME` or `CONTAINER_NAMES`.
- **Container directory not found:** check that the configured parent path
  and every configured workspace name point to an existing directory.
- **Workspace list rejected:** provide unique, non-empty comma-separated
  names in `CONTAINER_NAMES`. For backwards compatibility, one
  `CONTAINER_NAME` is also accepted; do not configure both.
- **`rsync` not found:** install it with the operating system package
  manager.
- **Cannot write the log file:** `/var/log/backup.log` must be writable by
  the account running the command. The backup stops if logging cannot be
  initialized.
- **Permission denied:** confirm read access to the source and write access
  to the destination. Preserving owners, ACLs, and extended attributes can
  require elevated permissions; see [Installation](INSTALLATION.md).
- **`rsync` returns an error:** its non-zero status is returned to the
  batch, which continues with later workspaces. The command returns the first
  non-zero status it encountered, and that workspace's destination may be
  incomplete. Inspect it before deciding what to do with it.

For a complete explanation of the Python functions and their relationships,
see the [Python learning guide](PYTHON_LEARNING.md). For system setup and
backup limitations, see [Installation](INSTALLATION.md).
