"""The repository's own contract: documents against the code they describe.

Prose drifts from implementation silently. Every check here binds a document
to a fact somewhere else in the tree, so a change that updates one and not the
other fails rather than shipping.
"""

import importlib.util
import os
import re
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

VERSION = "1.1.0"
TAGLINE = "Lightweight governance for frontier AI coding agents."

REQUIRED_FILES = (
    "README.md",
    "VERSION",
    "CHANGELOG.md",
    "LICENSE",
    "ATTRIBUTIONS.md",
    "AI_DISCLOSURE.md",
    "SECURITY.md",
    "SUPPORT.md",
    "CONTRIBUTING.md",
    "GOVERNANCE.md",
    "CODE_OF_CONDUCT.md",
    "UPSTREAM.md",
    "AGENTS.md",
    "docs/architecture.md",
    "docs/host-distributions.md",
    "docs/compatibility.md",
    "docs/release-model.md",
    "docs/lineage.md",
    "compatibility/upstreams.json",
    "scripts/manifest.py",
    "scripts/manifest.sh",
    "validate.sh",
    "validate.ps1",
    ".gitattributes",
    ".github/workflows/validate.yml",
    ".github/workflows/windows.yml",
    ".github/PULL_REQUEST_TEMPLATE.md",
    ".github/ISSUE_TEMPLATE/bug_report.yml",
    ".github/ISSUE_TEMPLATE/feature_request.yml",
    ".github/ISSUE_TEMPLATE/config.yml",
    "evals/core-cases.md",
)

HOST_DISTRIBUTIONS = ("codex", "claude-code")

LITE_SKILLS = (
    "super-hero-core",
    "super-hero-release-to-public",
    "super-hero-simplify",
)

# Every document that could plausibly quote a verification command.
VERIFICATION_DOCUMENTS = (
    "README.md",
    "UPSTREAM.md",
    "CONTRIBUTING.md",
    "GOVERNANCE.md",
    "SECURITY.md",
    "SUPPORT.md",
    "AGENTS.md",
    "ATTRIBUTIONS.md",
    "AI_DISCLOSURE.md",
    "docs/architecture.md",
    "docs/compatibility.md",
    "docs/host-distributions.md",
    "docs/release-model.md",
    "docs/lineage.md",
    ".github/PULL_REQUEST_TEMPLATE.md",
)

# The suites the root validator runs, in order. Both entry points declare this
# list, and validate.sh is driven below to prove it runs exactly this.
SUITES = (
    ("upstream compatibility", "evals/test_compatibility.py"),
    ("skill packages", "evals/test_skill_packages.py"),
    ("removed architecture", "evals/test_removed_architecture.py"),
    ("Codex lifecycle", "distributions/codex/evals/test_lifecycle.py"),
    ("Claude Code lifecycle", "distributions/claude-code/evals/test_lifecycle.py"),
    ("Claude Code plugin", "evals/test_claude_code_plugin.py"),
    ("repository contract", "evals/test_repository_contract.py"),
)

BOOTSTRAP_FRAGMENTS = {
    "codex": "distributions/codex/bootstrap/AGENTS.md.fragment",
    "claude-code": "distributions/claude-code/bootstrap/CLAUDE.md.fragment",
}
# A bootstrap block points at the core; it never embeds it. The ancestor's had
# grown past 2,500 characters, which is how a pointer becomes a copy.
BOOTSTRAP_CHARACTER_LIMIT = 2000


def document(path):
    return (ROOT / path).read_text(encoding="utf-8")


def collapse(text):
    """Compare wording without depending on where a line happens to wrap."""
    return " ".join(text.split())


def load_sibling_suite(name):
    """Load another suite in this directory without depending on sys.path."""
    spec = importlib.util.spec_from_file_location(
        f"sibling_{name}", Path(__file__).resolve().parent / f"{name}.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_compatibility_module(distribution):
    """Load one distribution's compatibility.py under a distinct module name.

    Both distributions ship a module literally named `compatibility`, so a
    plain import of either would collide with the other in this single
    process; loading each by path under a distribution-qualified name avoids
    that without touching sys.modules.
    """
    module_path = ROOT / "distributions" / distribution / "lib" / "compatibility.py"
    spec = importlib.util.spec_from_file_location(
        f"{distribution.replace('-', '_')}_compatibility", module_path
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


FENCE_OPENING = re.compile(r"^(?: {0,3})(?P<marker>`{3,}|~{3,})(?P<info>.*)$")
INLINE_CODE_SPAN = re.compile(
    r"(?<!`)(?P<marker>`+)(?!`)(?P<code>.*?)(?<!`)(?P=marker)(?!`)", re.DOTALL
)


def fence_marker(line):
    match = FENCE_OPENING.fullmatch(line)
    if match is None:
        return None
    marker = match.group("marker")
    if marker[0] == "`" and "`" in match.group("info"):
        return None
    return marker


def is_closing_fence(line, marker):
    return (
        re.fullmatch(
            rf" {{0,3}}{re.escape(marker[0])}{{{len(marker)},}}[ \t]*", line
        )
        is not None
    )


def markdown_commands(text):
    lines = text.splitlines()
    prose_lines = []
    index = 0
    while index < len(lines):
        marker = fence_marker(lines[index])
        if marker is not None:
            index += 1
            while index < len(lines) and not is_closing_fence(lines[index], marker):
                command = lines[index].strip()
                if command and not command.startswith("#"):
                    yield command.removeprefix("$ ")
                index += 1
            if index < len(lines):
                index += 1
            continue
        prose_lines.append(lines[index])
        index += 1
    for match in INLINE_CODE_SPAN.finditer("\n".join(prose_lines)):
        command = match.group("code").strip()
        if command:
            yield command


def is_local_verification_command(command):
    patterns = (
        r"(?:^|\s)pytest(?:\s|$)",
        r"(?:^|\s)python\d?(?:\s+-B)?\s+-m\s+unittest(?:\s|$)",
        r"^python(?:\d+(?:\.\d+)*)?(?:\s+-[A-Za-z0-9_-]+)*\s+(?:\./)?(?:[^\s]*/)?"
        r"(?:test_[^/\s]+|[^/\s]*eval[^/\s]*)\.py(?:\s|$)",
        r"(?:^|\s)(?:make|npm)\s+test(?:\s|$)",
        r"^(?:\./|bash\s+|sh\s+)(?:[^\s]*/)?validate\.sh(?:\s|$)",
        r"^(?:\.[\\/]|pwsh\s+)(?:[^\s]*[\\/])?validate\.ps1(?:\s|$)",
        r"^(?:\./|bash\s+|sh\s+)(?:[^\s]*/)?manifest\.sh(?:\s|$)",
    )
    return any(re.search(pattern, command) for pattern in patterns)


def markdown_section(text, heading):
    lines = text.splitlines()
    try:
        start = lines.index(f"## {heading}") + 1
    except ValueError as error:
        raise ValueError(f"missing section {heading}") from error
    end = next(
        (index for index in range(start, len(lines)) if lines[index].startswith("## ")),
        len(lines),
    )
    return "\n".join(lines[start:end])


def parse_markdown_table(section):
    lines = [line for line in section.splitlines() if line.strip()]
    table_start = next(
        (index for index, line in enumerate(lines) if line.startswith("|")), None
    )
    if table_start is None or table_start + 1 >= len(lines):
        raise ValueError("missing Markdown table")

    def cells(line):
        if not line.startswith("|") or not line.endswith("|"):
            raise ValueError("malformed Markdown table row")
        return [cell.strip() for cell in line[1:-1].split("|")]

    headers = cells(lines[table_start])
    divider = cells(lines[table_start + 1])
    if len(headers) != len(divider) or not all(
        re.fullmatch(r":?-{3,}:?", cell) for cell in divider
    ):
        raise ValueError("malformed Markdown table divider")
    rows = []
    for line in lines[table_start + 2 :]:
        if not line.startswith("|"):
            break
        row = cells(line)
        if len(row) != len(headers):
            raise ValueError("Markdown table row has the wrong number of cells")
        rows.append(dict(zip(headers, row)))
    return headers, rows


def workflow_step_run(workflow_text, step_name):
    """Return the non-empty lines of one named workflow step's run block."""
    pattern = re.compile(
        rf"^      - name: {re.escape(step_name)}\n(?P<body>(?:^ .*\n|^\n)*)",
        re.MULTILINE,
    )
    match = pattern.search(workflow_text)
    if match is None:
        raise ValueError(f"missing workflow step {step_name!r}")
    body = match.group("body")
    run = re.search(r"^        run: \|\n(?P<lines>(?:^ {10}.*\n|^\n)*)", body, re.MULTILINE)
    if run is None:
        single = re.search(r"^        run: (?P<line>.*)$", body, re.MULTILINE)
        if single is None:
            raise ValueError(f"workflow step {step_name!r} has no run block")
        return [single.group("line").strip()]
    return [line.strip() for line in run.group("lines").splitlines() if line.strip()]


def internal_links(text):
    """Every relative Markdown link target, without its anchor."""
    for match in re.finditer(r"\]\((?P<target>[^)]+)\)", text):
        target = match.group("target")
        if target.startswith(("http://", "https://", "mailto:", "#")):
            continue
        yield target.split("#", 1)[0]


class RequiredFilesTests(unittest.TestCase):
    def test_required_files_exist(self):
        for path in REQUIRED_FILES:
            with self.subTest(path=path):
                self.assertTrue((ROOT / path).is_file(), f"missing {path}")

    def test_every_distribution_ships_its_documented_files(self):
        for distribution in HOST_DISTRIBUTIONS:
            directory = ROOT / "distributions" / distribution
            for name in (
                "README.md",
                "install.sh",
                "install.command",
                "install.ps1",
                "uninstall.sh",
                "uninstall.ps1",
                "validate.sh",
                "validate.ps1",
                "lib/bootstrap.py",
                "lib/compatibility.py",
                "lib/managed_state.py",
                "evals/__init__.py",
                "evals/test_lifecycle.py",
            ):
                with self.subTest(distribution=distribution, name=name):
                    self.assertTrue((directory / name).is_file(), name)

    def test_no_internal_link_is_dead(self):
        markdown = [
            path
            for path in ROOT.rglob("*.md")
            if ".git" not in path.parts and "__pycache__" not in path.parts
        ]
        self.assertTrue(markdown)
        for path in markdown:
            text = path.read_text(encoding="utf-8")
            for target in internal_links(text):
                with self.subTest(
                    source=path.relative_to(ROOT).as_posix(), target=target
                ):
                    self.assertTrue(
                        (path.parent / target).exists(),
                        f"dead link to {target}",
                    )


class VersionTests(unittest.TestCase):
    def test_version_file_is_exactly_the_release_version(self):
        self.assertEqual(document("VERSION"), f"{VERSION}\n")

    def test_the_changelog_starts_at_this_version(self):
        releases = re.findall(r"^## (\S+)", document("CHANGELOG.md"), re.MULTILINE)
        self.assertTrue(releases, "the changelog records no release")
        self.assertEqual(releases[0], VERSION)
        self.assertEqual(
            len(releases),
            len(set(releases)),
            "the changelog repeats a version heading",
        )

    def test_the_readme_is_the_lite_front_door(self):
        readme = document("README.md")
        self.assertTrue(readme.startswith("# Super-Hero Lite\n"))
        self.assertIn(TAGLINE, readme)


class ValidatorContractTests(unittest.TestCase):
    @unittest.skipIf(
        os.name == "nt", "this check drives the POSIX entry point through bash"
    )
    def test_root_validator_runs_the_contract_in_order(self):
        """Drive validate.sh against recording shims and read back what it ran."""
        with tempfile.TemporaryDirectory() as temporary_name:
            package = Path(temporary_name) / "package"
            package.mkdir()
            shutil.copy(ROOT / "validate.sh", package / "validate.sh")
            command_log = Path(temporary_name) / "commands.tsv"
            fake_bin = Path(temporary_name) / "bin"
            fake_bin.mkdir()
            recorder = """#!/bin/sh
{
  printf '%s' "${0##*/}"
  for argument do
    printf '\t%s' "$argument"
  done
  printf '\n'
} >> "$COMMAND_LOG"
"""
            for command in ("python3", "find", "bash"):
                path = fake_bin / command
                path.write_text(recorder, encoding="utf-8")
                path.chmod(0o755)
            environment = os.environ.copy()
            environment["COMMAND_LOG"] = str(command_log)
            environment["PATH"] = f"{fake_bin}:/usr/bin:/bin"

            result = subprocess.run(
                ["/bin/bash", str(package / "validate.sh")],
                cwd=package,
                env=environment,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )

            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            commands = [
                line.split("\t")
                for line in command_log.read_text(encoding="utf-8").splitlines()
            ]
            expected = [
                ["python3", "-m", "unittest", module, "-v"] for _, module in SUITES
            ]
            expected.append(
                [
                    "find", ".", "-type", "f", "(", "-name", "*.sh", "-o",
                    "-name", "*.command", ")", "-not", "-path", "./.git/*",
                    "-exec", "sh", "-c",
                    'status=0; for file do bash -n "$file" || status=1; '
                    'done; exit "$status"',
                    "sh", "{}", "+",
                ]
            )
            expected.append(["bash", "scripts/manifest.sh", "--verify"])
            self.assertEqual(commands, expected)

    @unittest.skipIf(
        os.name == "nt", "this check drives the POSIX entry point through bash"
    )
    def test_root_validator_reports_a_failing_check_and_continues(self):
        """A failure must be counted and reported, not abort the run."""
        with tempfile.TemporaryDirectory() as temporary_name:
            package = Path(temporary_name) / "package"
            package.mkdir()
            shutil.copy(ROOT / "validate.sh", package / "validate.sh")
            fake_bin = Path(temporary_name) / "bin"
            fake_bin.mkdir()
            for command, status in (("python3", 1), ("find", 0), ("bash", 0)):
                path = fake_bin / command
                path.write_text(f"#!/bin/sh\nexit {status}\n", encoding="utf-8")
                path.chmod(0o755)
            environment = os.environ.copy()
            environment["PATH"] = f"{fake_bin}:/usr/bin:/bin"

            result = subprocess.run(
                ["/bin/bash", str(package / "validate.sh")],
                cwd=package,
                env=environment,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )

            self.assertNotEqual(result.returncode, 0)
            for label, _ in SUITES:
                with self.subTest(label=label):
                    self.assertIn(f"FAIL  {label}", result.stdout)
            self.assertIn("PASS  shell syntax", result.stdout)
            self.assertIn(
                f"Validation summary: {len(SUITES)} failure(s), 0 warning(s).",
                result.stdout,
            )

    @unittest.skipIf(
        os.name == "nt", "this check drives the POSIX entry point through bash"
    )
    def test_root_validator_rejects_an_unknown_mode(self):
        result = subprocess.run(
            ["/bin/bash", str(ROOT / "validate.sh"), "installed"],
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        self.assertEqual(result.returncode, 2)
        self.assertIn("Usage:", result.stderr)

    def test_windows_validator_declares_the_same_contract_in_the_same_order(self):
        """Static comparison; the windows-latest CI job proves it runs."""
        shell = document("validate.sh")
        powershell = document("validate.ps1")

        posix_suites = re.findall(
            r'run_check "([^"]+)" python3 -m unittest (\S+) -v', shell
        )
        windows_suites = re.findall(
            r"@\{ Label = '([^']+)'; Module = '([^']+)' \}", powershell
        )
        self.assertEqual(posix_suites, list(SUITES))
        self.assertEqual(posix_suites, windows_suites)

        # Both entry points end on the manifest, and the Windows one records
        # what it cannot check instead of reporting it as passed.
        self.assertIn("Invoke-Check 'package manifest'", powershell)
        self.assertIn("'scripts/manifest.py' --verify", powershell)
        for reduction in (
            "SKIP  shell syntax",
            "SKIP  POSIX lifecycle entry points",
        ):
            with self.subTest(reduction=reduction):
                self.assertIn(reduction, powershell)
        self.assertIn(
            "Validation summary: $script:Failures failure(s), "
            "$script:Warnings warning(s).",
            powershell,
        )


class EntryPointTests(unittest.TestCase):
    def test_every_distribution_entry_point_has_a_windows_sibling(self):
        for distribution in HOST_DISTRIBUTIONS:
            directory = ROOT / "distributions" / distribution
            variable = re.search(
                r"\$\{(\w+):-\$HOME/",
                document(f"distributions/{distribution}/install.sh"),
            )
            self.assertIsNotNone(variable)
            for entry in ("install", "uninstall", "validate"):
                with self.subTest(distribution=distribution, entry=entry):
                    self.assertTrue((directory / f"{entry}.sh").is_file())
                    windows = directory / f"{entry}.ps1"
                    self.assertTrue(windows.is_file())
                    text = windows.read_text(encoding="utf-8")
                    self.assertIn("lib/managed_state.py", text)
                    self.assertIn(f"$env:{variable.group(1)}", text)
                    self.assertIn("exit $LASTEXITCODE", text)

    def test_every_windows_entry_point_resolves_the_interpreter_identically(self):
        """One block copied seven times: a fix to it must reach all of them."""
        entry_points = [ROOT / "validate.ps1"] + [
            ROOT / "distributions" / distribution / f"{entry}.ps1"
            for distribution in HOST_DISTRIBUTIONS
            for entry in ("install", "uninstall", "validate")
        ]
        self.assertEqual(len(entry_points), 7)

        blocks = set()
        for entry_point in entry_points:
            script = entry_point.read_text(encoding="utf-8")
            start = script.index("$python = $null")
            end = script.index("exit 1\n}\n", start) + len("exit 1\n}\n")
            block = script[start:end]
            blocks.add(block)
            with self.subTest(entry_point=entry_point.name):
                # Several commands can answer to one name on Windows, so the
                # first match is taken rather than the whole match set.
                self.assertIn("$found[0].Source", block)
        self.assertEqual(len(blocks), 1, "the interpreter blocks have drifted")

    def test_committed_bytes_are_never_end_of_line_converted(self):
        """The manifest and every byte comparison depend on this."""
        self.assertIn("* -text", document(".gitattributes"))

    def test_posix_entry_points_are_executable(self):
        for path in list(ROOT.glob("*.sh")) + list(
            ROOT.glob("distributions/*/*.sh")
        ) + list(ROOT.glob("distributions/*/*.command")) + list(
            ROOT.glob("scripts/*.sh")
        ):
            with self.subTest(path=path.relative_to(ROOT).as_posix()):
                self.assertTrue(
                    os.access(path, os.X_OK), "entry point is not executable"
                )


class ContinuousIntegrationTests(unittest.TestCase):
    def test_linux_ci_runs_the_whole_contract_unconditionally(self):
        workflow = document(".github/workflows/validate.yml")
        self.assertIn("runs-on: ubuntu-latest", workflow)
        self.assertIn("run: bash ./validate.sh", workflow)
        # No path filter: every change is validated in full on Linux.
        self.assertNotIn("paths:", workflow)

    def test_windows_ci_runs_only_when_windows_is_touched(self):
        workflow = document(".github/workflows/windows.yml")
        self.assertIn("runs-on: windows-latest", workflow)
        self.assertIn("run: pwsh ./validate.ps1", workflow)
        self.assertEqual(workflow.count("paths:"), 2, "both triggers need a filter")
        for filtered in (
            "'**/*.ps1'",
            "'.gitattributes'",
            "'scripts/manifest.py'",
            "'distributions/*/lib/**'",
            "'distributions/*/evals/**'",
            "'distributions/claude-code/plugin/**'",
            "'.claude-plugin/**'",
            "'evals/**'",
        ):
            with self.subTest(path=filtered):
                self.assertEqual(workflow.count(filtered), 2)

    def test_windows_ci_proves_an_installation_and_its_uninstall(self):
        workflow = document(".github/workflows/windows.yml")
        for step in (
            "Install the Matt Pocock skills",
            "Install the Claude Code CLI",
            "Enable the Superpowers plugin",
            "Validate and install the Claude Code plugin",
            "Install and validate the distribution",
            "Uninstall must remove what it owns and nothing else",
        ):
            with self.subTest(step=step):
                self.assertIn(f"- name: {step}", workflow)
        # The uninstall job's whole point is that validation then fails and the
        # prerequisite survives.
        self.assertIn("the distribution still validates after uninstall", workflow)
        self.assertIn(
            "uninstall removed a prerequisite skill it does not own", workflow
        )
        self.assertIn(
            "uninstall removed the plugin, which it does not own", workflow
        )
        # The one shell the local suite cannot exercise.
        self.assertIn(
            "reproduces the session context under PowerShell", workflow
        )


class DocumentationConsistencyTests(unittest.TestCase):
    def test_every_readme_describes_exactly_the_three_lite_skills(self):
        for path in (
            "README.md",
            "distributions/codex/README.md",
            "distributions/claude-code/README.md",
        ):
            text = document(path)
            with self.subTest(path=path):
                for skill in LITE_SKILLS:
                    self.assertIn(f"`{skill}`", text, skill)
                self.assertIn("three", text.lower())

    def test_every_readme_names_the_same_dependency_identities(self):
        root = document("README.md")
        codex = document("distributions/codex/README.md")
        claude = document("distributions/claude-code/README.md")

        self.assertIn("`superpowers@openai-curated`", root)
        self.assertIn("`superpowers@openai-curated`", codex)
        self.assertNotIn("superpowers@openai-curated", claude)

        self.assertIn("`superpowers@superpowers-marketplace`", root)
        self.assertIn("`superpowers@superpowers-marketplace`", claude)
        self.assertNotIn("superpowers@superpowers-marketplace", codex)

        for text, path in ((root, "README.md"), (codex, "codex"), (claude, "claude")):
            with self.subTest(path=path):
                self.assertIn("eleven", text.lower())

    def test_the_eleven_pocock_skills_are_listed_identically_everywhere(self):
        expected = load_compatibility_module("codex").POCOCK_SKILLS
        self.assertEqual(len(expected), 11)
        self.assertEqual(
            expected, load_compatibility_module("claude-code").POCOCK_SKILLS
        )
        for path in (
            "README.md",
            "distributions/codex/README.md",
            "distributions/claude-code/README.md",
        ):
            text = document(path)
            for skill in expected:
                with self.subTest(path=path, skill=skill):
                    self.assertIn(f"`{skill}`", text)

    def test_readmes_quote_the_install_commands_the_code_actually_uses(self):
        for distribution in HOST_DISTRIBUTIONS:
            module = load_compatibility_module(distribution)
            prerequisites = markdown_section(
                document(f"distributions/{distribution}/README.md"), "Prerequisites"
            )
            with self.subTest(distribution=distribution):
                self.assertIn(
                    module.POCOCK_INSTALL_COMMAND,
                    prerequisites,
                    f"distributions/{distribution}/README.md must quote "
                    "compatibility.py's own POCOCK_INSTALL_COMMAND",
                )
        pocock_section = markdown_section(
            document("UPSTREAM.md"), "Matt Pocock skills"
        )
        for distribution in HOST_DISTRIBUTIONS:
            module = load_compatibility_module(distribution)
            with self.subTest(distribution=distribution):
                self.assertIn(module.POCOCK_INSTALL_COMMAND, pocock_section)

    def test_claude_superpowers_commands_match_the_tested_integration(self):
        run_lines = workflow_step_run(
            document(".github/workflows/windows.yml"),
            "Enable the Superpowers plugin",
        )
        commands = [line for line in run_lines if line != "claude plugin list --json"]
        self.assertEqual(
            len(commands),
            2,
            "expected the marketplace-add and install commands, got: "
            + repr(run_lines),
        )
        claude_prerequisites = markdown_section(
            document("distributions/claude-code/README.md"), "Prerequisites"
        )
        upstream_superpowers = markdown_section(
            document("UPSTREAM.md"), "Obra/Prime Radiant Superpowers"
        )
        for command in commands:
            with self.subTest(command=command):
                self.assertIn(command, claude_prerequisites)
                self.assertIn(command, upstream_superpowers)

    def test_codex_docs_invent_no_superpowers_install_command(self):
        """The Codex marketplace command was never verified, so none is given."""
        codex_readme = document("distributions/codex/README.md")
        upstream = document("UPSTREAM.md")
        for text, label in ((codex_readme, "codex README"), (upstream, "UPSTREAM.md")):
            with self.subTest(document=label):
                self.assertIsNone(
                    re.search(
                        r"codex plugin (?:marketplace add|install)", text
                    ),
                    "no verified Codex plugin-install command exists to quote",
                )
        for text, label in ((codex_readme, "codex README"), (upstream, "UPSTREAM.md")):
            with self.subTest(document=label):
                self.assertIn(
                    "no verified marketplace-add or install command",
                    collapse(text),
                )

    def test_documented_local_verification_uses_only_the_root_validator(self):
        verification_commands = {
            command
            for path in VERIFICATION_DOCUMENTS
            for command in markdown_commands(document(path))
            if is_local_verification_command(command)
        }
        self.assertEqual(verification_commands, {"./validate.sh", ".\\validate.ps1"})

    def test_host_distribution_document_covers_every_recorded_distribution(self):
        import json

        recorded = {
            item["id"]
            for item in json.loads(document("compatibility/upstreams.json"))[
                "distributions"
            ]
        }
        self.assertEqual(recorded, set(HOST_DISTRIBUTIONS))

        hosts = document("docs/host-distributions.md")
        _, rows = parse_markdown_table(markdown_section(hosts, "Current support"))
        self.assertEqual(
            {row["Host distribution"].strip("`") for row in rows},
            set(HOST_DISTRIBUTIONS),
        )

    def test_compatibility_document_renders_its_own_metadata(self):
        import json

        metadata = json.loads(document("compatibility/upstreams.json"))
        profiles = {item["id"]: item for item in metadata["distributions"]}
        compatibility = document("docs/compatibility.md")
        _, rows = parse_markdown_table(
            markdown_section(compatibility, "Recorded host profiles")
        )
        rendered = {row["Host distribution"].strip("`"): row for row in rows}
        self.assertEqual(set(rendered), set(profiles))
        for identifier, profile in profiles.items():
            with self.subTest(distribution=identifier):
                row = rendered[identifier]
                self.assertIn(profile["testedHostCli"], row["Tested host CLI"])
                self.assertEqual(profile["hostCliEvidence"], row["Evidence"])
                for capability in profile["requiredCapabilities"]:
                    self.assertIn(f"`{capability}`", row["Required capabilities"])

        for identifier, profile in profiles.items():
            section = markdown_section(
                compatibility, f"Recorded upstream baseline for {identifier}"
            )
            _, upstream_rows = parse_markdown_table(section)
            self.assertEqual(len(upstream_rows), len(profile["dependencies"]))
            for dependency in profile["dependencies"]:
                with self.subTest(distribution=identifier, dependency=dependency["id"]):
                    self.assertIn(f"`{dependency['testedRef']}`", section)
                    self.assertIn(f"`{dependency['testedCommit']}`", section)
                    self.assertIn(dependency["manager"], section)

    def test_upstream_document_agrees_with_the_metadata(self):
        import json

        metadata = json.loads(document("compatibility/upstreams.json"))
        upstream = document("UPSTREAM.md")
        identifiers = {
            dependency["id"]
            for profile in metadata["distributions"]
            for dependency in profile["dependencies"]
        }
        self.assertEqual(identifiers, {"mattpocock-skills", "superpowers"})
        # Exactly the recorded dependencies, named as the sections that
        # describe them, and nothing else presented as a dependency.
        for heading in ("Matt Pocock skills", "Obra/Prime Radiant Superpowers"):
            with self.subTest(heading=heading):
                self.assertIn(f"## {heading}", upstream)
        plugin_identities = {
            dependency["detection"]["pluginId"]
            for profile in metadata["distributions"]
            for dependency in profile["dependencies"]
            if dependency["id"] == "superpowers"
        }
        for plugin in plugin_identities:
            with self.subTest(plugin=plugin):
                self.assertIn(f"`{plugin}`", upstream)


class BootstrapBlockTests(unittest.TestCase):
    def test_each_bootstrap_block_is_current_concise_and_points_at_the_core(self):
        for distribution, relative in BOOTSTRAP_FRAGMENTS.items():
            fragment = document(relative)
            with self.subTest(distribution=distribution):
                marker = (
                    "SUPER_HERO_LITE_CODEX_BOOTSTRAP v1"
                    if distribution == "codex"
                    else "SUPER_HERO_LITE_CLAUDE_CODE_BOOTSTRAP v1"
                )
                self.assertEqual(fragment.count(f"<!-- BEGIN {marker} -->"), 1)
                self.assertEqual(fragment.count(f"<!-- END {marker} -->"), 1)
                self.assertLess(
                    len(fragment),
                    BOOTSTRAP_CHARACTER_LIMIT,
                    "a bootstrap block points at the core; it never embeds it",
                )
                self.assertIn("`super-hero-core`", fragment)
                self.assertIn("`super-hero-release-to-public`", fragment)
                self.assertIn("`super-hero-simplify`", fragment)
                for mode in ("DIRECT", "CONTROLLED", "EXTERNAL"):
                    self.assertIn(mode, fragment)

    def test_the_two_bootstrap_blocks_do_not_share_a_marker(self):
        codex = document(BOOTSTRAP_FRAGMENTS["codex"])
        claude = document(BOOTSTRAP_FRAGMENTS["claude-code"])
        self.assertNotIn("SUPER_HERO_LITE_CLAUDE_CODE_BOOTSTRAP", codex)
        self.assertNotIn("SUPER_HERO_LITE_CODEX_BOOTSTRAP", claude)

    def test_each_distribution_declares_the_marker_its_fragment_carries(self):
        for distribution, relative in BOOTSTRAP_FRAGMENTS.items():
            with self.subTest(distribution=distribution):
                bootstrap = document(
                    f"distributions/{distribution}/lib/bootstrap.py"
                )
                declared = re.findall(r'"(<!-- (?:BEGIN|END) [^"]+ -->)"', bootstrap)
                self.assertEqual(len(declared), 2, declared)
                fragment = document(relative)
                for marker in declared:
                    self.assertIn(marker, fragment)


class LineageTests(unittest.TestCase):
    def test_the_readme_records_the_exact_ancestor_baseline(self):
        readme = document("README.md")
        for fact in (
            "MicheleDataBeat/super-hero-workflow",
            "`1.6.4`",
            "`690cfdb2ad9827e75b0da7ed3307d9a01ee72ee7`",
        ):
            with self.subTest(fact=fact):
                self.assertIn(fact, readme)
        self.assertIn("**not a Git fork**", readme)
        self.assertIn("**not inherit the ancestor's Git history**", readme)

    def test_lineage_records_the_same_baseline_as_the_readme(self):
        lineage = document("docs/lineage.md")
        for fact in (
            "`MicheleDataBeat/super-hero-workflow`",
            "`1.6.4`",
            "`690cfdb2ad9827e75b0da7ed3307d9a01ee72ee7`",
        ):
            with self.subTest(fact=fact):
                self.assertIn(fact, lineage)

    def test_lineage_explains_every_removal_the_scan_enforces(self):
        """The scan and the explanation are one fact stated two ways."""
        removed = load_sibling_suite("test_removed_architecture")

        lineage = document("docs/lineage.md")
        for mechanism in removed.FORBIDDEN_MECHANISMS:
            with self.subTest(mechanism=mechanism):
                # Each mechanism is keyed in that table by a label whose first
                # word is the term the lineage explanation uses for it, so a
                # deletion cannot be enforced without being accounted for. A
                # new entry either uses vocabulary the explanation already has
                # or the explanation gains a sentence; either way the two stay
                # in step.
                keyword = mechanism.split()[0].lower()
                self.assertIn(keyword, lineage.lower())

    def test_attributions_carry_the_licence_obligations(self):
        attributions = document("ATTRIBUTIONS.md")
        for expected in (
            "mattpocock/skills",
            "obra/superpowers",
            "MicheleDataBeat/super-hero-workflow",
            "MIT",
            "No endorsement",
        ):
            with self.subTest(expected=expected):
                self.assertIn(expected, attributions)
        self.assertIn("MIT License", document("LICENSE"))
        self.assertIn("Copyright (c) 2026 MicheleDataBeat", document("LICENSE"))


if __name__ == "__main__":
    unittest.main()
