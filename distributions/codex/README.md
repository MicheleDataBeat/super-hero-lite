# Codex Distribution

This directory provides the Codex host distribution for Super-Hero Lite. It installs the three Lite skills—`super-hero-core`, `super-hero-release-to-public`, and `super-hero-simplify`—and manages one marked bootstrap block in `$CODEX_HOME/AGENTS.md`.

## Prerequisites

1. `git`, `gh`, a Python 3 interpreter, and `codex` on `PATH`, with `gh` authenticated (`gh auth status` must succeed).
2. The eleven Matt Pocock skills — `setup-matt-pocock-skills`, `grill-with-docs`, `to-spec`, `to-tickets`, `implement`, `wayfinder`, `tdd`, `code-review`, `diagnosing-bugs`, `domain-modeling`, and `codebase-design` — installed with `npx --yes skills add https://github.com/mattpocock/skills --skill '*' --agent codex --global --yes`. The validator checks, for each skill: the lock at `~/.agents/.skill-lock.json` names its source `mattpocock/skills`; and its `SKILL.md` is present either under `~/.agents/skills/<skill>/` or under `$CODEX_HOME/skills/<skill>/`. Codex has no per-skill override control, so there is no third condition here.
3. The `superpowers@openai-curated` plugin: install and update it through the official Codex plugin marketplace, then enable it there. This repository records no verified marketplace-add or install command for that step. The validator requires it enabled, as reported by `codex plugin list`.

The installer validates all of the above but never installs, copies, updates, or removes them. Upstream versions are recorded as tested refs, not required — see [UPSTREAM.md](../../UPSTREAM.md) and [Compatibility](../../docs/compatibility.md).

This distribution installs, updates, and removes only its own state. It reads no configuration belonging to another tool.

## Host seam

`CODEX_HOME` selects the configuration directory and defaults to `$HOME/.codex`. Within it this distribution owns exactly two things: the three Lite skill directories under `skills/`, and one marked block in `AGENTS.md`. Personal instructions, unrelated skills, dependency locks, and plugin state are not owned by this distribution and are never rewritten.

Skills and one instruction block are the whole of what this distribution installs. Which model runs a delegated unit of work, and at what reasoning effort, is Codex's own decision.

## Lifecycle

Run `./install.sh` (or open `install.command`) to install or update package-owned state. Run `./validate.sh` to validate an installed distribution, `./validate.sh --package` to validate only the package, and `./uninstall.sh` to remove only Super-Hero Lite state.

On Windows, run `install.ps1`, `validate.ps1`, `validate.ps1 -Package` and `uninstall.ps1` under PowerShell. They read the same `CODEX_HOME` variable and delegate to the same Python, so the lifecycle behavior is not a separate implementation.

Install and update are the same idempotent command. Both install and uninstall snapshot package-owned state before mutation and restore that snapshot after a post-mutation failure.

Super-Hero Lite is a new product with new installation state. It carries no migration path for an installation created by `super-hero-workflow`; uninstall that separately with its own uninstaller if you no longer want it.
