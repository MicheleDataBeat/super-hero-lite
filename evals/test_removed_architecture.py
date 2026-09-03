"""The deletions Super-Hero Lite is defined by.

Lite exists because its ancestor's deterministic runtime orchestration,
complexity-posture machinery and legacy-installation migration were removed.
Removal is only durable if something fails when it comes back, so this suite
scans the distributable file set and fails on reintroduction.

Historical explanation is legitimate and lives in `docs/lineage.md`. That file
and the eval documents that assert these absences are the only places a removed
term may appear.
"""

import importlib.util
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

# Directories the ancestor shipped that Lite must not.
FORBIDDEN_DIRECTORIES = (
    "distributions/codex/runtime",
    "distributions/claude-code/runtime",
    "distributions/claude-code/agents",
    "skills/super-hero-workflow-router",
    "skills/super-hero-ask-gate",
    "skills/super-hero-runtime-router",
    "skills/ponytail-policy-adapter",
)

# Files whose only purpose was the removed architecture.
FORBIDDEN_FILES = (
    "docs/runtime-routing.md",
    "distributions/codex/runtime/profile-registry.json",
    "distributions/claude-code/runtime/profile-registry.json",
    "evals/test_runtime_routing.py",
    "evals/test_ponytail_integration.py",
    "evals/test_no_legacy_source.py",
    "evals/runtime-routing-cases.md",
    "evals/complexity-routing-cases.md",
    "evals/debt-marker-cases.md",
    "evals/phase-precedence-cases.md",
    "evals/router-cases.md",
    "evals/ask-cases.md",
    "CONTEXT.md",
)

# Mechanisms, by the name they would come back under. Each pattern is written
# to catch the mechanism rather than any use of a common English word.
FORBIDDEN_MECHANISMS = {
    "capability profile ladder": r"\bBRONZE\b|\bSILVER\b|\bGOLD\b",
    "review and design profiles": r"\bREVIEW\b\s*/\s*\bDESIGN\b|profile registry",
    "role rung taxonomy": r"\brung\b|\bA[123]/I[123]\b|role matrix|role rungs?",
    "bounded execution class": r"bounded execution class|execution_class",
    "runtime envelope": r"runtime envelope|runtime_envelope",
    "routing manifest": r"routing manifest|routing_manifest",
    "model fallback ladder": r"model fallback|fallback ladder|next-available-inferior",
    "per-dispatch model policy": r"modelAlias|pinnedEffort|supportedEffort"
    r"|effort_enforcement|per-dispatch",
    "package-owned role definitions": r"roleAgents|ROLE_AGENTS",
    "complexity posture": r"complexity posture|overbuild_susceptibility"
    r"|ADVISORY|ENFORCED|REVIEW_ONLY|AGGRESSIVE",
    # Case matters in this table: `Pocock` and `Superpowers` are upstream
    # names Lite still depends on, while `POCOCK` and `SUPERPOWERS` were
    # route states it removed. Ponytail left in every casing.
    "ponytail integration": r"(?i:\bponytail\b)",
    "removed route states": r"\bPOCOCK\b|\bSUPERPOWERS route\b|\bHYBRID\b"
    r"|\bWAYFINDER\b|RELEASE-TO-PUBLIC",
    "removed first-party skills": r"super-hero-workflow-router|super-hero-ask-gate"
    r"|super-hero-runtime-router|ponytail-policy-adapter",
    "ancestor legacy installation": r"HYBRID_CODEX_WORKFLOW_BOOTSTRAP"
    r"|hybrid-workflow-router|LEGACY_SKILLS|Legacy Installation"
    r"|legacy bootstrap",
    "confirmation gate": r"Proceed\? \[Y/n\]|route confirmation gate",
}

# Where a removed term is allowed to appear, and why.
#
# `docs/lineage.md` explains what was removed; that is its entire job.
# The two eval suites below are the checks themselves: this file names every
# forbidden mechanism, and the skill-package suite names the removed skills.
# Each distribution's lifecycle suite plants a removed artifact to prove the
# installer rejects or ignores it, which is the only way that guarantee can be
# demonstrated at all.
HISTORICAL_PATHS = frozenset(
    {
        "docs/lineage.md",
        "evals/test_removed_architecture.py",
        "evals/test_skill_packages.py",
        "distributions/codex/evals/test_lifecycle.py",
        "distributions/claude-code/evals/test_lifecycle.py",
    }
)


def load_manifest_rule():
    """Load scripts/manifest.py, the single implementation of the shipped set."""
    spec = importlib.util.spec_from_file_location(
        "manifest_rule", ROOT / "scripts" / "manifest.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def distributable_files():
    """Every shipped file, selected by the manifest's own rule.

    Using the release-time definition means untracked build artifacts,
    `__pycache__`, `.pyc` and symlinks never reach the caller, so the scan
    covers exactly what a user would receive.
    """
    manifest = load_manifest_rule()
    return [
        relative[2:]  # strip the "./" prefix
        for relative in manifest.distributable_paths(ROOT)
    ]


def scanned_files():
    return [
        relative
        for relative in distributable_files()
        if relative not in HISTORICAL_PATHS
    ]


class RemovedArchitectureTests(unittest.TestCase):
    def test_no_forbidden_directory_ships(self):
        for relative in FORBIDDEN_DIRECTORIES:
            with self.subTest(path=relative):
                path = ROOT / relative
                self.assertFalse(
                    path.exists() or path.is_symlink(),
                    f"{relative} was removed in Lite and must not return",
                )

    def test_no_forbidden_file_ships(self):
        for relative in FORBIDDEN_FILES:
            with self.subTest(path=relative):
                path = ROOT / relative
                self.assertFalse(
                    path.exists() or path.is_symlink(),
                    f"{relative} was removed in Lite and must not return",
                )

    def test_no_distributable_file_reintroduces_a_removed_mechanism(self):
        files = scanned_files()
        self.assertTrue(files, "the scan selected nothing; the rule is broken")
        for relative in files:
            text = (ROOT / relative).read_text(encoding="utf-8")
            for mechanism, pattern in FORBIDDEN_MECHANISMS.items():
                with self.subTest(path=relative, mechanism=mechanism):
                    self.assertIsNone(
                        re.search(pattern, text),
                        f"{relative} reintroduces {mechanism}",
                    )

    def test_the_scan_would_catch_a_reintroduction(self):
        """Arm the instrument: a scan never shown to fire proves nothing."""
        planted = {
            mechanism: pattern
            for mechanism, pattern in FORBIDDEN_MECHANISMS.items()
        }
        samples = {
            "capability profile ladder": "the GOLD profile",
            "review and design profiles": "consult the profile registry",
            "role rung taxonomy": "escalate one rung",
            "bounded execution class": "declare the bounded execution class",
            "runtime envelope": "pin the runtime envelope",
            "routing manifest": "record it in the routing manifest",
            "model fallback ladder": "walk the model fallback chain",
            "per-dispatch model policy": "set modelAlias on the definition",
            "package-owned role definitions": "install ROLE_AGENTS",
            "complexity posture": "confirm the complexity posture",
            "ponytail integration": "read the Ponytail config",
            "removed route states": "confirm the HYBRID route",
            "removed first-party skills": "invoke super-hero-ask-gate",
            "ancestor legacy installation": "migrate the Legacy Installation",
            "confirmation gate": "Proceed? [Y/n]",
        }
        self.assertEqual(sorted(samples), sorted(planted))
        for mechanism, sample in samples.items():
            with self.subTest(mechanism=mechanism):
                self.assertIsNotNone(
                    re.search(planted[mechanism], sample),
                    f"the {mechanism} pattern no longer matches its own example",
                )

    def test_every_historical_exemption_is_still_needed(self):
        """An exemption nobody checks widens until the scan stops scanning."""
        shipped = set(distributable_files())
        for relative in sorted(HISTORICAL_PATHS):
            with self.subTest(path=relative):
                self.assertIn(
                    relative, shipped, "an exemption names a file that no longer ships"
                )
                text = (ROOT / relative).read_text(encoding="utf-8")
                self.assertTrue(
                    any(
                        re.search(pattern, text)
                        for pattern in FORBIDDEN_MECHANISMS.values()
                    ),
                    f"{relative} no longer needs its exemption; remove it",
                )

    def test_no_distribution_declares_a_runtime_or_agent_asset(self):
        """The installers own skills and one bootstrap block, nothing else."""
        for distribution in ("codex", "claude-code"):
            source = (
                ROOT / "distributions" / distribution / "lib" / "managed_state.py"
            ).read_text(encoding="utf-8")
            for term in (
                "profile-registry",
                "_load_registry",
                "_stage_agents",
                "ROLE_AGENTS",
                "_validate_agents_root",
                '/ "runtime"',
            ):
                with self.subTest(distribution=distribution, term=term):
                    self.assertNotIn(term, source)

        # Codex's own instruction file is AGENTS.md, so only the host that had
        # a role-definition directory is checked for one. Nothing may stage,
        # validate or remove a path under `agents/`.
        claude_source = (
            ROOT / "distributions" / "claude-code" / "lib" / "managed_state.py"
        ).read_text(encoding="utf-8")
        self.assertIsNone(
            re.search(r"agents", claude_source, re.IGNORECASE),
            "the Claude Code distribution must not reference agents/ at all",
        )


if __name__ == "__main__":
    unittest.main()
