#!/usr/bin/env python3
"""Read-only upstream compatibility validation for the Codex distribution."""

from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import subprocess


POCOCK_SOURCE = "mattpocock/skills"
POCOCK_SKILLS = (
    "setup-matt-pocock-skills",
    "grill-with-docs",
    "to-spec",
    "to-tickets",
    "implement",
    "wayfinder",
    "tdd",
    "code-review",
    "diagnosing-bugs",
    "domain-modeling",
    "codebase-design",
)
# Nothing here names a version. The CLI resolves its own latest release, and a
# repository URL without a /tree/<ref> suffix resolves the default branch, so
# whoever runs this gets what the upstream currently publishes.
POCOCK_INSTALL_COMMAND = (
    "npx --yes skills add "
    "https://github.com/mattpocock/skills "
    "--skill '*' --agent codex --global --yes"
)
SUPERPOWERS_PLUGIN = "superpowers@openai-curated"
DISTRIBUTION_ID = "codex"
SCHEMA_VERSION = 1


class CompatibilityError(Exception):
    """Raised when an installed upstream is unsupported or unavailable."""


# Windows resolves a bare command name against PATH for executables only, so an
# npm-installed CLI, which is a `.cmd` shim, is never found under its bare name.
# Resolve every host command to an installed path before running it.
INTERPRETER_NAMES = ("python3", "python", "py")


def resolve_command(command: str) -> str:
    """Return the installed path of a required command, or fail under its name."""
    candidates = INTERPRETER_NAMES if command == "python3" else (command,)
    for candidate in candidates:
        resolved = shutil.which(candidate)
        if resolved is not None:
            return resolved
    raise CompatibilityError(f"missing required command: {command}")


def _load_metadata(metadata: Path) -> dict[str, object]:
    """Return the recorded profile for this distribution alone."""
    try:
        result = json.loads(metadata.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise CompatibilityError(f"invalid compatibility metadata: {error}") from error
    if not isinstance(result, dict) or result.get("schemaVersion") != SCHEMA_VERSION:
        raise CompatibilityError(
            f"invalid compatibility metadata: expected schemaVersion {SCHEMA_VERSION}"
        )
    distributions = result.get("distributions")
    if not isinstance(distributions, list):
        raise CompatibilityError(
            "invalid compatibility metadata: distributions must be a list"
        )
    matches = [
        item
        for item in distributions
        if isinstance(item, dict) and item.get("id") == DISTRIBUTION_ID
    ]
    if len(matches) != 1:
        raise CompatibilityError(
            f"invalid compatibility metadata: expected one {DISTRIBUTION_ID} distribution"
        )
    profile = matches[0]
    if not isinstance(profile.get("dependencies"), list):
        raise CompatibilityError(
            "invalid compatibility metadata: dependencies must be a list"
        )
    return profile


def _dependency(profile: dict[str, object], identifier: str) -> dict[str, object]:
    dependencies = profile["dependencies"]
    assert isinstance(dependencies, list)
    matches = [
        item
        for item in dependencies
        if isinstance(item, dict) and item.get("id") == identifier
    ]
    if len(matches) != 1:
        raise CompatibilityError(
            f"invalid compatibility metadata: expected one {identifier} dependency"
        )
    return matches[0]


def _pocock_error(reason: str) -> CompatibilityError:
    return CompatibilityError(
        "incompatible Pocock prerequisite: "
        f"{reason}. Install the prerequisite with:\n{POCOCK_INSTALL_COMMAND}"
    )


def _validate_pocock(home: Path, codex_home: Path) -> str:
    lock_path = home / ".agents" / ".skill-lock.json"
    try:
        lock = json.loads(lock_path.read_text(encoding="utf-8"))
    except FileNotFoundError as error:
        raise _pocock_error(f"missing lock file {lock_path}") from error
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise _pocock_error(f"cannot parse lock file {lock_path}: {error}") from error
    if not isinstance(lock, dict) or not isinstance(lock.get("skills"), dict):
        raise _pocock_error(f"invalid skills mapping in {lock_path}")

    entries = lock["skills"]
    missing: list[str] = []
    incompatible: list[str] = []
    for skill in POCOCK_SKILLS:
        entry = entries.get(skill)
        if not isinstance(entry, dict) or entry.get("source") != POCOCK_SOURCE:
            incompatible.append(skill)
        candidates = (
            home / ".agents" / "skills" / skill / "SKILL.md",
            codex_home / "skills" / skill / "SKILL.md",
        )
        if not any(candidate.is_file() for candidate in candidates):
            missing.append(skill)
    if incompatible:
        raise _pocock_error(
            f"lock source must be {POCOCK_SOURCE} for {', '.join(incompatible)}"
        )
    if missing:
        raise _pocock_error(f"missing required skills: {', '.join(missing)}")
    return (
        f"PASS  Pocock prerequisite: {len(POCOCK_SKILLS)} skills from "
        f"{POCOCK_SOURCE}"
    )


def _validate_superpowers() -> str:
    environment = os.environ.copy()
    environment["NO_COLOR"] = "1"
    try:
        result = subprocess.run(
            [resolve_command("codex"), "plugin", "list"],
            env=environment,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
    except OSError as error:
        raise CompatibilityError(f"cannot run codex plugin list: {error}") from error

    enabled = False
    if result.returncode == 0:
        for line in result.stdout.splitlines():
            tokens = line.split()
            if SUPERPOWERS_PLUGIN not in tokens:
                continue
            states = {token.casefold() for token in tokens}
            if "enabled" in states and "disabled" not in states:
                enabled = True
                break
    if not enabled:
        raise CompatibilityError(
            "Superpowers plugin is missing or disabled: enable "
            f"{SUPERPOWERS_PLUGIN} from the official Codex plugin marketplace"
        )
    return f"PASS  Superpowers plugin enabled: {SUPERPOWERS_PLUGIN}"


def validate_upstreams(home: Path, codex_home: Path, metadata: Path) -> list[str]:
    """Return human-readable result lines; reject unsupported installed state.

    Two of the three lines are verdicts from checks that raise when they fail.
    The third is the recorded baseline, which nothing verifies against the
    installed state, so it is not labelled as a verdict.
    """
    parsed = _load_metadata(metadata)
    pocock = _dependency(parsed, "mattpocock-skills")
    superpowers = _dependency(parsed, "superpowers")
    if (
        not isinstance(pocock.get("detection"), dict)
        or pocock["detection"].get("source") != POCOCK_SOURCE
    ):
        raise CompatibilityError("invalid compatibility metadata: Pocock source identity")
    if (
        not isinstance(superpowers.get("detection"), dict)
        or superpowers["detection"].get("pluginId") != SUPERPOWERS_PLUGIN
        or superpowers["detection"].get("requiredState") != "enabled"
    ):
        raise CompatibilityError(
            "invalid compatibility metadata: Superpowers plugin identity"
        )
    return [
        _validate_pocock(home, codex_home),
        _validate_superpowers(),
        "NOTE  Recorded upstream refs, not verified against what is installed: "
        f"Pocock {pocock.get('testedRef')}, "
        f"Superpowers {superpowers.get('testedRef')}",
    ]
