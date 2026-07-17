md5tool
=======

Python script to generate or check MD5 checksums recursively for files in a
directory tree.

Designed for digital-preservation use: it is built to run cleanly across large
archival batches, report problem files clearly, and keep going rather than
aborting the whole run when it hits a bad file or a corrupt checksum sidecar.

Tested on Python 3.6+ (developed and used on Python 3.12).

**Version 2.0.0** — see the [What's new](#whats-new) section below, or the full
[CHANGELOG](CHANGELOG.md) for details.

> **Note:** This is a hardened Python 3 rewrite. The previous version targeted
> Python 2.7/3.4/3.6 and is no longer maintained. If you are upgrading from the
> old script, see [What's new](#whats-new) below — some behavior has changed.

## What's new

This rewrite addresses three failure modes seen in production preservation
batches, plus a few correctness fixes. For the complete, versioned history see
the [CHANGELOG](CHANGELOG.md).

- **No longer crashes on corrupt or empty `.md5` sidecar files.**
  A zero-byte sidecar (e.g. from a failed copy) or one containing non-text
  bytes previously aborted the *entire* run with a `UnicodeDecodeError`. Sidecar
  files are now read with tolerant decoding, so a bad sidecar is reported as
  `BAD_MD5` and the batch continues.

- **No longer crashes on unreadable or truncated source files.**
  A source file that errors out mid-read — for example a bad LTO tape pull whose
  header reports a larger size than the bytes actually on disk, raising
  `OSError: [Errno 22] Invalid argument` — is now caught, reported as
  `UNREADABLE_FILE`, and skipped so the rest of the batch still completes.

- **Python 3 compatible.**
  Uses a `#!/usr/bin/env python3` shebang (the old `#!/usr/bin/python` fails on
  recent macOS, which no longer ships `/usr/bin/python`). Command-line parsing
  moved from the deprecated `optparse` to `argparse`; the command syntax is
  unchanged.

Other fixes and additions:

- **Categorized results.** A genuine integrity failure (`MISMATCH`, the stored
  hash and the file's actual hash differ) is kept distinct from operational
  problems (`BAD_MD5`, `UNREADABLE_FILE`). This makes it easy to tell "a file's
  bits changed" apart from "a drive had an unreadable file or a bad sidecar."
- **Meaningful exit codes** for scripting and scheduled runs (see below).
- **Optional `--log` flag** to append a timestamped, itemized report of every
  problem file — an audit trail instead of just terminal scrollback.
- **Broader `.md5` format support.** The parser now reads bare-hash sidecars,
  `md5sum` binary-mode lines (`hash *filename`), and `md5sum`/GNU coreutils
  text-mode lines (`hash  filename`, two spaces). It also validates that the
  token it found is actually 32 hex characters.
- **Fixed a write-failure bug** in the generate path: if a `.md5` file could not
  be written, the old script printed an error and then crashed a second time
  trying to use an unopened file handle. This is now reported as `WRITE_ERROR`.

## Usage

Check files in one or more directories (and their subdirectories) against their
corresponding `.md5` checksum files:

    md5tool.py check dir1 [dir2 dir3 ...]

Generate `.md5` checksum files for any files that are missing them:

    md5tool.py generate dir1 [dir2 dir3 ...]

Display a help message:

    md5tool.py --help

### Options

- `-v`, `--verbose` — report files that have no matching `.md5` file, and
  `.md5` files that have no matching source file (orphaned sidecars). Useful for
  investigating failed copies or files removed after their sidecar was written.
- `-l LOGFILE`, `--log LOGFILE` — append a categorized summary and the full list
  of problem files to `LOGFILE`.

Example, capturing an audit log:

    md5tool.py check /Volumes/mydrive --log ~/mydrive_check_$(date +%Y%m%d).log

### Result statuses

Each checked or generated file produces one of these statuses:

- `OK` — the file matches its stored hash (check), or a sidecar was written
  successfully (generate).
- `MISMATCH` — the file's actual hash differs from the stored hash. **This is a
  genuine integrity failure and should be investigated.**
- `BAD_MD5` — the `.md5` sidecar is empty, corrupt, or otherwise contains no
  valid hash.
- `UNREADABLE_FILE` — the source file could not be read (truncated file, bad
  media, I/O error).
- `WRITE_ERROR` — (generate only) the `.md5` sidecar could not be written.

### Exit codes

Useful when running from a wrapper script, cron, or a scheduled job:

- `0` — everything OK.
- `1` — operational problems only (bad/empty sidecars, unreadable files, write
  errors), but no integrity mismatches.
- `2` — at least one `MISMATCH` (integrity failure). Highest priority.
- `130` — interrupted with Ctrl-C.

Check the exit code of the last run with:

    echo $?

## Naming scheme for checksum files

This script assumes the following naming scheme for the `.md5` checksum files:

 * Each `.md5` checksum file is stored in the same directory as the file for
   which that checksum was calculated.
 * Each `.md5` checksum file is named the same as the file it describes, with an
   additional `.md5` extension.
   - E.g. the checksum for `dir1/myfile.mov` is stored in
     `dir1/myfile.mov.md5`.

## A note on MD5

MD5 is well suited to detecting accidental corruption — bit rot, bad tape pulls,
and incomplete transfers — which is what this tool checks for. It is **not**
collision-resistant and should not be relied on as a safeguard against
deliberate tampering. If your workflow requires that guarantee, use a tool that
generates and verifies SHA-256 sidecars instead.

## Basic instructions for macOS

 1. Download the script from GitHub (ZIP archive, or clone with **git**).
 2. Place **md5tool.py** somewhere convenient, e.g. a `scripts` directory in your
    Documents folder.
 3. Open the **Terminal** app (in `Applications/Utilities`).
 4. Set the script as executable (only needed once):

        chmod a+x ~/Documents/scripts/md5tool.py
 5. Check files in a directory:

        ~/Documents/scripts/md5tool.py check MYDIRECTORY

    - Replace `MYDIRECTORY` with the directory you want checked.
    - To save typing, you can *drag and drop* a folder from the **Finder** into
      the Terminal window to insert its path.
    - If running the script directly does not work, invoke it explicitly with
      Python 3:

          python3 ~/Documents/scripts/md5tool.py check MYDIRECTORY

## Basic instructions for Microsoft Windows

 1. Install Python 3 from [python.org](https://www.python.org/downloads/). During
    installation, check **"Add Python to PATH"** so it can be found from the
    command line.
 2. Download the script from GitHub (ZIP archive, or clone with **git**).
 3. Place **md5tool.py** somewhere convenient, e.g. a `scripts` directory on your
    `C:` drive.
 4. Open **Command Prompt** or **PowerShell**.
 5. Check files in a directory:

        python C:\scripts\md5tool.py check MYDIRECTORY

    - Replace `MYDIRECTORY` with the directory you want checked.
    - You can also use the Python launcher: `py C:\scripts\md5tool.py check
      MYDIRECTORY`.
