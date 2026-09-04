# Compatibility

[`compatibility/upstreams.json`](../compatibility/upstreams.json) is the source
of record for the revisions tested with this repository. This document renders
those values; it is not an independent version registry.

Every recorded host baseline also says how it was established, so a number
inherited from the ancestor is never mistaken for one this release measured.
`evals/test_repository_contract.py` fails if a rendered value or a platform
mention disagrees with the metadata, and `evals/test_compatibility.py` fails if
a baseline carries no provenance.

## Recorded host profiles

| Host distribution | Tested host CLI | Evidence | Required capabilities |
| --- | --- | --- | --- |
| `codex` | Codex CLI `0.148.0-alpha.21` | inherited from super-hero-workflow 1.6.4; not re-measured for Lite 1.0.0 | `filesystem`, `shell`, `persistent-instruction-discovery`, `persistent-skill-discovery` |
| `claude-code` | Claude Code CLI `2.1.258` | measured 2026-09-03 on macOS 26 (arm64) | `filesystem`, `shell`, `persistent-instruction-discovery`, `persistent-skill-discovery` |

The supported-host contract is broader than those two profiles: a host needs
filesystem access, shell execution, and persistent instruction or skill
discovery through which all three Lite skill IDs are invocable or discoverable.

## What was measured for 1.0.0

On 2026-09-03, on macOS 26 (arm64) with Python 3.12.7, `git` 2.43.0 and `gh`
2.96.0:

| Check | Result |
| --- | --- |
| Both lifecycle suites against a fixture host, driving the real `.sh` entry points | pass |
| Root `./validate.sh`, the whole POSIX contract | pass |
| Claude Code CLI present and reporting its version | `2.1.258` |
| Eleven Pocock skills discoverable under the Claude Code path, none switched `off` | pass |
| `superpowers@superpowers-marketplace` enabled | pass, version `5.1.0` |
| Claude Code prerequisite validation against the real host directory, read-only | pass |

Two things were **not** measured, and are recorded as such rather than assumed:

- **The Codex host.** No `codex` CLI is installed on the machine where 1.0.0
  was built, so the Codex distribution was never exercised against a real
  Codex host. Its lifecycle is nevertheless covered in full: the suite drives
  the real entry points against a stubbed host command, so staging, snapshots,
  rollback, idempotency and ownership are all exercised. What that does not
  prove is the real Codex integration, and the recorded host CLI version is
  the ancestor's, inherited.
- **The PowerShell entry points.** No `pwsh` is installed on that machine
  either. They are exercised on Windows CI, which is where the `.ps1`
  behavior is verified. Locally they are checked statically:
  `evals/test_repository_contract.py` requires every one to exist, to read the
  same configuration variable as its POSIX sibling, to delegate to the same
  Python, to propagate the exit status, and to resolve the interpreter with one
  identical block.

## What was measured for 1.1.0

On 2026-09-04, on macOS 26 (arm64), for the Claude Code plugin added in
1.1.0, with `claude` reporting `2.1.258` as in 1.0.0:

| Check | Result |
| --- | --- |
| Root `./validate.sh`, including the new plugin suite | pass |
| `claude plugin validate` on the marketplace manifest and the plugin, `--strict` | pass, both |
| Plugin installed from a local marketplace into an isolated `CLAUDE_CONFIG_DIR` | pass |
| Component inventory read back from the host | 3 skills, 0 agents, 1 `SessionStart` hook |
| Installed skills compared with the packaged skills | byte-identical |
| Hook command run under `sh`, output compared with the packaged file | byte-identical |
| Plugin uninstalled | pass, nothing left in the inventory |

Three things were **not** measured at the time 1.1.0 was published, and were
recorded as such rather than assumed:

- ~~**That Claude Code invokes the hook and adds its output to a session.** No
  live session was run, because the CLI on the build machine had no valid
  authenticated session. What was verified is that the command resolves, runs
  and prints exactly the packaged file. That the host executes `SessionStart`
  hooks and adds their plain-text output to the context is the host's
  documented behavior, relied on here rather than measured.~~ **Measured
  2026-09-04, after publication**, once the host CLI was re-authenticated. See
  "What was measured after publishing 1.1.0" below.
- **The Windows shell path.** The local suite runs the hook command under
  `sh`, which is not the shell Windows uses. Windows CI runs the same command
  under PowerShell, where `cat` is `Get-Content`, and compares the text; that
  job is where this is verified.
- ~~**The published `owner/repo` marketplace source.** Only the local directory
  form was exercised, since the release had not been published when this was
  measured. The same workflow exercises the `owner/repo` form for the
  Superpowers marketplace, so the host path is not itself untested.~~
  **Measured 2026-09-04, after publication**, once there was a published
  repository to install from. See "What was measured after publishing 1.1.0"
  below.

## What was measured after publishing 1.1.0

On 2026-09-04, on the build machine — macOS 26 (arm64), `claude` `2.1.258` —
against the published 1.1.0 artifact, by two different methods. The install
rows used a real installation into a throwaway `CLAUDE_CONFIG_DIR`, so that the
published marketplace source was genuinely exercised. The session rows used
`claude --plugin-dir`, which loads a plugin for one session without installing
it, because the authenticated session is bound to the real configuration
directory and a throwaway one cannot start a session at all.

| Check | Method | Result |
| --- | --- | --- |
| Published `owner/repo` marketplace source, added and installed with the documented commands | real install | pass, recorded source `github: MicheleDataBeat/super-hero-lite`, enabled at `1.1.0` |
| Component inventory read back from the host | real install | 3 skills, 0 agents, 1 `SessionStart` hook |
| Installed skills compared with the published tree | real install | byte-identical |
| Hook output reaches a live session | `--plugin-dir` | pass |
| All three skills available to a session under their plugin-qualified ids | `--plugin-dir` | pass |

Neither session row asserts more than delivery. The hook's text reached the
session's context; whether a session then follows the policy is not something
this table measures.

The hook check is a two-arm comparison, because the build machine also carries
the installer's own block in `CLAUDE.md`, whose text is nearly identical. A
control session with no plugin reported one `## Super-Hero Lite` block, naming
`super-hero-core`. The same prompt with the plugin loaded reported two, the
second naming `super-hero-lite:super-hero-core` and saying the skills come from
the plugin — wording that appears only in the plugin's hook payload. A single
session would have proved nothing, since the control arm alone already answers
in the affirmative.

The skill check is the same comparison. The control session listed the three
Lite skills by their bare ids, alongside unrelated skills the machine happens
to carry; the plugin arm listed all of those plus
`super-hero-lite:super-hero-core`,
`super-hero-lite:super-hero-release-to-public` and
`super-hero-lite:super-hero-simplify`. Availability is what was observed: the
prompt forbade tool use, so no skill was invoked. That comparison is also the
measurement behind the claim that the two delivery forms coexist without either
overwriting the other — though what coexisted was a session-loaded plugin
beside an installed bootstrap block, since `--plugin-dir` installs nothing.
Installed-state ownership is covered instead by the Windows job, which
uninstalls the distribution and checks the plugin survives.

One item from the 1.1.0 list stands: the Windows shell path is still verified
by Windows CI rather than locally.

## Recorded upstream baseline for codex

| Upstream | Tested ref | Tested commit | Licence | Installation manager |
| --- | --- | --- | --- | --- |
| [Matt Pocock skills](https://github.com/mattpocock/skills) | `v1.2.3` | `6acc160e4e0cd062dbbbd7a1b26ae92855edf07e` | MIT | `skills` |
| [Obra/Prime Radiant Superpowers](https://github.com/obra/superpowers) | `v6.3.0` | `b36e0829c6d0140e93cfef2ca599b1b07d4a7797` | MIT | `codex-plugin-marketplace` |

The Superpowers row is inherited with the host row, for the same reason: no
Codex host was available to install a plugin into. The commit was
re-verified against the upstream repository on 2026-09-03, where the annotated
tag `v6.3.0` still dereferences to it.

## Recorded upstream baseline for claude-code

| Upstream | Tested ref | Tested commit | Licence | Installation manager |
| --- | --- | --- | --- | --- |
| [Matt Pocock skills](https://github.com/mattpocock/skills) | `v1.2.3` | `6acc160e4e0cd062dbbbd7a1b26ae92855edf07e` | MIT | `skills` |
| [Obra/Prime Radiant Superpowers](https://github.com/obra/superpowers) | `5.1.0` | `6fd4507659784c351abbd2bc264c7162cfd386dc` | MIT | `claude-code-plugin-marketplace` |

Both hosts share one Matt Pocock baseline, because it is the same upstream
release installed by the same `skills` CLI; only the install target differs.
The installed lock recorded ref `v1.2.3`, and that annotated tag was confirmed
against the upstream on 2026-09-03 to dereference to the commit above.

The two Superpowers rows say deliberately different things. Superpowers reaches
each host through a different marketplace with an independent version line:
the Codex row records the upstream Git tag, the Claude Code row records the
marketplace plugin version. The Claude Code figures were read from the
installation itself, which reported plugin version `5.1.0` at commit
`6fd4507659784c351abbd2bc264c7162cfd386dc`. That commit is not what the
upstream's `v5.1.0` tag points at, because the marketplace pins no ref and a
fresh install resolves whatever the source URL then held. Recording what is
installed, rather than what a tag suggests, is the point of the column.

## What "tested" means

The recorded refs are the revisions this release was tested against. They are a
record, not a requirement.

No distribution ever compares an installed version against a recorded one. A
prerequisite installed at a different version, later or earlier, is not
blocked, because no version is read at all. What the prerequisite checks verify
is source identity, the presence of the required skill files, whether the host
has switched one off, and enabled plugin state.

The documented install commands name no version either, so running one installs
whatever the upstream currently publishes rather than the revision recorded
above. That is deliberate: a command that pinned a tested revision would hand
new users an old one on purpose.

The honest consequence is that admitting a later version is not the same as
promising it works. A newer upstream is untested until a row here says
otherwise, and the way this project finds out is that its own suites fail, not
that an installer refuses to run.

## What the distributions cannot detect

The available lock and plugin state show source identity, required files and
enabled state. For Codex they do not prove the exact installed upstream commit.
Claude Code records the commit it installed for a plugin, so `claude-code` can
report a commit it did not itself verify against upstream history; the two
figures above were checked against the upstream separately.

A `skillOverrides` entry in a project's own settings can switch a prerequisite
skill off for that project. A host-directory validator reads only the user
scope and cannot see it.

## Platform verification

Linux CI runs `./validate.sh`, the whole contract, on every push and pull
request.

Windows CI runs only when a change touches Windows. It runs `.\validate.ps1`,
which covers the repository evals, the packaged distribution artifacts, the
documentation contract and the manifest, and it runs both lifecycle suites in
full through the `.ps1` entry points, so the transactional behavior is covered
there too. What stays Linux-only is the `.sh` entry points themselves, reported
as skipped rather than passed.

A second Windows job installs the real upstream prerequisites from public
sources and runs the real Claude Code lifecycle against them, because a package
validator cannot prove an installation. It needs no secret: `gh` authenticates
with the automatic workflow token. Since 1.1.0 it also validates both plugin
manifests against the host's own schema, installs the plugin and reads the
inventory back, and runs the `SessionStart` hook's command under PowerShell to
confirm it reproduces the packaged text; that is the only place the Windows
shell path is exercised.

## Changing a baseline

When compatibility metadata changes, update the metadata, its test, the tables
here, [Upstream integrations](../UPSTREAM.md) and the release evidence
together, and set each changed baseline's evidence to what was actually done.
Then run:

```bash
./validate.sh
```
