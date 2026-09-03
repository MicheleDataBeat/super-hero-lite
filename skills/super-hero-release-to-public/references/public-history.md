# Public history policy

## Initial publication

Create the public repository as a clean distribution history built from the
sanitized snapshot. Never import, filter, rewrite, mirror, or otherwise
transfer the private commit graph. This invariant is absolute: a user decision
may govern rewriting existing public-only target history, but can never
authorize transferring private history.

Preferred result:

```text
public main
  A  Initial public release <version>
```

The private source SHA may be kept in private release records. Do not expose it
in the public commit message by default.

## Subsequent publication

Preserve public-only history:

```text
public main
  A  Initial public release 1.0.0
  B  Release 1.1.0
  C  Release 1.2.0
```

Each public commit is produced by overlaying the newly sanitized snapshot onto
the latest verified public branch, reviewing the diff, and committing the
public delta. That gives useful public history without leaking private
development archaeology.

## Existing conflicting target

If the target already holds unrelated history, unexpected files, other
people's commits or a diverged publication model, stop before any mutation and
ask. Never erase existing public history merely to make the desired snapshot
fit.

## Force push

Default: forbidden.

A force push requires a separate explicit user decision, a fresh assessment of
the history-rewrite risk, and fresh remote-head verification immediately
before the push.
