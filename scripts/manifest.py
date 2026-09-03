#!/usr/bin/env python3
"""Write and verify the distributable file manifest.

This is the single implementation of the manifest rule. `scripts/manifest.sh`
is the POSIX entry point and delegates here, so a Host without `find`, `sort`
and `shasum` still verifies exactly the same file set and digests.
"""

from __future__ import annotations

import difflib
import hashlib
import os
from pathlib import Path
import sys


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
MANIFEST_NAME = "MANIFEST.sha256"
USAGE = "Usage: scripts/manifest.py --write|--verify"

# Directory trees that never ship: version control, release scratch space,
# agent worktrees, and interpreter caches.
PRUNED_DIRECTORIES = frozenset(
    {
        ".git",
        ".release",
        ".worktrees",
    }
)
PRUNED_DIRECTORY_NAMES = frozenset({"__pycache__"})
# A linked worktree records its repository in a regular file named `.git`, so
# these names are excluded as files as well as directories.
EXCLUDED_FILES = frozenset({".git", ".release", "AGENTS.md", MANIFEST_NAME})
EXCLUDED_SUFFIXES = (".pyc", ".pyo")


def distributable_paths(root: Path) -> list[str]:
    """Return every shipped file as a `./`-prefixed POSIX path, C-sorted."""
    paths: list[str] = []
    for directory, subdirectories, files in os.walk(root):
        relative = Path(directory).relative_to(root).as_posix()
        prefix = "" if relative == "." else f"{relative}/"
        subdirectories[:] = [
            name
            for name in subdirectories
            if name not in PRUNED_DIRECTORY_NAMES
            and f"{prefix}{name}" not in PRUNED_DIRECTORIES
        ]
        for name in files:
            path = f"{prefix}{name}"
            if path in EXCLUDED_FILES or name.endswith(EXCLUDED_SUFFIXES):
                continue
            entry = Path(directory) / name
            # find(1) without -L reports a symlink as a link, never as a file.
            if entry.is_symlink() or not entry.is_file():
                continue
            paths.append(f"./{path}")
    return sorted(paths, key=lambda path: path.encode("utf-8"))


def _digest(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def manifest_contents(root: Path) -> str:
    """Return the manifest text in the two-space `shasum -a 256` format."""
    return "".join(
        f"{_digest(root / path)}  {path}\n" for path in distributable_paths(root)
    )


def _write(root: Path) -> int:
    contents = manifest_contents(root)
    target = root / MANIFEST_NAME
    temporary = target.with_name(f".{MANIFEST_NAME}.new")
    temporary.write_text(contents, encoding="utf-8", newline="\n")
    os.replace(temporary, target)
    return 0


def _verify(root: Path) -> int:
    computed = manifest_contents(root)
    target = root / MANIFEST_NAME
    try:
        recorded = target.read_text(encoding="utf-8")
    except OSError as error:
        print(f"ERROR: cannot read {MANIFEST_NAME}: {error}", file=sys.stderr)
        return 1
    if recorded == computed:
        return 0
    sys.stdout.writelines(
        difflib.unified_diff(
            recorded.splitlines(keepends=True),
            computed.splitlines(keepends=True),
            fromfile=f"{MANIFEST_NAME} (recorded)",
            tofile=f"{MANIFEST_NAME} (computed)",
        )
    )
    return 1


def main(argv: list[str] | None = None) -> int:
    arguments = sys.argv[1:] if argv is None else argv
    if len(arguments) != 1 or arguments[0] not in ("--write", "--verify"):
        print(USAGE, file=sys.stderr)
        return 2
    if arguments[0] == "--write":
        return _write(PACKAGE_ROOT)
    return _verify(PACKAGE_ROOT)


if __name__ == "__main__":
    raise SystemExit(main())
