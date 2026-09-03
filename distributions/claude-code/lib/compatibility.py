#!/usr/bin/env python3
"""Read-only upstream compatibility validation for the Claude Code distribution."""

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
    "--skill '*' --agent claude-code --global --yes"
)
SUPERPOWERS_PLUGIN = "superpowers@superpowers-marketplace"
DISTRIBUTION_ID = "claude-code"
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


def _pocock_error(reason: str, *, install_hint: bool = True) -> CompatibilityError:
    message = f"incompatible Pocock prerequisite: {reason}"
    if install_hint:
        message += f". Install the prerequisite with:\n{POCOCK_INSTALL_COMMAND}"
    return CompatibilityError(message)


def _validate_pocock(home: Path, claude_home: Path) -> str:
    lock_path = home / ".agents" / ".skill-lock.json"
    try:
        lock = json.loads(lock_path.read_text(encoding="utf-8"))
    except FileNotFoundError as error:
        raise _pocock_error(f"missing lock file {lock_path}") from error
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise _pocock_error(f"cannot parse lock file {lock_path}: {error}") from error
    if not isinstance(lock, dict) or not isinstance(lock.get("skills"), dict):
        raise _pocock_error(f"invalid skills mapping in {lock_path}")

    # skillOverrides, observed on Claude Code 2.1.258 (see
    # docs/compatibility.md), is a per-skill availability control, separate
    # from disk presence, that only exists in settings.json's user scope.
    # Project (`.claude/settings.json`) and local
    # (`.claude/settings.local.json`) scopes are per-project and outside what
    # a host-directory validator can know, so they are deliberately not read
    # here; only the user-scope file below claude_home is consulted.
    settings_path = claude_home / "settings.json"
    try:
        settings_text = settings_path.read_text(encoding="utf-8")
    except FileNotFoundError:
        settings_text = ""
    except (OSError, UnicodeError) as error:
        raise _pocock_error(
            f"cannot parse settings file {settings_path}: {error}"
        ) from error
    # A fresh Claude Code install may leave the user-scope settings file
    # empty before any setting is written, and an empty file cannot switch a
    # skill off, so empty or whitespace-only text is treated as no
    # overrides rather than failing closed. A present, non-empty file that
    # will not parse still fails closed, exactly as an unparsable lock file
    # does.
    if not settings_text.strip():
        settings = {}
    else:
        try:
            settings = json.loads(settings_text)
        except json.JSONDecodeError as error:
            raise _pocock_error(
                f"cannot parse settings file {settings_path}: {error}"
            ) from error
    if not isinstance(settings, dict):
        raise _pocock_error(f"invalid settings in {settings_path}")
    skill_overrides = settings.get("skillOverrides", {})
    if not isinstance(skill_overrides, dict):
        raise _pocock_error(f"invalid skillOverrides in {settings_path}")

    entries = lock["skills"]
    missing: list[str] = []
    incompatible: list[str] = []
    switched_off: list[str] = []
    for skill in POCOCK_SKILLS:
        entry = entries.get(skill)
        if not isinstance(entry, dict) or entry.get("source") != POCOCK_SOURCE:
            incompatible.append(skill)
        # Claude Code discovers global skills only below its own configuration
        # directory, so a shared agent-neutral copy does not satisfy this host.
        if not (claude_home / "skills" / skill / "SKILL.md").is_file():
            missing.append(skill)
        # Only "off" hides a skill from both the model and the user. Pocock
        # skills are author-locked, and the CLI itself forces an author-locked
        # skill carrying disable-model-invocation to "user-invocable-only"
        # unless the user explicitly chose "off", so treating
        # "user-invocable-only" or "name-only" as missing would fail every
        # correctly installed Pocock skill. Absent is on.
        if skill_overrides.get(skill) == "off":
            switched_off.append(skill)
    if incompatible:
        raise _pocock_error(
            f"lock source must be {POCOCK_SOURCE} for {', '.join(incompatible)}"
        )
    if missing:
        raise _pocock_error(f"missing required skills: {', '.join(missing)}")
    if switched_off:
        raise _pocock_error(
            "switched off by skillOverrides in "
            f"{settings_path}: {', '.join(switched_off)}. Remove the "
            "override to restore the prerequisite.",
            install_hint=False,
        )
    return (
        f"PASS  Pocock prerequisite: {len(POCOCK_SKILLS)} skills from "
        f"{POCOCK_SOURCE}"
    )


def _validate_superpowers() -> str:
    environment = os.environ.copy()
    environment["NO_COLOR"] = "1"
    try:
        result = subprocess.run(
            [resolve_command("claude"), "plugin", "list", "--json"],
            env=environment,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
    except OSError as error:
        raise CompatibilityError(f"cannot run claude plugin list: {error}") from error

    enabled = False
    if result.returncode == 0:
        try:
            plugins = json.loads(result.stdout)
        except json.JSONDecodeError:
            plugins = None
        if isinstance(plugins, list):
            for plugin in plugins:
                if not isinstance(plugin, dict):
                    continue
                if plugin.get("id") != SUPERPOWERS_PLUGIN:
                    continue
                if plugin.get("enabled") is True:
                    enabled = True
                break
    if not enabled:
        raise CompatibilityError(
            "Superpowers plugin is missing or disabled: enable "
            f"{SUPERPOWERS_PLUGIN} from the Superpowers Claude Code plugin marketplace"
        )
    return f"PASS  Superpowers plugin enabled: {SUPERPOWERS_PLUGIN}"


def validate_upstreams(home: Path, claude_home: Path, metadata: Path) -> list[str]:
    """Return human-readable PASS lines; reject unsupported installed state."""
    profile = _load_metadata(metadata)
    pocock = _dependency(profile, "mattpocock-skills")
    superpowers = _dependency(profile, "superpowers")
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
        _validate_pocock(home, claude_home),
        _validate_superpowers(),
        f"PASS  Tested upstream refs: Pocock {pocock.get('testedRef')}, "
        f"Superpowers {superpowers.get('testedRef')}",
    ]
