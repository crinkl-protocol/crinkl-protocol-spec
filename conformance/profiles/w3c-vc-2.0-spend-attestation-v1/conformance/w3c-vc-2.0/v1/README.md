# W3C VC 2.0 Spend Attestation Profile V1

This profile fixes one deterministic `SpendAttestationCredentialV1` fixture,
its `eddsa-jcs-2022` proof, an example DID document, a signed retained
issuer-key-history chain, and signed Bitstring Status List fixtures. The fixture uses
an example issuer and public test key material. It does not assert a live
`did:web`, context, status-list, or refresh endpoint.

The profile is an optional bearer, correlatable wire form. It carries no
wallet, recipient handle, holder binding, ZK proof, or private witness. Native
tokens remain independently verifiable artifacts and may be issued alongside a
credential.

The status resolver retains deterministic signed
`BitstringStatusListCredential` fixtures for the Spend credential's
`revocation` and Crinkl product-profile `refresh` entries. Each list is at
least 16,384 uncompressed bytes and uses canonical `u` multibase
base64url-without-padding over a valid gzip stream. Index zero is the most
significant bit of byte zero. Fixture generation uses a deterministic stored
DEFLATE representation, but verification accepts any standards-conforming
gzip representation within the Crinkl profile's 1 MiB compressed and decoded
safety caps; those caps are not W3C requirements.
The checker rejects indexes beyond the 1 MiB capacity before numeric
conversion and bounds proof/Multikey text before base58 decoding.

Every status credential has an `eddsa-jcs-2022` proof authorized by the
status-only key appended in issuer-history sequence 2. The sequence-0 and
sequence-1 key records remain byte-for-byte unchanged, and the current DID
adds the status method for discovery only. The checker validates schema and
format, issuer, subject/list URL, purpose, proof context/configuration,
signature, history reference, key scope/purpose/time, canonical encoding,
gzip, length, and exact MSB-first bit extraction. Revocation and refresh bits
are irreversible: a newer authenticated retained version cannot shrink the
list or clear a bit set by an older version.

The offline resolver descriptor is pinned out of band by its JCS SHA-256
snapshot digest. Each retained credential is also bound by its own JCS SHA-256
digest. Signatures authenticate supplied versions but cannot prove collection
completeness. A runtime verifier therefore needs either a caller-pinned or
durably persisted per-list high-water state, or fresh trusted retrieval, and
must fail closed if a newer version may have been omitted. Freshness applies
to the uniquely selected newest version; older retained predecessors remain
authenticated inputs to the irreversible-bit check.
`issuer-history-trust-root.v1.json` is an out-of-band pinned trust root. The
bootstrap, Spend-current, and status-current histories are content-addressed with JCS SHA-256 and are
signed by its isolated Ed25519 root key. The fixture checker rejects an
unpinned root, signature or hash tampering, rollback, broken predecessors,
same-sequence equivocation, and append-only violations. Historical proof keys
are intentionally absent from the current DID fixture; retained history is the
historical authorization source.

The credential signs the bootstrap history reference that was available at
issuance. Verification authenticates that issuance reference in the chain and
separately applies the pinned current high-water history, including any later
append-only tightening of the historical key's `validUntil`. The trust-root
fixture represents verifier-local pinned state; it is not resolver data.
The issuance reference must lie on the selected history's exact predecessor
path; the checker rejects a root-signed side branch and any supplied sequence
greater than the selected high-water.
For a valid newer successor, the checker models the required durable atomic
high-water compare-and-advance and proves that acceptance fails closed when
that operation fails, is non-durable, is uncertain, or conflicts. It also
checks retry, restart after persisted success, and the deliberate rule that an
invalid or schema-invalid credential cannot roll back independently
authenticated history.

The checkers invoke `validate_draft202012.py` for every acceptance decision.
That helper uses `jsonschema.Draft202012Validator` with `FormatChecker` against
the closed credential and issuer-history schemas. It then checks RFC 8785
serialization, Ed25519 proofs, protected-context shape, historical key
authorization, native-token source linkage, signed status-list resolution,
and required negative cases.

`check_w3c_spend_attestation_credential_vectors.mjs` is explicitly a
`CONFORMANCE_FIXTURE_HARNESS_NOT_GENERIC_VERIFIER`. A generic
`@crinkl/verify` interface is deferred: it must accept caller-supplied issuer
history/status resolvers, a pinned issuer-history trust store, acceptance
policy, and verification time. This fixture does not claim conformance against
the complete official W3C test suites. The separate source-bound self-cell
under `official-suite/` executed 13 applicable EdDSA-JCS rows and 19 applicable
Bitstring Status List rows, with 8 profile-optional or upstream-skipped rows
pending and none failing. Its two interoperability rows are self-cells, not
peer interoperability. It does not exercise generic VC/VP APIs, the product
`did:web` and retained-history path, runtime binding, deployment, release,
production activation, or live endpoint availability.

Run:

```bash
node scripts/check_w3c_spend_attestation_credential_vectors.mjs
node scripts/generate_w3c_bitstring_status_list_vectors.mjs
node scripts/check_w3c_bitstring_status_list_vectors.mjs
```

These commands require Node.js and Python with the `jsonschema` package
available; it does not fetch a context, DID, status list, or refresh endpoint.
