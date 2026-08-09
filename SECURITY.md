# Security Policy

## Private reporting

Report a suspected specification vulnerability privately through
[GitHub Private Vulnerability Reporting](https://github.com/crinkl-protocol/crinkl-protocol-spec/security/advisories/new).
Do not post vulnerability details in a public issue, pull request, discussion,
or conduct report.

This policy does not state a response or remediation SLA. Reporters and
maintainers should coordinate disclosure privately and avoid public disclosure
until they agree that a remediation or disclosure plan is ready.

## Scope

Use this channel for defects in this repository's specification that could
affect verification, canonical bytes, signatures, authorization, version
handling, conformance interpretation, privacy, or the safe handling of portable
proofs. Include the exact document, schema, vector, binding, tag, or commit
where the issue appears.

This channel is not the intake for a bug solely in an implementation repository,
service, deployment, SDK, or application. Report an implementation-only issue
through the affected repository's own security process. If a specification
defect is the root cause, explain that boundary in the private report.

## Version and maturity boundary

State which artifact is affected:

- `v1.0.0-rc.4` is the immutable released tag.
- Current `main` is repository source and can contain work beyond that tag.
- `v1.0.0-rc.5` is the historical exact reviewed source candidate
  (`REVIEWED_CANDIDATE_NOT_PUBLISHED`), not a tag, GitHub Release, runtime
  activation, or production deployment.
- `v1.0.0-rc.7` is the current unreviewed source candidate and conformance
  suite 4 (`RELEASE_CANDIDATE_NOT_PUBLISHED`); it is unpublished and not
  publishable until separately reviewed.

The reviewed rc.5 source is exactly commit
`81237937833ab32e5ce92d3b5ceed72854baecef` / tree
`9121bdfbfc428f73557e993f1bd6e295ba733a12`; later source is unassigned.

Do not infer a release, deployment, or runtime claim from a report against
current `main`, the current rc.7 source candidate, or the historical exact
reviewed rc.5 candidate.

## Minimum safe report

Provide only the minimum evidence needed to reproduce and assess the issue:

- affected version, tag, commit, and artifact path;
- a concise description of the verification or privacy impact; and
- a minimal, benign reproducer or test case where safe.

Do not include credentials, private keys, tokens, raw receipts, wallet or
account identifiers, personal data, production secrets, or exploit material
that is unnecessary for assessment. Redact or replace sensitive values with
synthetic data.
