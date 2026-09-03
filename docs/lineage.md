# Lineage

Super-Hero Lite is a descendant of
[MicheleDataBeat/super-hero-workflow](https://github.com/MicheleDataBeat/super-hero-workflow).

This is the one document in the repository allowed to name the architecture
Lite removed. `evals/test_removed_architecture.py` scans every other
distributable file and fails if any of these names comes back, so historical
explanation lives here and nowhere else.

## Source baseline

| Fact | Value |
| --- | --- |
| Ancestor repository | `MicheleDataBeat/super-hero-workflow` |
| Ancestor version | `1.6.4` |
| Ancestor commit | `690cfdb2ad9827e75b0da7ed3307d9a01ee72ee7` |
| Resolved on | 2026-09-03 |
| Ancestor licence | MIT |

That commit was simultaneously the ancestor's latest published release and its
`main` head when Lite was derived, so there was no delta between the release
and the branch to reconcile.

Super-Hero Lite is **not a Git fork**. Its history begins with its own root
commit, no ancestor commit is reachable from it, and no ancestor branch, tag or
object was copied. Selected working-tree files were carried across and
rewritten; the `.git` directory was not.

## What was inherited

Conceptually:

- the idea that AI-assisted coding is not one kind of work, and that a
  reversible one-line fix and a public release deserve different safeguards;
- the separation of a host-neutral governance core from host-specific
  distributions;
- the material-decision boundary: facts are investigated, decisions are asked;
- the publication boundary, and its refusal to treat completion language as
  authorization to publish;
- evidence before a completion claim.

As tested implementation material:

- the transactional install, snapshot and rollback pattern, and its
  ownership-aware uninstall;
- each host's read-only prerequisite discovery, including the Claude Code
  `skillOverrides` semantics and the structured plugin inventory;
- the atomic instruction-file write that preserves a symlink and never converts
  a line ending;
- the shell and PowerShell entry points that delegate to one Python
  implementation;
- the distributable-file manifest rule;
- the publication guarantees of `super-hero-release-to-public`;
- the lifecycle test suites, minus the cases that asserted removed behavior.

## What was removed, and why

### The six-route state machine

The ancestor's router performed read-only reconnaissance, proposed one of six
routes (`DIRECT`, `POCOCK`, `SUPERPOWERS`, `HYBRID`, `WAYFINDER`,
`RELEASE-TO-PUBLIC`), and required confirmation before any development side
effect. Three of those routes named a methodology rather than a risk, which
made choosing a route a choice of vocabulary.

Lite has three modes that name consequence instead: `DIRECT`, `CONTROLLED`,
`EXTERNAL`. Pocock and Superpowers remain upstream technique families selected
inside `CONTROLLED` by what the work needs. `wayfinder` remains a Pocock skill
that is useful when exploration is; it is not a mode. Publication is `EXTERNAL`
plus the release skill.

### The mandatory confirmation gate

The router asked the user to confirm its route before touching anything. On
current models that gate mostly re-asked for permission the user had already
given, which is the specific failure both major vendors now warn about.

Lite replaced it with the facts-versus-decisions rule. Ordinary local work is
not confirmed twice; a material decision is still asked.

### The deterministic runtime router

`super-hero-runtime-router` classified every delegated unit of work by semantic
role and resolved it to a capability profile (`BRONZE`, `SILVER`, `GOLD`,
`REVIEW`, `DESIGN`), a rung on a three-step ladder, a pinned reasoning effort,
and a concrete model, with a declared model fallback ladder, a routing
manifest, a runtime envelope, a bounded execution class, and per-host profile
registries. That was a per-dispatch model and effort policy owned by this
project rather than by the host. The Claude Code distribution installed
twenty-one package-owned agent definitions to make those envelopes
harness-enforced.

All of it is gone: the skill, both `runtime/` directories, both profile
registries, the agent definitions, and the install, validate and uninstall
logic that owned them. Hosts now orchestrate subagents natively and choose
their own models and effort, and a vendor model table encoded as workflow
policy ages badly by construction. What survives is four sentences of
delegation guidance in `super-hero-core`.

### The ASK gate

`super-hero-ask-gate` was a separate skill with question templates. Its one
load-bearing rule moved into `super-hero-core` as the facts-versus-decisions
rule. The templates did not survive, because no test showed they were needed.

### The complexity posture and its upstream

The ancestor assessed `overbuild_susceptibility` as a second routing axis,
confirmed a posture from `OFF`, `ADVISORY`, `ENFORCED`, `REVIEW_ONLY` or
`AGGRESSIVE`, and shipped `ponytail-policy-adapter` to consume that pair. It
also required a `ponytail:` debt-marker gate before every ticket and route
completion, including when the posture was `OFF`, and carried Ponytail as an
optional upstream with precedence tables and phase-exclusion machinery.

Lite replaced the whole mechanism with one sentence of solution economy in
`super-hero-core`, plus the optional `super-hero-simplify` review. Ponytail is
not a Lite dependency: nothing installs, detects, modifies or reads a Ponytail
configuration, and no completion gate depends on a marker. The ancestor's
Ponytail attribution is not carried forward because no adapted Ponytail
material remains to attribute.

### The legacy Codex installation

The ancestor's Codex distribution recognized and migrated a pre-public
installation: legacy bootstrap markers, three legacy skill aliases, migration
branches in its managed state, and lifecycle fixtures that built and migrated
those layouts.

Lite is a new product with new installation state. It has no obligation to
migrate an installation created by `super-hero-workflow`, and carries no code
that could. If you have the ancestor installed, uninstall it with its own
uninstaller; Lite's uninstaller removes only Lite's state, exactly as the
ancestor's removes only the ancestor's.

### Duplicated verification prose

The ancestor stated verification requirements in several first-party skills.
Lite states the completion-evidence rule once, in the core, and
`evals/test_skill_packages.py` fails if another first-party skill restates it.
The release skill keeps its own checklist because publication's checks are
genuinely release-specific rather than a restatement, and every executable
check the ancestor had was kept or refactored rather than dropped.

## Skills, before and after

| Ancestor | Lite |
| --- | --- |
| `super-hero-workflow-router` | removed |
| `super-hero-ask-gate` | removed; its decision rule moved into the core |
| `super-hero-runtime-router` | removed |
| `ponytail-policy-adapter` | removed; replaced by one invariant and `super-hero-simplify` |
| `super-hero-release-to-public` | kept and simplified |
| — | `super-hero-core`, new |
| — | `super-hero-simplify`, new |

No alias, shim or successor ships for a removed skill. The deletion is the
migration.

## Versioning

Super-Hero Lite starts at `1.0.0` with its own changelog. It does not continue
the ancestor's version line, and the two projects' version numbers have no
relationship.
