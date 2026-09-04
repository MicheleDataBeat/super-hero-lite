# Changelog

This project follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

Super-Hero Lite's history starts here. It is a fresh-history descendant of
[MicheleDataBeat/super-hero-workflow](https://github.com/MicheleDataBeat/super-hero-workflow),
not a fork, so the ancestor's release chronology is deliberately not carried
over. What was inherited and what was removed is recorded in
[Lineage](docs/lineage.md).

## 1.1.2 — 2026-09-04

### Fixed

- Both distributions' validators reported the recorded upstream refs as a
  `PASS` line. Nothing verifies those refs: no installed version is read, by
  design, and [Compatibility](docs/compatibility.md) has always said they are
  "a record, not a requirement". A verdict was being printed for a check that
  does not exist — this project's own declared defect class, in its own
  validator, public since 1.0.0. The line now reads `NOTE  Recorded upstream
  refs, not verified against what is installed:`, and the document says that
  is how it is labelled. The two real prerequisite verdicts either side of it
  are unchanged, and still fail closed.

### Added

- `evals/test_repository_contract.py` holds that label in place. It calls
  `validate_upstreams` in both distributions and reads the lines it returns,
  requiring exactly three of them: the two prerequisite verdicts, and the
  recorded refs last under the `NOTE`, built from the recorded metadata. It
  fails if either distribution relabels the line, if a fourth line is added
  anywhere, if the two distributions' sentences diverge, or if the document
  stops describing the label.

  It pins this one line rather than a general rule. Two broader rules were
  written and discarded first, both of which would have read like guarantees
  while proving less than they claimed. "Every `PASS` sits in a function that
  can raise" is satisfied by the defective line itself, since the function
  emitting it raises on invalid metadata. And an earlier version of this check
  asserted against the module's source text, which was wrong in both
  directions: reflowing the string failed it, while the same verdict
  reintroduced under different wording passed it — along with the whole
  nine-check contract. Both bypasses were demonstrated before this was written
  the way it is.

  The two distributions record different Superpowers revisions on purpose, so
  their lines are not identical and comparing them to each other would be
  wrong. The sentence is what must match.

## 1.1.1 — 2026-09-04

A corrected record, and a check so it stays corrected. No skill,
distribution, plugin component or entry point changed behavior. The plugin
manifest's version moves because `evals/test_claude_code_plugin.py` pins the
plugin manifest, the marketplace manifest and the marketplace entry to
`VERSION`.

### Added

- `evals/test_repository_contract.py` gains a check on the compatibility
  document's measured / not-measured narrative, which until now was prose
  bound only to other prose and so invisible to every other check. It reads
  each release's list on its own terms and fails when a preamble's count
  disagrees with its bullets, when the sentence saying how many items still
  stand disagrees with how many are unstruck, or when a struck item does not
  carry a dated measurement claim naming a section that exists. It is a
  consistency check, not a truth check. Every shape was shown to fail against
  a planted defect, including the one that actually occurred.
- A list that has closed an item must say what still stands. Checking only the
  sentences that happen to exist would let one go missing; the obligation
  attaches to the first closure, so a list with nothing struck is not asked to
  restate itself.
- [Compatibility](docs/compatibility.md) named the wrong suite as its own
  gate: `evals/test_compatibility.py` never reads that document, and the check
  that fails when a rendered value disagrees with the metadata lives in
  `evals/test_repository_contract.py`. The claim has been public since 1.0.0.
  The protection it describes did exist; only the file name was wrong.
- The plugin README's links to the rest of the repository were relative, which
  resolves while browsing the source and escapes the plugin root once
  installed — which is where that README actually ships. They are absolute now.
- Every platform mention in [Compatibility](docs/compatibility.md) is read from
  `compatibility/upstreams.json` and must agree with it. Only the table's
  Evidence cell was bound before, so a correction could land in the table and
  not in the prose beside it and still pass all nine checks. That is the defect
  class this release exists to correct, applied to itself. It is a consistency
  check: it would not have caught the macOS error, which was uniformly wrong
  across the metadata and every mention. Nothing here measures the real
  platform, and no check should — the record states the platform a past
  measurement ran on, not the one a future reader is using.

### Fixed

- The recorded Claude Code host baseline said it was measured on macOS 15. The
  machine reports macOS 26.5.2 (Darwin 25.5.0, arm64), and always did: the
  claim has been wrong since the 1.0.0 release commit and public since. It is
  corrected in [Compatibility](docs/compatibility.md),
  `compatibility/upstreams.json` and the string `evals/test_compatibility.py`
  pins, which had to move together — the repository's own gate was holding the
  wrong fact in place. Nothing about what was tested changes; only the name of
  the platform it was tested on, which was overstated in the direction that
  tells a macOS 15 reader their platform is a tested baseline when it was never
  exercised.

### Changed

- The Claude Code plugin's README no longer says the hook's delivery into a
  session "rests on the host's documented behaviour rather than on a
  measurement made here". It was true when written and outlived the
  measurement that closed it. The two automated checks it names still do not
  start a session, and it now says that without implying nothing else does.
- [Compatibility](docs/compatibility.md) records two things 1.1.0 shipped
  unable to claim, both measured after it was published, against the published
  artifact: that Claude Code invokes the plugin's `SessionStart` hook and adds
  its output to a session, and that the published `owner/repo` marketplace
  source installs with the documented commands. Each original statement is
  struck through rather than removed, because both were true of 1.1.0, and the
  measurements are appended beside them.
- That section now says which method produced which row. The install rows come
  from a real installation into a throwaway configuration directory; the
  session rows come from `claude --plugin-dir`, which loads a plugin for one
  session without installing it. Describing both as one method, as the first
  draft of this section did, would have been the same class of claim/evidence
  mismatch this release exists to correct.
- The same comparison recorded the plugin-qualified skill ids and the
  coexistence of the two delivery forms.

The Windows shell path remains verified by Windows CI rather than locally,
and the note saying so is unchanged.

## 1.1.0 — 2026-09-04

### Added

- A Claude Code plugin, at `distributions/claude-code/plugin`, published
  through a marketplace manifest at the repository root. It is a second
  delivery form for the Claude Code host distribution, not a third host: the
  same three skills and the same governance, installed by Claude Code's own
  package manager instead of by `install.sh`. Installing it needs no clone, no
  shell and no prerequisite validation step.
- `evals/test_claude_code_plugin.py`, which binds the plugin to the material
  the installer already ships: the plugin's skills against the packaged skills
  byte for byte, its session context against the packaged bootstrap fragment
  under two declared substitutions, and its `SessionStart` hook by running the
  hook's own command and reading what it prints.

### Changed

- The root validators run one more suite. Both entry points still declare the
  same suites in the same order.

### Unchanged

- Both installers, both uninstallers, both distribution validators, the three
  skills and the recorded compatibility baselines. The plugin adds a way to
  install Super-Hero Lite; it changes nothing about the existing one, and no
  first-party skill gained, lost or altered a rule.

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
