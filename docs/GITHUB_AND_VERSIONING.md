# Git and GitHub: beginner to professional

This guide starts with installing Git and ends with a repeatable release
workflow. It is written for this project, whose package version is stored in
`setup.cfg`. Run project commands from the project root: the directory that
contains `README.md`, `setup.cfg`, and `src/`.

Git is the program that records project history on your computer. GitHub is a
website that hosts a Git repository so you can share work, review changes, and
publish releases. Git works locally; a GitHub account is needed only to host
and share the project there.

## 1. Install Git

Choose the instructions for the computer where you will edit or manage the
project. On Linux, run these commands in a terminal. On Windows, use Git Bash
or PowerShell after installation.

### Ubuntu or Debian

```bash
sudo apt update
sudo apt install git
```

### Fedora or a recent RHEL-compatible Linux

```bash
sudo dnf install git
```

### macOS

Install Apple's command-line developer tools:

```bash
xcode-select --install
```

Alternatively, if you already use Homebrew, install Git with `brew install git`.

### Windows

Download and install Git for Windows from
[git-scm.com/download/win](https://git-scm.com/download/win). The installer
includes Git Bash, which provides a terminal similar to the examples in this
guide. The defaults are suitable for most beginners.

### Verify the installation

Close and reopen the terminal, then run:

```bash
git --version
```

You should see a version number, for example `git version 2.x.x`. If the
terminal says that `git` is not found, install it for that operating system
and reopen the terminal.

## 2. Configure your Git identity

Git records a name and email address with each commit. Configure the identity
you want to use on this computer; replace the examples with your own details:

```bash
git config --global user.name "Your Name"
git config --global user.email "you@example.com"
git config --global init.defaultBranch main
```

These settings apply to all repositories for your computer account. To use a
different identity for just this project, run `git config user.name ...` and
`git config user.email ...` from the project root instead of using `--global`.
GitHub provides a private `noreply` email address in account settings if you
do not want your personal email shown in commit history.

Check the saved settings:

```bash
git config --global --list
```

## 3. Create a GitHub repository and choose sign-in

1. Sign in to [github.com](https://github.com/) or create an account.
2. Select **New repository**, choose a name such as `lxd-container-backup`,
   and select public or private.
3. This project already has a README and `.gitignore`, so leave the options
   to create a README, `.gitignore`, or license unchecked. The new GitHub
   repository should be empty.
4. Keep the repository page open; its URL will be used in a later step.

GitHub does not accept an account password for Git operations over HTTPS.
When prompted, use a supported browser sign-in or credential manager. GitHub
CLI is an optional tool that can authenticate with `gh auth login`; install it
only if you want to use it. SSH keys are another option; follow GitHub's
[SSH key setup guide](https://docs.github.com/en/authentication/connecting-to-github-with-ssh).
Never put an access token or password directly in a remote URL or source file.

## 4. Prepare this project for its first commit

Open a terminal and go to the project root. Replace the example path with the
actual location of your checkout:

```bash
cd /path/to/backup-code
```

First check whether Git is already initialized:

```bash
git status
```

If Git reports that this is not a repository, initialize it:

```bash
git init -b main
```

If your Git version does not support `-b`, run `git init` followed by
`git branch -M main`. If `git status` already works, do not initialize again.

Before adding files, check that the local config is ignored:

```bash
git check-ignore -v config/backup.env
```

The command should show a matching rule from `.gitignore`. The local
`config/backup.env` can contain machine-specific values; commit only
`config/backup.env.example`. Ignoring a file does not remove it from Git if it
was committed earlier. Check whether it is already tracked:

```bash
git ls-files config/backup.env
```

No output means it is not tracked. If it is tracked, stop before pushing and
remove it from Git's index with `git rm --cached config/backup.env`; this keeps
your local copy but does not erase the file from earlier commits. If a
credential was committed or pushed, revoke or rotate it immediately.

Stage the shareable project files explicitly:

```bash
git add .gitignore README.md requirements.txt pyproject.toml setup.cfg setup.py
git add src config/backup.env.example docs
```

Review exactly what is staged before committing:

```bash
git status --short
git diff --cached --name-only
git diff --cached --check
git diff --cached
```

The staged list should not contain `config/backup.env`, `.venv/`, generated
backups, build output, or credentials. If an unwanted file is staged, unstage
only that path with `git restore --staged path/to/file`, then inspect again.
Do not use `git add .` until you understand what it would include.

Create the first commit:

```bash
git commit -m "Initial LXD container backup package"
```

A **commit** is a named snapshot of the staged project changes. Keep each
commit focused on one understandable change.

## 5. Connect the local project to GitHub and push it

Copy the HTTPS repository URL from GitHub and replace the placeholders:

```bash
git remote add origin https://github.com/USERNAME/REPOSITORY.git
git remote -v
git push -u origin main
```

`origin` is the conventional name for the GitHub remote. The `-u` option
connects your local `main` branch to GitHub's `main`, so later `git push` and
`git pull` commands know which branch to use. If you choose SSH, use the SSH
URL shown by GitHub instead.

If `git remote add` says `origin` already exists, inspect it with `git remote
-v`; do not add a second remote with the same name. If the GitHub repository
was accidentally created with a README or other files, stop and resolve the
two histories rather than force-pushing over them.

## 6. Everyday workflow: make a change safely

For a small personal project, a simple workflow is:

1. Start from the latest `main` branch:

   ```bash
   git switch main
   git pull --ff-only origin main
   ```

2. Create a branch for one feature, fix, or documentation change:

   ```bash
   git switch -c docs/improve-install-guide
   ```

   Common prefixes include `feat/`, `fix/`, and `docs/`.

3. Edit files, then inspect and commit the change:

   ```bash
   git status --short
   git diff
   git add docs/INSTALLATION.md
   git diff --cached --check
   git diff --cached
   git commit -m "Improve installation instructions"
   ```

4. Push the branch:

   ```bash
   git push -u origin docs/improve-install-guide
   ```

5. On GitHub, open a pull request from that branch into `main`. Describe what
   changed, why it changed, and how you checked it. Review the diff before
   merging.
6. After the pull request is merged:

   ```bash
   git switch main
   git pull --ff-only origin main
   git branch -d docs/improve-install-guide
   ```

`--ff-only` prevents Git from silently creating a merge commit when local and
remote histories have diverged. If it fails, inspect `git status` and resolve
the situation deliberately; do not use force-push commands as a shortcut.

## 7. Team and professional practices

- Keep `main` releasable. For a team, enable branch protection on GitHub so
  changes enter `main` through reviewed pull requests and required checks.
- Use a branch per change and make small, descriptive commits. A commit
  message such as `fix: validate container source path` is clearer than
  `changes`. Follow the team's commit-message convention if it has one.
- Review `git diff` before staging and `git diff --cached` before committing.
  Never commit passwords, tokens, private keys, local config, or backup data.
- Treat `.gitignore` as protection for untracked files, not a way to remove
  tracked files or erase history.
- Do not rewrite shared history or force-push to `main`. If a secret reaches
  GitHub, rotate it even after deleting it from the latest commit.
- Keep release notes understandable: summarize user-visible changes,
  compatibility concerns, and any required configuration updates.
- For a growing project, keep a `CHANGELOG.md` with user-visible changes and
  link its entries from GitHub Releases.

## 8. Version the Python package

The package version currently lives in `setup.cfg` under `[metadata]`:

```ini
version = 1.1.0
```

Use the `MAJOR.MINOR.PATCH` pattern:

- **MAJOR**: an incompatible public API or behavior change.
- **MINOR**: a backward-compatible feature.
- **PATCH**: a backward-compatible fix.

The multi-workspace release requested for this project is package version
`1.1.0`, with Git tag `v1.1.0`. Keep the package version in `setup.cfg` and
the Git tag in sync. The tag convention adds `v`; for example, package version
`1.1.0` corresponds to Git tag `v1.1.0`.

The `1.1.0` release adds comma-separated `CONTAINER_NAMES`, preserves the
legacy single-name `CONTAINER_NAME` setting, and continues the batch after an
individual workspace failure.

## 9. Publish the multi-workspace release as `v1.1.0`

The package metadata is already set to `1.1.0` in `setup.cfg`. This is the
package version; the GitHub tag adds a `v`, so the tag is `v1.1.0`. The tag
must point to the commit containing the multiple-workspace code and updated
documentation.

First make sure this checkout is a Git repository connected to your GitHub
repository by following sections 4 and 5 above. From the project root, inspect
your current branch and changes:

```bash
git status --short
git diff
```

Build and check the package before publishing:

```bash
python3 -m pip install -e .
lxd-container-backup --help
python3 -m pip wheel --no-deps . --wheel-dir dist
```

The help command does not start a backup. This project does not currently
have an automated test suite; do not use a real container backup as a routine
code test.

If this is the first time you are using Git in this project, follow sections
4 and 5 instead: the initial commit and first push will already include the
`1.1.0` package and its current code and documentation. Do not make a duplicate
release commit; continue below after the initial push. If your working tree is
already clean because these changes were committed earlier, skip the staging
and commit commands and make sure the commit is pushed to `main`.

For a solo project working directly on `main`, stage and inspect the
release files:

```bash
git add setup.cfg README.md config/backup.env.example src/lxd_container_backup docs
git status --short
git diff --cached --check
git diff --cached --stat
git diff --cached
```

Confirm that the local `config/backup.env`, `.venv/`, generated backups, and
credentials are not staged. Then commit and push the release contents:

```bash
git commit -m "Add multi-workspace backups for v1.1.0"
git push origin main
```

If you work on a feature branch, push that branch and merge its pull request
into `main` instead. After it is merged, update your local `main`:

```bash
git switch main
git pull --ff-only origin main
```

Before creating a tag, check that `v1.1.0` does not already exist:

```bash
git tag --list v1.1.0
```

No output means the tag is unused. If the tag is already listed, stop; never
move a published release tag to another commit. Create and push the annotated
tag only after the release commit is on GitHub:

```bash
git tag -a v1.1.0 -m "Release v1.1.0"
git show --no-patch --decorate v1.1.0
git push origin v1.1.0
```

The branch push and tag push are separate: pushing `main` does not push the
tag automatically. On GitHub, open **Releases**, choose **Draft a new
release**, select `v1.1.0`, and publish release notes. Suggested notes:

- Add comma-separated `CONTAINER_NAMES` for multiple workspaces.
- Keep compatibility with the existing singular `CONTAINER_NAME` setting.
- Continue backing up later workspaces if one workspace fails; return a
  non-zero status if any backup fails.
- Update installation, command, Python learning, and daily Linux scheduling
  documentation.

Attach the `.whl` file from `dist/` to the GitHub Release if you want to
distribute the built package. The package still requires `rsync` and a
user-provided config file, for example:

```bash
lxd-container-backup --config /path/to/backup.env
```

## 10. Checklist for later releases

For a future release, update `version` in `setup.cfg`, prepare release notes,
run the package checks above, merge the release commit to `main`, and use a
new annotated tag that matches the version (for example, package version
`1.1.1` uses tag `v1.1.1`). Push the branch and tag, then create the matching
GitHub Release. Never reuse a published version tag.

## Common problems

- **`git` is not found:** install Git for your operating system, reopen the
  terminal, and check `git --version`.
- **Git asks for your identity:** configure `user.name` and `user.email` as
  described above.
- **GitHub rejects your password:** use browser-based credential-manager
  sign-in, GitHub CLI, or SSH; an account password is not Git authentication.
- **A local config file appears in a commit:** unstage it and check
  `.gitignore`. If it was already pushed, rotate any secret and follow
  GitHub's guidance for sensitive data in repository history.
- **Push is rejected:** inspect the branch and remote state. Usually you need
  to pull the latest changes and resolve them; do not force-push to bypass the
  rejection.

Further reading: [Git installation](https://git-scm.com/book/en/v2/Getting-Started-Installing-Git),
[GitHub's Git setup guide](https://docs.github.com/en/get-started/git-basics/set-up-git),
and [GitHub's release guide](https://docs.github.com/en/repositories/releasing-projects-on-github).
