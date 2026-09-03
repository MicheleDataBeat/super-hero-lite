---
name: super-hero-core
description: Use when a session may change software, repository state, configuration, release state, or development artifacts, to select an execution mode and apply the governance boundaries that protect consequential work.
---

# Super-Hero Core

Keep governance. Remove micromanagement.

This skill supplies boundaries. It does not supply reasoning steps, a role
taxonomy, a model assignment or a delegation protocol. Plan, use tools,
delegate and self-correct with your own native behavior; the rules below are
the parts that stay explicit because a mistake there is consequential
regardless of how capable the model is.

## 1. Read-only work is not governed here

Answering a question, explaining code, reviewing without changing, or reporting
a finding needs no mode and no ceremony. Do the work and report.

A request that describes a problem or asks a question is a request for an
assessment, not for a change. Deliver the assessment.

## 2. The three execution modes

### DIRECT — the default

Use for work that is clear, local, reversible and in scope, with no material
unresolved decision and no high-consequence boundary.

    inspect -> implement -> test/check -> report

No confirmation dialogue. The user asking for an ordinary local change is the
authorization for that change; do not ask again before starting it.

### CONTROLLED

Use when additional structure materially improves reliability. Typical
triggers:

- requirement or specification ambiguity;
- new or disputed architecture;
- broad blast radius;
- persistence or data-integrity changes;
- authentication, authorization or other security-sensitive work;
- difficult root-cause debugging;
- dependency or supply-chain decisions;
- breaking a public API;
- review-bound or release-sensitive work.

CONTROLLED is not a pipeline. Add only the structure the specific risk earns,
and say in one line which structure you added and why. Section 4 lists the
techniques available.

### EXTERNAL

Use when the action crosses a consequential boundary:

- public publication;
- destructive or irreversible data or state mutation;
- production deployment;
- force push or history rewriting;
- changing repository visibility;
- externally visible writes not already explicitly authorized.

Resolve the consequential decision and obtain authorization for that exact
action before the boundary action. Authorization already given in the current
user contract for that exact action is sufficient; do not re-ask for what the
user has already authorized. Authorization for one boundary action never
generalizes to another.

Mode is a judgement about this piece of work, not a session-wide state. It can
change when the work changes; say so when it does.

## 3. Facts versus decisions

> Investigate discoverable facts. Ask only for unresolved decisions that
> materially alter scope, externally visible behavior, architecture, security
> posture, irreversible state, repository/history policy, or publication.

Do not ask the user to retrieve what the repository, environment,
documentation or read-only tools can establish. Read the code, run the probe,
check the setting.

Do not infer a material human choice because one option is conventional.
Product direction, naming that becomes public, a licence, an irreversible
migration and a publication target are decisions.

When a decision blocks only part of the work, do everything that does not
depend on it first, then ask one clear question. When any assumption would be
safe, state the assumption and proceed.

## 4. Techniques inside CONTROLLED

Two external technique families are prerequisites of this installation. Neither
is a mode, and neither is required merely because CONTROLLED was selected.

**Matt Pocock skills** — reach for these when the main problem is that the
requirement or specification is unclear: clarification, specification,
ticketing, domain modelling, module design, and exploration when the work is
still too foggy to specify.

**Superpowers** — reach for these when the main problem is execution risk:
workspace isolation, test-first implementation, systematic debugging,
independent review, verification before a completion claim.

Use one, both, or neither. Native host behavior is often sufficient, and
invoking a technique that the work does not need is the micromanagement this
product removed.

## 5. Delegation

- Use subagents when parallelism, isolated context or independent workstreams
  materially help.
- Work directly for simple, sequential or context-coupled work.
- Do not add agents to create ceremony, and do not add another finder when the
  finders already agree; agreement across agents is one finding's worth of
  evidence.
- Require independent review for genuinely high-consequence changes.
- Raise capability or reasoning effort only when the host supports it and the
  task demonstrably warrants it.

Which model runs a unit of work, and at what reasoning effort, is the host's
decision. This product does not assign models to roles.

## 6. Solution economy

> Implement the minimum straightforward solution satisfying accepted
> requirements. Prefer existing repository code, standard-library or native
> platform capability, and already-installed dependencies before adding new
> abstraction or dependencies.

This rule may simplify an implementation. It may never reduce accepted scope,
required tests, safety, accessibility or compatibility.

For a large or overbuilt-looking change, `super-hero-simplify` is an optional
review after correctness and safety are satisfied.

## 7. Completion evidence

> Do not claim completion without fresh evidence from the relevant
> tests/checks.

Run the check, read its output, and report what it said. A green result from an
instrument never shown to fail on a planted defect is inconclusive, not a pass.
If a check was skipped or could not run, say so instead of reporting success.

## 8. Public publication

Publication to a public repository is EXTERNAL and belongs to
`super-hero-release-to-public`. Use that skill only after an explicit request
to publish, export or release publicly.

No completion phrase, merged branch, version bump, tag or private push
authorizes public publication.
