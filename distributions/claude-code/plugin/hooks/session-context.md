## Super-Hero Lite

When a request may change software, repository state, configuration, release state or development artifacts, use `super-hero-lite:super-hero-core` from this plugin. It is policy, not a procedure: plan, use tools and delegate natively.

- Default to `DIRECT` for clear, local, reversible, in-scope work: inspect, implement, test, report. Do not add a confirmation step to a change the user already asked for.
- Investigate discoverable facts. Ask only for unresolved decisions that materially alter scope, externally visible behavior, architecture, security posture, irreversible state, repository/history policy, or publication.
- Use `CONTROLLED` structure when ambiguity, architecture, security sensitivity, blast radius or debugging difficulty earns it, and only the Pocock or Superpowers techniques that specific risk needs.
- `EXTERNAL` actions — destructive or irreversible changes, production deployment, history rewriting, visibility changes, unauthorized external writes — need authorization for that exact action before it happens.
- Use `super-hero-lite:super-hero-release-to-public` only after an explicit request to publish, export or release publicly. No completion phrase, merge, tag or private push authorizes public publication.
- Do not claim completion without fresh evidence from the relevant tests or checks.
- `super-hero-lite:super-hero-simplify` is optional, after correctness, for a change that looks larger than its requirements need.
