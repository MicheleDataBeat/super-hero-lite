# Changelog

This project follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

Super-Hero Lite's history starts here. It is a fresh-history descendant of
[MicheleDataBeat/super-hero-workflow](https://github.com/MicheleDataBeat/super-hero-workflow),
not a fork, so the ancestor's release chronology is deliberately not carried
over. What was inherited and what was removed is recorded in
[Lineage](docs/lineage.md).

## 1.0.0 — 2026-09-03

First release.

### Added

- `super-hero-core`: the DIRECT, CONTROLLED and EXTERNAL execution modes, the
  facts-versus-decisions rule, the solution-economy invariant, the
  completion-evidence invariant, and the handoff to the public-release skill.
- `super-hero-simplify`: an optional post-implementation simplicity review that
  cannot weaken accepted scope, tests, security, accessibility or compatibility.
- `super-hero-release-to-public`: the private-to-public publication boundary,
  carrying forward the ancestor's substantive publication guarantees.
- Codex and Claude Code host distributions with transactional, idempotent,
  ownership-aware install, validate and uninstall, on POSIX and PowerShell
  entry points that share one Python implementation.
- Read-only prerequisite validation for the eleven Matt Pocock skills and the
  host-specific Superpowers plugin. Neither is ever installed, updated or
  removed by a Lite installer.
- Executable governance: the skill-package contract, compatibility metadata,
  the removed-architecture scan, the repository contract, both lifecycle
  suites, and the distributable-file manifest.
- Public-release prerequisites: a Contributor Covenant `CODE_OF_CONDUCT.md`
  with a private reporting address, GitHub issue forms, and `SECURITY.md` /
  `SUPPORT.md` pointing at the public repository's channels.

### Changed from the ancestor

- Six workflow route states became three execution modes.
- The mandatory route-confirmation gate was replaced by the
  facts-versus-decisions rule. Ordinary local work no longer asks twice.
- Five first-party skills became three.

### Removed from the ancestor

The deterministic runtime router and everything it owned, the complexity
posture machinery and its upstream dependency, and the ancestor's legacy Codex
installation migration. [Lineage](docs/lineage.md) lists these in full and
explains each removal; `evals/test_removed_architecture.py` fails if any of
them returns.
