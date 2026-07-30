---
status: draft
layer: lifecycle
version: v1
normative: true
---

# Validator Signing-Key Independence

This page defines one registry and quorum invariant for all proof-validator
surfaces in this specification. It is not a verifier-specific variant. Neither
the platform implementation nor the proof-validator implementation becomes
normative merely because it shipped first; implementations conform to this
rule.

## Registry Invariant

A validator registry row is a registration record, not an independent
cryptographic actor. In one accepted registry view, every active signing key of
every active validator MUST resolve to a distinct Ed25519 public key.

Key identity is the canonical raw 32-byte Ed25519 public key. A different
`validatorId`, `keyId`, wrapper, encoding layout, or caller-supplied hash does
not create a second cryptographic identity for the same key bytes.

Two active rows that resolve to one public key make the registry view invalid.
The verifier MUST reject the view as `DUPLICATE_ACTIVE_SIGNING_KEY`. It MUST
NOT:

- count both rows;
- choose one row and ignore the other;
- lower or recompute the quorum threshold from a deduplicated row count; or
- mutate a local registry copy to force acceptance.

Inactive historical rows MAY retain a formerly active key. They have no current
signing or quorum authority.

The registry authority signature authenticates the registry bytes; it does not
make an aliased registry safe. Registry authenticity and signing-key
independence are separate mandatory checks.

## Enforcement Boundaries

A conforming implementation MUST enforce the invariant:

1. when parsing a validator registry snapshot;
2. when authenticating the authority-signed registry bundle; and
3. at each signature-quorum verification boundary.

The third check is defense in depth for callers that supply an already-decoded
registry object or a certificate assembled outside the canonical parser.

## Quorum Counting

Every registry-backed validator quorum MUST require:

1. the exact pinned registry and assignment view;
2. an active selected validator and active signing key for each signature;
3. a valid Ed25519 signature over the surface-specific preimage;
4. distinct validator ids;
5. distinct canonical Ed25519 public keys; and
6. the threshold to be met by those distinct verified keys.

Distinct validator ids or key ids alone are insufficient. If two records use
different ids but verify with the same key, the second record contributes no
additional quorum weight and the artifact MUST reject.

This rule applies to proof finality, aggregate finality, GMV price evidence,
evidence-checkpoint countersignatures, participation certificates, and any
future validator quorum resolved through the validator registry.

## Strict-BFT Example

For `N` selected validators, v1 strict BFT requires:

```text
required = floor(2 * N / 3) + 1
```

For 1,000 valid selected validators, quorum requires 667 distinct verified
Ed25519 public keys. A registry with 1,000 active rows but only 999 distinct
active keys is invalid. It is neither a valid 1,000-member committee nor an
automatically resized 999-member committee.

## Activation and Failure

Before activating this tightening, an operator MUST inspect the exact
authority-signed registry intended for activation and verify that all active
rows have distinct canonical keys. One node's local snapshot is evidence only
for that snapshot and MUST NOT be described as a network-wide observation.

An active key alias is a deterministic semantic failure, not a transport or
liveness failure. A verifier MUST retain the conflicting signed artifact as
diagnostic evidence and wait for an authority-signed successor registry. It
MUST NOT infer that an unseen remote validator is offline or manufacture
replacement signatures.

