---
name: super-hero-release-to-public
description: Use when the user explicitly asks to publish, export, or release a private GitHub repository to a separate public repository.
---

# Super-Hero Release to Public

Publication is an EXTERNAL boundary in `super-hero-core`: irreversible,
externally visible, and impossible to take back once a secret has left. This
skill is deliberately procedural for that reason.

## Safety boundary

Run this skill only after an explicit user request to publish, export or
release a project publicly.

Never interpret "done", "finish", "ship", "merge", "release candidate", a
version bump or branch completion as authorization to publish publicly.

Never change the canonical private repository's visibility.

Never push, mirror, filter or rewrite the private Git history into the public
repository. Never use `git push --mirror` for this workflow.

Never force-push public history unless the user has separately and explicitly
authorized rewriting that public history.

## Publication architecture

```text
PRIVATE canonical repo
  code + private history + private Issues + internal artifacts
            |
            | exact committed source tree only
            v
release contract -> sanitized staging tree
            |
            v
secret scan + forbidden scan + tests/build
            |
            v
preview + explicit PUBLISH confirmation
            |
            v
SEPARATE PUBLIC distribution repo
  sanitized public tree + public-only history
```

Read as needed:

- `references/release-phases.md`
- `references/contract-schema.md`
- `references/sanitization.md`
- `references/public-history.md`
- `references/verification.md`

## Non-negotiable properties

### 1. Exact source revision

Export only from a known committed source SHA. Never publish uncommitted or
untracked files.

If the working tree is dirty and the intended release source is not
unambiguous, ask whether to commit, stash, exclude or cancel before
proceeding.

### 2. Private source must remain private

Verify the source repository's visibility read-only from GitHub metadata. If
the source is unexpectedly public, or visibility cannot be established, stop
and ask rather than assuming.

### 3. Separate target

The public target must be a different GitHub repository. If source and target
identities resolve to the same repository, abort.

### 4. Persisted release contract

Prefer `.release/public-release.yaml` in the private canonical repository. It
holds policy, never secrets, and must itself be excluded from the public
export.

If no valid contract exists, discover the facts read-only, resolve the
remaining material decisions with the user, then write the contract.

Use `assets/public-release-contract.yaml` as the starting schema. Fill
project-specific values only from discovered facts or decisions the user
actually made.

### 5. No secrets in contracts or the public tree

Require a real secret scanner before publication, for example `gitleaks` or an
equivalent the user or project has explicitly accepted. If none is available,
ask whether to install or configure one, or cancel. Never silently downgrade to
grep-only scanning.

Do not reproduce a discovered secret in a message, Issue, log or contract.
Name the file, path and finding category instead.

### 6. Deterministic export

Build the staging tree from the exact committed revision, not from a live
working directory. Apply only persisted include, exclude and replacement
rules. Fail on unresolved forbidden literals.

### 7. Public-only history

Initial publication creates a clean public history from the sanitized
snapshot. Later publications update the public repository from its own public
branch and preserve only public distribution history.

The private SHA may be recorded privately for traceability. Do not inject it
into public commit messages by default.

### 8. Explicit final publication gate

Preparation and verification do not authorize the push. Immediately before the
externally visible publish action, show a concise release preview and ask for
explicit `PUBLISH` confirmation.

## Release preview

At minimum show:

```text
Public release candidate

Private source: <owner/repo>@<short sha> (visibility: PRIVATE)
Public target:  <owner/repo> (visibility: PUBLIC or to-be-created)
Version/tag:    <version>
History mode:   <initial-clean | preserve-public-history>
Files:          <count> staged

Checks:
- contract validation: PASS
- secret scan: PASS
- forbidden literals: PASS
- tests: PASS / N/A by explicit contract
- build: PASS / N/A by explicit contract
- public diff review: PASS

No private Git history or private Issues will be transferred.

Type/confirm PUBLISH to publish this candidate.
```

After the preview, re-check that the public target branch has not changed since
it was inspected. If it changed, abort the push, refresh the diff and
re-verify rather than racing the remote.

## Failure behavior

Fail closed. A failed or unavailable required check blocks publication until it
is resolved with evidence or by an explicit user decision. Never convert a
warning into a pass to complete a release.
