---
name: super-hero-simplify
description: Use when a completed change looks larger or more elaborate than its requirements need, or when the user asks for a simplicity review, to propose reductions that preserve accepted behavior.
---

# Super-Hero Simplify

An optional review that asks one question about a change that is already
correct: is any of this unnecessary?

## When to run it

Run it after correctness and safety are satisfied, unless the user explicitly
asks for a simplicity analysis earlier.

It is worth running when a change added a lot of surface for a small
requirement: many new files, a new dependency, a new abstraction layer,
configuration nobody asked for.

It is not worth running on a small, obvious change. Reviewing a two-line fix
for overbuild is itself overbuild.

## What to look for

- **Duplicate implementation.** Something in this repository already does
  this. Name the existing code.
- **Unnecessary abstraction.** An interface, base class, factory, registry or
  indirection layer with one implementation and no second caller in sight.
- **Unnecessary dependencies.** A new package for what the standard library,
  the platform, or an already-installed dependency does.
- **Speculative configurability.** Options, flags, hooks and extension points
  no accepted requirement asked for.
- **Indirection that buys no required property.** A layer is worth its cost
  only if it buys testability, a boundary, a performance characteristic or a
  safety property that is actually required. Name the property or drop the
  layer.
- **Avoidable new files and modules.** New structure where the change would
  read better beside the code it belongs to.

## What it must preserve

A simplification is invalid if it weakens any of these:

- accepted behavior and scope;
- required tests;
- security posture;
- accessibility;
- compatibility, including public interfaces;
- architecture the user or the repository decided on deliberately.

If a reduction would touch one of these, it is a scope question for the user,
not a simplification.

## Output

Report findings as proposals, most valuable first. For each one give the
location, what to remove or reuse, and what it costs to leave it in. Say
plainly when a proposal is a matter of taste rather than a real cost.

Then stop. Applying a proposal is ordinary work under `super-hero-core`, and a
change made here needs the same fresh test evidence as any other change: run
the tests after simplifying and report what they said.

If nothing is worth changing, say that. An empty result is a legitimate
outcome, and inventing findings to look useful is the failure mode of this
review.
