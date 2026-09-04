"""The Claude Code plugin package contract.

The Claude Code host has two delivery forms for one product: the installer,
which copies the three skills into the host's configuration directory and
manages one marked block in `CLAUDE.md`, and the plugin, which the host's own
package manager installs. Two forms of the same thing drift unless something
fails when they disagree, so this suite pins the plugin against the material
the installer already ships:

- the plugin's skills against the packaged skills, byte for byte;
- the plugin's session context against the packaged bootstrap fragment, under
  two declared substitutions, because a plugin skill is invoked by its
  plugin-qualified id and an installed skill by its bare one, and because the
  clause saying where those skills live is not true of a plugin;
- the hook that delivers that context, by running its command and reading what
  it prints.

Nothing here installs anything or reads user state.
"""

import json
import os
import re
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

PLUGIN_ROOT = ROOT / "distributions" / "claude-code" / "plugin"
PLUGIN_MANIFEST = PLUGIN_ROOT / ".claude-plugin" / "plugin.json"
MARKETPLACE_MANIFEST = ROOT / ".claude-plugin" / "marketplace.json"
HOOKS_MANIFEST = PLUGIN_ROOT / "hooks" / "hooks.json"
SESSION_CONTEXT = PLUGIN_ROOT / "hooks" / "session-context.md"
BOOTSTRAP_FRAGMENT = (
    ROOT / "distributions" / "claude-code" / "bootstrap" / "CLAUDE.md.fragment"
)

# The plugin and the marketplace entry are published under these identities.
# They appear in the command a user types, so they are pinned rather than
# derived.
PLUGIN_NAME = "super-hero-lite"
MARKETPLACE_NAME = "super-hero-lite"
PLUGIN_SOURCE = "./distributions/claude-code/plugin"

LITE_SKILLS = (
    "super-hero-core",
    "super-hero-release-to-public",
    "super-hero-simplify",
)

# Every component key a plugin manifest may carry. This plugin declares none
# of them: `skills/` and `hooks/hooks.json` are auto-discovered, which was
# verified against a real installation. Declaring one would point the host at
# a path these tests do not inspect, so the manifest would keep validating
# while the host loaded something else.
COMPONENT_KEYS = (
    "skills",
    "commands",
    "agents",
    "workflows",
    "hooks",
    "mcpServers",
    "lspServers",
    "outputStyles",
    "experimental",
)

# What the plugin contains, exactly. Naming what ships is stronger than naming
# what must not, and it does not go stale when the host gains a component type.
# `agents/` is the absence that matters most: Lite assigns no work role to a
# model and ships no role definitions, in either delivery form.
PLUGIN_TREE = {
    ".": {".claude-plugin", "README.md", "hooks", "skills"},
    ".claude-plugin": {"plugin.json"},
    "hooks": {"hooks.json", "session-context.md"},
}

# The two declared differences between the installed block and the plugin's
# copy of it: the clause naming where the skills live, and the skill ids,
# which the host namespaces so a plugin session can invoke them. Every other
# sentence must be identical, which is what makes the two delivery forms one
# policy rather than two.
SESSION_CONTEXT_SUBSTITUTIONS = (
    ("from the persistent Claude Code skills directories", "from this plugin"),
    ("`super-hero-core`", "`super-hero-lite:super-hero-core`"),
    (
        "`super-hero-release-to-public`",
        "`super-hero-lite:super-hero-release-to-public`",
    ),
    ("`super-hero-simplify`", "`super-hero-lite:super-hero-simplify`"),
)


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def file_map(root: Path) -> dict[str, bytes]:
    """Every file below root, as a relative POSIX path mapped to its bytes."""
    return {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


def tree_differences(expected: Path, actual: Path) -> list[str]:
    """Report every path that is missing, extra, or different in `actual`."""
    left, right = file_map(expected), file_map(actual)
    differences = [f"missing: {path}" for path in sorted(set(left) - set(right))]
    differences += [f"extra: {path}" for path in sorted(set(right) - set(left))]
    differences += [
        f"differs: {path}"
        for path in sorted(set(left) & set(right))
        if left[path] != right[path]
    ]
    return differences


def bootstrap_body(fragment: str) -> str:
    """The fragment without the marker pair the installer needs and a plugin
    does not: a plugin owns its whole context contribution, so it has nothing
    to delimit."""
    lines = fragment.splitlines(keepends=True)
    if not lines[0].startswith("<!-- BEGIN ") or not lines[-1].startswith("<!-- END "):
        raise ValueError("the bootstrap fragment is not a single marked block")
    return "".join(lines[1:-1])


def plugin_session_context(fragment: str) -> str:
    """The bootstrap block expressed for the plugin delivery form."""
    text = bootstrap_body(fragment)
    for installed, plugin in SESSION_CONTEXT_SUBSTITUTIONS:
        if installed not in text:
            raise ValueError(f"the bootstrap block no longer says {installed!r}")
        text = text.replace(installed, plugin)
    return text


class PluginManifestTests(unittest.TestCase):
    def test_the_plugin_manifest_declares_the_published_identity(self):
        manifest = read_json(PLUGIN_MANIFEST)
        self.assertEqual(manifest["name"], PLUGIN_NAME)
        self.assertEqual(manifest["license"], "MIT")
        self.assertEqual(
            manifest["repository"],
            "https://github.com/MicheleDataBeat/super-hero-lite",
        )

    def test_the_plugin_version_is_the_release_version(self):
        """One product, one version. A plugin pinned to a stale version would
        keep serving it after the repository moved on."""
        version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
        self.assertEqual(read_json(PLUGIN_MANIFEST)["version"], version)
        self.assertEqual(read_json(MARKETPLACE_MANIFEST)["version"], version)
        self.assertEqual(self.marketplace_entry()["version"], version)

    def test_the_two_manifests_describe_the_plugin_identically(self):
        """The description is typed twice, so it can say two things."""
        self.assertEqual(
            read_json(PLUGIN_MANIFEST)["description"],
            self.marketplace_entry()["description"],
        )

    def marketplace_entry(self) -> dict:
        marketplace = read_json(MARKETPLACE_MANIFEST)
        self.assertEqual(marketplace["name"], MARKETPLACE_NAME)
        entries = [
            entry for entry in marketplace["plugins"] if entry["name"] == PLUGIN_NAME
        ]
        self.assertEqual(len(entries), 1, "the marketplace must list the plugin once")
        return entries[0]

    def test_the_marketplace_lists_only_this_plugin(self):
        marketplace = read_json(MARKETPLACE_MANIFEST)
        self.assertEqual([entry["name"] for entry in marketplace["plugins"]], [PLUGIN_NAME])

    def test_every_document_quotes_the_install_command_that_works(self):
        """A wrong id here is invisible: nothing else a user reads corrects it,
        and no other check compares the prose to the manifests."""
        install = f"/plugin install {PLUGIN_NAME}@{MARKETPLACE_NAME}"
        for relative in (
            "README.md",
            "distributions/claude-code/README.md",
            "distributions/claude-code/plugin/README.md",
        ):
            with self.subTest(document=relative):
                text = (ROOT / relative).read_text(encoding="utf-8")
                self.assertIn(install, text)
                self.assertIn(
                    "/plugin marketplace add MicheleDataBeat/super-hero-lite", text
                )

    def test_the_marketplace_source_resolves_to_the_plugin(self):
        """A relative source resolves against the marketplace root, which is
        the repository root. If the plugin moves, this is what fails."""
        entry = self.marketplace_entry()
        self.assertEqual(entry["source"], PLUGIN_SOURCE)
        manifest = ROOT / entry["source"] / ".claude-plugin" / "plugin.json"
        self.assertTrue(manifest.is_file(), f"no plugin at {entry['source']}")
        self.assertEqual(read_json(manifest)["name"], entry["name"])

    def test_the_plugin_contains_exactly_what_it_declares(self):
        """Lite ships three skills and one instruction contribution, and
        nothing else. A stray file here is invisible once the manifest is
        regenerated, and `CLAUDE.md` is the one this delivery form invites:
        the host does not load it, so it would be dead weight that reads like
        governance."""
        manifest = read_json(PLUGIN_MANIFEST)
        for key in COMPONENT_KEYS:
            with self.subTest(key=key):
                self.assertNotIn(
                    key,
                    manifest,
                    f"declaring {key} points the host away from the shipped tree",
                )
        for relative, expected in PLUGIN_TREE.items():
            with self.subTest(directory=relative):
                present = {entry.name for entry in (PLUGIN_ROOT / relative).iterdir()}
                self.assertEqual(present, expected)


class PluginSkillTests(unittest.TestCase):
    def test_the_plugin_ships_the_packaged_skills_byte_for_byte(self):
        """A plugin cannot reference a path outside its own root, so it carries
        its own copy. The copy is only trustworthy while it is identical."""
        self.assertEqual(tree_differences(ROOT / "skills", PLUGIN_ROOT / "skills"), [])

    def test_the_plugin_ships_exactly_the_three_lite_skills(self):
        shipped = sorted(
            entry.name
            for entry in (PLUGIN_ROOT / "skills").iterdir()
            if entry.is_dir() or entry.is_symlink()
        )
        self.assertEqual(shipped, sorted(LITE_SKILLS))

    def test_the_comparison_would_catch_a_drifted_copy(self):
        """Arm the instrument: a comparison never shown to fire proves nothing."""
        with tempfile.TemporaryDirectory() as temporary_name:
            copy = Path(temporary_name) / "skills"
            shutil.copytree(PLUGIN_ROOT / "skills", copy)
            self.assertEqual(tree_differences(ROOT / "skills", copy), [])

            edited = copy / "super-hero-core" / "SKILL.md"
            edited.write_bytes(edited.read_bytes() + b"drift\n")
            self.assertIn(
                "differs: super-hero-core/SKILL.md", tree_differences(ROOT / "skills", copy)
            )

            edited.unlink()
            self.assertIn(
                "missing: super-hero-core/SKILL.md",
                tree_differences(ROOT / "skills", copy),
            )

            (copy / "unexpected.md").write_text("extra\n", encoding="utf-8")
            self.assertIn("extra: unexpected.md", tree_differences(ROOT / "skills", copy))


class SessionContextTests(unittest.TestCase):
    def fragment(self) -> str:
        return BOOTSTRAP_FRAGMENT.read_text(encoding="utf-8")

    def test_the_session_context_is_the_bootstrap_block_in_plugin_form(self):
        self.assertEqual(
            SESSION_CONTEXT.read_text(encoding="utf-8"),
            plugin_session_context(self.fragment()),
        )

    def test_the_session_context_names_only_invocable_skill_ids(self):
        """A plugin skill is invoked by its plugin-qualified id. Text naming the
        bare id would send a plugin-only session after a skill it does not have."""
        context = SESSION_CONTEXT.read_text(encoding="utf-8")
        for skill in LITE_SKILLS:
            with self.subTest(skill=skill):
                self.assertIn(f"`{PLUGIN_NAME}:{skill}`", context)
                self.assertNotIn(f"`{skill}`", context)

    def test_the_transform_would_catch_a_drifted_block(self):
        """Arm the instrument, in both directions: an edit to either file that
        the other does not mirror has to fail."""
        fragment = self.fragment()
        self.assertEqual(
            SESSION_CONTEXT.read_text(encoding="utf-8"), plugin_session_context(fragment)
        )

        edited_fragment = fragment.replace(
            "It is policy, not a procedure", "It is a procedure"
        )
        self.assertNotEqual(fragment, edited_fragment)
        self.assertNotEqual(
            SESSION_CONTEXT.read_text(encoding="utf-8"),
            plugin_session_context(edited_fragment),
        )

        # A fragment that stopped naming a skill is a missing substitution, not
        # a silent pass.
        with self.assertRaises(ValueError):
            plugin_session_context(fragment.replace("`super-hero-simplify`", "it"))

        # A fragment that lost its marker pair is not a block this can strip.
        with self.assertRaises(ValueError):
            plugin_session_context(fragment.replace("<!-- BEGIN", "<!-- START", 1))


class SessionStartHookTests(unittest.TestCase):
    def hooks(self) -> list[dict]:
        manifest = read_json(HOOKS_MANIFEST)
        self.assertEqual(list(manifest), ["hooks"])
        self.assertEqual(list(manifest["hooks"]), ["SessionStart"])
        matchers = manifest["hooks"]["SessionStart"]
        self.assertEqual(len(matchers), 1, "one contribution, one entry")
        # An omitted matcher fires on every session start. Naming one, such as
        # "startup", would quietly stop the block reaching a resumed, cleared,
        # compacted or forked session, which is most long sessions, while the
        # manifest still validated and the inventory still reported one hook.
        self.assertNotIn("matcher", matchers[0])
        return matchers[0]["hooks"]

    def command(self) -> str:
        handlers = self.hooks()
        self.assertEqual(len(handlers), 1)
        handler = handlers[0]
        self.assertEqual(handler["type"], "command")
        return handler["command"]

    def test_the_hook_reads_the_packaged_session_context(self):
        """Shell form, so the host runs it under `sh` on macOS and Linux and
        under Git Bash or PowerShell on Windows. `cat` is a POSIX utility and a
        PowerShell alias for Get-Content, so one command covers all three. The
        host substitutes the plugin root before any shell sees it."""
        command = self.command()
        self.assertIn("${CLAUDE_PLUGIN_ROOT}", command)
        self.assertIn("hooks/session-context.md", command)
        self.assertTrue(command.startswith("cat "), command)
        # A path that is not quoted breaks on the first installation directory
        # containing a space.
        self.assertIn('"${CLAUDE_PLUGIN_ROOT}/hooks/session-context.md"', command)

    @unittest.skipIf(os.name == "nt", "this check runs the shell form under sh")
    def test_the_hook_command_prints_exactly_the_session_context(self):
        """Run the real command the way the host runs it, and read back what a
        session would receive. Declaring a hook is not evidence that it emits
        anything."""
        command = self.command().replace("${CLAUDE_PLUGIN_ROOT}", str(PLUGIN_ROOT))
        result = subprocess.run(
            ["sh", "-c", command],
            capture_output=True,
            text=False,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr.decode("utf-8"))
        self.assertEqual(result.stdout, SESSION_CONTEXT.read_bytes())
        # Claude Code adds a SessionStart hook's stdout to the session as
        # plain text unless it both starts with `{` and ends with `}`.
        printed = result.stdout.decode("utf-8").strip()
        self.assertFalse(printed.startswith("{") and printed.endswith("}"))

    @unittest.skipIf(os.name == "nt", "this check runs the shell form under sh")
    def test_the_command_check_would_catch_a_hook_that_prints_nothing(self):
        """Arm the instrument against the failure that matters: a hook whose
        command runs cleanly and contributes nothing."""
        with tempfile.TemporaryDirectory() as temporary_name:
            empty_root = Path(temporary_name)
            (empty_root / "hooks").mkdir()
            (empty_root / "hooks" / "session-context.md").write_bytes(b"")
            command = self.command().replace("${CLAUDE_PLUGIN_ROOT}", str(empty_root))
            result = subprocess.run(["sh", "-c", command], capture_output=True, check=False)
            self.assertEqual(result.returncode, 0)
            self.assertNotEqual(result.stdout, SESSION_CONTEXT.read_bytes())

    def test_the_hook_adds_no_second_confirmation_step(self):
        """The gate Lite removed must not creep back in through the one piece
        of text that reaches every session."""
        context = SESSION_CONTEXT.read_text(encoding="utf-8")
        self.assertIsNone(re.search(r"Proceed\?|\[Y/n\]|confirm the route", context))


if __name__ == "__main__":
    unittest.main()
