---
status: draft
layer: portability
version: v1
normative: false
---

# W3C VC 2.0 Spend Attestation candidate bundle

Profile release state: candidate.

This is a source-only candidate bundle for the optional W3C VC 2.0 Spend
Attestation wire form. It is present in the unpublished `v1.0.0-rc.5`
candidate conformance suite. It does not change the immutable released
`v1.0.0-rc.4` manifest or tag, and it does not activate runtime behavior. The
rc.7/suite-4 source candidate retains this candidate bundle without changing its
independent release or runtime boundary.
The candidate review applies only to public-spec commit
`81237937833ab32e5ce92d3b5ceed72854baecef` / tree
`9121bdfbfc428f73557e993f1bd6e295ba733a12`; later source is unassigned.

Issuers can use opt-in dual issuance: issue the native Spend Attestation Token
and, where this profile is enabled, the matching
`SpendAttestationCredentialV1`. Native verification remains independent; the
credential is an additional bearer, correlatable wire form and is not a
replacement for native tokens.

The bundle preserves the adopted engineering source layout under its root.
Its verifier first checks each pinned source artifact and the public binding
transform, then executes the adopted checkers:

```bash
python3 07-conformance/profiles/w3c-vc-2.0-spend-attestation-v1/scripts/check_w3c_vc_2_0_spend_attestation_bundle.py
node 07-conformance/profiles/w3c-vc-2.0-spend-attestation-v1/scripts/check_w3c_spend_attestation_credential_vectors.mjs
node 07-conformance/profiles/w3c-vc-2.0-spend-attestation-v1/scripts/generate_w3c_bitstring_status_list_vectors.mjs
node 07-conformance/profiles/w3c-vc-2.0-spend-attestation-v1/scripts/check_w3c_bitstring_status_list_vectors.mjs
python3 07-conformance/profiles/w3c-vc-2.0-spend-attestation-v1/conformance/w3c-vc-2.0/v1/validate_draft202012.py --check
```

The Python schema check requires the `jsonschema` package. The commands use
only checked-in fixtures and do not fetch an issuer, context, status list, or
refresh endpoint.

The pinned applicable official self-cell evidence records 32 passing rows and
8 pending profile-optional or upstream-skipped rows. This is not a claim of
complete official-suite conformance or peer interoperability. It also makes no
claim of a generic VC/VP API, live `did:web`, immutable context, signed status
list, or refresh endpoint; runtime adoption, QA, release, and production
authority remain separate gates.

Publication state: P4.4 exact-candidate review and P9 accepted public-release authority remain blockers.
The endpoint, runtime, QA, and production blockers above remain unchanged.

The copied official-suite manifest and execution-evidence files are immutable
publication receipts, not a portable test runner. Reproduce that source-bound
self-cell from `crinkl-protocol` at the exact engineering commit recorded in
`manifest.json`; its adapter provenance checks intentionally depend on the
protocol repository's Git history.
