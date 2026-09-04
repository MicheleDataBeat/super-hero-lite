# Release contract schema

Recommended private path: `.release/public-release.yaml`.

The contract is policy, not credentials. Commit it to the private canonical
repository when appropriate, and always exclude it from the public export.

Minimum conceptual fields:

```yaml
schema_version: 1

source:
  canonical_repository: owner/private-repo
  required_visibility: private
  branch: main
  require_clean_tree: true

public:
  repository: owner/public-repo
  required_visibility: public
  branch: main

history:
  initial: clean_snapshot
  subsequent: preserve_public_history
  allow_force_push: false

release:
  version_source: package_manifest  # or explicit, tag, or another agreed source
  tag_format: "v{version}"
  public_commit_message: "Release {version}"

export:
  deny:
    - .release/**
    - .scratch/**
    - .agents/**
    - .codex/**
  allow: []

branding:
  replacements: []
  forbidden_literals: []

verification:
  secret_scanner: gitleaks
  test_commands: []
  build_commands: []
  forbidden_literal_scan: true
```

Project-specific values must come from discoverable facts or from decisions the
user actually made.

## Determinism rules

- Every intentional omission must be represented by a contract rule, or by a
  source-level export rule the workflow has reviewed.
- Every text transformation must be an explicit mapping. Do not "clean up
  branding" heuristically.
- Commands that define required verification must be persisted.
- A later run against the same source revision with the same contract should
  produce an equivalent staging tree.
- If the environment or toolchain makes deterministic output impossible
  (timestamps, generated bundles, lockfile drift), surface that fact and ask
  for the intended policy rather than hiding it.

## Not applicable is a decision

A missing test or build command is not automatically not-applicable. If the
project genuinely has no relevant command, persist that fact in the contract.
If a normally required check cannot run, ask rather than silently waiving it.
