# Contributing to the Crinkl Protocol Specification

Thank you for improving the public specification. This repository describes
protocol behavior; it is not an implementation backlog or a release channel.

## Before opening a change

Read the applicable normative material first. When sources disagree, use the
authority order in [`08-governance/change-process.md`](08-governance/change-process.md):
external standards, normative protocol specification, formal invariants,
bindings and schemas, reference material, generated artifacts, then
implementations. The proof-lifecycle order in
[`08-governance/authority-hierarchy.md`](08-governance/authority-hierarchy.md)
also applies: downstream profiles cannot redefine Core behavior.

Classify the proposal before writing it:

- Normative changes affect portable semantics, validity, canonical bytes,
  hashes, signatures, state transitions, schemas, bindings, or verifier rules.
  They require the complete Boundary impact record from
  [`08-governance/protocol-business-boundary.md`](08-governance/protocol-business-boundary.md),
  appropriate versioning analysis, and conformance updates where behavior
  changes.
- Non-normative changes clarify or correct explanatory material without
  changing protocol behavior. Say why the change is non-normative and do not
  use it to imply a release, runtime availability, or adoption state.

A branch, draft, README, or candidate manifest is not a released protocol
identity. Follow [`08-governance/versioning.md`](08-governance/versioning.md)
for the accepted release and compatibility rules.

## Pull requests

Keep each pull request narrow and explain the affected authority, maturity, and
compatibility boundary. For normative changes, complete every line of the
Boundary impact section in the pull-request template; a blank answer is not a
classification.

Run the local checks that match the change and record the exact commands and
results in the pull request. For documentation-only changes, start with:

```bash
python3 scripts/check_drift.py
python3 scripts/check_successor_release_finalization.py --mode candidate
git diff --check
```

For changes to vectors, schemas, bindings, or verification behavior, also run
the relevant conformance command, for example:

```bash
node scripts/verify_conformance.mjs
```

Do not claim that GitHub Actions ran or are required by this guide. Local
evidence should state exactly what was run and what was not run.

## Security and sensitive information

Do not put vulnerabilities, exploit details, credentials, private keys, raw
receipts, personal data, or other sensitive evidence in a public issue or pull
request. Follow the private reporting process in [SECURITY.md](SECURITY.md).

## Conduct

By participating, you agree to follow the
[Code of Conduct](CODE_OF_CONDUCT.md).
