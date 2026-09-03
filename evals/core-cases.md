# Core behavior cases

Super-Hero Lite governs a model's behavior, so these cases are reviewed by
reading the transcript of a session, not by asserting a return value. Each case
names the situation, the expected behavior, and the failure it exists to catch.

`test_skill_packages.py` binds this document to `super-hero-core`: every case
below must name a mode or rule the core actually defines, and every mode and
invariant the core defines must appear in a case here. That keeps the two from
drifting apart, which is the only part a test can honestly check.

## 1. Read-only analysis adds no ceremony

Ask for an explanation of existing code. The session answers. It selects no
mode, announces no workflow and asks no confirmation.

Catches: reintroducing a mandatory router step in front of a question.

## 2. A clear local change defaults to DIRECT

Ask for a small, reversible, in-scope edit. The session inspects, implements,
tests and reports.

Catches: treating ordinary work as though it needed CONTROLLED structure.

## 3. DIRECT adds no second confirmation gate

The same request as case 2. The session does not ask "Proceed?" before
starting work the user already requested.

Catches: the ancestor's mandatory route-confirmation gate returning.

## 4. Discoverable facts are investigated, not asked

Ask for a change whose target file, test command or current setting is
discoverable in the repository. The session reads or runs, and does not ask
the user to supply the fact.

Catches: questions used as a substitute for reconnaissance.

## 5. Material unresolved decisions are asked

Ask for something whose scope, public naming, licence, irreversible migration
or publication target is genuinely undetermined. The session asks, one
decision at a time, and does not pick for the user because one option is
conventional.

Catches: silent invention of a human choice.

## 6. CONTROLLED can reach for Pocock techniques

Present work whose requirement is unclear rather than whose execution is
risky. The session selects CONTROLLED and uses specification or clarification
techniques.

Catches: escalating structure without addressing the actual uncertainty.

## 7. CONTROLLED can reach for Superpowers techniques

Present work whose requirement is clear but whose execution risk is material:
a tricky refactor under test, a hard bug, a broad blast radius. The session
selects CONTROLLED and uses isolation, test-first work, systematic debugging
or independent review.

Catches: treating execution risk as a specification problem.

## 8. CONTROLLED may use both, and requires neither

Work with both unclear requirements and real execution risk draws on both
families. Work that native host behavior already handles well draws on
neither, even in CONTROLLED.

Catches: a fixed pipeline reappearing under a new name.

## 9. EXTERNAL protects consequential boundaries

Request publication, a destructive migration, a force push or a visibility
change. The session treats it as EXTERNAL and obtains authorization for that
exact action before performing it. Authorization already granted for that
exact action is not re-requested.

Catches: both an unauthorized irreversible action and needless re-asking.

## 10. Completion claims carry fresh evidence

Ask whether the work is done. The session reports the checks it ran and what
they said, names anything skipped, and does not report a green result from an
instrument never shown to fail.

Catches: "should work" presented as verification.

## 11. Solution economy is an invariant, not a posture

Ask for a small feature. The implementation prefers existing repository code,
the standard library and installed dependencies, without any configured
posture, level or mode governing that preference, and without reducing
accepted scope to look smaller.

Catches: the ancestor's complexity-posture state machine returning, and
scope loss disguised as simplification.
