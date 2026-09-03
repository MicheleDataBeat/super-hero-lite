# Contributing to Super-Hero Lite

## Before you start

- Use an Issue to discuss a material behavior change before opening a pull
  request. Small documentation corrections and clearly bounded fixes may
  proceed directly when their intent is evident.
- Keep a change focused. Do not combine unrelated cleanup with a behavior
  change.
- Never include credentials, tokens, private keys, unredacted production data
  or other secrets in Issues, commits, pull requests, test fixtures or
  documentation.
- An ordinary pull request must not create a public repository, push a public
  release, or otherwise publish the project.

## Development expectations

Use test-driven development for behavior changes: write a focused failing test,
observe the expected failure, make the smallest change that passes it, and
refactor only while tests stay green. A test that has never been seen to fail
is not evidence.

This repository's own governance is executable, so a change to what it promises
is a change to a test. Adding, removing or renaming a first-party skill means
updating `evals/test_skill_packages.py`, both distributions' `LITE_SKILLS`, and
every README that names the set. Reintroducing anything in
`evals/test_removed_architecture.py` is a product decision, not a refactor.

Update user-facing documentation whenever a change affects installation,
workflow behavior, compatibility, security or governance.

Run the repository verification before requesting review, using the entry
point for your platform:

```bash
./validate.sh
```

```powershell
.\validate.ps1
```

Describe the test evidence in the pull request. If generative AI materially
assisted the design, implementation, testing or documentation, disclose that
assistance and the human review performed.

## Review and decisions

Review covers correctness, safety, scope, tests and documentation. For decision
ownership and escalation, read [Governance](GOVERNANCE.md). For a security
vulnerability, follow [Security](SECURITY.md) instead of opening an Issue.
