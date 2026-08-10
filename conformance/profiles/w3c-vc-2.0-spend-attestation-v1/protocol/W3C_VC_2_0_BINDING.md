# W3C Verifiable Credentials 2.0 Binding

`SpendAttestationCredentialV1` is an optional W3C Verifiable Credential 2.0
wire form for an authenticated canonical Spend head. The native Spend
Attestation Token remains the portable artifact for native verification. A
credential MAY be issued alongside the matching native token. The credential
source includes an authenticated canonical-head context because the native
token does not carry its stream namespace; neither artifact validates the
other's signature.

This profile is adopted protocol source only. It does not authorize a live
context, DID, status-list, refresh, package, or runtime endpoint.

## Credential subject and identity exclusion

The subject is one canonical spend stream, never a person, wallet, holder, or
recipient. Its canonical identity is the exact tuple:

```text
(spendStreamNamespaceRef, issuerId, spendId)
```

`credentialSubject.id` is:

```text
urn:crinkl:spend:<namespace-component>:<issuer-component>:<spend-component>
```

Each component is the UTF-8 input value encoded byte-for-byte with RFC 3986
percent encoding: ASCII letters, digits, `-`, `.`, `_`, and `~` remain literal;
every other byte is `%` followed by two uppercase hexadecimal digits. The
colons between components are separators and are not part of a component.
This representation preserves the distinction between equal `spendId` values
from different issuers or stream namespaces.

`credentialSubject` MUST contain `spendStreamNamespaceRef`, `issuerId`, and
`spendId` in addition to its identifier. VC issuance requires authenticated
canonical-head context for that exact composite key. A legacy portable token
alone does not carry its stream namespace and is therefore not a lossless VC
conversion source. It MUST NOT contain `wallet`,
`recipientId`, `holderBinding`, a holder key, a ZK proof, a witness, receipt
text, or an ingestion reference. The credential is therefore a bearer and
correlatable claim about a spend event; it does not prove holder control.

Initial issuance is permitted only for a `HARD_VERIFIED` or `CORRECTED`
canonical head. An `INVALIDATED` head MUST NOT produce a new credential.
Invalidation of an already issued credential is represented by its irreversible
revocation status entry.

## Credential shape

The protected context source is `context/spend-v1.jsonld`. A published
deployment MUST serve its immutable bytes as `application/ld+json` at
`https://crinkl.xyz/ns/spend/v1`; this source artifact alone does not assert
that the endpoint is live.

Credentials MUST use the ordered context and type values below:

```json
{
  "@context": [
    "https://www.w3.org/ns/credentials/v2",
    "https://crinkl.xyz/ns/spend/v1"
  ],
  "type": ["VerifiableCredential", "SpendAttestationCredential"]
}
```

`id` MUST equal `urn:crinkl:token:<native-token-hash>`, where the native hash
uses the normal native unsigned-token hash procedure. `validFrom` and
`credentialSubject.occurredAt` MUST equal the canonical spend timestamp.
`validUntil` MUST be absent. `proof.created` records VC issuance time and MUST
NOT be substituted for the spend timestamp. It MUST NOT precede `validFrom`.

The binding is a constrained outward projection. Issuance requires a complete
accepted or corrected canonical head carrying every mapped field below. Native
`date`, `geoRegion`, and `cbsaCode` are not represented, and a credential MUST
NOT be converted back into a native token. `totalCents` retains the native
`Amount` JSON-string representation and decimal grammar; it is not converted
to a JSON number.

The credential subject maps the canonical claim as follows:

| Native/canonical claim | Credential property |
|---|---|
| stream namespace | `credentialSubject.spendStreamNamespaceRef` |
| issuer | `credentialSubject.issuerId` |
| spend ID | `credentialSubject.spendId` |
| status | `credentialSubject.verificationState` |
| store hash | `credentialSubject.storeHash` |
| timestamp | `credentialSubject.occurredAt`, `validFrom` |
| total cents | `credentialSubject.totalCents` |
| currency | `credentialSubject.currency` |
| verification version | `credentialSubject.verificationVersion` |
| protocol version | `credentialSubject.protocolVersion` |
| lineage head and count | `credentialSubject.lineage` |

`lineage` has a protected scoped JSON-LD context. Its `headEventHash` and
`eventCount` terms resolve to the Crinkl namespace and the latter has the
`xsd:integer` type. The credential profile does not rely on an unscoped or
application-defined interpretation of this nested object.

## Issuer authorization and key history

`issuer` MUST be a `did:web` identifier. The intended production issuer identifier is
`did:web:crinkl.xyz`; the conformance fixture uses an example DID and asserts
no live DID document.

A current verification method MUST be a `Multikey` carrying one Ed25519 public key as
`publicKeyMultibase`. The multicodec prefix is `0xed01`; the bytes are encoded
with base58-btc multibase and prefixed with `z`. The method MUST be listed in
the current DID document's `assertionMethod` relationship.

The current DID document is a controlled mutable discovery surface. Historical
verification MUST resolve the proof method through a retained immutable
`W3CIssuerKeyHistoryV1` artifact. That artifact is the authority for issuer
control, `assertionMethod` authorization, artifact type, and key validity at
`proof.created`; the current DID document MUST NOT be required to retain a
retired fragment, and temporary unavailability of the current DID document
MUST NOT by itself invalidate a historically authorized proof. Each rotation
uses a new fragment identifier; retired fragments are never reused.
`refreshServiceBaseUrl` in the retained issuer
history supplies the refresh-service origin for credentials issued under that
history.

For issuer-history hashing, clone the complete artifact, remove `historyId` and
`signatures`, and compute `historyDigest = SHA-256(JCS(unsignedHistory))`.
`historyId` MUST equal `sha256:<lowercase-hex-historyDigest>` and
`signatures.historyHash` MUST equal the same lowercase hexadecimal digest
without the `sha256:` prefix. `signatures.signature` MUST be the canonical
base64 encoding of a pure Ed25519 signature over the raw 32-byte
`historyDigest`.

The credential proof MUST carry the `issuerHistoryRef` that was authenticated
and available when the credential was issued. The referenced history MUST be
on the exact predecessor path from the verifier's selected accepted high-water
history to its pinned bootstrap, and its `publishedAt` MUST NOT be later than
`proof.created`; a separately root-signed side branch is not sufficient. The
reference is part of the signed proof configuration. The selected history MUST
have the greatest sequence among the authenticated artifacts supplied for the
decision. The verifier applies any later, append-only `validUntil` tightening
from that selected path when evaluating the proof key and MUST confirm that
the retained key identifier, verification method, public key, activation time,
artifact scope, and proof purpose still match the issuance history.
An out-of-band pinned
issuer-history trust root identifies the issuer-history root verification
method, root public key, bootstrap history reference, minimum sequence, and
the verifier's accepted high-water mark. Verifiers MUST reject a chain with an
untrusted root, invalid content hash or root signature, missing or broken
predecessor, sequence rollback, same-sequence equivocation, or a change to an
existing key other than tightening its `validUntil`. The issuer-history root
key and credential proof keys are distinct roles: a proof key MUST NOT be
accepted as a history root.

If the selected authenticated history is newer than the verifier's stored
high-water mark, the verifier MUST durably and atomically compare-and-advance
the `(sequence, historyRef)` pair before it reports acceptance or performs any
relying-party action. Concurrent decisions MUST serialize on that pair. A
failed, unavailable, or uncertain persistence result is
`issuer_history_state_unavailable` and MUST fail closed; an implementation MUST
NOT accept in memory and persist later. A stored greater sequence, or the same
sequence with a different reference, is rollback or equivocation and MUST be
rejected.

This state transition records acceptance of independently authenticated issuer
history, not acceptance of the presented credential. Once the history succeeds
and the durable pair advances, a later schema, shape, proof, mapping, status, or
policy failure for that credential MUST NOT roll the pair back; even a
schema-invalid credential cannot suppress an authenticated key retirement.

Within one history artifact, every `keyId` and `verificationMethod` MUST be
unique, every `publicKeyMultibase` MUST be unique, and each method MUST equal
`<issuer>#<keyId>`. Public-key material retired under one fragment MUST NOT be
reauthorized under a new fragment. Duplicate, reused, or mismatched key
identities make the history ambiguous and MUST be rejected.

## Data Integrity proof

The credential MUST carry a `DataIntegrityProof` with cryptosuite
`eddsa-jcs-2022`, proof purpose `assertionMethod`, and a base58-btc multibase
`proofValue` beginning with `z`.

Proof generation is deterministic for a fixed credential, proof configuration,
and Ed25519 key:

1. Remove `proof` to form the unsecured document.
2. Copy the credential's complete ordered `@context` value into
   `proof.@context` and retain that field in the final proof.
3. Form the proof configuration from all proof fields except `proofValue`.
   `proof.@context` MUST be byte-for-byte equal to the credential context,
   including its two-item array order.
4. Compute `proofConfigHash = SHA-256(JCS(proofConfiguration))`.
5. Compute `transformedDocumentHash = SHA-256(JCS(unsecuredDocument))`.
6. Sign `proofConfigHash || transformedDocumentHash` with pure Ed25519.
7. Encode the 64-byte signature as base58-btc multibase.

Omitting the context-copy step, altering either context, or changing its
prefix order creates different signed bytes and MUST be rejected. The
conformance profile records the divergent proof value made without the copy.

## Media type

An HTTP representation of a conforming credential under this profile MUST use
`Content-Type: application/vc`. A client requesting this representation SHOULD
send `Accept: application/vc`. The context document remains a separate
`application/ld+json` resource as specified above.

## Corrections, invalidations, and status

Every credential carries two ordered `BitstringStatusListEntry` objects: a
`revocation` entry followed by a `refresh` entry. An `INVALIDATED` canonical
head is represented by a set revocation bit and MUST be rejected for current
acceptance. A set refresh bit means the credential remains authentic but is not
current; the verifier MUST resolve the canonical head through `refreshService`
or return an indeterminate freshness result. Neither bit alters historical
proof bytes.

A `CORRECTED` head is a superseding claim and MUST NOT be marked revoked only
because a later head exists. Every credential MUST carry a `refreshService`
for its exact canonical stream identity; a corrected credential uses that
service to obtain the current head:

```json
{
  "refreshService": {
    "id": "<refreshServiceBaseUrl>/tokens/<namespace-component>/<issuer-component>/<spend-component>/head",
    "type": "CrinklSpendHeadRefresh"
  }
}
```

`refreshServiceBaseUrl` is the exact immutable issuer-history value and MUST
NOT end in `/`. The namespace, issuer, and spend path components use the same
RFC 3986 encoding as `credentialSubject.id`. The status-list credential and
retained historical status-list versions are
immutable signed artifacts. Current status-list and refresh locations are
controlled mutable pointers. A verifier requires an explicit freshness policy
and applicable retained status evidence; it MUST NOT treat a mutable HTTP
response as native protocol truth.

Both entries resolve a VCDM 2.0 `BitstringStatusListCredential` with the exact
ordered context triple `[https://www.w3.org/ns/credentials/v2,
https://www.w3.org/ns/credentials/status/v1,
https://crinkl.xyz/ns/spend/v1]`; `proof.@context` MUST equal that complete ordered value. The
credential carries an `eddsa-jcs-2022` assertion proof. Its subject identifier
MUST equal the credential identifier
plus `#list`; issuer, list URL, purpose, proof context/configuration, issuer
history, key scope, key purpose, key validity, and signature MUST all match the
requested entry. The status-list proof key is a distinct
`BITSTRING_STATUS_LIST_CREDENTIAL`-only key in retained issuer history. Its
presence in the current DID is discovery only and does not replace history
authorization.

`encodedList` MUST be canonical `u` multibase base64url without padding over a
valid gzip stream. The uncompressed bitstring MUST contain at least 16,384
bytes. Status index zero is the most-significant bit of byte zero; within a
byte, index interpretation proceeds from most-significant to least-significant
bit. Implementations MUST bound compressed input and decoded output before
using the list. The conformance harness uses 1 MiB caps as Crinkl profile
safety limits; those caps and its deterministic stored-DEFLATE fixture encoding
are not W3C interoperability requirements, and a verifier MUST accept other
standards-conforming gzip encodings within its declared bounds.
Under that 1 MiB decoded cap, an index greater than `8388607` is out of range
and MUST be rejected lexically before arbitrary-precision conversion. A
verifier MUST also bound base58 input before decoding: an Ed25519 proof value
under this profile is at most 89 characters including its `z` prefix, and an
Ed25519 `publicKeyMultibase` is exactly 48 characters.

For both `revocation` and `refresh`, a set bit is irreversible. Across retained
authenticated versions ordered by `validFrom`, each newer decoded bitstring
MUST be at least as long as, and a bitwise superset of, every older version. A set-to-clear transition is
invalid even when the newer credential has a valid signature. `refresh` is a
Crinkl product-profile use of the status mechanism and does not change the
standard semantics or claim an official W3C refresh profile.

Offline resolution requires an immutable resolver snapshot pinned by the
caller and content hashes for every retained signed credential. Credential
signatures authenticate the versions supplied; they do not prove that the
collection is complete. A runtime verifier MUST therefore persist and pin a
per-list high-water state or perform fresh trusted retrieval, and MUST fail
closed if omission of a newer version cannot be excluded. Freshness age is
applied to the uniquely selected newest version. Older retained versions are
still authenticated and decoded to enforce irreversible-bit history.

## Conformance profile

`conformance/w3c-vc-2.0/v1` contains a deterministic public fixture and an
executable conformance-fixture harness, not a generic verifier. It invokes an
actual Draft 2020-12 validator with format checking before every acceptance
decision and covers a valid proof; modified subject
and proof configuration fields; missing or misordered contexts; identity-handle
rejection; the proof value created without the context-copy step; and signed
revocation/refresh Bitstring Status List credentials with bounded decoding,
MSB-first index evaluation, retained-version monotonicity, and rollback
failures. A separate pinned Node.js 22 self-cell has executed the applicable
official EdDSA-JCS and Bitstring Status List rows: 32 passed and 8
profile-optional or upstream-skipped rows remain pending, with no failures.
That evidence is source-bound under
`conformance/w3c-vc-2.0/v1/official-suite` and is not peer interoperability,
complete official-suite conformance, generic VC/VP API capability, generic
verifier adoption, runtime binding, deployment, release, production
activation, or live endpoint availability.

A generic `@crinkl/verify` interface is deferred. Before it is adopted, it
MUST take explicit caller-provided issuer-history and status resolvers, a
pinned issuer-history trust store, a caller-pinned or durably persisted status
high-water, acceptance policy, and verification time;
it MUST NOT silently make the fixture's test resolver a runtime trust source.

The credential and issuer-history schemas are deliberately closed profiles:
`additionalProperties: false` freezes the V1 interoperability surface. A later
VCDM optional property or Crinkl extension requires a new profile version.
