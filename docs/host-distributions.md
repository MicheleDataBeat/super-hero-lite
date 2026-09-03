# Host distributions

A host distribution is the installable Super-Hero Lite implementation for one
AI coding agent. It keeps the core portable while making host-specific
prerequisites and behavior explicit.

## Current support

Two host distributions ship in version 1.0.0: `codex` and `claude-code`. This
release promises no third host.

| Host distribution | Configuration directory | Persistent instructions | Persistent skills |
| --- | --- | --- | --- |
| `codex` | `$CODEX_HOME`, default `~/.codex` | `AGENTS.md` | `skills/` |
| `claude-code` | `$CLAUDE_CONFIG_DIR`, default `~/.claude` | `CLAUDE.md` | `skills/` |

## What a distribution owns

Exactly two things: the three Lite skill directories under `skills/`, and one
marked bootstrap block in the host's persistent instruction file.

Everything else in the configuration directory belongs to the user or to
another tool: personal instructions, unrelated skills, host settings,
dependency locks, plugin state, and anything under `agents/`. A distribution
never reads or rewrites them, and its uninstaller never removes them.

Ownership is by exact name. Adding a fourth owned skill means changing
`LITE_SKILLS` in both distributions and the set in
`evals/test_skill_packages.py`, which fails if the two disagree.

## Supported platforms

A distribution's work is done by Python, so the platform difference is confined
to the entry point that launches it.

| Platform | Entry points | Interpreter | Shell |
| --- | --- | --- | --- |
| macOS, Linux | `install.sh`, `uninstall.sh`, `validate.sh` | `python3` | `bash` |
| Windows | `install.ps1`, `uninstall.ps1`, `validate.ps1` | `python3`, `python`, or the `py` launcher | PowerShell |

A `.ps1` entry point takes the same arguments and reads the same
configuration-directory variable as its `.sh` sibling, then hands the same
command to the same `lib/managed_state.py`. It does not repeat the prerequisite
checks the shell wrapper performs, because that Python performs them itself.

Two things genuinely differ rather than being wrapped:

- A host command installed by npm is a `.cmd` shim, and Windows resolves a bare
  command name against `PATH` for executables only. Every host command is
  therefore resolved to an installed path before it is run.
- Line endings must survive checkout unchanged. The manifest records a digest
  of committed bytes and every installer compares installed bytes against
  packaged bytes, so `.gitattributes` marks every path as never converted.

## Lifecycle

Install and update are the same idempotent command. Both install and uninstall
are transactional:

1. validate the required commands, the authenticated `gh` session, and both
   upstream prerequisites, read-only;
2. validate the package, including that it ships exactly the three Lite skills;
3. stage the skills into a transaction directory on the host's own filesystem
   and verify the staged bytes against the package;
4. snapshot only Lite-owned existing state;
5. replace the owned state by rename rather than by deletion, keeping the
   displaced state for rollback;
6. synchronize the one marked bootstrap block;
7. validate the installed result;
8. restore the snapshot if any post-mutation step fails.

Step 5 matters: an existing owned skill is moved aside, never deleted before
its replacement is in place, so an interruption cannot leave a hole. Each
distribution's lifecycle suite proves this by forcing a failure after the
mutation, and by interrupting the transaction mid-rename, then comparing every
byte in the fixture home against its prior state.

Each distribution's validator has two modes. Package-only validation
inspects packaged artifacts and never reads user state, so it passes with
nothing installed. Installed-state validation additionally requires the
installed state to match the package byte for byte, so it fails after an
uninstall, which is the correct answer. Each distribution's README gives the
commands; the repository's own `./validate.sh` is a separate thing and takes
no arguments.

## Prerequisite detection

Detection is read-only and deliberately host-specific.

For the eleven Matt Pocock skills, both hosts read `~/.agents/.skill-lock.json`
and require the recorded source to be `mattpocock/skills`. They then differ on
where the skill files must be:

- `codex` accepts `~/.agents/skills/<skill>/SKILL.md` or
  `$CODEX_HOME/skills/<skill>/SKILL.md`;
- `claude-code` requires `$CLAUDE_CONFIG_DIR/skills/<skill>/SKILL.md`, because
  that is the only global location this host discovers. A shared agent-neutral
  copy does not satisfy it.

`claude-code` additionally reads `skillOverrides` in the user scope of
`$CLAUDE_CONFIG_DIR/settings.json`. A required skill switched `"off"` there
fails the prerequisite even though its file is present, while
`"user-invocable-only"` and `"name-only"` still satisfy it: the host itself
forces an author-locked skill to `"user-invocable-only"` unless the user
explicitly chose `"off"`, so treating that value as missing would fail every
correct installation. A project-scope override is invisible to a
host-directory validator and is not read.

For Superpowers, `codex` parses the text output of `codex plugin list` and
`claude-code` reads the structured `claude plugin list --json` inventory. Both
require the host's own plugin id to be enabled, matched exactly, so a
similarly named plugin does not satisfy the check.

No installer ever installs, updates or removes either upstream, and no recorded
version is compared against an installed one.

## Qualification checklist

A future host distribution must demonstrate:

- filesystem access sufficient to inspect and edit a repository;
- shell execution sufficient to run its validation and the project's
  verification;
- persistent instruction or skill discovery through which all three Lite skill
  IDs are invocable or discoverable;
- read-only detection of both external prerequisites, as far as the host makes
  that possible;
- a host-specific installer, uninstaller and conformance validation that manage
  only Lite's own state;
- evidence that the host can preserve the decision boundary, evidence-backed
  completion, and the explicit public-release boundary.

Note what is absent: nothing on this list concerns models. A host qualifies on
what it can discover and what its lifecycle can manage safely, never on what it
can be made to route. [Lineage](lineage.md) records the requirement this
replaced.

## Adding a host

Start by documenting the host's actual capabilities and comparing them with the
checklist. Host-specific code stays in its own distribution rather than being
generalized by guesswork; [Architecture](architecture.md) explains why two
implementations did not justify a shared framework.
