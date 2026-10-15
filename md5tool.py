#!/usr/bin/env python3
"""md5tool.py -- generate or verify MD5 checksums recursively across a directory tree.

Python 3 rewrite hardened for digital-preservation batches:

  * Empty, unreadable, or non-text .md5 sidecar files are reported and skipped
    instead of crashing with UnicodeDecodeError.
  * Source files that error out mid-read (truncated tape pulls, bad media,
    OSError [Errno 22] Invalid argument, etc.) are logged and skipped so the
    rest of the batch still completes.
  * Every problem is categorised -- a hash MISMATCH (real integrity failure) is
    kept distinct from operational errors (BAD_MD5, UNREADABLE_FILE) -- and the
    run can append a timestamped report to a log file.

Tested on Python 3.6+ (developed on 3.12).

Usage:
    md5tool.py check    dir1 [dir2 ...]      verify files against .md5 sidecars
    md5tool.py generate dir1 [dir2 ...]      create .md5 sidecars where missing
    md5tool.py --help

Exit codes:
    0  everything OK
    1  operational problems only (bad/empty .md5, unreadable source, write error)
    2  at least one hash MISMATCH (integrity failure) -- highest priority
    130 interrupted with Ctrl-C
"""

import argparse
import hashlib
import os
import os.path
import sys
from datetime import datetime

HASH_LENGTH = 32          # hex characters in an MD5 digest
SEPARATOR = "=" * 63

# Result status codes
OK = 'OK'
MISMATCH = 'MISMATCH'                # hash differs -> genuine integrity failure
BAD_MD5 = 'BAD_MD5'                  # empty/corrupt/unreadable .md5 sidecar
UNREADABLE_FILE = 'UNREADABLE_FILE'  # source file could not be read
WRITE_ERROR = 'WRITE_ERROR'          # could not write a .md5 sidecar (generate)


# ---------------------------------------------------------------------------
# Terminal progress helpers
# ---------------------------------------------------------------------------

def _write_progress(percent, filename):
    """Overwrite the current terminal line with a progress indicator."""
    label = "{0:>3}% {1}".format(percent, os.path.basename(filename))
    sys.stdout.write("\r{0:<78}".format(label[:78]))
    sys.stdout.flush()


def _clear_progress():
    """Wipe the progress line so a result line prints cleanly."""
    sys.stdout.write("\r{0:<78}\r".format(""))
    sys.stdout.flush()


# ---------------------------------------------------------------------------
# Hashing and .md5 parsing
# ---------------------------------------------------------------------------

def is_md5_hex(token):
    """Return True if token looks like a 32-character hex MD5 digest."""
    if len(token) != HASH_LENGTH:
        return False
    try:
        int(token, 16)
    except ValueError:
        return False
    return True


def read_hash_from_md5_file(md5_filename):
    """Read an MD5 hash out of a .md5 sidecar file.

    Returns the lowercase hex hash, or None if no valid hash can be found
    (empty file, corrupt/binary content, unreadable file, ...).

    errors='replace' means a binary or partially written .md5 degrades into
    replacement characters instead of raising UnicodeDecodeError, so a bad
    sidecar becomes a clean "no valid hash" result rather than a crash.
    """
    try:
        with open(md5_filename, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()
    except OSError:
        return None

    for line in content.splitlines():
        stripped = line.strip()
        if not stripped or stripped[0] == ';':
            continue  # blank line or comment

        # "hash" on its own
        if is_md5_hex(stripped):
            return stripped.lower()

        # "hash *filename" (md5sum binary mode)
        star = stripped.find('*')
        if star != -1:
            candidate = stripped[:star].strip().lower()
            if is_md5_hex(candidate):
                return candidate

        # "hash  filename" (md5sum text mode / GNU coreutils)
        first_token = stripped.split()[0].lower()
        if is_md5_hex(first_token):
            return first_token

    return None


def generate_md5_hash(filename, block_size=2 ** 20, progress_blocks=128):
    """Stream a file in blocks and return its MD5 hex digest.

    Raises OSError if the file cannot be opened or read (truncated file, bad
    media, invalid argument, ...). Callers catch this and continue the batch.
    """
    md5 = hashlib.md5()
    blocks = 0
    file_size = os.path.getsize(filename)          # may raise OSError
    total_blocks = 1 + (file_size // block_size)

    with open(filename, 'rb') as f:                # may raise OSError
        while True:
            data = f.read(block_size)              # may raise OSError mid-read
            if not data:
                break
            md5.update(data)
            if (blocks % progress_blocks) == 0:
                percent = 100 * blocks // total_blocks
                _write_progress(percent, filename)
            blocks += 1

    return md5.hexdigest()


# ---------------------------------------------------------------------------
# Per-file operations
# ---------------------------------------------------------------------------

def check_against_md5_file(filename, md5_filename):
    """Verify filename against its md5 sidecar.

    Returns a (status, filename, detail) tuple.
    """
    expected_hash = read_hash_from_md5_file(md5_filename)
    if expected_hash is None:
        _clear_progress()
        print("BAD_MD5    {0}".format(filename))
        print("           no valid hash in {0} (empty or corrupt?)".format(md5_filename))
        return (BAD_MD5, filename, "no valid hash in {0}".format(md5_filename))

    try:
        actual_hash = generate_md5_hash(filename)
    except OSError as e:
        _clear_progress()
        print("UNREADABLE {0}".format(filename))
        print("           {0}".format(e))
        return (UNREADABLE_FILE, filename, str(e))

    _clear_progress()
    if actual_hash == expected_hash:
        print("OK         {0}".format(filename))
        return (OK, filename, "")

    print("MISMATCH   {0}".format(filename))
    print("           expected {0}".format(expected_hash))
    print("           actual   {0}".format(actual_hash))
    return (MISMATCH, filename,
            "expected {0}, actual {1}".format(expected_hash, actual_hash))


def generate_md5_file_for(filename, md5_filename):
    """Create a .md5 sidecar for an existing file.

    Returns a (status, filename, detail) tuple.
    """
    try:
        generated_hash = generate_md5_hash(filename)
    except OSError as e:
        _clear_progress()
        print("UNREADABLE {0}".format(filename))
        print("           {0}".format(e))
        return (UNREADABLE_FILE, filename, str(e))

    try:
        with open(md5_filename, 'w', encoding='utf-8') as out:
            out.write("{0} *{1}\n".format(generated_hash,
                                          os.path.basename(filename)))
    except OSError as e:
        _clear_progress()
        print("WRITEFAIL  {0}".format(md5_filename))
        print("           {0}".format(e))
        return (WRITE_ERROR, filename, str(e))

    _clear_progress()
    print("DONE       {0}".format(filename))
    return (OK, filename, "")


# ---------------------------------------------------------------------------
# Directory walk
# ---------------------------------------------------------------------------

def get_file_info_dictionaries(dirs, verbose=False):
    """Walk directories recursively and pair .md5 sidecars with their files."""
    file_info = {}
    for d in dirs:
        for dirpath, _dirnames, filenames in os.walk(d):
            for name in filenames:
                full_path = os.path.join(dirpath, name)
                is_md5 = full_path[-4:].lower() == '.md5'
                key = full_path[:-4] if is_md5 else full_path
                entry = file_info.setdefault(key, {'file': False, 'md5': False})
                entry['md5' if is_md5 else 'file'] = True

    files_only = md5_only = both = 0
    for key, entry in file_info.items():
        if entry['md5'] and entry['file']:
            both += 1
        elif entry['file']:
            files_only += 1
            if verbose:
                print('File "{0}" has no matching .md5 file.'.format(key))
        elif entry['md5']:
            md5_only += 1
            if verbose:
                print('MD5 file "{0}.md5" has no matching file.'.format(key))

    print("Found {0} files with matching .md5 files.".format(both))
    print("Found {0} .md5 files with no matching file.".format(md5_only))
    print("Found {0} files with no matching .md5 file.".format(files_only))
    return file_info


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------

def report(results, operation, log_path=None):
    """Print a categorised summary, optionally append it to a log, return exit code."""
    counts = {}
    for status, _f, _d in results:
        counts[status] = counts.get(status, 0) + 1

    lines = [SEPARATOR,
             "SUMMARY  ({0})".format(datetime.now().isoformat(timespec='seconds')),
             "{0} files processed.".format(len(results)),
             "  OK:              {0}".format(counts.get(OK, 0))]
    if operation == 'check':
        lines.append("  MISMATCH:        {0}".format(counts.get(MISMATCH, 0)))
        lines.append("  BAD_MD5:         {0}".format(counts.get(BAD_MD5, 0)))
    lines.append("  UNREADABLE_FILE: {0}".format(counts.get(UNREADABLE_FILE, 0)))
    if operation == 'generate':
        lines.append("  WRITE_ERROR:     {0}".format(counts.get(WRITE_ERROR, 0)))

    problems = [r for r in results if r[0] != OK]
    if problems:
        lines.append("")
        lines.append("PROBLEM FILES:")
        for status, filename, detail in problems:
            lines.append("  [{0}] {1}".format(status, filename))
            if detail:
                lines.append("        {0}".format(detail))
    lines.append(SEPARATOR)

    text = "\n".join(lines)
    print(text)

    if log_path:
        try:
            with open(log_path, 'a', encoding='utf-8') as log:
                log.write(text + "\n")
            print("Log appended to {0}".format(log_path))
        except OSError as e:
            print("WARNING: could not write log file {0}: {1}".format(log_path, e))

    if counts.get(MISMATCH, 0):
        return 2
    if any(counts.get(s, 0) for s in (BAD_MD5, UNREADABLE_FILE, WRITE_ERROR)):
        return 1
    return 0


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="Generate or verify MD5 checksums recursively.")
    parser.add_argument(
        'operation', choices=['check', 'generate'],
        help="'check' verifies files against .md5 sidecars; "
             "'generate' creates .md5 sidecars for files missing them.")
    parser.add_argument(
        'dirs', nargs='+', metavar='DIR',
        help="one or more directories to walk recursively.")
    parser.add_argument(
        '-v', '--verbose', action='store_true',
        help="report files / .md5 files that have no matching pair.")
    parser.add_argument(
        '-l', '--log', metavar='LOGFILE', default=None,
        help="append a categorised report to this log file.")

    args = parser.parse_args(argv)
    for d in args.dirs:
        if not os.path.isdir(d):
            parser.error("{0} is not a valid directory.".format(d))
    return args


def main(argv=None):
    args = parse_args(argv)
    file_info = get_file_info_dictionaries(args.dirs, verbose=args.verbose)
    print(SEPARATOR)

    results = []
    if args.operation == 'check':
        for filename, entry in sorted(file_info.items()):
            if entry['file'] and entry['md5']:
                results.append(check_against_md5_file(filename, filename + '.md5'))
    else:  # generate
        for filename, entry in sorted(file_info.items()):
            if entry['file'] and not entry['md5']:
                results.append(generate_md5_file_for(filename, filename + '.md5'))

    return report(results, args.operation, args.log)


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        _clear_progress()
        print("\nInterrupted.")
        sys.exit(130)
