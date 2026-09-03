"""The first-party skill package contract.

Super-Hero Lite ships exactly three skills. This suite enforces the set in
both directions, enforces each skill's declared references, and pins the
release skill's publication guarantees and the core's invariants.
"""

import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILLS_ROOT = ROOT / "skills"

# The exact shipped set. A skill added here must also be installed, validated
# and uninstalled by both distributions, and named in every README.
SKILLS = {
    "super-hero-core": [],
    "super-hero-release-to-public": [
        "assets/public-release-contract.yaml",
        "references/contract-schema.md",
        "references/public-history.md",
        "references/release-phases.md",
        "references/sanitization.md",
        "references/verification.md",
    ],
    "super-hero-simplify": [],
}

# Removed architecture. Lite ships no alias, shim or successor for any of
# these; the deletion is the migration.
REMOVED_SKILLS = (
    "super-hero-workflow-router",
    "super-hero-ask-gate",
    "super-hero-runtime-router",
    "ponytail-policy-adapter",
)

FRONTMATTER = re.compile(r"\A---\n(?P<contents>.*?)\n---\n", re.DOTALL)

MODES = ("DIRECT", "CONTROLLED", "EXTERNAL")

# The canonical wording of each permanent rule. The core states each once, and
# no other first-party skill restates it.
CORE_INVARIANTS = {
    "facts versus decisions": (
        "Investigate discoverable facts. Ask only for unresolved decisions "
        "that materially alter scope, externally visible behavior, "
        "architecture, security posture, irreversible state, "
        "repository/history policy, or publication."
    ),
    "solution economy": (
        "Implement the minimum straightforward solution satisfying accepted "
        "requirements."
    ),
    "completion evidence": (
        "Do not claim completion without fresh evidence from the relevant "
        "tests/checks."
    ),
}

PRIVATE_HISTORY_BAN = (
    "Never import, filter, rewrite, mirror, or otherwise transfer the private "
    "commit graph."
)
REQUIRED_RELEASE_SKILL_DESCRIPTION = (
    "description: Use when the user explicitly asks to publish, export, or release "
    "a private GitHub repository to a separate public repository."
)
# The release skill is host-neutral: a host's own paths belong to a
# distribution, never to a skill.
FORBIDDEN_HOST_TERMS = re.compile(
    r"CODEX_HOME|CLAUDE_CONFIG_DIR|codex plugin|claude plugin|global AGENTS"
    r"|\$HOME/\.codex|\$HOME/\.claude",
    re.IGNORECASE,
)
# Terms whose presence in a live skill would mean removed architecture came
# back. Historical explanation belongs in docs/lineage.md, which is not a skill.
REMOVED_ARCHITECTURE_TERMS = re.compile(
    r"\bponytail\b|\bBRONZE\b|\bSILVER\b|\bGOLD\b|capability profile"
    r"|runtime envelope|routing manifest|complexity posture|rung ladder"
    r"|bounded execution class|super-hero-ask-gate|super-hero-runtime-router"
    r"|super-hero-workflow-router",
    re.IGNORECASE,
)

CASES_DOCUMENT = ROOT / "evals" / "core-cases.md"


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def collapse(text: str) -> str:
    """Compare wording without depending on wrapping or blockquote markers."""
    return " ".join(
        re.sub(r"^\s*>\s?", "", line) for line in text.splitlines()
    ).strip()


def first_party_files() -> list[Path]:
    return sorted(path for path in SKILLS_ROOT.rglob("*") if path.is_file())


class SkillSetTests(unittest.TestCase):
    def test_exactly_the_three_lite_skills_ship(self):
        shipped = sorted(
            entry.name
            for entry in SKILLS_ROOT.iterdir()
            if entry.is_dir() or entry.is_symlink()
        )
        self.assertEqual(shipped, sorted(SKILLS))

    def test_no_removed_skill_or_alias_ships(self):
        for skill in REMOVED_SKILLS:
            with self.subTest(skill=skill):
                self.assertFalse(
                    (SKILLS_ROOT / skill).exists()
                    or (SKILLS_ROOT / skill).is_symlink(),
                    f"{skill} was removed in Lite; it must not ship as an alias",
                )

    def test_both_distributions_own_exactly_the_shipped_set(self):
        """The set in the package and the set each installer owns are one fact."""
        for distribution in ("codex", "claude-code"):
            with self.subTest(distribution=distribution):
                source = read(
                    ROOT / "distributions" / distribution / "lib" / "managed_state.py"
                )
                declared = re.search(
                    r"LITE_SKILLS = \((?P<body>.*?)\)", source, re.DOTALL
                )
                self.assertIsNotNone(declared)
                owned = sorted(re.findall(r'"([^"]+)"', declared.group("body")))
                self.assertEqual(owned, sorted(SKILLS))


class SkillPackageTests(unittest.TestCase):
    def test_skill_packages_have_valid_metadata_and_declared_references(self):
        for skill_name, references in SKILLS.items():
            with self.subTest(skill=skill_name):
                skill_directory = SKILLS_ROOT / skill_name
                skill_file = skill_directory / "SKILL.md"
                self.assertTrue(skill_file.is_file(), f"missing {skill_file}")

                skill_text = read(skill_file)
                frontmatter = FRONTMATTER.match(skill_text)
                self.assertIsNotNone(frontmatter, "missing first YAML frontmatter block")
                self.assertLessEqual(len(frontmatter.group(0)), 1024)

                metadata_lines = frontmatter.group("contents").splitlines()
                self.assertEqual(
                    [line for line in metadata_lines if line.startswith("name:")],
                    [f"name: {skill_name}"],
                )
                self.assertTrue(
                    any(
                        line.startswith("description: Use when")
                        for line in metadata_lines
                    ),
                    "description must begin with 'Use when'",
                )

                declared = set(references)
                for reference in declared:
                    self.assertTrue(
                        (skill_directory / reference).is_file(),
                        f"missing declared reference {reference}",
                    )

                present = {
                    path.relative_to(skill_directory).as_posix()
                    for path in skill_directory.rglob("*")
                    if path.is_file() and path.name != "SKILL.md"
                }
                self.assertEqual(
                    present,
                    declared,
                    "a skill ships a file it does not declare, or declares one "
                    "it does not ship",
                )

    def test_no_first_party_file_reintroduces_removed_architecture(self):
        for path in first_party_files():
            with self.subTest(path=path.relative_to(ROOT).as_posix()):
                self.assertIsNone(
                    REMOVED_ARCHITECTURE_TERMS.search(read(path)),
                    "removed architecture must not reappear in a shipped skill",
                )

    def test_skills_stay_host_neutral(self):
        """A host's paths and commands belong to a distribution, not a skill."""
        for path in first_party_files():
            with self.subTest(path=path.relative_to(ROOT).as_posix()):
                self.assertIsNone(FORBIDDEN_HOST_TERMS.search(read(path)))


class CoreSkillTests(unittest.TestCase):
    def core(self) -> str:
        return read(SKILLS_ROOT / "super-hero-core" / "SKILL.md")

    def test_the_core_defines_exactly_the_three_execution_modes(self):
        core = self.core()
        headings = re.findall(r"^### ([A-Z]+)", core, re.MULTILINE)
        self.assertEqual(headings, list(MODES))

    def test_each_permanent_rule_is_stated_once_in_the_core(self):
        core = collapse(self.core())
        for label, wording in CORE_INVARIANTS.items():
            with self.subTest(rule=label):
                self.assertEqual(
                    core.count(collapse(wording)),
                    1,
                    f"the core must state the {label} rule exactly once",
                )

    def test_no_other_first_party_skill_restates_a_core_rule(self):
        """Verification prose lives in one place; the release checklist is
        release-specific, which is a different thing from a restatement."""
        for path in first_party_files():
            if path.parts[-2:] == ("super-hero-core", "SKILL.md"):
                continue
            body = collapse(read(path))
            for label, wording in CORE_INVARIANTS.items():
                with self.subTest(
                    path=path.relative_to(ROOT).as_posix(), rule=label
                ):
                    self.assertNotIn(collapse(wording), body)

    def test_the_core_hands_publication_to_the_release_skill(self):
        core = self.core()
        self.assertIn("super-hero-release-to-public", core)
        self.assertIn("super-hero-simplify", core)

    def test_the_core_adds_no_confirmation_gate(self):
        """The gate Lite removed must not creep back into the core's wording."""
        self.assertIsNone(
            re.search(r"Proceed\?|\[Y/n\]|confirm the route", self.core())
        )

    def test_core_cases_and_the_core_skill_cover_the_same_ground(self):
        cases = read(CASES_DOCUMENT)
        headings = re.findall(r"^## (\d+)\. (.+)$", cases, re.MULTILINE)
        self.assertEqual(
            [number for number, _ in headings],
            [str(index) for index in range(1, len(headings) + 1)],
            "core cases must be numbered consecutively from 1",
        )
        self.assertGreaterEqual(len(headings), 11)
        for mode in MODES:
            with self.subTest(mode=mode):
                self.assertIn(mode, cases, "every mode needs a case")
        for label in CORE_INVARIANTS:
            with self.subTest(rule=label):
                # Each rule is named in a case by its own vocabulary rather
                # than by quoting the rule, which would defeat the
                # stated-once check above.
                keyword = label.split()[0]
                self.assertIn(keyword, cases.lower())


class ReleaseSkillTests(unittest.TestCase):
    def skill(self) -> str:
        return read(SKILLS_ROOT / "super-hero-release-to-public" / "SKILL.md")

    def test_the_trigger_description_is_unchanged(self):
        frontmatter = FRONTMATTER.match(self.skill())
        self.assertIn(
            REQUIRED_RELEASE_SKILL_DESCRIPTION,
            frontmatter.group("contents").splitlines(),
            "the release gate must retain its complete required trigger description",
        )

    def test_private_history_transfer_is_never_waived(self):
        public_history = read(
            SKILLS_ROOT
            / "super-hero-release-to-public"
            / "references"
            / "public-history.md"
        )
        self.assertIn(collapse(PRIVATE_HISTORY_BAN), collapse(public_history))
        self.assertIsNone(
            re.search(
                r"private commit graph\s+unless", public_history, re.IGNORECASE
            ),
            "private commit history transfer must never be waived",
        )

    def test_every_publication_guarantee_survives(self):
        skill = collapse(self.skill())
        references = collapse(
            "\n".join(
                read(path)
                for path in sorted(
                    (
                        SKILLS_ROOT / "super-hero-release-to-public" / "references"
                    ).iterdir()
                )
            )
        )
        guarantees = {
            "explicit publication request": "explicit user request to publish",
            "exact committed SHA": "Export only from a known committed source SHA",
            "source stays private": "Private source must remain private",
            "separate target": "must be a different GitHub repository",
            "deterministic export": "Build the staging tree from the exact committed revision",
            "no private history": "Never push, mirror, filter or rewrite the private Git history",
            "real secret scan": "Require a real secret scanner before publication",
            "forbidden literals": "Fail on unresolved forbidden literals",
            "preview": "show a concise release preview",
            "explicit PUBLISH": "ask for explicit `PUBLISH` confirmation",
            "fail closed": "Fail closed",
        }
        for label, wording in guarantees.items():
            with self.subTest(guarantee=label):
                self.assertIn(collapse(wording), skill)
        for label, wording in {
            "tests and build in isolation": "Run the required tests and builds",
            "post-publication verification": "the source repository is still PRIVATE",
            "remote head re-check": "Re-check the remote head and visibility",
        }.items():
            with self.subTest(guarantee=label):
                self.assertIn(collapse(wording), references)


if __name__ == "__main__":
    unittest.main()
