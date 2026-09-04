# Sanitization policy

## Default private and control-plane candidates

These are candidates for exclusion, not proof that every project should
exclude them. Persist the final policy in the release contract:

- `.release/**`
- `.scratch/**`
- `.codex/**`
- agent-only `.agents/**` material
- private planning documents
- private decision records not intended as product documentation
- local environment files (`.env*`), except intentionally public examples such
  as `.env.example`
- internal test fixtures containing non-public data
- private operational or runbook material
- internal branding assets or names

## Secret handling

A private repository is not permission to publish secrets accidentally.

Required before a public push:

1. a real secret scanner over the staged tree;
2. contract rules denying obviously secret-bearing files;
3. a scan for explicit forbidden literals and identifiers;
4. inspection of the public diff;
5. fail closed on any suspicious finding until it is resolved.

Never paste a discovered secret into a message, Issue, log or contract. Refer
to the file, path and finding category without reproducing the secret.

## Branding

Brand transformations must be explicit mappings:

```yaml
branding:
  replacements:
    - from: "InternalProjectName"
      to: "PublicProjectName"
  forbidden_literals:
    - "OldCompanyLiteral"
    - "InternalProjectName"
```

After the mappings are applied, the forbidden-literal scan must come back
clean. Binary assets with ambiguous branding need inspection or a user
decision, not blind string replacement.

## Public-facing completeness

Sanitization must not leave the public project broken. Verify that readme
links, package metadata, import paths, CI files, badges, licence references,
screenshots, assets and build commands still make sense after every removal
and replacement.
