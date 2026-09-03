# Upstream integrations

Super-Hero Lite requires two external upstream projects. Their tested baseline
is recorded in [`compatibility/upstreams.json`](compatibility/upstreams.json),
and rendered with its provenance in [Compatibility](docs/compatibility.md).

Those two are the complete dependency set. Anything else this project once
coordinated is recorded in [Lineage](docs/lineage.md), not here.

## Matt Pocock skills

Matt Pocock's [skills](https://github.com/mattpocock/skills) are an external
MIT-licensed dependency. Each host distribution expects the prerequisite to be
installed for its own agent before its installer runs. It does not expect a
particular version.

For Codex:

```bash
npx --yes skills add https://github.com/mattpocock/skills --skill '*' --agent codex --global --yes
```

For Claude Code:

```bash
npx --yes skills add https://github.com/mattpocock/skills --skill '*' --agent claude-code --global --yes
```

The two commands install the same upstream to different agent-owned locations.
Neither names a version: the `skills` CLI resolves its own latest release, and
a repository URL with no `/tree/<ref>` suffix resolves the default branch. So
these commands install what the upstream currently publishes, which is
deliberately not pinned to the revision recorded as tested.

Each distribution verifies the recorded source identity and the presence of the
required skill files its own host can discover. Neither runs these commands,
rewrites the `skills` lock, forks the project, or modifies any upstream skill.

## Obra/Prime Radiant Superpowers

[Obra/Prime Radiant Superpowers](https://github.com/obra/superpowers) is an
external MIT-licensed project distributed to each host as a plugin.

For Claude Code, install and update it through the Superpowers Claude Code
plugin marketplace, then enable `superpowers@superpowers-marketplace`, with:

```bash
claude plugin marketplace add obra/superpowers-marketplace
claude plugin install superpowers@superpowers-marketplace
```

These are the commands the Windows CI job runs against a real installation
(`.github/workflows/windows.yml`, "Enable the Superpowers plugin" step).

For Codex, install and update it through the official Codex plugin marketplace,
then enable `superpowers@openai-curated`. This repository records no verified
marketplace-add or install command for that step, and does not invent one.

The two marketplaces carry independent version lines, so the recorded baselines
differ per host. Each distribution detects its own enabled plugin; neither
clones, vendors, patches nor duplicates Superpowers.

## Compatibility and ownership

The recorded refs are tested compatibility targets, not promises about newly
released upstream versions. See [Compatibility](docs/compatibility.md) before
changing either baseline.

No Lite installer ever installs, updates or removes an upstream, and no
recorded ref is compared against an installed version at run time. Super-Hero
Lite retains responsibility for its own releases and implies no endorsement by
Matt Pocock, Obra or Prime Radiant.
