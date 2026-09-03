# Repository instructions

Super-Hero Lite's canonical development happens in a private repository. Work
is governed by the product this repository ships: read
`skills/super-hero-core/SKILL.md`.

## What that means in practice

Default to `DIRECT` for a clear, local, reversible change. Investigate what the
repository can tell you rather than asking. Ask when a decision would change
scope, externally visible behavior, architecture, security posture,
irreversible state, repository policy or publication.

## Governance here is executable

This repository's promises are tests, so changing a promise means changing a
test:

- `evals/test_skill_packages.py` fixes the first-party skill set at exactly
  three, in both directions, and pins the release skill's guarantees.
- `evals/test_removed_architecture.py` fails if any deleted mechanism returns.
  Bringing one back is a product decision, not a refactor.
- `evals/test_repository_contract.py` binds the documents to the code they
  describe.
- Each distribution's lifecycle suite drives the real entry points.

Run `./validate.sh` and read its output before claiming anything works.

## Publication

Development remains in the canonical private repository. No completion
phrase, merge, tag or private push authorizes publication. A public release
requires an explicit request and `super-hero-release-to-public`.
