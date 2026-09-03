# Public-release verification

`super-hero-core` states the general rule once: no completion claim without
fresh evidence. This file is not a restatement of it. It is the release-specific
checklist of the checks publication itself requires, each of which exists
because publication cannot be undone.

## Required

- source repository identity and PRIVATE visibility verified;
- source exact SHA recorded;
- release contract valid;
- source and target are distinct repositories;
- staged tree created from the committed source revision;
- release-control and private paths absent from the staged tree;
- a real secret scan passes;
- the forbidden-literal scan passes;
- licence, version and readme consistency passes;
- required tests pass in the isolated staging context;
- the required build passes in the isolated staging context;
- the public diff has been reviewed;
- the target branch's remote head is unchanged immediately before the push;
- explicit final `PUBLISH` confirmation obtained;
- the public target's commit, tag and visibility verified after the push;
- the private source's visibility re-verified as PRIVATE after publication.

## Fail closed

A scanner warning, an unexpected file, a forbidden literal, target divergence
or a failed test or build blocks publication until it is resolved. "Probably
safe" is not a verification result.
