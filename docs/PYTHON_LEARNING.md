# Python package: beginner and developer guide

This guide explains how the backup package is organized, how to follow its
code, how it was put together, and how to add another module. It assumes basic
Python familiarity, but explains the package-specific ideas as they appear.

## 1. Prepare a development environment

From the project directory, create the local config if needed:

```bash
if [ ! -f config/backup.env ]; then
    cp config/backup.env.example config/backup.env
fi
```

An isolated environment is optional, but recommended when developing:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e .
```

The `-e` option installs the project in editable mode: Python imports the code
from `src/`, so changes are available without reinstalling. The package has
no third-party runtime dependencies. Install `rsync` separately with your
operating system.

For a beginner-friendly first check, display the command help without starting
a backup:

```bash
lxd-container-backup --help
```

## 2. Understand the project layout

```text
config/
  backup.env.example      Safe-to-share config template
  backup.env              Local settings; ignored by Git
src/lxd_container_backup/
  config.py               Read settings and create BackupConfig
  backup.py               Perform one reusable rsync copy
  cli.py                  Parse command-line options and handle errors
  __main__.py             Support python -m lxd_container_backup
  __init__.py             Define the package's public API
docs/
  INSTALLATION.md         Setup, running, and sharing instructions
  PYTHON_LEARNING.md      This guide
pyproject.toml            Select the build system
setup.cfg                 Package name, version, Python floor, CLI command
setup.py                  Small setuptools build entry point
requirements.txt          Notes about Python and the system rsync dependency
```

There are two different names to notice:

- `lxd_container_backup` uses underscores because it is a Python package name.
- `lxd-container-backup` uses hyphens because it is a shell command name.

The `src/` layout keeps importable Python code separate from project
configuration, docs, and packaging files.

## 3. Follow the call flow

When a user runs:

```bash
lxd-container-backup --config config/backup.env
```

the modules work together in this order:

```text
shell command
  └── setup.cfg console entry point -> cli.main()
        ├── argparse reads --config
        ├── config.load_config(path) -> BackupConfig
        └── backup.backup_container(config) -> exit status
              └── subprocess.run(command) -> rsync process
```

The same `main()` function is used by
`python -m lxd_container_backup`: Python loads `__main__.py`, which calls
`cli.main()`. Importing `lxd_container_backup` does not start a copy.

## 4. Learn what each module owns

### `config.py`: settings and data

`BackupConfig` is a frozen dataclass. A dataclass groups related values into
one object; `frozen=True` prevents accidentally changing those settings after
they have been loaded.

Its fields are:

```python
BackupConfig(
    container_name="admin---demo-workspaces",
    containers_path=Path("/var/snap/lxd/common/lxd/storage-pools/local/containers"),
    backup_root=Path("/root/sundar/lxd-container-backup"),
)
```

`load_config(path)` reads the simple `KEY=VALUE` file, skips comments and
blank lines, rejects invalid, unknown, or duplicate settings, and returns a
`BackupConfig`. It does not run rsync.

### `backup.py`: reusable operation

`backup_container(config)` accepts a `BackupConfig`, validates the container
and paths, makes a timestamped destination, then starts rsync. It returns `0`
for success or rsync's non-zero exit status. Invalid settings or inaccessible
paths raise an exception for the caller to handle.

The rsync arguments are passed as a Python list, not as a shell command
string. This makes argument boundaries clear and avoids shell interpretation.
The flags preserve common file metadata, hard links, ACLs, extended
attributes, and numeric user/group IDs.

### `cli.py`: command-line interface

`argparse` defines the `--config` option and automatically provides `--help`.
The CLI loads settings, calls the reusable backup function, and turns handled
errors into a clear message and non-zero process status.

### `__init__.py` and `__main__.py`: package entry points

`__init__.py` re-exports `BackupConfig`, `load_config`, and
`backup_container`, so another Python project can import them directly:

```python
from lxd_container_backup import BackupConfig, backup_container
```

`__main__.py` allows the package to be run with `python -m
lxd_container_backup`. The installed shell command is declared in `setup.cfg`.

## 5. Read config without making a backup

This example imports the config module and displays its values. It does not
call `backup_container()` and does not start rsync. Run it from the project
directory:

```bash
PYTHONPATH=src python3 - <<'PY'
from pathlib import Path

from lxd_container_backup.config import load_config

config = load_config(Path("config/backup.env"))
print(config.container_name)
print(config.containers_path)
print(config.backup_root)
PY
```

`PYTHONPATH=src` tells Python to search the `src/` folder for the package.
The import path
`lxd_container_backup.config` means “the `config` module inside the
`lxd_container_backup` package.” `load_config(...)` calls that module's
function; the returned object's fields are accessed with dot notation, such
as `config.container_name`.

## 6. Build a similar package from scratch

When starting a small Python tool, build it in layers:

1. **Write down the inputs and outputs.** This program needs a container name,
   a source parent directory, and a backup root; it produces a timestamped
   copy and an exit status.
2. **Choose module responsibilities.** Put config parsing in `config.py`,
   file-copy logic in `backup.py`, and command-line handling in `cli.py`.
3. **Define the data passed between modules.** `BackupConfig` carries the
   container name and paths from the config parser to the backup function.
4. **Implement and check the core operation.** Validate paths before building
   the rsync command. Pass command arguments as a list and return the process
   status.
5. **Add the CLI last.** The CLI should connect inputs and outputs, not contain
   the file-copy implementation itself.
6. **Add packaging metadata and docs.** `setup.cfg` names the project and
   declares the command; `pyproject.toml` selects the build backend.

This order keeps the reusable function independent of the command line.
Another program can call the function with a `BackupConfig`, while a human
can use the shell command.

## 7. Add a new module

Create a new module when you have a distinct responsibility, not just to move
one line of code. For example, container-name validation could later be
separated from the rsync operation.

1. Create `src/lxd_container_backup/validation.py`.
2. Put the validation function there:

   ```python
   import re


   def validate_container_name(name: str) -> None:
       if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]*", name):
           raise ValueError("invalid container name")
   ```

3. In `backup.py`, import and call that function:

   ```python
   from .validation import validate_container_name

   # Inside backup_container():
   validate_container_name(config.container_name)
   ```

4. Remove the old validation code and its `re` import from `backup.py`; do not
   keep two copies of the same rule.
5. Export the function from `__init__.py` only if you intend it to be part of
   the public API. Internal helpers can stay in their own module.
6. Update this guide or other docs if the new module changes how a developer
   uses the package.

The leading dot in `from .validation import ...` is a **relative import**: it
means “import from this same package.” Keep dependencies flowing one way
where practical. For example, `cli.py` may import `config.py` and `backup.py`;
`config.py` should not import `cli.py`. Avoid circular imports where two
modules import each other.

## 8. Package and share changes

For development, install the checkout in editable mode:

```bash
python -m pip install -e .
```

To build a wheel for another Python user:

```bash
python -m pip wheel --no-deps . --wheel-dir dist
```

Share the wheel or the source project. A source project is best when the
recipient will edit modules. Include `src/`, `config/backup.env.example`,
`setup.cfg`, `setup.py`, `pyproject.toml`, `requirements.txt`, and `docs/`.
Do not share your local `config/backup.env` unless its machine-specific paths
are intended for the recipient. The recipient must install rsync separately
and provide a config path when running an installed package:

```bash
lxd-container-backup --config /path/to/backup.env
```

## 9. Safe development checks

- Run `lxd-container-backup --help` to check CLI setup without starting a copy.
- Use the config-reading example above to check parsing without invoking
  rsync.
- When changing copy behavior, use a temporary source directory and mock
  `subprocess.run()` so development checks cannot copy the real container.
- Do not treat a successful filesystem copy as proof that a live container is
  application-consistent or fully restorable.
