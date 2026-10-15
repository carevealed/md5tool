# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/).

## [2.0.0] - 2026-07-17

Hardened Python 3 rewrite for digital-preservation use. This version processes
large archival batches without aborting on a single bad file or corrupt
checksum sidecar, and reports problem files by category.

### Added
- Graceful handling of empty, corrupt, or non-text `.md5` sidecar files. These
  are now reported as `BAD_MD5` and skipped instead of aborting the run.
- Graceful handling of unreadable or truncated source files. A file that errors
  out mid-read (e.g. a bad LTO tape pull raising `OSError: [Errno 22] Invalid
  argument`) is reported as `UNREADABLE_FILE` and skipped so the rest of the
  batch completes.
- Categorized result statuses: `OK`, `MISMATCH`, `BAD_MD5`, `UNREADABLE_FILE`,
  and `WRITE_ERROR`. A genuine integrity failure (`MISMATCH`) is kept distinct
  from operational problems.
- Meaningful exit codes for scripting and scheduled runs: `0` (all OK),
  `1` (operational problems only), `2` (at least one integrity `MISMATCH`),
  `130` (interrupted with Ctrl-C).
- `-l` / `--log` option to append a timestamped, itemized report of every
  problem file to a log file, for an audit trail.
- Support for GNU coreutils text-mode sidecars (`hash  filename`, two spaces),
  in addition to the existing bare-hash and binary-mode (`hash *filename`)
  formats. The parser now also validates that the token it found is 32 hex
  characters.

### Changed
- Requires Python 3.6+. Python 2 is no longer supported.
- Shebang is now `#!/usr/bin/env python3`, fixing the `bad interpreter:
  /usr/bin/python` error on recent macOS, which no longer ships
  `/usr/bin/python`.
- Command-line parsing moved from the deprecated `optparse` to `argparse`. The
  command syntax is unchanged (`md5tool.py check DIR`, `md5tool.py generate
  DIR`).
- The progress percentage now uses integer division (Python 3 no longer floors
  division automatically).

### Fixed
- `UnicodeDecodeError` crash when a `.md5` sidecar contained non-UTF-8 bytes,
  which aborted the entire batch before any files were verified. Sidecars are
  now read with tolerant decoding.
- `OSError: [Errno 22] Invalid argument` crash when reading a truncated or
  corrupt source file.
- A second crash in the generate path: if a `.md5` file could not be written,
  the previous version printed an error and then failed again trying to use an
  unopened file handle. This is now reported cleanly as `WRITE_ERROR`.

## [1.0.0] - 2014

Original release by matt-grounds. Recursive MD5 generate/check tool for
Python 2.7, 3.4, and 3.6. (Retroactively versioned; the original was not
tagged.)
