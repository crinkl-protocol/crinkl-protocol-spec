---
status: draft
layer: lifecycle
version: v1
normative: true
---

# GMV Price Aggregate (GmvPriceAggregateV1)

`GmvPriceAggregateV1` is a threshold-signed price-evidence artifact. A selected committee of proof validators observes an on-chain AMM pool over a bounded time window, commits to the observed sample set, and co-signs a single aggregated token price. Downstream GMV sealing consumes the aggregate as evidence for the token price used in a sealed day.

The aggregate carries **price-evidence authority only**. It does not establish GMV proof finality, perform a lifecycle transition, authorize consumption, mutate points, or settle anything. That boundary is embedded in the artifact itself (see `authorityBoundary`) and a verifier MUST reject any aggregate that claims more.

Verifier behavior, the ordered check sequence, and the failure-code vocabulary are specified in `../07-conformance/gmv-price-aggregate-verification.md`.

## Identifiers and Domains

| Constant | Value |
|---|---|
| Object domain | `crinkl:gmv:price-aggregate:v1` |
| Hash domain | `CRINKL_GMV_PRICE_AGGREGATE_V1` |
| Evidence capability | `GMV_PRICE_AGGREGATE_V1` |
| Artifact reference | `artifactType` `GmvPriceAggregateV1`, `artifactVersion` `"1"` |

## Object Shape

Every object in the aggregate is closed: it MUST contain exactly the keys listed for it — no additional keys, no missing keys. The single exception is the optional tolerance-policy pair in `aggregation` (see below).

### Top level

| Field | Type | Rule |
|---|---|---|
| `domain` | string | MUST be `crinkl:gmv:price-aggregate:v1`. |
| `schemaVersion` | integer | MUST be `1`. |
| `protocolVersion` | string | MUST be `1.0.0-rc.1`. |
| `networkId` | identifier | Network the evidence belongs to (e.g. `solana-devnet`). |
| `source` | object | Price source binding. |
| `window` | object | Observation window. |
| `sampleCommitment` | object | Commitment to the observed sample set. |
| `aggregation` | object | Aggregation rule, policy, and the aggregated price. |
| `committee` | object | Registry, assignment, and quorum binding. |
| `publishedAt` | timestamp | Publication instant of the aggregate. |
| `authorityBoundary` | object | Explicit authority denial (all flags `false`). |
| `aggregateHash` | sha256 | Hash of the unsigned aggregate (construction below). |
| `signatures` | array | 1–1024 committee signatures over `aggregateHash`. |

### `source`

| Field | Type | Rule |
|---|---|---|
| `sourceType` | string | MUST be `SOLANA_AMM_POOL_RESERVES`. |
| `chainId` | identifier | Chain the pool lives on. |
| `programId` | base58 | AMM program id (32–44 base58 chars). |
| `poolId` | base58 | Pool account id. |
| `baseMintId` | base58 | Base token mint. |
| `quoteMintId` | base58 | Quote token mint. |
| `baseDecimals` | integer | 0–18. |
| `quoteDecimals` | integer | 0–18. |
| `poolLayoutRef` | string | Pool layout decoder reference, at most 200 ASCII chars. |
| `sourceProfileHash` | sha256 | Hash pinning the full source profile. |
| `priceUnit` | string | MUST be `MICRO_USD_PER_BASE_TOKEN`. |

### `window`

| Field | Type | Rule |
|---|---|---|
| `windowStart` | timestamp | Start of the observation window. |
| `windowEndExclusive` | timestamp | End of the window (exclusive). |
| `firstObservedAt` | timestamp | First observation actually taken. |
| `lastObservedAt` | timestamp | Last observation actually taken. |
| `firstFinalizedSlot` | integer | Non-negative; MUST be `<= lastFinalizedSlot`. |
| `lastFinalizedSlot` | integer | Non-negative. |
| `chainCommitment` | string | MUST be `finalized`. |

Ordering rule: `windowStart <= firstObservedAt <= lastObservedAt < windowEndExclusive`.

### `sampleCommitment`

| Field | Type | Rule |
|---|---|---|
| `observationSet.artifactType` | string | MUST be `GmvPriceObservationSetV1`. |
| `observationSet.artifactVersion` | string | MUST be `"1"`. |
| `observationSet.contentHash` | sha256 | Content hash of the full observation-set artifact. |
| `observationSet.byteLength` | integer | Positive; canonical byte length of that artifact. |
| `sampleSetRoot` | sha256 | Root over the valid samples. |
| `sampleSetRootRule` | string | MUST be `GMV_PRICE_SAMPLE_SET_ROOT_V1`. |
| `validSampleCount` | integer | Positive. |
| `contributingValidatorCount` | integer | Positive. |

Sample floor: `validSampleCount >= contributingValidatorCount * minimumSamplesPerContributor`.

### `aggregation`

| Field | Type | Rule |
|---|---|---|
| `rule` | string | MUST be `MEDIAN_OF_SIGNED_VALIDATOR_TWAP_V1`. |
| `aggregationPolicyHash` | sha256 | Hash pinning the aggregation policy. |
| `minimumSamplesPerContributor` | integer | Positive. |
| `maximumPublicationDelaySeconds` | integer | Positive; also bounds aggregate freshness for sealing attempts. |
| `minimumPoolTvlMicroUsd` | string | OPTIONAL; decimal string matching `^[1-9][0-9]*$`. |
| `toleranceBps` | integer | OPTIONAL; 0–10000. |
| `priceMicroUsdPerToken` | integer | Positive; the aggregated price in micro-USD per base token. |

The two tolerance-policy fields are a pair: an aggregate MUST carry both `minimumPoolTvlMicroUsd` and `toleranceBps` or neither. When present, `toleranceBps` permits a bounded difference between the aggregate price and the price embedded in an already threshold-signed statement: the difference is acceptable when `|statementPrice - aggregatePrice| * 10000 <= aggregatePrice * toleranceBps` (integer arithmetic, no rounding).

Publication rule: `windowEndExclusive <= publishedAt <= windowEndExclusive + maximumPublicationDelaySeconds`. When the aggregate is consumed by a sealing attempt, the aggregate MUST additionally have been published at or before the attempt start and no more than `maximumPublicationDelaySeconds` before it.

### `committee`

| Field | Type | Rule |
|---|---|---|
| `registrySequence` | integer | Non-negative; sequence of the pinned registry snapshot. |
| `registryHash` | sha256 | Content hash of the exact signed registry snapshot. |
| `assignmentId` | identifier | Committee assignment id. |
| `assignmentHash` | sha256 | Content hash of the exact signed assignment. |
| `selectedValidatorIds` | array | 1–1024 identifiers; the selected committee. |
| `quorumRule` | string | MUST be `bft_strict_supermajority_v1`. |
| `requiredSignatures` | integer | MUST equal `floor(2n/3) + 1` where `n = selectedValidatorIds.length`. |

`selectedValidatorIds` MUST be strictly increasing under UTF-8 byte order (which also makes the entries distinct).

#### Registry and assignment binding

The committee section pins the aggregate to one exact, authority-signed registry snapshot and one exact, authority-signed committee assignment:

- `registryHash` and `registrySequence` MUST match the content hash and sequence of a `ValidatorRegistrySnapshotV1` whose signature verifies against the pinned network-authority key.
- `assignmentHash` and `assignmentId` MUST match a `ValidatorAssignmentV1` that (a) is signed by the same authority, (b) names `registrySnapshotHash` equal to `registryHash`, (c) has `statementType` `GMV_PRICE_AGGREGATE_V1`, (d) has `policyHash` equal to `aggregationPolicyHash`, (e) carries quorum rule `bft_strict_supermajority_v1` with `required` equal to the strict-BFT threshold of the selected committee, and (f) lists exactly the same `selectedValidatorIds`.

From the authenticated registry snapshot, the verifier derives a **registry key view**: one row per signing key, each row being `(validatorId, keyId, publicKey, active)`. A row is **active** exactly when both the validator's registry status and the signing key's status are `active`. The view MUST be internally consistent:

- No two rows may share the same `(validatorId, keyId)` identity.
- No two rows may share the same `(keyId, publicKey)` pair.

Two ACTIVE rows that share a `publicKey` under different `keyId`s are currently accepted (see the open hardening question in `../07-conformance/gmv-price-aggregate-verification.md`).

### `authorityBoundary`

| Field | Rule |
|---|---|
| `claim` | MUST be `PRICE_EVIDENCE_ONLY`. |
| `gmvProofFinality` | MUST be `false`. |
| `lifecycleTransition` | MUST be `false`. |
| `consumptionAuthorization` | MUST be `false`. |
| `pointsMutation` | MUST be `false`. |
| `settlement` | MUST be `false`. |

### `signatures[]`

| Field | Type | Rule |
|---|---|---|
| `validatorId` | identifier | MUST be a member of `selectedValidatorIds`. |
| `signerRole` | string | MUST be `PRICE_AGGREGATE_SIGNER`. |
| `keyId` | identifier | Signing key id registered for this validator. |
| `publicKey` | base64 | Canonical base64 of the raw 32-byte Ed25519 public key (43 chars + `=`). |
| `signatureAlgorithm` | string | MUST be `Ed25519`. |
| `signedDigestRule` | string | MUST be `SIGN_RAW_32_BYTE_AGGREGATE_HASH`. |
| `signature` | base64 | Canonical base64 of the raw 64-byte Ed25519 signature (86 chars + `==`). |

Signature-list rules:

- Entries MUST be strictly increasing by `validatorId` under UTF-8 byte order; the list therefore contains at most one signature per validator.
- The `(keyId, publicKey)` pair of each signature MUST be distinct across the list.
- Each signature's `(validatorId, keyId)` MUST resolve to an active registry-view row whose `publicKey` equals the signature's `publicKey`.
- The signed message is the raw 32-byte digest decoded from `aggregateHash` (not the `sha256:`-prefixed string, and not a re-hash of it).
- Quorum: the list MUST contain at least `requiredSignatures` valid signatures.

## Data Encoding Rules

- **Strings** are ASCII-only. Identifiers match `^[A-Za-z0-9][A-Za-z0-9._:-]{0,159}$`.
- **Hashes** are lowercase-hex SHA-256 digests with the `sha256:` prefix (`sha256:` + 64 hex chars).
- **Timestamps** are millisecond-precision UTC ISO 8601 strings (`YYYY-MM-DDThh:mm:ss.mmmZ`) that round-trip exactly through date parsing.
- **Base58 account ids** match `^[1-9A-HJ-NP-Za-km-z]{32,44}$`.
- **Base64 values** are canonical: decoding then re-encoding MUST reproduce the input exactly, and the decoded length MUST equal the declared byte length (32 for public keys, 64 for signatures).
- **Numbers** are JSON numbers that are safe integers; negative zero is invalid. Fractional, non-finite, and out-of-range values are invalid.

## Canonicalization

The canonical serialization of an aggregate (and of its unsigned projection) is deterministic JSON:

- Object keys sorted lexicographically (with ASCII-only content this is equal to UTF-8 byte order).
- No insignificant whitespace.
- Numbers MUST be safe integers; `-0` and `undefined` values are unrepresentable and invalid.
- Arrays keep their declared order.

## Hashing

**`aggregateHash`** commits to the unsigned aggregate. The preimage is the concatenation:

```text
ASCII("CRINKL_GMV_PRICE_AGGREGATE_V1") || 0x00 || UTF8(canonical(aggregate minus aggregateHash and signatures))
```

`aggregateHash = "sha256:" + hex(SHA-256(preimage))`. The stored `aggregateHash` MUST equal the recomputed value.

**Artifact content hash** commits to the full signed artifact: `contentHash = "sha256:" + hex(SHA-256(UTF8(canonical(aggregate))))`, with `aggregateHash` and `signatures` included. The canonical byte length of that serialization is the artifact `byteLength`. External references to the aggregate (candidate price evidence, transport manifests) carry `{artifactType: "GmvPriceAggregateV1", artifactVersion: "1", contentHash, byteLength}` and MUST match the recomputed values.

## Worked Example

Values from a production devnet aggregate (hashes truncated):

```jsonc
{
  "domain": "crinkl:gmv:price-aggregate:v1",
  "schemaVersion": 1,
  "protocolVersion": "1.0.0-rc.1",
  "networkId": "solana-devnet",
  "source": {
    "sourceType": "SOLANA_AMM_POOL_RESERVES",
    "chainId": "solana-devnet",
    "programId": "cpamdpZCGKUy5JxQXB4dcpGPiikHawvSWAd6mEn1sGG",
    "poolId": "FpE6eBe63XeZUoYSFmwNFZ7bJwsFwLevtyjN3Z17dibJ",
    "baseMintId": "4F7MCTUgvADox3mm5FDTUYNYe3TSKrKzSJx8giiVrPMT",
    "quoteMintId": "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",
    "baseDecimals": 9,
    "quoteDecimals": 6,
    "poolLayoutRef": "@meteora-ag/cp-amm-sdk@1.4.4:Pool/bytemuck",
    "sourceProfileHash": "sha256:5b364f48…82f561",
    "priceUnit": "MICRO_USD_PER_BASE_TOKEN"
  },
  "window": {
    "windowStart": "2026-07-28T22:12:07.000Z",
    "windowEndExclusive": "2026-07-28T23:12:07.000Z",
    "firstObservedAt": "2026-07-28T22:12:09.189Z",
    "lastObservedAt": "2026-07-28T23:11:47.240Z",
    "firstFinalizedSlot": 435825762,
    "lastFinalizedSlot": 435834198,
    "chainCommitment": "finalized"
  },
  "sampleCommitment": {
    "observationSet": {
      "artifactType": "GmvPriceObservationSetV1",
      "artifactVersion": "1",
      "contentHash": "sha256:74413835…598ad2",
      "byteLength": 7141
    },
    "sampleSetRoot": "sha256:da5a27f1…8fc1d7",
    "sampleSetRootRule": "GMV_PRICE_SAMPLE_SET_ROOT_V1",
    "validSampleCount": 268,
    "contributingValidatorCount": 5
  },
  "aggregation": {
    "rule": "MEDIAN_OF_SIGNED_VALIDATOR_TWAP_V1",
    "aggregationPolicyHash": "sha256:c0271977…d7b3d7",
    "minimumSamplesPerContributor": 1,
    "maximumPublicationDelaySeconds": 86400,
    "minimumPoolTvlMicroUsd": "1000000",
    "toleranceBps": 100,
    "priceMicroUsdPerToken": 101335
  },
  "committee": {
    "registrySequence": 40,
    "registryHash": "sha256:cff71076…5b25cd",
    "assignmentId": "gmv-price:09020de5…94dcd4",
    "assignmentHash": "sha256:ee6ace15…1c4168",
    "selectedValidatorIds": [
      "ChipotLayer", "McDowells", "PriceChain_Labs",
      "TheWanderers", "crinklb4ucrinkle"
    ],
    "quorumRule": "bft_strict_supermajority_v1",
    "requiredSignatures": 4
  },
  "publishedAt": "2026-07-28T23:16:53.329Z",
  "authorityBoundary": {
    "claim": "PRICE_EVIDENCE_ONLY",
    "gmvProofFinality": false,
    "lifecycleTransition": false,
    "consumptionAuthorization": false,
    "pointsMutation": false,
    "settlement": false
  },
  "aggregateHash": "sha256:0d7a851e…42e40c",
  "signatures": [
    {
      "validatorId": "ChipotLayer",
      "signerRole": "PRICE_AGGREGATE_SIGNER",
      "keyId": "ChipotLayer_key_001",
      "publicKey": "kTd/6q1yeCdd0rV5EZHd+8yI8O0qi/fhtjhZrVtCop0=",
      "signatureAlgorithm": "Ed25519",
      "signedDigestRule": "SIGN_RAW_32_BYTE_AGGREGATE_HASH",
      "signature": "KxqUVCjM…xBiFDQ=="
    }
    // … one entry per signer, ascending by validatorId
  ]
}
```

Checkable properties of this example:

- Committee size is 5, so `requiredSignatures = floor(10/3) + 1 = 4`; the artifact carries 5 signatures, satisfying quorum.
- `selectedValidatorIds` is strictly increasing in UTF-8 byte order (uppercase letters sort before lowercase, so `crinklb4ucrinkle` is last).
- `windowStart <= firstObservedAt <= lastObservedAt < windowEndExclusive`, and `publishedAt` falls within `maximumPublicationDelaySeconds` of the window end.
- `validSampleCount` (268) meets the floor `contributingValidatorCount * minimumSamplesPerContributor` (5).
- The price is 101335 micro-USD per token, i.e. $0.101335.

## Consumption by Sealed-Day Candidates

A GMV day-seal candidate (V4) references the aggregate through its `priceEvidence` section: artifact reference (`contentHash`, `byteLength`), `aggregateHash`, `sourceProfileHash`, `aggregationPolicyHash`, `sampleSetRoot`, registry and assignment identifiers, window bounds, `publishedAt`, and `priceMicroUsdPerToken`. Every one of those fields MUST equal the corresponding aggregate field. The candidate's own statement price MUST equal the aggregate price or fall within the aggregate's signed tolerance, and the aggregate's `windowStart` MUST NOT precede the candidate's day-window end (the price is observed after the day being sealed). Sealing attempts that consume price evidence MUST declare the `GMV_PRICE_AGGREGATE_V1` capability. The exact checks and failure codes are in `../07-conformance/gmv-price-aggregate-verification.md`.
