# Super-Hero Lite — Claude Code plugin

This directory is the Super-Hero Lite plugin for Claude Code. It is the second delivery form of the [Claude Code Distribution](https://github.com/MicheleDataBeat/super-hero-lite/blob/main/distributions/claude-code/README.md), not a separate product and not a third host: the same three skills and the same governance, installed by Claude Code's own package manager instead of by `install.sh`.

## Install

```
/plugin marketplace add MicheleDataBeat/super-hero-lite
/plugin install super-hero-lite@super-hero-lite
```

The same two steps from a shell:

```bash
claude plugin marketplace add MicheleDataBeat/super-hero-lite
claude plugin install super-hero-lite@super-hero-lite
```

There is no repository to clone and no shell script to run. The plugin writes no state of its own; what it installs lives in the plugin cache Claude Code manages, so `$CLAUDE_CONFIG_DIR/skills/` and `CLAUDE.md` are never touched. To remove it, run `/plugin uninstall super-hero-lite@super-hero-lite`.

The product's prerequisites are unchanged and are *not* validated here. `super-hero-core` reaches for the eleven Matt Pocock skills and the `superpowers@superpowers-marketplace` plugin inside `CONTROLLED` work, and this delivery form checks for neither: the host owns the lifecycle, so a missing prerequisite surfaces when the technique is wanted rather than at install time. The installer's [prerequisite contract](https://github.com/MicheleDataBeat/super-hero-lite/blob/main/distributions/claude-code/README.md#prerequisites) lists both and is what to install alongside this plugin.

The marketplace manifest is at the repository root, so the marketplace and the plugin ship from one repository.

## What it installs

| Component | Contents |
| --- | --- |
| Skills | `super-hero-core`, `super-hero-release-to-public`, `super-hero-simplify` |
| Hooks | one `SessionStart` hook, which prints `hooks/session-context.md` |
| Agents | none |
| MCP servers | none |

Super-Hero Lite assigns no work role to a model and no reasoning effort to a task. Which model runs a delegated unit of work is Claude Code's decision, in this delivery form exactly as in the other.

## How it relates to the installer

The installer copies the three skills into `$CLAUDE_CONFIG_DIR/skills/` and manages one marked block in `$CLAUDE_CONFIG_DIR/CLAUDE.md`. A plugin can do neither: it owns no path in the configuration directory, and a `CLAUDE.md` at a plugin root is deliberately not loaded as context. The plugin therefore delivers the same two things the host's own way.

| | Installer | Plugin |
| --- | --- | --- |
| Skills | copied into `$CLAUDE_CONFIG_DIR/skills/` | shipped in `skills/`, loaded by the host |
| Skill invocation | `super-hero-core` | `super-hero-lite:super-hero-core` |
| Persistent instructions | a marked block in `CLAUDE.md` | a `SessionStart` hook printing the same block |
| Prerequisites | validated before any mutation | not checked; the host owns the lifecycle |
| Removal | `./uninstall.sh` | `/plugin uninstall` |

The two forms coexist. Claude Code namespaces a plugin skill, so a machine carrying both has both, and neither overwrites the other's state.

The hook's text is the installer's bootstrap block with its marker pair stripped — a plugin owns its whole contribution, so it has nothing to delimit — under two declared substitutions: the skill ids are written the way a plugin session can actually invoke them, and the clause saying the skills come from the persistent skills directories is replaced, because in this form they do not. `evals/test_claude_code_plugin.py` derives the expected text from the packaged fragment and fails if either file drifts from the other, so the two delivery forms cannot come to say different things.

A plugin may not reference a path outside its own root, so `skills/` here is a copy of the repository's `skills/`. The same suite compares the two trees byte for byte.

## Why the hook command is `cat`

The hook uses shell form. Claude Code documents that as `sh` on macOS and Linux, and Git Bash — or PowerShell, when Git Bash is absent — on Windows. `cat` is a POSIX utility and a PowerShell alias for `Get-Content`, so one command covers all three without shipping a script or depending on an interpreter. The host substitutes `${CLAUDE_PLUGIN_ROOT}` before any shell sees the command, and the path is quoted so an installation directory containing a space still resolves.

What is exercised, and what is not, is recorded in [Compatibility](https://github.com/MicheleDataBeat/super-hero-lite/blob/main/docs/compatibility.md). `evals/test_claude_code_plugin.py` runs the command under `sh` and compares its output to the packaged file byte for byte; Windows CI runs it under PowerShell and compares the text. Neither starts a real session, so neither of those two checks establishes that Claude Code invokes the hook and adds its output to the context. That was measured separately, by hand, after 1.1.0 was published, and is recorded in Compatibility.

Claude Code adds a `SessionStart` hook's plain-text stdout to the session, which is what makes this the plugin's equivalent of the block the installer writes.

## Validate

From the repository root, the whole repository contract, including this plugin's suite:

```bash
./validate.sh
```

Both manifests can also be checked against the host's own schema, which needs the `claude` CLI:

```bash
claude plugin validate . --strict
claude plugin validate distributions/claude-code/plugin --strict
```
