#!/usr/bin/env python3
"""Total, atomic management of the package-owned Claude Code bootstrap block."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import stat
import sys
import tempfile


MARKERS = (
    "<!-- BEGIN SUPER_HERO_LITE_CLAUDE_CODE_BOOTSTRAP v1 -->",
    "<!-- END SUPER_HERO_LITE_CLAUDE_CODE_BOOTSTRAP v1 -->",
)


class BootstrapError(Exception):
    """Raised when bootstrap state cannot be classified safely."""


def classify(text: str) -> str:
    """Return 'absent' or 'complete'; raise for duplicates or halves."""
    begin, end = MARKERS
    begin_count = text.count(begin)
    end_count = text.count(end)
    if begin_count == 0 and end_count == 0:
        return "absent"
    if begin_count != 1 or end_count != 1 or text.index(begin) > text.index(end):
        raise BootstrapError("malformed bootstrap marker pair")
    return "complete"


def _remove(text: str) -> str:
    if classify(text) == "absent":
        return text
    begin, end = MARKERS
    start = text.index(begin)
    stop = text.index(end, start) + len(end)
    # A final line ending belongs to a terminal managed block. Never consume a
    # line ending when unrelated content follows it.
    trailing = text[stop:]
    if trailing in ("\n", "\r", "\r\n"):
        stop = len(text)
    return text[:start] + text[stop:]


def install(text: str, fragment: str) -> str:
    """Validate the owned pair, remove any owned block, and append one block."""
    classify(text)
    if classify(fragment) != "complete":
        raise BootstrapError("invalid packaged bootstrap fragment")

    return _remove(text) + fragment


def uninstall(text: str) -> str:
    """Validate the owned pair and remove a complete package-owned block."""
    classify(text)
    return _remove(text)


def atomic_write(path: Path, text: str) -> None:
    """Replace path atomically using a sibling temporary file."""
    atomic_write_bytes(path, text.encode("utf-8"))


def atomic_write_bytes(path: Path, content: bytes) -> None:
    """Replace path atomically without newline or encoding transformations."""
    write_path = resolve_write_path(path)
    try:
        if write_path.read_bytes() == content:
            return
    except FileNotFoundError:
        pass
    write_path.parent.mkdir(parents=True, exist_ok=True)
    prior_mode = (
        stat.S_IMODE(write_path.stat().st_mode) if write_path.exists() else 0o644
    )
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{write_path.name}.", dir=write_path.parent
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        temporary.chmod(prior_mode)
        os.replace(temporary, write_path)
    finally:
        temporary.unlink(missing_ok=True)


def resolve_write_path(path: Path) -> Path:
    """Return the referent to update while preserving a top-level symlink."""
    if not path.is_symlink():
        return path
    link_target = Path(os.readlink(path))
    if not link_target.is_absolute():
        link_target = path.parent / link_target
    return link_target.resolve(strict=False)


def _read_optional(path: Path) -> str:
    try:
        return path.read_bytes().decode("utf-8")
    except FileNotFoundError:
        return ""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    install_parser = subparsers.add_parser("install")
    install_parser.add_argument("instructions_path", type=Path)
    install_parser.add_argument("fragment_path", type=Path)
    validate_parser = subparsers.add_parser("validate")
    validate_parser.add_argument("instructions_path", type=Path)
    uninstall_parser = subparsers.add_parser("uninstall")
    uninstall_parser.add_argument("instructions_path", type=Path)
    arguments = parser.parse_args(argv)

    try:
        text = _read_optional(arguments.instructions_path)
        if arguments.command == "install":
            fragment = arguments.fragment_path.read_bytes().decode("utf-8")
            atomic_write(arguments.instructions_path, install(text, fragment))
        elif arguments.command == "validate":
            classify(text)
        else:
            result = uninstall(text)
            if result:
                atomic_write(arguments.instructions_path, result)
            elif arguments.instructions_path.is_symlink():
                atomic_write_bytes(arguments.instructions_path, b"")
            elif arguments.instructions_path.exists():
                arguments.instructions_path.unlink()
    except (BootstrapError, OSError, UnicodeError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
