# Release model

Super-Hero Lite develops in a private canonical repository and distributes
public releases through a separate public repository. The public repository
has existed since version `1.0.0`; this document does not create anything,
change a repository's visibility, tag a release, or publish anything.

## Controlled export

When an explicit public-release request is made, `super-hero-release-to-public`
works from one exact committed source tree:

1. Resolve the material choices through the release contract, and keep the
   canonical repository private.
2. Export a sanitized tree from the exact committed revision. Transfer no
   private Git history, no Issues and no private control-plane material.
3. Scan the staging tree for secrets and forbidden content, then verify the
   release artifact in isolation.
4. Present the evidence and require the explicit final `PUBLISH` gate before
   changing the separate public repository.

The first public release creates clean public history. Later releases preserve
only that public distribution history. Neither branch completion nor an
ordinary pull request is permission to cross this boundary.

A required check that fails or cannot run blocks publication. A warning is
never converted into a pass to complete a release.

## Prerequisites of a first public release

These are settings and documents rather than steps a release performs:

- GitHub Private Vulnerability Reporting enabled on the public target, with
  [Security](../SECURITY.md) updated to point at it;
- a code of conduct with a real private reporting address, and issue intake
  pointing at channels that exist, as [Governance](../GOVERNANCE.md) records.

## Local verification

Before any release boundary is considered ready for review, run the
repository verifier:

```bash
./validate.sh
```
