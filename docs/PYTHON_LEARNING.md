# Python package: beginner and developer guide

This guide follows the files and code currently in this project. It explains
how the command reaches the backup function, what each module does, how
settings are read, and how to extend the package without mixing unrelated
responsibilities.

For prerequisites and commands to make an actual backup, first follow
[Installation and running the backup](INSTALLATION.md). The examples here
that only load config or print help do not copy container files.

## 1. Project files

```text
.
├── .gitignore
├── README.md
├── requirements.txt
├── pyproject.toml
├── setup.cfg
├── setup.py
├── config/
│   ├── backup.env.example
│   └── backup.env                 Local config; ignored by Git
├── docs/
│   ├── INSTALLATION.md
│   ├── PYTHON_LEARNING.md
│   ├── COMMAND_GUIDE.md
│   ├── DAILY_BACKUP_LINUX.md
│   └── GITHUB_AND_VERSIONING.md
└── src/
    └── lxd_container_backup/
        ├── __init__.py
        ├── __main__.py
        ├── backup.py
        ├── cli.py
        ├── config.py
        ├── logging_config.py
        └── workspace_backup.py
```

The local `config/backup.env` is created from the example and is not meant to
be committed. The example is safe to share because it contains defaults, not
machine secrets. A `.venv/` directory, if created, contains a local Python
environment and is also ignored.

There are two similar-looking but different names:

- `lxd_container_backup` is the Python import/package name; Python package
  names use underscores here.
- `lxd-container-backup` is the installed terminal command; the command name
  is declared in `setup.cfg`.

The `src/` layout keeps importable package code separate from configuration,
documentation, and build metadata.

## 2. How the command flows through the modules

After installing the project in an active virtual environment, a user can
run:

```bash
lxd-container-backup --config config/backup.env
```

The relevant `setup.cfg` entry maps that command to the `main` function:

```ini
[options.entry_points]
console_scripts =
    lxd-container-backup = lxd_container_backup.cli:main
```

The call flow is:

```text
shell command
  └── setup.cfg console entry point
       └── cli.main()
            ├── logging_config.configure_logging() -> /var/log/backup.log
            ├── argparse reads --config
            ├── config.load_config(path) -> BackupConfig
            └── workspace_backup.backup_workspaces(config)
                  └── for each workspace:
                       └── backup.backup_container(config) -> exit status
                            └── subprocess.run(argument_list) -> rsync
```

The same CLI can be started without the installed terminal command:

```bash
PYTHONPATH=src python3 -m lxd_container_backup --config config/backup.env
```

Python first loads `__main__.py`, which calls `cli.main()`. Importing
`lxd_container_backup` by itself does not start a copy.

## 3. `config.py`: parse settings into a data object

This module imports `dataclass` and `Path` from Python's standard library.
`ALLOWED_SETTINGS` lists the supported keys. A config must provide both path
keys and exactly one of `CONTAINER_NAME` or `CONTAINER_NAMES`:

```python
CONTAINER_SETTINGS = {"CONTAINER_NAME", "CONTAINER_NAMES"}
REQUIRED_PATH_SETTINGS = {"LXD_CONTAINERS_PATH", "BACKUP_ROOT"}
```

`DEFAULT_CONFIG_PATH` calculates the source-checkout default path to
`config/backup.env`. When the package is installed as a wheel, that local
project config may not be beside the installed Python package. For that
reason, pass `--config /path/to/backup.env` explicitly when using an installed
package.

The settings object is:

```python
@dataclass(frozen=True)
class BackupConfig:
    container_name: str
    containers_path: Path
    backup_root: Path
    container_names: tuple[str, ...] = ()
```

`@dataclass` creates a class for storing related values. `frozen=True` makes
its fields read-only after construction. The first three fields preserve the
original single-workspace API. `container_names` stores the complete tuple
from the config, and the `workspaces` property falls back to `container_name`
for code that creates a `BackupConfig` using the original three arguments.
The loader returns one config object for the whole batch.

`load_config(config_path)` processes the file one line at a time:

1. `read_text(encoding="utf-8").splitlines()` reads text and splits it into
   lines.
2. `enumerate(..., start=1)` records human-readable line numbers for errors.
3. Stripping whitespace lets blank lines and lines beginning with `#` be
   skipped.
4. `partition("=")` splits a setting at its first equals sign.
5. The loader rejects lines without `=`, empty values, unrecognized keys,
   duplicate keys, and missing path settings.
6. It requires exactly one workspace setting: singular `CONTAINER_NAME` or
   plural `CONTAINER_NAMES`. The plural value is split on commas, trimmed,
   and rejected if a name is empty or repeated.
7. It creates `Path` objects for the two path settings and expands a leading
   `~` with `expanduser()`.
8. It returns a `BackupConfig` containing the names and paths.

This is a simple `KEY=VALUE` format, not a full shell script or dotenv
interpreter. Do not quote values or add inline comments. For example:

```dotenv
CONTAINER_NAMES=admin---demo-workspaces,admin---team-workspace
LXD_CONTAINERS_PATH=/var/snap/lxd/common/lxd/storage-pools/local/containers
BACKUP_ROOT=/root/sundar/lxd-container-backup
```

Existing config files with `CONTAINER_NAME=admin---demo-workspaces` remain
supported. Do not include both workspace keys in one file. Loading settings
validates their format and keys, but does not check that each container
directory exists; that filesystem check happens in `backup.py`.

## 4. `backup.py`: validate paths and run rsync

`backup_container(config)` takes a `BackupConfig` and returns an integer exit
status for one workspace. It uses `config.container_name`; the batch module
creates a per-workspace copy of the config before calling it. Its main steps
are:

1. **Validate the container name.** A regular expression allows ASCII letters,
   numbers, dots, underscores, and hyphens, and requires the first character
   to be a letter or number. Invalid names raise `ValueError`.
2. **Build and check the source path.** The source is
   `config.containers_path / config.container_name`. It must be an existing
   directory or `FileNotFoundError` is raised.
3. **Find rsync.** `shutil.which("rsync")` searches the executable path. If it
   is missing, the function raises `FileNotFoundError`.
4. **Protect the source from destination overlap.** The function rejects a
   backup directory equal to, or inside, the source container directory.
5. **Create a unique destination.** A timestamp is formatted as
   `YYYYMMDD_HHMMSS_microseconds` and a directory is created under
   `BACKUP_ROOT/WORKSPACE_NAME/`.
6. **Run rsync.** `subprocess.run()` receives a list of arguments, not a
   shell-command string. It uses `check=False` so the code can inspect rsync's
   exit status itself.

The rsync options are:

- `-a`: archive mode, preserving common file attributes and directory
  structure.
- `-H`: preserve hard links.
- `-A`: preserve ACLs.
- `-X`: preserve extended attributes.
- `--numeric-ids`: preserve numeric user and group IDs rather than mapping
  names.
- `--human-readable` and `--info=progress2`: make progress information easier
  to read.
- `--`: marks the end of options, so paths are treated as paths.
- A trailing slash on the source means copy the contents of the container
  directory into the timestamped destination.

The function prints progress messages. On rsync success it returns `0`; on
rsync failure it prints a warning that the destination may be incomplete and
returns rsync's non-zero status. An error before starting rsync is raised for
the CLI to report. It also writes start, success, or rsync-failure messages
to the package logger.

## 5. `cli.py`: connect settings and backup operation

`argparse` creates the command-line interface and automatically implements
`--help`. The `--config` option accepts a path and has
`DEFAULT_CONFIG_PATH` as its default.

`main(argv=None)` can parse the real command-line arguments or a supplied
sequence, which is useful when another Python function calls it. It initializes
logging, loads config, and calls `backup_workspaces()`. `OSError` and
`ValueError` exceptions are printed to standard error as `Backup failed: ...`;
these handled errors return status `2`. Otherwise, the CLI returns the backup
batch's status. The command runner uses that return value as the process exit
status.

The CLI parses arguments before it configures logging, so `--help` displays
usage and exits without creating the log file. If logging cannot be
initialized, the CLI prints the error and returns `2` without starting a
backup.

### `logging_config.py`: create the application log

This module uses Python's built-in `logging` package. `LOG_FILE` is
`/var/log/backup.log`. `configure_logging(log_file=LOG_FILE)` resolves the
path, creates its parent directory if needed, and configures the
`lxd_container_backup` logger at `INFO` level. It adds a UTF-8 `FileHandler`
only if a handler for that path is not already attached. The handler appends
timestamped messages instead of replacing existing log entries.

The CLI calls this function before loading the config, so config and backup
errors can be logged. The default `/var/log` location usually requires
elevated permission. If the file cannot be opened, the program reports the
error and does not proceed without logging. The file is not automatically
rotated; configure system log rotation if the command will run regularly.

## 6. `workspace_backup.py`: process multiple workspaces

`backup_workspaces(config)` loops over `config.workspaces` in the order listed
in the config. It uses `dataclasses.replace()` to create a copy of the config
with one `container_name` and one `container_names` entry at a time, then
calls the existing `backup_container()` function. That keeps the rsync
implementation focused on one directory while the new module coordinates
the batch.

If a workspace raises an `OSError` or `ValueError`, the module logs and prints
that workspace's error, then continues to the next name. An rsync non-zero
status is also recorded and does not stop the remaining copies. The batch
returns `0` only if all workspaces succeeded; otherwise it returns the first
non-zero status. The CLI uses that as the command's exit status.

## 7. `__init__.py` and `__main__.py`: public imports and launchers

`__init__.py` defines the package's public API by re-exporting
`BackupConfig`, `load_config`, `backup_container`, and `backup_workspaces`.
Another Python program can import them from the package:

```python
from lxd_container_backup import (
    BackupConfig,
    backup_container,
    backup_workspaces,
    load_config,
)
```

`__main__.py` imports `main` from `cli.py` and raises `SystemExit(main())`.
This is what makes `python -m lxd_container_backup` run the CLI and return its
exit status to the operating system.

## 8. Read settings without starting a backup

This example loads the config and prints its values; it does not call rsync.
Run it from the project root after creating `config/backup.env`:

```bash
PYTHONPATH=src python3 - <<'PY'
from pathlib import Path

from lxd_container_backup.config import load_config

config = load_config(Path("config/backup.env"))
print(config.container_name)
print(config.workspaces)
print(config.containers_path)
print(config.backup_root)
PY
```

`PYTHONPATH=src` adds `src/` to Python's import search path. The dotted import
`lxd_container_backup.config` means the `config` module inside the
`lxd_container_backup` package. `load_config(...)` returns an object, and dot
notation such as `config.container_name` reads one of its fields.

## 9. Packaging and project support files

- **`setup.cfg`** contains the package name, current version (`1.1.0`),
  minimum Python version (`>=3.9`), package discovery settings, and the
  `lxd-container-backup` console command.
- **`pyproject.toml`** tells build tools to use the setuptools build backend.
- **`setup.py`** calls `setuptools.setup()` so setuptools reads metadata from
  `setup.cfg`.
- **`requirements.txt`** documents Python and system requirements. It is not
  an installable list of pip packages because there are no third-party
  runtime Python dependencies.
- **`.gitignore`** excludes the virtual environment, Python cache files,
  local config, and generated build output from Git.
- **`config/backup.env.example`** provides shareable default settings.
- **`README.md`** is the project overview and quick start.
- **`docs/INSTALLATION.md`** explains setup and running the program.
- **`docs/COMMAND_GUIDE.md`** explains the installed command and its call flow.
- **`docs/DAILY_BACKUP_LINUX.md`** explains how to schedule daily Linux runs.
- **`docs/GITHUB_AND_VERSIONING.md`** explains Git, GitHub, and releases.
- **`src/lxd_container_backup/logging_config.py`** configures the application
  log file.
- **`src/lxd_container_backup/workspace_backup.py`** backs up each configured
  workspace and aggregates the results.

## 10. How to add another module

Add a module when it has a clear responsibility. Keep the current division:
config parsing belongs in `config.py`, copying one directory belongs in
`backup.py`, batch orchestration belongs in `workspace_backup.py`, logging
setup belongs in `logging_config.py`, and command-line handling belongs in
`cli.py`. A module should not import the CLI just to access a helper; keep
dependencies flowing in one direction where possible to avoid circular
imports.

For example, if the program later gains a separate validation responsibility,
you could create `src/lxd_container_backup/validation.py`, move the existing
container-name rule there, and import that function in `backup.py`. The
current implementation performs this check directly in `backup.py`; do not
add a second copy of the rule. Export a helper from `__init__.py` only if you
intend it to be part of the package's supported public API.

When adding or changing behavior:

1. Decide which module owns the behavior.
2. Pass data between modules using explicit arguments and return values.
3. Update callers and documentation that depend on the behavior.
4. Check `lxd-container-backup --help` and use a temporary source plus a mock
   for rsync-related checks; do not test against a real container by
   accident.

## 11. Build and share the package

For local development, create and activate a virtual environment as described
in [Installation](INSTALLATION.md), then install the project:

```bash
python -m pip install -e .
```

To build a wheel:

```bash
python3 -m pip wheel --no-deps . --wheel-dir dist
```

The generated `.whl` file is written in `dist/`. Share that wheel for
installation, or share the source files when another developer needs to edit
the code. Do not include `.venv/`, generated backups, or local
`config/backup.env`.

An installed package should be run with an explicit config path:

```bash
lxd-container-backup --config /path/to/backup.env
```

The package does not include your machine's config file. The recipient must
install `rsync`, create their own config from `config/backup.env.example`,
and provide that config path.

## 12. Safe checks and limits

- `lxd-container-backup --help` checks that the command is available without
  starting a copy.
- The config-reading example checks parsing without starting rsync.
- This project currently has no automated test suite.
- A successful directory copy does not include LXD configuration,
  snapshots, or storage-pool metadata.
- A running container can change during the copy; application-aware backup
  steps may be required for consistent databases or other stateful services.
