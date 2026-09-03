# Architecture

Super-Hero Lite separates a host-neutral core from host distributions, and
keeps both as small as the risks they protect against allow.

## The core

`skills/super-hero-core/SKILL.md` owns:

- interpretation of the three execution modes;
- the facts-versus-decisions rule;
- when to reach for a Pocock or a Superpowers technique inside `CONTROLLED`;
- delegation guidance;
- the solution-economy invariant;
- the completion-evidence invariant;
- the handoff to `super-hero-release-to-public`.

It answers how work should be governed. It does not answer where a host stores
instructions, how that host installs a skill, or which model performs a task.

It is deliberately short enough to read in one sitting, and it encodes policy
rather than simulated cognition. Anything that reads like a prescribed
reasoning procedure has been removed, because current hosts plan better
natively than a prompt can plan for them. See [Lineage](lineage.md).

## What the core does not own

Lite assigns no model and no reasoning effort to anything, and installs no
agent definitions of its own. The host decides who executes a delegated unit
of work and how hard it thinks.

That is a deliberate reversal of the ancestor's design, made because hosts now
orchestrate subagents natively, and because a table of vendor model names
encoded as workflow policy is wrong the moment the vendor ships another model.
The distributions validate that a host and its prerequisites are present; they
never decide which model does what. [Lineage](lineage.md) records in full what
the reversal removed.

## The host seam

A host distribution owns installation for one AI coding agent: its
configuration directory, its persistent instruction file, its skill-discovery
path, its prerequisite detection, its transactional state management, and its
own conformance validation.

The two implemented distributions differ in exactly five places, which is what
the seam exists to hold:

| | Codex | Claude Code |
| --- | --- | --- |
| Configuration directory | `$CODEX_HOME`, default `~/.codex` | `$CLAUDE_CONFIG_DIR`, default `~/.claude` |
| Persistent instructions | `AGENTS.md` | `CLAUDE.md` |
| Required host command | `codex` | `claude` |
| Pocock discovery path | `~/.agents/skills/` or `$CODEX_HOME/skills/` | `$CLAUDE_CONFIG_DIR/skills/` only |
| Plugin inventory | `codex plugin list`, text | `claude plugin list --json`, structured |

Claude Code also honors a per-skill availability control in the user scope of
its `settings.json`, which Codex has no equivalent for. That is a real
difference in what a host can express, not an inconsistency to paper over.

## Why the two distributions are not merged

Their lifecycle implementations are structurally similar and deliberately
separate. Extracting a shared framework would freeze today's parameterization
as an interface before a third host can contradict it, and it would hide the
host-specific discovery logic that is the interesting part of each file.

The duplication is bounded and legible: two files that read the same way, whose
differences are exactly the five rows above. `evals/test_repository_contract.py`
holds the parts that must stay identical, such as the interpreter resolution in
every PowerShell entry point, so drift fails a test rather than going
unnoticed.

## Governance is executable

Documents drift; tests do not. The checks under `evals/` are the enforcement
mechanism for the claims this repository makes about itself:

| Suite | What it protects |
| --- | --- |
| `test_skill_packages.py` | exactly three first-party skills, their declared contents, the release guarantees, and each invariant stated once |
| `test_compatibility.py` | the recorded baselines, their provenance, and the distributable-file manifest rule |
| `test_removed_architecture.py` | every deletion in [Lineage](lineage.md), by scanning what actually ships |
| `test_repository_contract.py` | the documents against the code they describe, and both validators against each other |
| each distribution's `test_lifecycle.py` | the real entry points against a fixture host: staging, snapshot, rollback, idempotency, ownership |

`evals/core-cases.md` carries the behavioral cases a unit test cannot honestly
evaluate, and `test_skill_packages.py` binds it to the core so the two cannot
drift apart.

## Boundaries in practice

Development stays in the canonical private repository. A public distribution
is not a branch or a visibility switch: it is a separate repository built
from a sanitized export of an exact committed revision, behind an explicit
final authorization. See the [release model](release-model.md).
