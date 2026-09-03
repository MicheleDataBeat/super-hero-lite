# Super-Hero Lite

> Lightweight governance for frontier AI coding agents.

Super-Hero Lite is a simplified descendant of [MicheleDataBeat/super-hero-workflow](https://github.com/MicheleDataBeat/super-hero-workflow). It keeps the parts of the ancestor that protect consequential software-development boundaries while removing the deterministic prompt and runtime orchestration that current Codex and Claude Code hosts handle natively.

The design principle is:

**Keep governance. Remove micromanagement.**

## Why Lite exists

Current frontier coding models are substantially better at inferring the user's intended level of work, planning tool use, sustaining long tasks and orchestrating subagents than they were when the ancestor was designed.

OpenAI's current GPT-5.6 guidance recommends leaner prompts, says the model can infer underlying intent without every step being prescribed, and warns that repeated approval instructions can themselves cause unnecessary approval requests.

Anthropic's current guidance for its fifth-generation Claude models recommends general instructions over hand-written procedural reasoning in many cases, and says current Claude models can orchestrate subagents natively.

Super-Hero Lite therefore hands ordinary reasoning, delegation and effort selection back to the host.

It keeps explicit controls exactly where a mistake stays expensive no matter how capable the model is: material human decisions, destructive or external actions, evidence before completion claims, security-sensitive work, and private-to-public publication.

See [Architecture](docs/architecture.md) and [Lineage](docs/lineage.md).

## Three execution modes

| Mode | Use it when | Default behavior |
| --- | --- | --- |
| `DIRECT` | Work is clear, local, reversible and in scope. | Inspect, implement, test/check, report. |
| `CONTROLLED` | Material ambiguity, architecture, security sensitivity, debugging difficulty or blast radius warrants additional structure. | Use only the specification or execution techniques that materially help. |
| `EXTERNAL` | Work crosses a destructive, irreversible, externally visible, repository-history or publication boundary. | Resolve the consequential decision and authorization before the boundary action. |

`DIRECT` is the default. It adds no second confirmation step after the user has already asked for an ordinary local change.

The permanent decision rule is:

> Investigate discoverable facts. Ask only for unresolved decisions that materially alter scope, externally visible behavior, architecture, security posture, irreversible state, repository/history policy, or publication.

## Upstream techniques

Super-Hero Lite coordinates two external methodology families without turning either into a global workflow state. Inside `CONTROLLED` it reaches for whichever one the specific risk calls for, both when both apply, and neither when native host behavior is enough.

### Matt Pocock skills

Use when `CONTROLLED` work benefits from clarification, specification, ticketing, design or the related upstream techniques.

Required skills:

- `setup-matt-pocock-skills`
- `grill-with-docs`
- `to-spec`
- `to-tickets`
- `implement`
- `wayfinder`
- `tdd`
- `code-review`
- `diagnosing-bugs`
- `domain-modeling`
- `codebase-design`

### Superpowers

Use when `CONTROLLED` work benefits from isolation, test-first implementation, systematic debugging, review, verification or other Superpowers execution discipline.

Host plugin identifiers:

- Codex: `superpowers@openai-curated`
- Claude Code: `superpowers@superpowers-marketplace`

Both dependencies are externally managed. Lite installers validate them and never install, update or remove them.

## Native host autonomy

Lite assigns no work role to a model and no reasoning effort to a task, and it installs no agent definitions of its own. Which model runs a delegated unit of work, and how hard it thinks, is the host's decision. [Lineage](docs/lineage.md) records the machinery this replaced and why it went.

Use the host's current model and native delegation behavior. One small delegation rule remains:

- use subagents when parallelism, isolated context or independent workstreams materially help;
- work directly for simple, sequential or context-coupled work;
- use independent review for genuinely high-consequence changes.

## Solution economy

Lite keeps one implementation invariant:

> Implement the minimum straightforward solution satisfying accepted requirements. Prefer existing repository code, standard-library or native platform capability, and already-installed dependencies before adding new abstraction or dependencies.

It may simplify an implementation and never reduce accepted scope. `super-hero-simplify` is an optional post-implementation review for changes that look unnecessarily complex.

## Completion evidence

Do not claim completion without fresh evidence from the relevant tests or checks.

Lite states that once, in the core, and relies on repository tests, CI and host tooling to produce the evidence.

## First-party skills

Lite ships exactly three:

- `super-hero-core`
- `super-hero-release-to-public`
- `super-hero-simplify`

## Install

### Codex

Prerequisites: `git`, `gh`, Python 3, `codex`, an authenticated GitHub CLI session, the eleven Pocock skills, and `superpowers@openai-curated` enabled.

Install or update:

```bash
./distributions/codex/install.sh
```

Windows:

```powershell
.\distributions\codex\install.ps1
```

See [`distributions/codex/README.md`](distributions/codex/README.md#prerequisites) for the complete prerequisite contract and validation behavior.

### Claude Code

Prerequisites: `git`, `gh`, Python 3, `claude`, an authenticated GitHub CLI session, the eleven Pocock skills, and `superpowers@superpowers-marketplace` enabled.

Install or update:

```bash
./distributions/claude-code/install.sh
```

Windows:

```powershell
.\distributions\claude-code\install.ps1
```

See [`distributions/claude-code/README.md`](distributions/claude-code/README.md#prerequisites) for the complete prerequisite contract and validation behavior.

Install and update are the same idempotent command. An installer manages only Super-Hero Lite state and restores what it owned if a post-mutation step fails. To remove only that state, run the distribution's uninstaller:

```bash
./distributions/claude-code/uninstall.sh
```

## Validate

From the repository root:

```bash
./validate.sh
```

Windows:

```powershell
.\validate.ps1
```

Both run the same checks in the same order. The PowerShell entry point reports the checks that need a POSIX shell as skipped rather than passing them silently. Each distribution also provides package-only and installed-state validation.

## Public publication boundary

Super-Hero Lite develops in a private canonical repository.

Public publication is a separate `EXTERNAL` operation governed by `super-hero-release-to-public`. It requires an exact committed source SHA, a separate public target, deterministic sanitization, real secret scanning, the release contract's required tests and build checks, public-only history, and an explicit final `PUBLISH` authorization.

No ordinary completion phrase, branch state, version tag or private push authorizes public publication. See the [release model](docs/release-model.md).

## Lineage

Super-Hero Lite is derived from the design and selected implementation material of:

`MicheleDataBeat/super-hero-workflow`

- ancestor version: `1.6.4`
- ancestor commit: `690cfdb2ad9827e75b0da7ed3307d9a01ee72ee7`

That commit was the ancestor's latest stable release and its `main` head when Lite was derived on 2026-09-03.

Super-Hero Lite is **not a Git fork** of the ancestor and does **not inherit the ancestor's Git history**. This repository starts with new Lite-only history, and no ancestor commit is reachable from it.

The ancestor's MIT licence obligations and the relevant upstream attributions are preserved. See [Attributions](ATTRIBUTIONS.md) and [Lineage](docs/lineage.md).

## Compatibility

Compatibility records the host and dependency baselines that were actually tested, and says of each one whether it was measured for this release or inherited from the ancestor. It prescribes no role-to-model routing.

See [Compatibility](docs/compatibility.md) and [Upstream integrations](UPSTREAM.md).

## Documentation map

- [Architecture](docs/architecture.md)
- [Host distributions](docs/host-distributions.md)
- [Compatibility](docs/compatibility.md)
- [Release model](docs/release-model.md)
- [Lineage](docs/lineage.md)
- [Upstream integrations](UPSTREAM.md)

## Credits

Super-Hero Lite coordinates methods other people designed.

- [Matt Pocock's skills](https://github.com/mattpocock/skills): clarify intent, write the specification, cut it into tickets.
- [Obra/Prime Radiant Superpowers](https://github.com/obra/superpowers): worktree isolation, test-first execution, verification before any completion claim.

Both are external, unmodified, MIT-licensed upstream projects. Read the full [attributions](ATTRIBUTIONS.md), including their licences and the no-endorsement notice.

## AI disclosure

Generative AI materially assisted this project's design, implementation, testing and documentation, under human direction and review. [AI disclosure](AI_DISCLOSURE.md) explains the accountability behind that statement.

## Contributing, security, and support

- [Contributing guide](CONTRIBUTING.md)
- [Security policy](SECURITY.md)
- [Support policy](SUPPORT.md)
- [Governance](GOVERNANCE.md)
- [Code of Conduct](CODE_OF_CONDUCT.md)

## License

Super-Hero Lite is licensed under the [MIT License](LICENSE).
