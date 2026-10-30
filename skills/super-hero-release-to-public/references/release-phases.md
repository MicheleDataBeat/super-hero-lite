# Release phases

## Phase 0 — authorization

Require an explicit public-publication request from the user. Nothing else
starts this workflow.

## Phase 1 — read-only discovery

Discover without mutation:

- source repository identity, visibility, default branch, current branch;
- clean/dirty status and the exact HEAD SHA;
- any existing release contract;
- target repository existence, visibility and default branch;
- the source's version and tag conventions;
- licence, readme and package metadata;
- likely internal or agent-private artifacts;
- branding literals and historical names present in the committed tree;
- available secret scanners;
- declared test and build commands, and CI expectations;
- build outputs the tests need but Git ignores (native helpers, generated
  bundles): the staging tree will not contain them, so record the build step
  CI runs before its tests;
- comments, docstrings and ignore files that describe the private publication
  model or point at files the contract will exclude;
- whether the target already has public history or releases.

These are facts. Discover them; do not ask for them.

## Phase 2 — decisions

Resolve every material decision a valid contract does not already govern.
Typical decisions:

- the public owner and repository name;
- the licence, if missing or ambiguous;
- the public version and tag;
- public-facing branding and replacements;
- which docs, assets and examples are distributable;
- explicit exceptional inclusions or exclusions;
- what to do with an existing target whose public state conflicts with the
  intended release;
- installing or configuring a secret scanner when none is available;
- whether a failed verification is legitimately not applicable. This must be
  explicit and persisted, never waved away.

Ask one decision at a time.

## Phase 3 — contract

Create or update `.release/public-release.yaml` in the private repository.
Ensure `.release/**` is excluded from publication. Never place secrets in the
contract.

Validate the contract before using it.

## Phase 4 — exact export

Create a pristine staging snapshot from the exact committed source revision.
`git archive <sha>` is preferred: it excludes uncommitted and untracked state
and honors export policy encoded in Git attributes.

Then apply the contract's exclusions and its approved deterministic
transformations. Do not improvise file removal or renaming outside the
contract.

## Phase 5 — sanitization checks

- assert release-control and agent-private paths are absent;
- run the secret scanner on the staging tree;
- scan for forbidden literals;
- inspect generated and public metadata;
- verify licence, readme and version consistency;
- ensure no nested `.git`, private remote or private config survives;
- grep every excluded path inside the staging tree: a reference to an
  excluded document is a broken public link or a leak of its existence;
- inspect ignore files for un-ignore rules (`!path`) and comments that reveal
  excluded content or an earlier distribution model;
- scan for concept wording, not only names: see "Concept scan" in
  `sanitization.md`.

## Phase 6 — isolated verification

Run the required tests and builds in the staging tree or another isolated
copy, never in a way that contaminates the canonical tree. Record fresh
results.

Replicate first, in the isolated copy, the build steps CI runs before its
tests. A suite that passes only in the canonical checkout because of ignored
build outputs has not verified the public tree; a suite that hangs instead of
failing when a helper is missing is a defect to record.

## Phase 7 — public diff preparation

If the target does not exist and the contract authorizes creating it, prepare
the creation without exposing source history.

Reborn slug: when the public target must carry the same name as the private
source, first rename the private repository to an archive name and keep it
private, point every local checkout's remote at the archive, then create the
empty target without generated files. Creating a repository under the old
name removes the redirect the rename left behind, so until then the old name
resolves to the archive and a live visibility check must treat that answer as
a mismatch, not as the target.

Multi-repository releases: push in link order (documentation before the page
that links it, a personal site that links everything last).

If the target exists:

1. clone or fetch the public target independently;
2. record its current remote head;
3. overlay the sanitized snapshot while preserving `.git`;
4. inspect the full public diff;
5. confirm every removed file is intentional under the contract.

## Phase 8 — final PUBLISH gate

Show the release preview. Ask for explicit `PUBLISH` confirmation.

## Phase 9 — publication

Re-check the remote head and visibility immediately before pushing. If
unchanged, create the public commit, tag and release according to the
contract, and push normally. No force by default.

If the target publishes a site from a workflow, enable the site with the
workflow build type before the first push; otherwise the first deployment
fails on the site-configuration step and must be rerun by hand.

## Phase 10 — post-publication verification

Fetch or query the public repository after the push and verify:

- the expected commit, tag and release exist;
- the target's visibility is PUBLIC;
- the source repository is still PRIVATE;
- secret and forbidden-content checks still pass against the published tree;
- published artifact and build metadata match the intended version;
- every workflow the push triggered completed successfully;
- the published site, if any, answers with the expected version data;
- links between the published repositories, and from any page that
  references them, resolve.

Report the public commit and tag with all verification evidence.
