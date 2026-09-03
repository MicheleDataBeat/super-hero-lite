#!/usr/bin/env python3
"""Transactional package-owned state management for the Codex distribution."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import os
from pathlib import Path
import re
import shutil
import stat
import subprocess
import sys
import tempfile

try:
    from . import bootstrap, compatibility
except ImportError:
    import bootstrap  # type: ignore[no-redef]
    import compatibility  # type: ignore[no-redef]


LITE_SKILLS = (
    "super-hero-core",
    "super-hero-release-to-public",
    "super-hero-simplify",
)
REQUIRED_COMMANDS = ("git", "gh", "python3", "codex")
TRANSACTION_PREFIX = ".super-hero-lite-transaction-"


class ManagedStateError(Exception):
    """Raised when managed state cannot be changed or validated safely."""


def _resolve_required(command: str) -> str:
    """Resolve a required command, restating any failure in this module's terms."""
    try:
        return compatibility.resolve_command(command)
    except compatibility.CompatibilityError as error:
        raise ManagedStateError(str(error)) from error


def _validate_commands() -> list[str]:
    for command in REQUIRED_COMMANDS:
        _resolve_required(command)
    return [f"PASS  Required commands: {', '.join(REQUIRED_COMMANDS)}"]


def _validate_github_authentication() -> list[str]:
    environment = os.environ.copy()
    environment["NO_COLOR"] = "1"
    result = subprocess.run(
        [_resolve_required("gh"), "auth", "status"],
        env=environment,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode != 0:
        raise ManagedStateError("GitHub CLI authentication failed: run gh auth login")
    return ["PASS  GitHub CLI authenticated"]


def _skill_frontmatter(skill_file: Path, expected_name: str) -> None:
    try:
        text = skill_file.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as error:
        raise ManagedStateError(f"missing or unreadable skill: {skill_file}") from error
    match = re.match(r"\A---\r?\n(.*?)\r?\n---(?:\r?\n|\Z)", text, re.DOTALL)
    if not match:
        raise ManagedStateError(f"invalid skill frontmatter: {skill_file}")
    fields: dict[str, str] = {}
    for line in match.group(1).splitlines():
        if ":" in line:
            key, value = line.split(":", 1)
            fields[key.strip()] = value.strip()
    if fields.get("name") != expected_name or not fields.get("description"):
        raise ManagedStateError(
            f"invalid skill identity for {skill_file}: expected {expected_name}"
        )


def _validate_skill_root(skills_root: Path) -> list[str]:
    for skill in LITE_SKILLS:
        _skill_frontmatter(skills_root / skill / "SKILL.md", skill)
    return [f"PASS  Super-Hero Lite skills: {len(LITE_SKILLS)}"]


def _package_paths(package_root: Path) -> tuple[Path, Path, Path]:
    return (
        package_root / "skills",
        package_root
        / "distributions"
        / "codex"
        / "bootstrap"
        / "AGENTS.md.fragment",
        package_root / "compatibility" / "upstreams.json",
    )


def validate_package(package_root: Path) -> list[str]:
    """Validate only packaged artifacts; never inspect user state."""
    packaged_skills, fragment_path, metadata_path = _package_paths(package_root)
    lines = _validate_skill_root(packaged_skills)
    _validate_no_unowned_skill_packages(packaged_skills)
    try:
        fragment = fragment_path.read_bytes().decode("utf-8")
        if bootstrap.classify(fragment) != "complete":
            raise ManagedStateError("packaged bootstrap is absent")
    except (OSError, UnicodeError, bootstrap.BootstrapError) as error:
        raise ManagedStateError(f"invalid packaged bootstrap: {error}") from error
    # Parsing the metadata in package mode is intentionally local and read-only.
    try:
        compatibility._load_metadata(metadata_path)
    except compatibility.CompatibilityError as error:
        raise ManagedStateError(str(error)) from error
    lines.extend(
        (
            "PASS  Codex bootstrap fragment",
            "PASS  Compatibility metadata",
        )
    )
    return lines


def _validate_no_unowned_skill_packages(packaged_skills: Path) -> None:
    """The package ships exactly the Lite skills and nothing else."""
    if not packaged_skills.is_dir():
        raise ManagedStateError(f"missing packaged skills directory: {packaged_skills}")
    shipped = {
        entry.name
        for entry in packaged_skills.iterdir()
        if entry.is_dir() or entry.is_symlink()
    }
    unexpected = sorted(shipped - set(LITE_SKILLS))
    if unexpected:
        raise ManagedStateError(
            f"package ships a skill this distribution does not own: {', '.join(unexpected)}"
        )


def _validate_markers(agents_path: Path) -> str:
    try:
        text = agents_path.read_bytes().decode("utf-8")
    except FileNotFoundError:
        text = ""
    except (OSError, UnicodeError) as error:
        raise ManagedStateError(f"cannot read {agents_path}: {error}") from error
    try:
        bootstrap.classify(text)
    except bootstrap.BootstrapError as error:
        raise ManagedStateError(f"malformed bootstrap marker: {error}") from error
    return text


def _file_map(root: Path) -> dict[str, bytes]:
    if not root.is_dir():
        return {}
    return {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


def _validate_installed_state(package_root: Path, codex_home: Path) -> list[str]:
    packaged_skills, _, _ = _package_paths(package_root)
    installed_skills = codex_home / "skills"
    lines = _validate_skill_root(installed_skills)
    for skill in LITE_SKILLS:
        if _file_map(packaged_skills / skill) != _file_map(installed_skills / skill):
            raise ManagedStateError(f"installed skill differs from package: {skill}")
    agents_text = _validate_markers(codex_home / "AGENTS.md")
    if bootstrap.classify(agents_text) != "complete":
        raise ManagedStateError("bootstrap marker is not installed")
    lines.extend(("PASS  Installed skill bytes", "PASS  Bootstrap installed"))
    return lines


def _remove_path(path: Path) -> None:
    if path.is_symlink() or path.is_file():
        path.unlink(missing_ok=True)
    elif path.is_dir():
        shutil.rmtree(path)


@dataclass
class Snapshot:
    root: Path
    agents_kind: str
    agents_link_target: str | None
    agents_content_present: bool
    agents_mode: int | None
    owned_kinds: dict[str, str]


def _snapshot(codex_home: Path, snapshot_root: Path) -> Snapshot:
    snapshot_root.mkdir()
    agents = codex_home / "AGENTS.md"
    agents_kind = "absent"
    agents_link_target: str | None = None
    agents_content_present = False
    agents_mode: int | None = None
    if agents.is_symlink():
        agents_kind = "symlink"
        agents_link_target = os.readlink(agents)
    elif agents.exists():
        agents_kind = "file"
    if agents_kind != "absent":
        try:
            content = agents.read_bytes()
            (snapshot_root / "AGENTS.md.content").write_bytes(content)
            agents_content_present = True
            agents_mode = stat.S_IMODE(agents.stat().st_mode)
        except FileNotFoundError:
            pass
    owned_kinds: dict[str, str] = {}
    skills_root = codex_home / "skills"
    snapshot_skills = snapshot_root / "skills"
    for skill in LITE_SKILLS:
        source = skills_root / skill
        if source.is_symlink():
            snapshot_skills.mkdir(exist_ok=True)
            shutil.copy2(
                source,
                snapshot_skills / skill,
                follow_symlinks=False,
            )
            owned_kinds[skill] = "symlink"
        elif source.is_dir():
            snapshot_skills.mkdir(exist_ok=True)
            shutil.copytree(source, snapshot_skills / skill, symlinks=True)
            owned_kinds[skill] = "directory"
        elif source.exists():
            snapshot_skills.mkdir(exist_ok=True)
            shutil.copy2(source, snapshot_skills / skill)
            owned_kinds[skill] = "file"
    return Snapshot(
        snapshot_root,
        agents_kind,
        agents_link_target,
        agents_content_present,
        agents_mode,
        owned_kinds,
    )


def _path_present(path: Path) -> bool:
    return path.exists() or path.is_symlink()


def _move_to_rollback(path: Path, rollback_path: Path) -> None:
    if not _path_present(path):
        return
    rollback_path.parent.mkdir(parents=True, exist_ok=True)
    os.replace(path, rollback_path)


def _restore(codex_home: Path, snapshot: Snapshot, rollback_root: Path) -> None:
    agents = codex_home / "AGENTS.md"
    if snapshot.agents_kind == "absent":
        _remove_path(agents)
    elif snapshot.agents_kind == "file":
        if agents.is_symlink():
            agents.unlink()
        bootstrap.atomic_write_bytes(
            agents, (snapshot.root / "AGENTS.md.content").read_bytes()
        )
        if snapshot.agents_mode is not None:
            agents.chmod(snapshot.agents_mode)
    else:
        if (
            not agents.is_symlink()
            or os.readlink(agents) != snapshot.agents_link_target
        ):
            _remove_path(agents)
            codex_home.mkdir(parents=True, exist_ok=True)
            assert snapshot.agents_link_target is not None
            agents.symlink_to(snapshot.agents_link_target)
        target = bootstrap.resolve_write_path(agents)
        if snapshot.agents_content_present:
            bootstrap.atomic_write_bytes(
                agents, (snapshot.root / "AGENTS.md.content").read_bytes()
            )
            if snapshot.agents_mode is not None:
                target.chmod(snapshot.agents_mode)
        else:
            _remove_path(target)
    skills_root = codex_home / "skills"
    for skill in LITE_SKILLS:
        target = skills_root / skill
        rollback_path = rollback_root / "skills" / skill
        if _path_present(rollback_path):
            _remove_path(target)
            skills_root.mkdir(parents=True, exist_ok=True)
            os.replace(rollback_path, target)
            continue
        if skill not in snapshot.owned_kinds:
            _remove_path(target)
            continue
        if _path_present(target):
            continue
        skills_root.mkdir(parents=True, exist_ok=True)
        source = snapshot.root / "skills" / skill
        if snapshot.owned_kinds[skill] == "directory":
            shutil.copytree(source, target, symlinks=True)
        else:
            shutil.copy2(source, target, follow_symlinks=False)


def _stage_skills(package_root: Path, staging_root: Path) -> Path:
    packaged_skills, _, _ = _package_paths(package_root)
    staged_skills = staging_root / "staged-skills"
    staged_skills.mkdir()
    try:
        for skill in LITE_SKILLS:
            shutil.copytree(packaged_skills / skill, staged_skills / skill)
        _validate_skill_root(staged_skills)
        for skill in LITE_SKILLS:
            if _file_map(packaged_skills / skill) != _file_map(staged_skills / skill):
                raise ManagedStateError(f"staged skill differs from package: {skill}")
    except Exception as error:
        raise ManagedStateError(f"staged skill validation failed: {error}") from error
    return staged_skills


def _replace_lite_skills(
    staged_skills: Path, codex_home: Path, rollback_root: Path
) -> None:
    skills_root = codex_home / "skills"
    skills_root.mkdir(parents=True, exist_ok=True)
    for skill in LITE_SKILLS:
        target = skills_root / skill
        _move_to_rollback(target, rollback_root / "skills" / skill)
        os.replace(staged_skills / skill, target)


def _remove_owned_skills(codex_home: Path, rollback_root: Path) -> None:
    skills_root = codex_home / "skills"
    for skill in LITE_SKILLS:
        _move_to_rollback(
            skills_root / skill,
            rollback_root / "skills" / skill,
        )


def _validate_failpoint() -> None:
    failpoint = os.environ.get("SUPER_HERO_LITE_TEST_FAILPOINT")
    testing = os.environ.get("SUPER_HERO_LITE_TESTING")
    if failpoint is None:
        return
    if failpoint != "after-mutation" or testing != "1":
        raise ManagedStateError("unsupported test failpoint")


def _forced_failure_requested() -> bool:
    return (
        os.environ.get("SUPER_HERO_LITE_TESTING") == "1"
        and os.environ.get("SUPER_HERO_LITE_TEST_FAILPOINT") == "after-mutation"
    )


def install_state(package_root: Path, home: Path, codex_home: Path) -> list[str]:
    """Validate, stage, snapshot, mutate, validate, and roll back on failure."""
    lines = _validate_commands()
    lines.extend(_validate_github_authentication())
    _, _, metadata = _package_paths(package_root)
    lines.extend(compatibility.validate_upstreams(home, codex_home, metadata))
    lines.extend(validate_package(package_root))
    _validate_failpoint()
    agents_path = codex_home / "AGENTS.md"
    prior_agents = _validate_markers(agents_path)

    codex_home_existed = codex_home.is_dir()
    codex_home.mkdir(parents=True, exist_ok=True)
    completed = False
    try:
        with tempfile.TemporaryDirectory(
            prefix=TRANSACTION_PREFIX, dir=codex_home
        ) as transaction_name:
            transaction = Path(transaction_name)
            staged_skills = _stage_skills(package_root, transaction)
            snapshot = _snapshot(codex_home, transaction / "snapshot")
            rollback_root = transaction / "rollback"
            try:
                _replace_lite_skills(staged_skills, codex_home, rollback_root)
                fragment = _package_paths(package_root)[1].read_bytes().decode("utf-8")
                bootstrap.atomic_write(
                    agents_path, bootstrap.install(prior_agents, fragment)
                )
                if _forced_failure_requested():
                    raise ManagedStateError("controlled after-mutation failure")
                lines.extend(_validate_installed_state(package_root, codex_home))
            except BaseException:
                _restore(codex_home, snapshot, rollback_root)
                raise
        completed = True
    finally:
        if not codex_home_existed and not completed:
            skills_root = codex_home / "skills"
            if skills_root.is_dir() and not any(skills_root.iterdir()):
                skills_root.rmdir()
            if codex_home.is_dir() and not any(codex_home.iterdir()):
                codex_home.rmdir()
    return lines


def validate_state(package_root: Path, home: Path, codex_home: Path) -> list[str]:
    lines = _validate_commands()
    lines.extend(_validate_github_authentication())
    _, _, metadata = _package_paths(package_root)
    lines.extend(compatibility.validate_upstreams(home, codex_home, metadata))
    lines.extend(validate_package(package_root))
    lines.extend(_validate_installed_state(package_root, codex_home))
    return lines


def _validate_absence(codex_home: Path) -> None:
    skills_root = codex_home / "skills"
    for skill in LITE_SKILLS:
        if _path_present(skills_root / skill):
            raise ManagedStateError(f"owned skill remains after uninstall: {skill}")
    text = _validate_markers(codex_home / "AGENTS.md")
    if bootstrap.classify(text) != "absent":
        raise ManagedStateError("owned bootstrap remains after uninstall")


def uninstall_state(codex_home: Path) -> list[str]:
    """Remove only package-owned blocks and skills, restoring on failure."""
    agents_path = codex_home / "AGENTS.md"
    prior_agents = _validate_markers(agents_path)
    skills_root = codex_home / "skills"
    has_owned_skills = any(
        _path_present(skills_root / skill) for skill in LITE_SKILLS
    )
    if not has_owned_skills and bootstrap.classify(prior_agents) == "absent":
        return ["PASS  Super-Hero Lite managed state already absent"]
    codex_home.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(
        prefix=TRANSACTION_PREFIX, dir=codex_home
    ) as transaction_name:
        transaction = Path(transaction_name)
        snapshot = _snapshot(codex_home, transaction / "snapshot")
        rollback_root = transaction / "rollback"
        try:
            _remove_owned_skills(codex_home, rollback_root)
            updated_agents = bootstrap.uninstall(prior_agents)
            if updated_agents:
                bootstrap.atomic_write(agents_path, updated_agents)
            elif agents_path.is_symlink():
                bootstrap.atomic_write_bytes(agents_path, b"")
            else:
                agents_path.unlink(missing_ok=True)
            _validate_absence(codex_home)
        except BaseException:
            _restore(codex_home, snapshot, rollback_root)
            raise
    return ["PASS  Super-Hero Lite managed state removed"]


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    for command in ("install", "validate", "uninstall"):
        child = subparsers.add_parser(command)
        child.add_argument("--package-root", type=Path, required=True)
        child.add_argument("--home", type=Path, required=True)
        child.add_argument("--codex-home", type=Path, required=True)
        if command == "validate":
            child.add_argument("--package", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    arguments = _parser().parse_args(argv)
    try:
        if arguments.command == "install":
            lines = install_state(
                arguments.package_root.resolve(),
                arguments.home.resolve(),
                arguments.codex_home.resolve(),
            )
        elif arguments.command == "uninstall":
            lines = uninstall_state(arguments.codex_home.resolve())
        elif arguments.package:
            lines = validate_package(arguments.package_root.resolve())
        else:
            lines = validate_state(
                arguments.package_root.resolve(),
                arguments.home.resolve(),
                arguments.codex_home.resolve(),
            )
    except Exception as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1
    for line in lines:
        print(line)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
