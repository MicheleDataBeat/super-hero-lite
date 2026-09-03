#!/usr/bin/env python3
"""Real-command lifecycle tests for the Claude Code distribution."""

from __future__ import annotations

import errno
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock


REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPOSITORY_ROOT / "distributions" / "claude-code" / "lib"))
import compatibility  # noqa: E402
import managed_state  # noqa: E402


LITE_SKILLS = (
    "super-hero-core",
    "super-hero-release-to-public",
    "super-hero-simplify",
)
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
BEGIN = "<!-- BEGIN SUPER_HERO_LITE_CLAUDE_CODE_BOOTSTRAP v1 -->"
END = "<!-- END SUPER_HERO_LITE_CLAUDE_CODE_BOOTSTRAP v1 -->"
CODEX_BEGIN = "<!-- BEGIN SUPER_HERO_LITE_CODEX_BOOTSTRAP v1 -->"
POCOCK_INSTALL_COMMAND = (
    "npx --yes skills add "
    "https://github.com/mattpocock/skills "
    "--skill '*' --agent claude-code --global --yes"
)
ENABLED_PLUGIN_LIST = json.dumps(
    [
        {
            "id": "superpowers@superpowers-marketplace",
            "version": "5.1.0",
            "scope": "user",
            "enabled": True,
        }
    ]
)
FRAGMENT_PATH = (
    REPOSITORY_ROOT
    / "distributions"
    / "claude-code"
    / "bootstrap"
    / "CLAUDE.md.fragment"
)


# pwsh caches startup data below the profile it is handed, and on Windows that
# profile has to be the fixture home so the entry points pass it as --home.
# That cache belongs to the harness's own interpreter, not to the code under
# test, and it has no POSIX counterpart. It is the one thing file_hashes skips,
# and the exclusion is held to exactly this prefix by
# test_the_only_harness_footprint_in_the_home_is_the_powershell_cache.
POWERSHELL_CACHE = "AppData/Local/Microsoft/PowerShell/"

WINDOWS = os.name == "nt"


def relative_files(root: Path) -> list[str]:
    """Return every file below root, including what file_hashes excludes."""
    if not root.exists():
        return []
    return sorted(
        path.relative_to(root).as_posix()
        for path in root.rglob("*")
        if path.is_file()
    )


def file_hashes(root: Path) -> dict[str, str]:
    """Return the complete relative-file hash mapping below root."""
    return {
        name: hashlib.sha256((root / name).read_bytes()).hexdigest()
        for name in relative_files(root)
        if not (WINDOWS and name.startswith(POWERSHELL_CACHE))
    }


def bytecode_artifacts(root: Path) -> list[str]:
    if not root.exists():
        return []
    return sorted(
        path.relative_to(root).as_posix()
        for path in root.rglob("*")
        if path.name == "__pycache__" or path.suffix in (".pyc", ".pyo")
    )


# The fixture replaces the child environment wholesale rather than inheriting
# it, so on Windows these have to be handed back before a child can start at
# all. PATHEXT is load-bearing twice over: without it neither shutil.which nor
# Get-Command -CommandType Application finds a .cmd shim.
WINDOWS_BASE_KEYS = (
    "ComSpec",
    "NUMBER_OF_PROCESSORS",
    "PATHEXT",
    "PROCESSOR_ARCHITECTURE",
    "PSModulePath",
    "SystemDrive",
    "SystemRoot",
    "windir",
)
POWERSHELL = (shutil.which("pwsh") or shutil.which("powershell")) if WINDOWS else None


class LifecycleFixture:
    def __init__(self, temporary_root: Path) -> None:
        self.root = temporary_root
        self.home = self.root / "home"
        self.claude_home = self.home / ".claude"
        self.bin = self.root / "bin"
        self.home.mkdir()
        self.bin.mkdir()
        self._stub_files: dict[str, list[Path]] = {}
        if WINDOWS:
            self._write_interpreter_shim()
        else:
            self._link_runtime("bash")
            self._link_runtime("python3")
        self._write_stub("git", "exit 0\n", "raise SystemExit(0)\n")
        self._write_stub(
            "gh",
            'if [[ "${1:-} ${2:-}" == "auth status" ]]; then '
            'exit "${GH_AUTH_EXIT:-0}"; fi\nexit 0\n',
            "import os, sys\n"
            'if sys.argv[1:3] == ["auth", "status"]:\n'
            '    raise SystemExit(int(os.environ.get("GH_AUTH_EXIT") or "0"))\n'
            "raise SystemExit(0)\n",
        )
        self._write_stub(
            "claude",
            'if [[ "${1:-} ${2:-} ${3:-}" == "plugin list --json" ]]; then\n'
            '  printf \'%s\\n\' "${SUPER_HERO_LITE_TEST_PLUGIN_OUTPUT:-}"\n'
            '  exit "${SUPER_HERO_LITE_TEST_PLUGIN_EXIT:-0}"\n'
            "fi\n"
            "exit 2\n",
            "import os, sys\n"
            'if sys.argv[1:4] == ["plugin", "list", "--json"]:\n'
            '    sys.stdout.write(os.environ.get("SUPER_HERO_LITE_TEST_PLUGIN_OUTPUT", "") + "\\n")\n'
            '    raise SystemExit(int(os.environ.get("SUPER_HERO_LITE_TEST_PLUGIN_EXIT") or "0"))\n'
            "raise SystemExit(2)\n",
        )
        self.environment = {
            "HOME": str(self.home),
            "CLAUDE_CONFIG_DIR": str(self.claude_home),
            "PATH": str(self.bin),
            "LC_ALL": "C",
            "SUPER_HERO_LITE_TEST_PLUGIN_OUTPUT": ENABLED_PLUGIN_LIST,
        }
        if WINDOWS:
            # The dict above replaces the environment wholesale, so a Windows
            # child starts with nothing. USERPROFILE is the load-bearing key:
            # PowerShell derives $HOME from it and every .ps1 entry point passes
            # $HOME as --home. Measured on windows-latest: HOME alone leaves
            # $HOME empty, and HOMEDRIVE with HOMEPATH does not move it either,
            # so a fixture that set only HOME would point --home at the real
            # profile and quietly make the prerequisite assertions vacuous.
            scratch = {name: self.root / name for name in ("temp", "appdata", "local")}
            for directory in scratch.values():
                directory.mkdir()
            self.environment.update(
                {key: os.environ[key] for key in WINDOWS_BASE_KEYS if key in os.environ}
            )
            self.environment.update(
                {
                    "USERPROFILE": str(self.home),
                    "TEMP": str(scratch["temp"]),
                    "TMP": str(scratch["temp"]),
                    # PowerShell caches startup data under LOCALAPPDATA, and with
                    # that unset it derives the path from USERPROFILE — writing
                    # inside the home whose bytes these tests compare. Point it
                    # somewhere fixture-owned but outside the compared tree, so
                    # the comparison stays total instead of learning exceptions.
                    "APPDATA": str(scratch["appdata"]),
                    "LOCALAPPDATA": str(scratch["local"]),
                    # shutil.which searches the current directory before PATH on
                    # Windows, and the child's cwd is the checkout.
                    "NoDefaultCurrentDirectoryInExePath": "1",
                }
            )
        self.write_pocock_lock()
        self.install_pocock_skills(self.claude_home)

    def _link_runtime(self, command: str) -> None:
        target = shutil.which(command)
        if target is None:
            raise RuntimeError(f"test runtime is missing {command}")
        (self.bin / command).symlink_to(target)

    def _write_launcher(self, name: str, arguments: str) -> Path:
        """Write a .cmd shim, the only executable form Windows resolves by name."""
        launcher = self.bin / f"{name}.cmd"
        launcher.write_text(
            f'@echo off\r\n"{sys.executable}" {arguments}\r\nexit /b %ERRORLEVEL%\r\n',
            encoding="ascii",
            newline="",
        )
        return launcher

    def _write_interpreter_shim(self) -> None:
        """Reach this interpreter under a name the entry points look for.

        Copying python.exe would strand it from its DLL and standard library, and
        resolving "python3" on PATH would meet the Store alias, so the shim names
        sys.executable outright.
        """
        self._write_launcher("python3", "%*")

    def _write_stub(self, command: str, body: str, windows_body: str) -> None:
        if not WINDOWS:
            path = self.bin / command
            path.write_text("#!/usr/bin/env bash\n" + body, encoding="utf-8", newline="")
            path.chmod(0o755)
            self._stub_files[command] = [path]
            return
        # A batch body would have to re-implement these in a language whose echo
        # rewrites metacharacters and whose empty variables print "ECHO is off.".
        # The host stub's output is parsed as JSON, so it is written by Python.
        script = self.bin / f"{command}_stub.py"
        script.write_text(windows_body, encoding="utf-8", newline="")
        launcher = self._write_launcher(command, f'"%~dp0{script.name}" %*')
        self._stub_files[command] = [script, launcher]

    def remove_stub(self, command: str) -> None:
        """Remove every file that made a command resolvable, and fail if any is missing."""
        for path in self._stub_files.pop(command):
            path.unlink()

    def write_pocock_lock(self) -> None:
        lock = {
            "version": 3,
            "skills": {
                skill: {"source": "mattpocock/skills"} for skill in POCOCK_SKILLS
            },
        }
        lock_path = self.home / ".agents" / ".skill-lock.json"
        lock_path.parent.mkdir(parents=True, exist_ok=True)
        lock_path.write_text(json.dumps(lock, indent=2) + "\n", encoding="utf-8", newline="")

    def install_pocock_skills(self, skills_home: Path) -> None:
        """Place the prerequisite skills where the given host discovers them."""
        for skill in POCOCK_SKILLS:
            skill_file = skills_home / "skills" / skill / "SKILL.md"
            skill_file.parent.mkdir(parents=True, exist_ok=True)
            skill_file.write_text(
                f"---\nname: {skill}\ndescription: fixture\n---\n",
                encoding="utf-8", newline="",
            )

    def remove_pocock_skills(self, skills_home: Path) -> None:
        for skill in POCOCK_SKILLS:
            shutil.rmtree(skills_home / "skills" / skill, ignore_errors=True)

    def install_lite_state(
        self, *, instructions_prefix: str = "", instructions_suffix: str = ""
    ) -> None:
        """Plant the state a successful install leaves behind."""
        skills_root = self.claude_home / "skills"
        skills_root.mkdir(parents=True, exist_ok=True)
        for skill in LITE_SKILLS:
            shutil.copytree(
                REPOSITORY_ROOT / "skills" / skill,
                skills_root / skill,
                dirs_exist_ok=True,
            )
        fragment = FRAGMENT_PATH.read_text(encoding="utf-8")
        self.claude_home.mkdir(parents=True, exist_ok=True)
        (self.claude_home / "CLAUDE.md").write_text(
            instructions_prefix + fragment + instructions_suffix,
            encoding="utf-8", newline="",
        )

    def run(
        self,
        command: str,
        *arguments: str,
        package_root: Path = REPOSITORY_ROOT,
        extra_environment: dict[str, str] | None = None,
    ) -> subprocess.CompletedProcess[str]:
        environment = dict(self.environment)
        if extra_environment:
            environment.update(extra_environment)
        name = Path(command).with_suffix(".ps1").name if WINDOWS else command
        script = package_root / "distributions" / "claude-code" / name
        if WINDOWS:
            if POWERSHELL is None:
                raise RuntimeError("test runtime is missing pwsh")
            # An absolute interpreter, so the entry point is reached by design
            # rather than by whatever the caller's context happens to resolve.
            argv = [
                POWERSHELL,
                "-NoLogo",
                "-NoProfile",
                "-NonInteractive",
                "-ExecutionPolicy",
                "Bypass",
                "-File",
                str(script),
            ]
            # The POSIX validator takes --package; its PowerShell sibling takes
            # the -Package switch for the same mode.
            argv += ["-Package" if item == "--package" else item for item in arguments]
        else:
            argv = ["bash", str(script), *arguments]
        return subprocess.run(
            argv,
            cwd=package_root,
            env=environment,
            # Not text=True: that decodes with the locale encoding, which is
            # cp1252 on Windows, and shipped documents contain non-ASCII text.
            encoding="utf-8",
            errors="replace",
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )


class ClaudeCodeLifecycleTests(unittest.TestCase):
    def fixture(self) -> tuple[tempfile.TemporaryDirectory[str], LifecycleFixture]:
        temporary = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        return temporary, LifecycleFixture(Path(temporary.name))

    def assert_controlled_failure(
        self,
        result: subprocess.CompletedProcess[str],
        reason: str,
    ) -> None:
        self.assertNotEqual(result.returncode, 0, result.stdout)
        self.assertIn(reason, result.stderr)
        self.assertNotIn("Traceback", result.stderr)

    def assert_no_owned_skills(self, fixture: LifecycleFixture) -> None:
        for skill in LITE_SKILLS:
            self.assertFalse((fixture.claude_home / "skills" / skill).exists(), skill)

    def copied_package(self, fixture: LifecycleFixture, **copy_arguments) -> Path:
        """A writable copy of the package, so a defect can be planted in it."""
        package_root = fixture.root / "package"
        shutil.copytree(
            REPOSITORY_ROOT / "distributions" / "claude-code",
            package_root / "distributions" / "claude-code",
            **copy_arguments,
        )
        shutil.copytree(REPOSITORY_ROOT / "skills", package_root / "skills")
        (package_root / "compatibility").mkdir()
        shutil.copy2(
            REPOSITORY_ROOT / "compatibility" / "upstreams.json",
            package_root / "compatibility" / "upstreams.json",
        )
        return package_root

    @unittest.skipUnless(WINDOWS, "PowerShell writes this cache only on Windows")
    def test_the_only_harness_footprint_in_the_home_is_the_powershell_cache(self) -> None:
        """Bound the single exclusion file_hashes makes.

        An exclusion nobody checks widens quietly until the assertion it lives
        in stops asserting. This fails the moment anything other than pwsh's
        own cache appears in the home without the installer putting it there.
        """
        temporary, fixture = self.fixture()
        with temporary:
            before = set(relative_files(fixture.home))
            install = fixture.run("install.sh")
            self.assertEqual(install.returncode, 0, install.stderr)
            uninstall = fixture.run("uninstall.sh")
            self.assertEqual(uninstall.returncode, 0, uninstall.stderr)

            appeared = set(relative_files(fixture.home)) - before
            self.assertTrue(appeared, "the exclusion is no longer needed; remove it")
            self.assertEqual(
                {name for name in appeared if not name.startswith(POWERSHELL_CACHE)},
                set(),
            )

    @unittest.skipUnless(WINDOWS, "the redirection this guards is Windows-only")
    def test_the_fixture_redirects_the_windows_home(self) -> None:
        """Arm the one failure this suite could not otherwise see.

        Every .ps1 entry point passes PowerShell's $HOME as --home, and $HOME is
        not $env:HOME. If the redirection ever breaks, the installer reads the
        real profile's prerequisites, the suite stays green, and it proves
        nothing. So assert it directly rather than trusting it.
        """
        temporary, fixture = self.fixture()
        with temporary:
            self.assertIsNotNone(POWERSHELL)
            result = subprocess.run(
                [
                    POWERSHELL,
                    "-NoLogo",
                    "-NoProfile",
                    "-NonInteractive",
                    "-ExecutionPolicy",
                    "Bypass",
                    "-Command",
                    "Write-Output $HOME",
                ],
                env=fixture.environment,
                encoding="utf-8",
                errors="replace",
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(str(fixture.home), result.stdout.strip())

    def test_fresh_lite_install(self) -> None:
        temporary, fixture = self.fixture()
        with temporary:
            lock_before = file_hashes(fixture.home / ".agents")
            result = fixture.run("install.sh")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(LITE_SKILLS, managed_state.LITE_SKILLS)
            instructions = (fixture.claude_home / "CLAUDE.md").read_text(
                encoding="utf-8"
            )
            self.assertEqual(instructions.count(BEGIN), 1)
            self.assertEqual(instructions.count(END), 1)
            for skill in LITE_SKILLS:
                self.assertTrue(
                    (fixture.claude_home / "skills" / skill / "SKILL.md").is_file()
                )
            self.assertEqual(lock_before, file_hashes(fixture.home / ".agents"))
            validation = fixture.run("validate.sh")
            self.assertEqual(validation.returncode, 0, validation.stderr)
            self.assertIn("PASS", validation.stdout)

    def test_install_creates_no_agent_definitions(self) -> None:
        """Lite ships no role definitions, so `agents/` is never created."""
        temporary, fixture = self.fixture()
        with temporary:
            result = fixture.run("install.sh")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertFalse((fixture.claude_home / "agents").exists())
            self.assertFalse(
                (REPOSITORY_ROOT / "distributions" / "claude-code" / "agents").exists(),
                "the package must ship no agents/ directory",
            )
            installed = sorted(
                entry.name
                for entry in (fixture.claude_home / "skills").iterdir()
                if entry.name not in POCOCK_SKILLS
            )
            self.assertEqual(installed, sorted(LITE_SKILLS))

    def test_foreign_agent_definitions_are_never_touched(self) -> None:
        """The operator's own agents/ content is not this distribution's state."""
        temporary, fixture = self.fixture()
        with temporary:
            agents_root = fixture.claude_home / "agents"
            agents_root.mkdir(parents=True)
            foreign = agents_root / "super-hero-implementer.md"
            foreign.write_bytes(b"---\nname: super-hero-implementer\n---\nmine\n")
            before = file_hashes(agents_root)

            install = fixture.run("install.sh")
            self.assertEqual(install.returncode, 0, install.stderr)
            self.assertEqual(before, file_hashes(agents_root))

            uninstall = fixture.run("uninstall.sh")
            self.assertEqual(uninstall.returncode, 0, uninstall.stderr)
            self.assertEqual(before, file_hashes(agents_root))

    def test_installed_bootstrap_is_claude_code_specific(self) -> None:
        temporary, fixture = self.fixture()
        with temporary:
            result = fixture.run("install.sh")
            self.assertEqual(result.returncode, 0, result.stderr)
            instructions = (fixture.claude_home / "CLAUDE.md").read_text(
                encoding="utf-8"
            )
            self.assertNotIn(CODEX_BEGIN, instructions)
            self.assertFalse((fixture.claude_home / "AGENTS.md").exists())

    def test_install_over_installed_state_is_idempotent(self) -> None:
        temporary, fixture = self.fixture()
        with temporary:
            fixture.install_lite_state()
            before = file_hashes(fixture.home)
            result = fixture.run("install.sh")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(before, file_hashes(fixture.home))

    def test_repeated_install_is_byte_identical(self) -> None:
        temporary, fixture = self.fixture()
        with temporary:
            first = fixture.run("install.sh")
            self.assertEqual(first.returncode, 0, first.stderr)
            first_state = file_hashes(fixture.home)
            second = fixture.run("install.sh")
            self.assertEqual(second.returncode, 0, second.stderr)
            self.assertEqual(first_state, file_hashes(fixture.home))

    def test_unrelated_instructions_content_is_byte_identical(self) -> None:
        temporary, fixture = self.fixture()
        with temporary:
            prefix = "# Personal\n\nkeep trailing spaces   \n"
            suffix = "\n## Local\n`literal`\n"
            fixture.install_lite_state(
                instructions_prefix=prefix,
                instructions_suffix=suffix,
            )
            result = fixture.run("install.sh")
            self.assertEqual(result.returncode, 0, result.stderr)
            instructions = (fixture.claude_home / "CLAUDE.md").read_text(
                encoding="utf-8"
            )
            # The line ending after a non-terminal END marker separates unrelated
            # content and therefore survives; only the block itself is replaced.
            fragment = FRAGMENT_PATH.read_text(encoding="utf-8")
            self.assertEqual(instructions, prefix + "\n" + suffix + fragment)
            self.assertEqual(instructions.count(BEGIN), 1)

    def test_install_and_uninstall_preserve_crlf_bytes(self) -> None:
        original = b"# Windows instructions\r\n\r\nkeep trailing spaces   \r\n"
        fragment = FRAGMENT_PATH.read_bytes()

        with self.subTest(operation="install"):
            temporary, fixture = self.fixture()
            with temporary:
                instructions_path = fixture.claude_home / "CLAUDE.md"
                instructions_path.write_bytes(original)
                result = fixture.run("install.sh")
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertTrue(instructions_path.read_bytes().startswith(original))

        with self.subTest(operation="uninstall"):
            temporary, fixture = self.fixture()
            with temporary:
                fixture.install_lite_state()
                instructions_path = fixture.claude_home / "CLAUDE.md"
                instructions_path.write_bytes(original + fragment)
                result = fixture.run("uninstall.sh")
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(original, instructions_path.read_bytes())

    def test_install_uninstall_round_trip_is_byte_identical(self) -> None:
        temporary, fixture = self.fixture()
        with temporary:
            instructions_path = fixture.claude_home / "CLAUDE.md"
            original = b"# Local instructions\nkeep trailing spaces   "
            instructions_path.write_bytes(original)

            install = fixture.run("install.sh")
            self.assertEqual(install.returncode, 0, install.stderr)
            uninstall = fixture.run("uninstall.sh")
            self.assertEqual(uninstall.returncode, 0, uninstall.stderr)

            self.assertEqual(original, instructions_path.read_bytes())

    def test_uninstall_without_owned_state_is_inode_and_byte_noop(self) -> None:
        temporary, fixture = self.fixture()
        with temporary:
            instructions_path = fixture.claude_home / "CLAUDE.md"
            original = b"# Unrelated only\nleave this inode alone\n"
            instructions_path.write_bytes(original)
            inode_before = instructions_path.stat().st_ino
            home_before = file_hashes(fixture.home)

            result = fixture.run("uninstall.sh")

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("already absent", result.stdout)
            self.assertEqual(inode_before, instructions_path.stat().st_ino)
            self.assertEqual(original, instructions_path.read_bytes())
            self.assertEqual(home_before, file_hashes(fixture.home))

    def test_instructions_symlink_is_preserved_across_install_and_uninstall(
        self,
    ) -> None:
        temporary, fixture = self.fixture()
        with temporary:
            target = fixture.root / "shared-instructions.md"
            original = b"# Shared instructions\n"
            target.write_bytes(original)
            instructions_path = fixture.claude_home / "CLAUDE.md"
            instructions_path.symlink_to(target)
            link_target = os.readlink(instructions_path)

            install = fixture.run("install.sh")
            self.assertEqual(install.returncode, 0, install.stderr)
            self.assertTrue(instructions_path.is_symlink())
            self.assertEqual(link_target, os.readlink(instructions_path))
            self.assertIn(BEGIN.encode("utf-8"), target.read_bytes())

            uninstall = fixture.run("uninstall.sh")
            self.assertEqual(uninstall.returncode, 0, uninstall.stderr)
            self.assertTrue(instructions_path.is_symlink())
            self.assertEqual(link_target, os.readlink(instructions_path))
            self.assertEqual(original, target.read_bytes())

    def test_malformed_marker_fails_before_mutation(self) -> None:
        for label, content in (
            ("unterminated", f"unrelated\n{BEGIN}\nunterminated\n"),
            ("orphan end", f"unrelated\n{END}\n"),
            ("duplicated", f"{BEGIN}\na\n{END}\n{BEGIN}\nb\n{END}\n"),
        ):
            with self.subTest(state=label):
                temporary, fixture = self.fixture()
                with temporary:
                    (fixture.claude_home / "CLAUDE.md").write_text(
                        content, encoding="utf-8", newline="",
                    )
                    before = file_hashes(fixture.home)
                    result = fixture.run("install.sh")
                    self.assert_controlled_failure(
                        result, "malformed bootstrap marker"
                    )
                    self.assertEqual(before, file_hashes(fixture.home))

    def test_missing_required_command_fails_before_mutation(self) -> None:
        temporary, fixture = self.fixture()
        with temporary:
            fixture.remove_stub("gh")
            before = file_hashes(fixture.home)
            result = fixture.run("install.sh")
            self.assert_controlled_failure(result, "missing required command: gh")
            self.assertEqual(before, file_hashes(fixture.home))

    def test_failed_github_authentication_fails_before_mutation(self) -> None:
        temporary, fixture = self.fixture()
        with temporary:
            before = file_hashes(fixture.home)
            result = fixture.run(
                "install.sh", extra_environment={"GH_AUTH_EXIT": "1"}
            )
            self.assert_controlled_failure(
                result, "GitHub CLI authentication failed"
            )
            self.assertEqual(before, file_hashes(fixture.home))

    def test_incompatible_pocock_source_fails_closed(self) -> None:
        temporary, fixture = self.fixture()
        with temporary:
            lock_path = fixture.home / ".agents" / ".skill-lock.json"
            lock = json.loads(lock_path.read_text(encoding="utf-8"))
            lock["skills"][POCOCK_SKILLS[0]]["source"] = "untrusted/fork"
            lock_path.write_text(json.dumps(lock) + "\n", encoding="utf-8", newline="")
            before = file_hashes(fixture.home)
            result = fixture.run("install.sh")
            # Assert the branch, not the shared prefix. _pocock_error prefixes a
            # missing lock file identically, so the prefix alone would let this
            # test pass while proving nothing about the source check.
            self.assert_controlled_failure(result, "lock source must be mattpocock/skills")
            self.assertIn(POCOCK_INSTALL_COMMAND, result.stderr)
            self.assertEqual(before, file_hashes(fixture.home))

    def test_pocock_outside_the_claude_configuration_directory_fails_closed(
        self,
    ) -> None:
        temporary, fixture = self.fixture()
        with temporary:
            # A shared agent-neutral install is not on Claude Code's global
            # discovery path, so it must not satisfy the prerequisite.
            fixture.remove_pocock_skills(fixture.claude_home)
            fixture.install_pocock_skills(fixture.home / ".agents")
            before = file_hashes(fixture.home)
            result = fixture.run("install.sh")
            self.assert_controlled_failure(result, "missing required skills")
            self.assertIn(POCOCK_INSTALL_COMMAND, result.stderr)
            self.assertEqual(before, file_hashes(fixture.home))

    def test_pocock_switched_off_by_skill_overrides_fails_closed(self) -> None:
        temporary, fixture = self.fixture()
        with temporary:
            settings_path = fixture.claude_home / "settings.json"
            settings_path.write_text(
                json.dumps({"skillOverrides": {POCOCK_SKILLS[0]: "off"}}) + "\n",
                encoding="utf-8", newline="",
            )
            before = file_hashes(fixture.home)
            result = fixture.run("install.sh")
            # Assert the branch, not the shared prefix (see
            # test_incompatible_pocock_source_fails_closed).
            # managed_state resolves claude_home before validation runs, so the
            # path in the error can differ from the fixture's own by a symlink
            # (e.g. macOS's /var -> /private/var); resolve to compare the same
            # way.
            self.assert_controlled_failure(
                result,
                f"switched off by skillOverrides in {settings_path.resolve()}: "
                f"{POCOCK_SKILLS[0]}",
            )
            # The reinstall command cannot fix an override, so this is the
            # one _pocock_error branch that omits it; its absence is what
            # this assertion pins.
            self.assertNotIn(POCOCK_INSTALL_COMMAND, result.stderr)
            self.assertEqual(before, file_hashes(fixture.home))

    def test_pocock_skill_overrides_short_of_off_still_satisfy_the_prerequisite(
        self,
    ) -> None:
        # "user-invocable-only" and "name-only" leave the skill invocable, and
        # the CLI itself forces an author-locked skill carrying
        # disable-model-invocation to "user-invocable-only" unless the user
        # explicitly chose "off" — so neither may be treated as missing.
        for value in ("user-invocable-only", "name-only"):
            with self.subTest(skillOverrides=value):
                temporary, fixture = self.fixture()
                with temporary:
                    settings_path = fixture.claude_home / "settings.json"
                    settings_path.write_text(
                        json.dumps({"skillOverrides": {POCOCK_SKILLS[0]: value}})
                        + "\n",
                        encoding="utf-8", newline="",
                    )
                    settings_before = settings_path.read_bytes()
                    result = fixture.run("install.sh")
                    self.assertEqual(result.returncode, 0, result.stderr)
                    self.assertEqual(settings_before, settings_path.read_bytes())

    def test_pocock_unparsable_settings_fails_closed(self) -> None:
        temporary, fixture = self.fixture()
        with temporary:
            settings_path = fixture.claude_home / "settings.json"
            settings_path.write_text("{not json", encoding="utf-8", newline="")
            before = file_hashes(fixture.home)
            result = fixture.run("install.sh")
            # See the resolve() note above: managed_state resolves claude_home
            # before validation runs.
            self.assert_controlled_failure(
                result, f"cannot parse settings file {settings_path.resolve()}"
            )
            self.assertIn(POCOCK_INSTALL_COMMAND, result.stderr)
            self.assertEqual(before, file_hashes(fixture.home))

    def test_pocock_settings_wrong_shape_fails_closed(self) -> None:
        cases = (
            ("[]", "invalid settings in"),
            (json.dumps({"skillOverrides": None}), "invalid skillOverrides in"),
        )
        for content, reason in cases:
            with self.subTest(content=content):
                temporary, fixture = self.fixture()
                with temporary:
                    settings_path = fixture.claude_home / "settings.json"
                    settings_path.write_text(
                        content + "\n", encoding="utf-8", newline=""
                    )
                    before = file_hashes(fixture.home)
                    result = fixture.run("install.sh")
                    # See the resolve() note above.
                    self.assert_controlled_failure(
                        result, f"{reason} {settings_path.resolve()}"
                    )
                    self.assertIn(POCOCK_INSTALL_COMMAND, result.stderr)
                    self.assertEqual(before, file_hashes(fixture.home))

    def test_pocock_empty_settings_is_no_override(self) -> None:
        # Empty is no override (see _validate_pocock).
        for content in ("", "\n  \n"):
            with self.subTest(content=repr(content)):
                temporary, fixture = self.fixture()
                with temporary:
                    settings_path = fixture.claude_home / "settings.json"
                    settings_path.write_text(
                        content, encoding="utf-8", newline=""
                    )
                    settings_before = settings_path.read_bytes()
                    result = fixture.run("install.sh")
                    self.assertEqual(result.returncode, 0, result.stderr)
                    self.assertEqual(settings_before, settings_path.read_bytes())

    def test_missing_or_disabled_superpowers_fails_closed(self) -> None:
        disabled = json.dumps(
            [{"id": "superpowers@superpowers-marketplace", "enabled": False}]
        )
        for label, output in (("missing", "[]"), ("disabled", disabled)):
            with self.subTest(state=label):
                temporary, fixture = self.fixture()
                with temporary:
                    fixture.environment["SUPER_HERO_LITE_TEST_PLUGIN_OUTPUT"] = output
                    before = file_hashes(fixture.home)
                    result = fixture.run("install.sh")
                    self.assert_controlled_failure(
                        result, "Superpowers plugin is missing or disabled"
                    )
                    self.assertIn("superpowers@superpowers-marketplace", result.stderr)
                    self.assertIn(
                        "Superpowers Claude Code plugin marketplace", result.stderr
                    )
                    self.assertEqual(before, file_hashes(fixture.home))

    def test_superpowers_plugin_id_must_match_exactly(self) -> None:
        impostors = (
            [{"id": "evil-superpowers@superpowers-marketplace-copy", "enabled": True}],
            [{"id": "superpowers@superpowers-marketplace-copy", "enabled": True}],
            [{"id": "superpowers@openai-curated", "enabled": True}],
        )
        for plugins in impostors:
            with self.subTest(plugin_id=plugins[0]["id"]):
                temporary, fixture = self.fixture()
                with temporary:
                    fixture.environment["SUPER_HERO_LITE_TEST_PLUGIN_OUTPUT"] = json.dumps(
                        plugins
                    )
                    before = file_hashes(fixture.home)
                    result = fixture.run("install.sh")
                    self.assert_controlled_failure(
                        result, "Superpowers plugin is missing or disabled"
                    )
                    self.assertEqual(before, file_hashes(fixture.home))

    def test_unreadable_plugin_inventory_fails_closed(self) -> None:
        cases = (
            ("malformed json", {"SUPER_HERO_LITE_TEST_PLUGIN_OUTPUT": "not json"}),
            ("wrong shape", {"SUPER_HERO_LITE_TEST_PLUGIN_OUTPUT": '{"id": "x"}'}),
            ("truthy string", {"SUPER_HERO_LITE_TEST_PLUGIN_OUTPUT": json.dumps(
                [{"id": "superpowers@superpowers-marketplace", "enabled": "true"}]
            )}),
            ("command failure", {"SUPER_HERO_LITE_TEST_PLUGIN_EXIT": "1"}),
        )
        for label, extra_environment in cases:
            with self.subTest(case=label):
                temporary, fixture = self.fixture()
                with temporary:
                    before = file_hashes(fixture.home)
                    result = fixture.run(
                        "install.sh", extra_environment=extra_environment
                    )
                    self.assert_controlled_failure(
                        result, "Superpowers plugin is missing or disabled"
                    )
                    self.assertEqual(before, file_hashes(fixture.home))

    def test_staged_skill_validation_fails_before_mutation(self) -> None:
        temporary, fixture = self.fixture()
        with temporary:
            package_root = self.copied_package(fixture)
            (package_root / "skills" / LITE_SKILLS[0] / "broken-link").symlink_to(
                "missing-target"
            )
            before = file_hashes(fixture.home)
            result = fixture.run("install.sh", package_root=package_root)
            self.assert_controlled_failure(result, "staged skill validation failed")
            self.assertEqual(before, file_hashes(fixture.home))

    def test_package_shipping_an_unowned_skill_fails_closed(self) -> None:
        """Lite ships exactly three skills; a fourth is a packaging defect."""
        temporary, fixture = self.fixture()
        with temporary:
            package_root = self.copied_package(fixture)
            intruder = package_root / "skills" / "ponytail-policy-adapter"
            intruder.mkdir()
            (intruder / "SKILL.md").write_text(
                "---\nname: ponytail-policy-adapter\ndescription: Use when posturing.\n---\n",
                encoding="utf-8", newline="",
            )
            before = file_hashes(fixture.home)
            result = fixture.run("install.sh", package_root=package_root)
            self.assert_controlled_failure(
                result,
                "package ships a skill this distribution does not own: "
                "ponytail-policy-adapter",
            )
            self.assertEqual(before, file_hashes(fixture.home))

            package_validation = fixture.run(
                "validate.sh", "--package", package_root=package_root
            )
            self.assertNotEqual(package_validation.returncode, 0)

    def test_missing_skill_in_package_fails_closed(self) -> None:
        temporary, fixture = self.fixture()
        with temporary:
            package_root = self.copied_package(fixture)
            shutil.rmtree(package_root / "skills" / LITE_SKILLS[2])
            before = file_hashes(fixture.home)
            result = fixture.run("install.sh", package_root=package_root)
            self.assert_controlled_failure(result, "missing or unreadable skill")
            self.assertEqual(before, file_hashes(fixture.home))

    def test_lifecycle_does_not_create_distribution_bytecode(self) -> None:
        temporary, fixture = self.fixture()
        with temporary:
            package_root = self.copied_package(
                fixture,
                ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "*.pyo"),
            )
            distribution = package_root / "distributions" / "claude-code"
            self.assertEqual([], bytecode_artifacts(distribution))

            install = fixture.run("install.sh", package_root=package_root)
            self.assertEqual(install.returncode, 0, install.stderr)
            validate = fixture.run("validate.sh", package_root=package_root)
            self.assertEqual(validate.returncode, 0, validate.stderr)
            uninstall = fixture.run("uninstall.sh", package_root=package_root)
            self.assertEqual(uninstall.returncode, 0, uninstall.stderr)

            self.assertEqual([], bytecode_artifacts(distribution))

    def test_plain_unittest_command_does_not_create_distribution_bytecode(self) -> None:
        if os.environ.get("SUPER_HERO_LITE_PLAIN_UNITTEST_CHILD") == "1":
            return

        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as temporary_name:
            package_root = Path(temporary_name) / "package"
            shutil.copytree(
                REPOSITORY_ROOT / "distributions" / "claude-code",
                package_root / "distributions" / "claude-code",
                ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "*.pyo"),
            )
            shutil.copytree(REPOSITORY_ROOT / "skills", package_root / "skills")
            (package_root / "compatibility").mkdir()
            shutil.copy2(
                REPOSITORY_ROOT / "compatibility" / "upstreams.json",
                package_root / "compatibility" / "upstreams.json",
            )
            distribution = package_root / "distributions" / "claude-code"
            self.assertEqual([], bytecode_artifacts(distribution))
            environment = os.environ.copy()
            environment.pop("PYTHONDONTWRITEBYTECODE", None)
            environment.pop("PYTHONPYCACHEPREFIX", None)
            environment["SUPER_HERO_LITE_PLAIN_UNITTEST_CHILD"] = "1"
            # The child is itself a unittest runner writing to a pipe.
            environment["PYTHONIOENCODING"] = "utf-8"

            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "unittest",
                    "distributions/claude-code/evals/test_lifecycle.py",
                    "-v",
                ],
                cwd=package_root,
                env=environment,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )

            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertEqual([], bytecode_artifacts(distribution))

    def test_post_mutation_failure_restores_exact_snapshot(self) -> None:
        temporary, fixture = self.fixture()
        with temporary:
            fixture.install_lite_state(
                instructions_prefix="before\n",
                instructions_suffix="\nafter\n",
            )
            for skill in LITE_SKILLS:
                custom = fixture.claude_home / "skills" / skill / "custom.bin"
                custom.parent.mkdir(parents=True, exist_ok=True)
                custom.write_bytes(b"prior\x00state:" + skill.encode("utf-8"))
            before = file_hashes(fixture.home)
            result = fixture.run(
                "install.sh",
                extra_environment={
                    "SUPER_HERO_LITE_TESTING": "1",
                    "SUPER_HERO_LITE_TEST_FAILPOINT": "after-mutation",
                },
            )
            self.assert_controlled_failure(result, "controlled after-mutation failure")
            self.assertEqual(before, file_hashes(fixture.home))

    def test_an_unsupported_failpoint_is_rejected(self) -> None:
        """The failpoint is a test seam, not a switch a user can trip."""
        for extra in (
            {"SUPER_HERO_LITE_TEST_FAILPOINT": "after-mutation"},
            {
                "SUPER_HERO_LITE_TESTING": "1",
                "SUPER_HERO_LITE_TEST_FAILPOINT": "somewhere-else",
            },
        ):
            with self.subTest(environment=sorted(extra)):
                temporary, fixture = self.fixture()
                with temporary:
                    before = file_hashes(fixture.home)
                    result = fixture.run("install.sh", extra_environment=extra)
                    self.assert_controlled_failure(
                        result, "unsupported test failpoint"
                    )
                    self.assertEqual(before, file_hashes(fixture.home))

    def test_transaction_stays_on_claude_home_filesystem(self) -> None:
        temporary, fixture = self.fixture()
        with temporary:
            separate = fixture.root / "separate-volume-claude"
            shutil.move(fixture.claude_home, separate)
            fixture.claude_home = separate
            fixture.environment["CLAUDE_CONFIG_DIR"] = str(separate)
            real_replace = os.replace
            real_temporary_directory = tempfile.TemporaryDirectory
            transaction_parents: list[Path] = []

            def recorded_temporary_directory(*args: object, **kwargs: object):
                transaction_parents.append(Path(str(kwargs["dir"])))
                return real_temporary_directory(*args, **kwargs)

            def simulated_cross_device_replace(
                source: str | os.PathLike[str],
                destination: str | os.PathLike[str],
            ) -> None:
                source_path = Path(source).resolve()
                destination_path = Path(destination).resolve()
                resolved_claude_home = fixture.claude_home.resolve()
                source_is_local = source_path.is_relative_to(resolved_claude_home)
                destination_is_local = destination_path.is_relative_to(
                    resolved_claude_home
                )
                if destination_is_local and not source_is_local:
                    raise OSError(errno.EXDEV, "simulated cross-device rename")
                real_replace(source, destination)

            with (
                mock.patch.dict(os.environ, fixture.environment, clear=True),
                mock.patch.object(
                    managed_state.tempfile,
                    "TemporaryDirectory",
                    side_effect=recorded_temporary_directory,
                ),
                mock.patch.object(
                    managed_state.os,
                    "replace",
                    side_effect=simulated_cross_device_replace,
                ),
            ):
                managed_state.install_state(
                    REPOSITORY_ROOT, fixture.home, fixture.claude_home
                )

            self.assertTrue(transaction_parents)
            self.assertTrue(
                all(parent == fixture.claude_home for parent in transaction_parents),
                transaction_parents,
            )

    def test_existing_skills_are_not_deleted_before_safe_replacement(self) -> None:
        temporary, fixture = self.fixture()
        with temporary:
            fixture.install_lite_state()
            real_remove_path = managed_state._remove_path
            lite_targets = {
                fixture.claude_home / "skills" / skill for skill in LITE_SKILLS
            }
            destructively_removed: list[Path] = []
            safely_renamed: set[Path] = set()
            real_replace = os.replace

            def observe_remove(path: Path) -> None:
                if path in lite_targets and (path.exists() or path.is_symlink()):
                    destructively_removed.append(path)
                real_remove_path(path)

            def observe_replace(
                source: str | os.PathLike[str],
                destination: str | os.PathLike[str],
            ) -> None:
                source_path = Path(source)
                destination_path = Path(destination)
                if source_path in lite_targets:
                    self.assertIn("rollback", destination_path.parts)
                    safely_renamed.add(source_path)
                real_replace(source, destination)

            with (
                mock.patch.dict(os.environ, fixture.environment, clear=True),
                mock.patch.object(
                    managed_state, "_remove_path", side_effect=observe_remove
                ),
                mock.patch.object(
                    managed_state.os, "replace", side_effect=observe_replace
                ),
            ):
                managed_state.install_state(
                    REPOSITORY_ROOT, fixture.home, fixture.claude_home
                )

            self.assertEqual([], destructively_removed)
            self.assertEqual(lite_targets, safely_renamed)

    def test_keyboard_interrupt_during_install_restores_exact_snapshot(self) -> None:
        temporary, fixture = self.fixture()
        with temporary:
            fixture.install_lite_state(instructions_prefix="# preserve\n")
            custom = (
                fixture.claude_home
                / "skills"
                / LITE_SKILLS[0]
                / "prior-state.bin"
            )
            custom.write_bytes(b"prior\x00install-state")
            before = file_hashes(fixture.home)
            real_replace = os.replace
            interrupted = False

            def interrupt_staged_replace(
                source: str | os.PathLike[str],
                destination: str | os.PathLike[str],
            ) -> None:
                nonlocal interrupted
                source_path = Path(source)
                if not interrupted and "staged-skills" in source_path.parts:
                    interrupted = True
                    raise KeyboardInterrupt("interrupt staged replacement")
                real_replace(source, destination)

            with (
                mock.patch.dict(os.environ, fixture.environment, clear=True),
                mock.patch.object(
                    managed_state.os,
                    "replace",
                    side_effect=interrupt_staged_replace,
                ),
            ):
                with self.assertRaises(KeyboardInterrupt):
                    managed_state.install_state(
                        REPOSITORY_ROOT, fixture.home, fixture.claude_home
                    )

            self.assertTrue(interrupted)
            self.assertEqual(before, file_hashes(fixture.home))

    def test_keyboard_interrupt_during_uninstall_restores_exact_snapshot(self) -> None:
        temporary, fixture = self.fixture()
        with temporary:
            fixture.install_lite_state(instructions_prefix="# preserve\n")
            before = file_hashes(fixture.home)
            real_atomic_write = managed_state.bootstrap.atomic_write
            interrupted = False

            def write_then_interrupt(path: Path, text: str) -> None:
                nonlocal interrupted
                real_atomic_write(path, text)
                if not interrupted:
                    interrupted = True
                    raise KeyboardInterrupt("interrupt uninstall bootstrap write")

            with mock.patch.object(
                managed_state.bootstrap,
                "atomic_write",
                side_effect=write_then_interrupt,
            ):
                with self.assertRaises(KeyboardInterrupt):
                    managed_state.uninstall_state(fixture.claude_home)

            self.assertTrue(interrupted)
            self.assertEqual(before, file_hashes(fixture.home))

    def test_uninstall_removes_installed_state(self) -> None:
        temporary, fixture = self.fixture()
        with temporary:
            fixture.install_lite_state()
            result = fixture.run("uninstall.sh")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assert_no_owned_skills(fixture)
            self.assertFalse((fixture.claude_home / "CLAUDE.md").exists())

    def test_validate_fails_after_uninstall(self) -> None:
        """A validator that still passed here would prove nothing at all."""
        temporary, fixture = self.fixture()
        with temporary:
            install = fixture.run("install.sh")
            self.assertEqual(install.returncode, 0, install.stderr)
            self.assertEqual(fixture.run("validate.sh").returncode, 0)
            uninstall = fixture.run("uninstall.sh")
            self.assertEqual(uninstall.returncode, 0, uninstall.stderr)
            self.assertNotEqual(fixture.run("validate.sh").returncode, 0)
            # Package-only validation never inspects user state, so it still
            # passes with nothing installed.
            self.assertEqual(
                fixture.run("validate.sh", "--package").returncode, 0
            )

    def test_uninstall_preserves_pocock_superpowers_and_unrelated_content(self) -> None:
        temporary, fixture = self.fixture()
        with temporary:
            fixture.install_lite_state(instructions_prefix="# Unrelated\n")
            unrelated_skill = (
                fixture.claude_home / "skills" / "personal-skill" / "SKILL.md"
            )
            unrelated_skill.parent.mkdir(parents=True)
            unrelated_skill.write_bytes(b"personal\x00skill\n")
            plugin_state = fixture.claude_home / "plugins" / "installed_plugins.json"
            plugin_state.parent.mkdir(parents=True)
            plugin_state.write_text("{}\n", encoding="utf-8", newline="")
            settings = fixture.claude_home / "settings.json"
            settings.write_text(
                "{\n  \"model\": \"opus\"\n}\n", encoding="utf-8", newline=""
            )
            ponytail_state = fixture.home / ".config" / "ponytail" / "config.json"
            ponytail_state.parent.mkdir(parents=True)
            ponytail_state.write_text(
                '{"personal_mode":"ADVISORY"}\n', encoding="utf-8", newline=""
            )
            preserved_paths = (
                fixture.home / ".agents",
                fixture.claude_home / "skills" / POCOCK_SKILLS[0],
                unrelated_skill.parent,
                plugin_state.parent,
                ponytail_state.parent,
            )
            settings_before = settings.read_bytes()
            before = {str(path): file_hashes(path) for path in preserved_paths}
            result = fixture.run("uninstall.sh")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assert_no_owned_skills(fixture)
            self.assertEqual(
                before,
                {str(path): file_hashes(path) for path in preserved_paths},
            )
            self.assertEqual(settings_before, settings.read_bytes())
            self.assertEqual(
                (fixture.claude_home / "CLAUDE.md").read_text(encoding="utf-8"),
                "# Unrelated\n",
            )


class ClaudeCodeHostCommandResolutionTests(unittest.TestCase):
    """How host commands are located before they are run, on any platform.

    Windows resolves a bare command name against PATH for executables only, so
    an npm-installed CLI, which is a `.cmd` shim, is never found under its bare
    name. Every host command is therefore resolved to a path before it is run.
    """

    def test_a_required_command_resolves_to_its_installed_path(self) -> None:
        resolved = compatibility.resolve_command("git")
        self.assertEqual(resolved, shutil.which("git"))
        self.assertTrue(Path(resolved).is_absolute())

    def test_the_interpreter_requirement_accepts_the_windows_names(self) -> None:
        for installed in ("python", "py"):
            with self.subTest(interpreter=installed):
                expected = f"C:\\Python\\{installed}.exe"
                with mock.patch.object(
                    compatibility.shutil,
                    "which",
                    side_effect=lambda name, want=installed, path=expected: (
                        path if name == want else None
                    ),
                ):
                    self.assertEqual(
                        compatibility.resolve_command("python3"), expected
                    )

    def test_an_absent_command_is_reported_under_its_required_name(self) -> None:
        with mock.patch.object(compatibility.shutil, "which", return_value=None):
            with self.assertRaises(compatibility.CompatibilityError) as raised:
                compatibility.resolve_command("python3")
        self.assertIn("missing required command: python3", str(raised.exception))

    def test_the_plugin_inventory_runs_the_resolved_host_path(self) -> None:
        shim = r"C:\Users\a\AppData\Roaming\npm\claude.cmd"
        completed = subprocess.CompletedProcess(
            args=[], returncode=0, stdout=ENABLED_PLUGIN_LIST, stderr=""
        )
        with mock.patch.object(compatibility.shutil, "which", return_value=shim):
            with mock.patch.object(
                compatibility.subprocess, "run", return_value=completed
            ) as run:
                compatibility._validate_superpowers()
        self.assertEqual(run.call_args.args[0][0], shim)

    def test_github_authentication_runs_the_resolved_gh_path(self) -> None:
        shim = r"C:\Program Files\GitHub CLI\gh.exe"
        completed = subprocess.CompletedProcess(
            args=[], returncode=0, stdout="", stderr=""
        )
        with mock.patch.object(compatibility.shutil, "which", return_value=shim):
            with mock.patch.object(
                managed_state.subprocess, "run", return_value=completed
            ) as run:
                managed_state._validate_github_authentication()
        self.assertEqual(run.call_args.args[0][0], shim)


if __name__ == "__main__":
    unittest.main()
