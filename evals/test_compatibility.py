"""Compatibility metadata and the distributable-file manifest rule."""

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

POCOCK_BASELINE = {
    "testedRef": "v1.2.3",
    "testedCommit": "6acc160e4e0cd062dbbbd7a1b26ae92855edf07e",
    "license": "MIT",
    "manager": "skills",
}

EXPECTED = {
    "codex": {
        "testedHostCli": "0.148.0-alpha.21",
        "hostCliEvidence": (
            "inherited from super-hero-workflow 1.6.4; "
            "not re-measured for Lite 1.0.0"
        ),
        "dependencies": {
            "mattpocock-skills": POCOCK_BASELINE,
            "superpowers": {
                "testedRef": "v6.3.0",
                "testedCommit": "b36e0829c6d0140e93cfef2ca599b1b07d4a7797",
                "license": "MIT",
                "manager": "codex-plugin-marketplace",
            },
        },
        "detection": {"superpowers": {"pluginId": "superpowers@openai-curated"}},
    },
    "claude-code": {
        "testedHostCli": "2.1.258",
        "hostCliEvidence": "measured 2026-09-03 on macOS 26 (arm64)",
        "dependencies": {
            "mattpocock-skills": POCOCK_BASELINE,
            "superpowers": {
                "testedRef": "5.1.0",
                "testedCommit": "6fd4507659784c351abbd2bc264c7162cfd386dc",
                "license": "MIT",
                "manager": "claude-code-plugin-marketplace",
            },
        },
        "detection": {
            "superpowers": {"pluginId": "superpowers@superpowers-marketplace"}
        },
    },
}

REQUIRED_CAPABILITIES = (
    "filesystem",
    "shell",
    "persistent-instruction-discovery",
    "persistent-skill-discovery",
)

LITE_SKILLS = (
    "super-hero-core",
    "super-hero-release-to-public",
    "super-hero-simplify",
)

# A recorded baseline says how it was established, so an inherited number is
# never mistaken for one this release measured.
EVIDENCE_PREFIXES = ("measured ", "inherited from ")


class CompatibilityTests(unittest.TestCase):
    def metadata(self):
        return json.loads(
            (ROOT / "compatibility/upstreams.json").read_text(encoding="utf-8")
        )

    def test_every_distribution_is_recorded_exactly_once(self):
        data = self.metadata()
        self.assertEqual(data["schemaVersion"], 1)
        recorded = [item["id"] for item in data["distributions"]]
        self.assertEqual(sorted(recorded), sorted(EXPECTED))
        self.assertEqual(len(recorded), len(set(recorded)))

    def test_every_distribution_declares_its_own_tested_upstreams(self):
        distributions = {item["id"]: item for item in self.metadata()["distributions"]}
        for distribution_id, expected in EXPECTED.items():
            with self.subTest(distribution=distribution_id):
                distribution = distributions[distribution_id]
                self.assertEqual(
                    distribution["testedHostCli"], expected["testedHostCli"]
                )
                self.assertEqual(
                    distribution["requiredCapabilities"], list(REQUIRED_CAPABILITIES)
                )

                dependencies = {
                    item["id"]: item for item in distribution["dependencies"]
                }
                self.assertEqual(sorted(dependencies), sorted(expected["dependencies"]))
                for dependency_id, values in expected["dependencies"].items():
                    with self.subTest(dependency=dependency_id):
                        for key, value in values.items():
                            self.assertEqual(dependencies[dependency_id][key], value)
                        # A record names the revision that was tested. A
                        # floating alias would record nothing at all.
                        self.assertNotIn(
                            "latest", json.dumps(dependencies[dependency_id]).lower()
                        )
                for dependency_id, detection in expected["detection"].items():
                    with self.subTest(detection=dependency_id):
                        for key, value in detection.items():
                            self.assertEqual(
                                dependencies[dependency_id]["detection"][key], value
                            )

    def test_every_host_baseline_states_how_it_was_established(self):
        """Recording only what was tested means saying which numbers those are."""
        distributions = {item["id"]: item for item in self.metadata()["distributions"]}
        for distribution_id, expected in EXPECTED.items():
            with self.subTest(distribution=distribution_id):
                evidence = distributions[distribution_id]["hostCliEvidence"]
                self.assertEqual(evidence, expected["hostCliEvidence"])
                self.assertTrue(
                    evidence.startswith(EVIDENCE_PREFIXES),
                    f"unrecognized evidence form: {evidence!r}",
                )

    def test_no_model_or_role_assignment_is_recorded(self):
        """Compatibility records tested versions; it never routes work."""
        recorded = json.dumps(self.metadata()).lower()
        for term in (
            "profile",
            "modelalias",
            "supportedeffort",
            "fallback",
            "roleagents",
            "bronze",
            "silver",
            "gold",
        ):
            with self.subTest(term=term):
                self.assertNotIn(term, recorded)

    def test_host_specific_detection_identities_are_distinct(self):
        distributions = {item["id"]: item for item in self.metadata()["distributions"]}
        plugin_identities = {
            distribution_id: next(
                dependency["detection"]["pluginId"]
                for dependency in distribution["dependencies"]
                if dependency["id"] == "superpowers"
            )
            for distribution_id, distribution in distributions.items()
        }
        self.assertEqual(
            len(set(plugin_identities.values())),
            len(plugin_identities),
            plugin_identities,
        )

    def test_each_distribution_library_requires_the_recorded_schema(self):
        for distribution in EXPECTED:
            with self.subTest(distribution=distribution):
                source = (
                    ROOT
                    / "distributions"
                    / distribution
                    / "lib"
                    / "compatibility.py"
                ).read_text(encoding="utf-8")
                self.assertIn(
                    f"SCHEMA_VERSION = {self.metadata()['schemaVersion']}", source
                )


class ManifestTests(unittest.TestCase):
    """The manifest rule, exercised through its platform-neutral implementation."""

    USAGE = "Usage: scripts/manifest.py --write|--verify"

    def setUp(self):
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.package = Path(self.temporary_directory.name)
        scripts = self.package / "scripts"
        scripts.mkdir()
        for name in ("manifest.sh", "manifest.py"):
            copy = scripts / name
            shutil.copy(ROOT / "scripts" / name, copy)
            copy.chmod(0o755)

        (self.package / "README.md").write_text("package readme\n", encoding="utf-8")
        nested = self.package / "nested"
        nested.mkdir()
        (nested / "included.txt").write_text("included\n", encoding="utf-8")

        (self.package / "AGENTS.md").write_text("excluded\n", encoding="utf-8")
        (self.package / ".git").mkdir()
        (self.package / ".git/config").write_text("excluded\n", encoding="utf-8")
        (self.package / ".release").mkdir()
        (self.package / ".release/state").write_text("excluded\n", encoding="utf-8")
        (self.package / "evals/__pycache__").mkdir(parents=True)
        (self.package / "evals/__pycache__/test.cpython-312.pyc").write_text(
            "excluded\n"
        )

    def tearDown(self):
        self.temporary_directory.cleanup()

    def manifest(self, *arguments):
        return subprocess.run(
            [sys.executable, "-B", "scripts/manifest.py", *arguments],
            cwd=self.package,
            capture_output=True,
            text=True,
            check=False,
        )

    def test_write_and_verify_cover_the_distributable_file_set(self):
        write = self.manifest("--write")
        self.assertEqual(write.returncode, 0, write.stderr)
        manifest_paths = [
            line.rsplit(" ", 1)[1]
            for line in (self.package / "MANIFEST.sha256")
            .read_text(encoding="utf-8")
            .splitlines()
        ]
        self.assertEqual(
            manifest_paths,
            [
                "./README.md",
                "./nested/included.txt",
                "./scripts/manifest.py",
                "./scripts/manifest.sh",
            ],
        )

        verify = self.manifest("--verify")
        self.assertEqual(verify.returncode, 0, verify.stdout + verify.stderr)

    def test_verify_rejects_changed_missing_and_extra_files(self):
        write = self.manifest("--write")
        self.assertEqual(write.returncode, 0, write.stderr)

        included = self.package / "nested/included.txt"
        included.write_text("changed\n", encoding="utf-8")
        self.assertNotEqual(self.manifest("--verify").returncode, 0)

        included.write_text("included\n", encoding="utf-8")
        included.unlink()
        self.assertNotEqual(self.manifest("--verify").returncode, 0)

        included.write_text("included\n", encoding="utf-8")
        (self.package / "extra.txt").write_text("extra\n", encoding="utf-8")
        rejected = self.manifest("--verify")
        self.assertNotEqual(rejected.returncode, 0)
        self.assertIn("./extra.txt", rejected.stdout)

    def test_verify_ignores_nested_agent_worktrees(self):
        write = self.manifest("--write")
        self.assertEqual(write.returncode, 0, write.stderr)

        nested_worktree = self.package / ".worktrees/manifest-hotfix"
        nested_worktree.mkdir(parents=True)
        (nested_worktree / "README.md").write_text(
            "not distributable\n", encoding="utf-8"
        )

        verify = self.manifest("--verify")
        self.assertEqual(verify.returncode, 0, verify.stdout + verify.stderr)

    def test_verify_rejects_regular_file_named_worktrees(self):
        write = self.manifest("--write")
        self.assertEqual(write.returncode, 0, write.stderr)

        (self.package / ".worktrees").write_text(
            "ordinary extra file\n", encoding="utf-8"
        )

        self.assertNotEqual(self.manifest("--verify").returncode, 0)

    def test_rejects_invalid_arguments(self):
        invalid = self.manifest("--unknown")
        self.assertEqual(invalid.returncode, 2)
        self.assertIn(self.USAGE, invalid.stdout + invalid.stderr)

        write = self.manifest("--write")
        self.assertEqual(write.returncode, 0, write.stderr)
        extra_argument = self.manifest("--verify", "unexpected")
        self.assertEqual(extra_argument.returncode, 2)
        self.assertIn(self.USAGE, extra_argument.stdout + extra_argument.stderr)

    def test_manifest_can_package_every_lite_skill(self):
        for skill in LITE_SKILLS:
            skill_file = self.package / "skills" / skill / "SKILL.md"
            skill_file.parent.mkdir(parents=True)
            skill_file.write_text(f"{skill}\n", encoding="utf-8")

        write = self.manifest("--write")
        self.assertEqual(write.returncode, 0, write.stdout + write.stderr)
        manifest_paths = {
            line.rsplit(" ", 1)[1]
            for line in (self.package / "MANIFEST.sha256")
            .read_text(encoding="utf-8")
            .splitlines()
        }
        for skill in LITE_SKILLS:
            with self.subTest(skill=skill):
                self.assertIn(f"./skills/{skill}/SKILL.md", manifest_paths)


@unittest.skipIf(os.name == "nt", "the POSIX entry point needs bash")
class ManifestShellEntryPointTests(ManifestTests):
    """The same contract through scripts/manifest.sh, which names the rule."""

    USAGE = "Usage: scripts/manifest.sh --write|--verify"

    def manifest(self, *arguments):
        return subprocess.run(
            ["bash", "scripts/manifest.sh", *arguments],
            cwd=self.package,
            capture_output=True,
            text=True,
            check=False,
        )


class ShippedManifestTests(unittest.TestCase):
    def test_the_committed_manifest_matches_the_tree(self):
        result = subprocess.run(
            [sys.executable, "-B", "scripts/manifest.py", "--verify"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
