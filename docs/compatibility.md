# Compatibility

[`compatibility/upstreams.json`](../compatibility/upstreams.json) is the source
of record for the revisions tested with this repository. This document renders
those values; it is not an independent version registry.

Every recorded host baseline also says how it was established, so a number
inherited from the ancestor is never mistaken for one this release measured.
`evals/test_compatibility.py` fails if a rendered value and the metadata
disagree, or if a baseline carries no provenance.

## Recorded host profiles

| Host distribution | Tested host CLI | Evidence | Required capabilities |
| --- | --- | --- | --- |
| `codex` | Codex CLI `0.148.0-alpha.21` | inherited from super-hero-workflow 1.6.4; not re-measured for Lite 1.0.0 | `filesystem`, `shell`, `persistent-instruction-discovery`, `persistent-skill-discovery` |
| `claude-code` | Claude Code CLI `2.1.258` | measured 2026-09-03 on macOS 15 (arm64) | `filesystem`, `shell`, `persistent-instruction-discovery`, `persistent-skill-discovery` |

The supported-host contract is broader than those two profiles: a host needs
filesystem access, shell execution, and persistent instruction or skill
discovery through which all three Lite skill IDs are invocable or discoverable.

## What was measured for 1.0.0

On 2026-09-03, on macOS 15 (arm64) with Python 3.12.7, `git` 2.43.0 and `gh`
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
with the automatic workflow token.

## Changing a baseline

When compatibility metadata changes, update the metadata, its test, the tables
here, [Upstream integrations](../UPSTREAM.md) and the release evidence
together, and set each changed baseline's evidence to what was actually done.
Then run:

```bash
./validate.sh
```
