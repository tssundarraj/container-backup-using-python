# Schedule a daily backup on Linux

The installed `lxd-container-backup` command is already an executable
program; a second Python script is not required. This guide shows how to run
it automatically each day with a systemd timer (recommended) or cron.

> **Storage warning:** every run creates a new, full timestamped copy under
> `BACKUP_ROOT`. Old backups are not deleted automatically. Check available
> storage and decide on a retention/cleanup policy before enabling a daily
> schedule.

## Before scheduling

Complete the [installation guide](INSTALLATION.md) first:

1. Install Python and `rsync`.
2. Create and review `config/backup.env`.
3. Install the project in `.venv/`.
4. Run `lxd-container-backup --help`.
5. After verifying the config and permissions, run one real backup manually
   and confirm the destination contains the expected files.

Use absolute paths in scheduled commands. The examples below use this project
location:

```text
/root/sundar/lxd-container-backup/backup-code
```

Replace it if the project is installed elsewhere. The sample config writes
backups under `/root/sundar/lxd-container-backup` and logs to
`/var/log/backup.log`; the scheduled process needs permission to read all
configured sources and write both locations. A system-level service running
as root has those permissions for the sample paths.

## Recommended: schedule with a systemd timer

Systemd runs the command as a managed one-shot service and keeps its output in
the system journal.

### 1. Create a service unit

Create `/etc/systemd/system/lxd-container-backup.service`:

```ini
[Unit]
Description=Back up configured LXD workspace directories

[Service]
Type=oneshot
User=root
Group=root
WorkingDirectory=/root/sundar/lxd-container-backup/backup-code
ExecStart=/root/sundar/lxd-container-backup/backup-code/.venv/bin/lxd-container-backup --config /root/sundar/lxd-container-backup/backup-code/config/backup.env
```

For example, open the file as an administrator:

```bash
sudo nano /etc/systemd/system/lxd-container-backup.service
```

Paste the unit content, save it, and replace the example paths if needed.
Because this unit explicitly runs as root, only use it after checking the
config file. Do not put passwords or access tokens in the unit.

### 2. Create a daily timer

Create `/etc/systemd/system/lxd-container-backup.timer`:

```ini
[Unit]
Description=Run the LXD workspace backup every day

[Timer]
OnCalendar=*-*-* 02:00:00
Persistent=true
Unit=lxd-container-backup.service

[Install]
WantedBy=timers.target
```

The example runs at 02:00 in the machine's local time zone. Change the time
if another hour is more suitable. `Persistent=true` asks systemd to run a
missed timer once after the machine starts again; it does not replay every
missed day.

### What if yesterday's backup is still running?

Because this is a `Type=oneshot` systemd service, systemd will not start a
second instance of this same service while the first one is still active. A
timer event that occurs while the service is active is skipped; it is not
queued to start immediately when the backup finishes. The next attempt is at
the next scheduled time. `Persistent=true` handles a timer missed while the
machine was off; it is not a retry policy for an already-running backup.
See the
[systemd timer documentation](https://www.freedesktop.org/software/systemd/man/latest/systemd.timer.html)
for the service activation behavior.

Create the timer file:

```bash
sudo nano /etc/systemd/system/lxd-container-backup.timer
```

### 3. Load and enable the schedule

After saving both files:

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now lxd-container-backup.timer
```

Confirm that the timer is scheduled:

```bash
systemctl list-timers lxd-container-backup.timer
sudo systemctl status lxd-container-backup.timer
```

The timer schedules future runs; enabling it does not necessarily run a
backup immediately. To test the service now, first re-check the config, then
run:

```bash
sudo systemctl start lxd-container-backup.service
```

This command performs a real backup immediately. Confirm that it succeeded
before relying on the daily timer.

### 4. Check status and logs

Check the latest service result:

```bash
sudo systemctl status lxd-container-backup.service
```

Read recent service output:

```bash
sudo journalctl -u lxd-container-backup.service -n 100 --no-pager
```

The application's timestamped summary messages are also appended to:

```bash
sudo tail -n 50 /var/log/backup.log
```

Rsync's live progress output goes to the systemd journal, not the application
log. Neither log is automatically rotated by this project. Configure system
log rotation for `/var/log/backup.log`; systemd manages the journal according
to the host's journal settings.

### 5. Change or stop the schedule

After changing a unit file, reload systemd:

```bash
sudo systemctl daemon-reload
```

To disable future daily runs:

```bash
sudo systemctl disable --now lxd-container-backup.timer
```

The service creates a new timestamped folder for every configured workspace
on each run. It does not prune old folders. Choose and test a retention policy
separately before automating any deletion.

## Alternative: schedule with cron

Use cron if it is already the standard scheduler on your Linux machine. Since
the example config and log path are under root-owned directories, edit root's
crontab:

```bash
sudo crontab -e
```

Add one line to run every day at 02:00. Replace the paths if your checkout is
elsewhere. Use `flock -n` so cron skips this occurrence if the previous
backup command is still running:

```cron
0 2 * * * /usr/bin/flock -n /run/lock/lxd-container-backup.lock /root/sundar/lxd-container-backup/backup-code/.venv/bin/lxd-container-backup --config /root/sundar/lxd-container-backup/backup-code/config/backup.env >> /var/log/backup-cron-output.log 2>&1
```

The application still writes its summary to `/var/log/backup.log`. The cron
redirection stores command output, including rsync progress, separately in
`/var/log/backup-cron-output.log`. Root's crontab can write these files; set
up log rotation for them if you keep the job enabled. `flock -n` does not wait
for an active backup and does not queue a retry; the next attempt is at the
next cron time. The lock is released automatically when the command exits.
Check that `flock` is installed with `command -v flock`; it is usually
provided by the Linux `util-linux` package. See the
[flock manual](https://man7.org/linux/man-pages/man1/flock.1.html) for its
nonblocking option.

List root's scheduled jobs with:

```bash
sudo crontab -l
```

Remove or edit the line with `sudo crontab -e` to change or stop the schedule.
Do not install both the systemd timer and cron entry for the same backup
unless you intentionally want it to run twice per day.

## Important backup considerations

- Each scheduled run copies every configured workspace into a new timestamped
  folder. This is not an incremental or deduplicated backup, so storage use
  can grow quickly.
- The systemd service or cron `flock` example prevents overlapping runs from
  that scheduler. The backup program itself does not have a global process
  lock, so do not start a manual CLI run while a scheduled backup is active.
- The tool does not delete old backups. Do not add a cleanup command until
  you have decided how many copies to retain and have tested the deletion
  rules against a temporary directory.
- A running container can change during the copy. Stop it first if an
  application-consistent point-in-time filesystem copy is required and
  downtime is acceptable.
- The directory copy does not include LXD configuration, snapshots, or
  storage-pool metadata; it may not be sufficient to restore the full
  container.

For the config format and multiple-workspace behavior, see
[Installation](INSTALLATION.md). For command and module details, see the
[command guide](COMMAND_GUIDE.md) and [Python learning guide](PYTHON_LEARNING.md).
