# Claude Code Distribution

This directory provides the Claude Code host distribution for Super-Hero Lite. It installs the three Lite skills—`super-hero-core`, `super-hero-release-to-public`, and `super-hero-simplify`—and manages one marked bootstrap block in `$CLAUDE_CONFIG_DIR/CLAUDE.md`.

## Prerequisites

1. `git`, `gh`, a Python 3 interpreter, and `claude` on `PATH`, with `gh` authenticated (`gh auth status` must succeed).
2. The eleven Matt Pocock skills — `setup-matt-pocock-skills`, `grill-with-docs`, `to-spec`, `to-tickets`, `implement`, `wayfinder`, `tdd`, `code-review`, `diagnosing-bugs`, `domain-modeling`, and `codebase-design` — installed with `npx --yes skills add https://github.com/mattpocock/skills --skill '*' --agent claude-code --global --yes`. The validator checks, for each skill: the lock at `~/.agents/.skill-lock.json` names its source `mattpocock/skills`; `$CLAUDE_CONFIG_DIR/skills/<skill>/SKILL.md` is present; and it is not switched `"off"` under `skillOverrides` in `$CLAUDE_CONFIG_DIR/settings.json`.
3. The `superpowers@superpowers-marketplace` plugin, installed and enabled with:

   ```bash
   claude plugin marketplace add obra/superpowers-marketplace
   claude plugin install superpowers@superpowers-marketplace
   ```

   These are the commands the Windows CI job runs against a real installation (`.github/workflows/windows.yml`, "Enable the Superpowers plugin" step). The validator requires it enabled, as reported by `claude plugin list --json`.

The installer validates all of the above but never installs, copies, updates, or removes them. Upstream versions are recorded as tested refs, not required — see [UPSTREAM.md](../../UPSTREAM.md) and [Compatibility](../../docs/compatibility.md).

This distribution installs, updates, and removes only its own state. It reads no configuration belonging to another tool.

## Host seam

`CLAUDE_CONFIG_DIR` selects the configuration directory and defaults to `$HOME/.claude`. Within it this distribution owns exactly two things: the three Lite skill directories under `skills/`, and one marked block in `CLAUDE.md`. Personal instructions, unrelated skills, `settings.json`, everything under `agents/`, dependency locks, and plugin state are not owned by this distribution and are never read or rewritten.

Skills and one instruction block are the whole of what this distribution installs. Super-Hero Lite does not assign work roles to models: which model runs a delegated unit of work, and at what reasoning effort, is Claude Code's own decision. Anything you keep under `agents/` yourself is untouched by install, validate and uninstall.

Prerequisite detection is deliberately host-specific rather than shared with the Codex Distribution. Claude Code discovers global skills only below its own configuration directory, so the Pocock check requires `$CLAUDE_CONFIG_DIR/skills/<skill>/SKILL.md`; a shared agent-neutral copy under `~/.agents/skills/` does not satisfy this host. The check also reads `skillOverrides` in the user scope of `$CLAUDE_CONFIG_DIR/settings.json`: a skill switched `"off"` there fails the prerequisite even though its `SKILL.md` is present, while `"user-invocable-only"` and `"name-only"` still satisfy it. Superpowers is detected by reading the structured `claude plugin list --json` inventory and requiring `superpowers@superpowers-marketplace` to be enabled.

## Lifecycle

Run `./install.sh` (or open `install.command`) to install or update package-owned state. Run `./validate.sh` to validate an installed distribution, `./validate.sh --package` to validate only the package, and `./uninstall.sh` to remove only Super-Hero Lite state.

On Windows, run `install.ps1`, `validate.ps1`, `validate.ps1 -Package` and `uninstall.ps1` under PowerShell. They read the same `CLAUDE_CONFIG_DIR` variable and delegate to the same Python, so the lifecycle behavior is not a separate implementation.

Install and update are the same idempotent command. Both install and uninstall snapshot package-owned state before mutation and restore that snapshot after a post-mutation failure.

Super-Hero Lite is a new product with new installation state. It carries no migration path for an installation created by `super-hero-workflow`; uninstall that separately with its own uninstaller if you no longer want it.
