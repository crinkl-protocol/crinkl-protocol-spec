---
status: draft
layer: extension
version: v1
normative: true
---

# Boost Matching Profile

> **Status: draft v1 optional extension - runtime matching profile**
>
> This document defines the runtime matching artifacts for Boost campaigns that pair an active promoter slot with an independent buyer conversion. It composes campaign rules and existing Spend Attestation Tokens; it does not change canonical spend semantics.

## 1) Scope and Boundary

Boost is a runtime matching profile over a campaign policy.

This profile consumes:

- `CampaignRuleV1`, `AudienceQualificationV1`, `VerifiedConversionV1`, `ConversionApprovalV1`, and `CampaignSettlementLeafV1` from `../04-condition-layer/campaign-commitment.md`
- `SpendAttestationTokenV1` from `../03-portability/spend-attestation-token.md`
- canonical market fields such as `canonical.cbsaCode` and `canonical.geoRegion` from the Spend Attestation Token
- reward issuance and settlement commitments from `../05-reward-and-settlement/reward-layer.md` and `../05-reward-and-settlement/settlement-bindings.md`

This profile does **not**:

- introduce a new core `tokenType`
- mint or modify Spend Attestation Tokens
- define campaign rules, reward math, budgets, or sponsor pricing
- define a global identity graph or portable promoter profile
- require public disclosure of wallet identity, raw receipts, or precise location
- require a durable per-market queue table

Campaign rules define who can qualify and what buyer conversion counts. Boost matching defines which active promoter slot is selected for a buyer conversion and how that slot is consumed.

## 2) Runtime Invariants

Conforming Boost implementations MUST preserve these invariants:

1. Campaign qualification does not mint a Spend Token.
2. A buyer conversion MUST reference a normal `SpendAttestationTokenV1` produced by the hard-verification flow.
3. A promoter slot MUST be opened from valid campaign qualification and eligible promoter spend anchors.
4. The active roster is global per campaign/runtime profile, ordered by slot activation.
5. Local-market eligibility is applied at conversion time before FIFO selection.
6. FIFO selection is over the filtered eligible roster, not over a precomputed per-market queue.
7. A slot consumed by one approved match MUST be unavailable for later matches in every market.
8. If no active slot satisfies the local-market policy, matching MUST fail closed without blocking other markets.
9. Campaign routing metadata is discovery metadata only. Local-area settlement truth MUST come from canonical Spend Token market fields for the buyer conversion and promoter spend anchors.

## 3) Hashing Rules

All profile objects MUST be serialized with RFC 8785 canonical JSON before hashing.

Hash fields use:

```text
"sha256:" + lowercase_hex(SHA-256(canonical_json(unsigned_object)))
```

For each object below, its own hash field MUST be omitted from the hash preimage. Transport-only metadata and signatures, if present, MUST also be omitted unless a profile-specific verifier policy explicitly includes them.

## 4) Roster Policy

`BoostRosterPolicyV1` is the campaign-bound runtime policy for local-area matching.

```text
BoostRosterPolicyV1 {
  schemaVersion: 1,
  profileId: "BOOST_LOCAL_AREA_MATCHING",
  campaignId: Identifier,
  predicateId?: "sha256:" + Hash,

  locationPolicy: {
    mode: "SAME_CBSA" | "SAME_GEO_REGION" | "NEARBY_CBSA",
    marketSource: "SPEND_TOKEN_CANONICAL_LOCATION",
    nearbyMaxHops?: Integer
  },

  rosterOrder: "GLOBAL_ACTIVATED_AT_ASC",
  slotConsumption: "CONSUME_ON_APPROVED_MATCH",
  routingMetadataUse: "DISCOVERY_ONLY",

  rosterPolicyHash: "sha256:" + Hash
}
```

Normative constraints:

- `campaignId` MUST match the `CampaignRuleV1` that authorizes settlement.
- `rosterPolicyHash` MUST match `CampaignRuleV1.settlement.runtimeProfile.profilePolicyHash`.
- `BoostRosterPolicyV1` MUST NOT include `campaignParamsHash` in its own hash preimage; otherwise the campaign rule hash and profile-policy hash become circular. Runtime artifacts bind both `campaignParamsHash` and `rosterPolicyHash` after the campaign rule is frozen.
- `marketSource` MUST be `SPEND_TOKEN_CANONICAL_LOCATION`.
- `routingMetadataUse` MUST be `DISCOVERY_ONLY`; campaign routing metadata MUST NOT replace canonical buyer/promoter Spend Token market fields.
- `rosterOrder` MUST preserve activation order across the whole campaign/runtime profile.
- `slotConsumption` MUST consume the selected active slot after an approved match.

## 5) Promoter Queue Slot

`PromoterQueueSlotV1` records that a qualified promoter has opened an active slot for a campaign.

```text
PromoterQueueSlotV1 {
  schemaVersion: 1,
  slotType: "PROMOTER_QUEUE_SLOT",
  slotId: Identifier,
  campaignId: Identifier,
  campaignParamsHash: "sha256:" + Hash,
  rosterPolicyHash: "sha256:" + Hash,

  promoterQualificationHash: "sha256:" + Hash,
  promoterScopeId: "sha256:" + Hash,
  promoterNullifier: "sha256:" + Hash,

  promoterAnchorSpendTokenHashes: ["sha256:" + Hash],
  promoterAnchorHeadEventHashes: [Hash],
  promoterMarketProofMode: "DISCLOSED" | "COMMITTED" | "ZK_PROOF",
  promoterMarketProof?: Object,

  activatedAt: TimestampISO,
  activationSequence: Integer,
  expiresAt?: TimestampISO,
  slotStatus: "ACTIVE" | "WAITING" | "MATCHED" | "CONSUMED" | "SETTLED" | "EXPIRED" | "CANCELLED",

  slotHash: "sha256:" + Hash
}
```

Normative constraints:

- A slot MUST NOT be treated as a Spend Token or as proof that a buyer conversion occurred.
- `promoterQualificationHash` MUST reference a valid `AudienceQualificationV1` for the same campaign and campaign params.
- Each promoter anchor spend token MUST be valid under the campaign's promoter eligibility rule.
- `activationSequence` MUST be monotonic within the campaign/runtime profile.
- An `ACTIVE` slot MAY match in any market where its verified promoter spend anchors satisfy the `BoostRosterPolicyV1.locationPolicy`.
- Wallet identifiers SHOULD NOT appear in public slot artifacts. Recipient routing, if required for payout, is an application-layer or Reward Layer concern.

## 6) Local-Area Match

`LocalAreaBoostMatchV1` records the verifier decision that one buyer conversion selected one active promoter slot.

```text
LocalAreaBoostMatchV1 {
  schemaVersion: 1,
  matchType: "LOCAL_AREA_BOOST_MATCH",
  matchId: Identifier,
  campaignId: Identifier,
  campaignParamsHash: "sha256:" + Hash,
  rosterPolicyHash: "sha256:" + Hash,

  buyerConversionHash: "sha256:" + Hash,
  buyerSpendTokenHash: "sha256:" + Hash,
  buyerHeadEventHash: Hash,

  selectedSlotId: Identifier,
  selectedSlotHash: "sha256:" + Hash,
  selectedActivationSequence: Integer,

  rosterSnapshotHash: "sha256:" + Hash,
  eligibleSlotCount: Integer,

  marketMatch: {
    mode: "SAME_CBSA" | "SAME_GEO_REGION" | "NEARBY_CBSA",
    proofMode: "DISCLOSED" | "COMMITTED" | "ZK_PROOF",
    buyerMarketRef?: String,
    promoterMarketRef?: String,
    proof?: Object
  },

  matchedAt: TimestampISO,
  matchHash: "sha256:" + Hash
}
```

`rosterSnapshotHash` commits the active roster in activation order at the verifier's match decision point. The committed roster entries MUST be slot hashes, ordered by `activationSequence`.

Normative constraints:

- `buyerSpendTokenHash` and `buyerHeadEventHash` MUST match the buyer conversion Spend Attestation Token referenced by `VerifiedConversionV1`.
- The buyer Spend Attestation Token canonical status MUST be accepted by the campaign conversion rule.
- `selectedSlotHash` MUST reference an `ACTIVE` `PromoterQueueSlotV1`.
- The selected slot's promoter anchor spends and the buyer conversion spend MUST satisfy `BoostRosterPolicyV1.locationPolicy`.
- The selected slot MUST be the first eligible active slot after applying local-market filtering to the global roster.
- A verifier MUST reject a match if an earlier active slot in `rosterSnapshotHash` also satisfies the campaign rule and local-market policy.
- `eligibleSlotCount` MUST be the number of active slots in the roster snapshot that satisfy the campaign rule and local-market policy.

## 7) Slot Consumption

`BoostSlotConsumptionV1` records that a selected slot was consumed by an approved match.

```text
BoostSlotConsumptionV1 {
  schemaVersion: 1,
  consumptionType: "BOOST_SLOT_CONSUMPTION",
  campaignId: Identifier,
  campaignParamsHash: "sha256:" + Hash,
  rosterPolicyHash: "sha256:" + Hash,
  slotId: Identifier,
  slotHash: "sha256:" + Hash,
  matchHash: "sha256:" + Hash,
  consumptionNullifier: "sha256:" + Hash,
  consumedAt: TimestampISO,
  slotStatusAfter: "CONSUMED",
  consumptionHash: "sha256:" + Hash
}
```

Normative constraints:

- `consumptionNullifier` MUST be scoped to the campaign/runtime profile and selected slot.
- The same active slot MUST NOT produce more than one valid `BoostSlotConsumptionV1`.
- Consumption MUST happen only after `LocalAreaBoostMatchV1` is valid.
- Once consumed, the slot MUST be unavailable for all later buyer conversions in the campaign/runtime profile.

## 8) Settlement Binding

`BoostSettlementBindingV1` is the profile-specific object that campaign settlement binds by hash.

```text
BoostSettlementBindingV1 {
  schemaVersion: 1,
  profileId: "BOOST_LOCAL_AREA_MATCHING",
  campaignId: Identifier,
  campaignParamsHash: "sha256:" + Hash,
  rosterPolicyHash: "sha256:" + Hash,
  buyerConversionHash: "sha256:" + Hash,
  buyerSpendTokenHash: "sha256:" + Hash,
  selectedSlotHash: "sha256:" + Hash,
  matchHash: "sha256:" + Hash,
  slotConsumptionHash: "sha256:" + Hash,
  settlementBindingHash: "sha256:" + Hash
}
```

For Boost campaigns, `ConversionApprovalV1.runtimeProfileBinding.profileId` MUST equal `BOOST_LOCAL_AREA_MATCHING`, and `runtimeProfileBinding.profileBindingHash` MUST equal `BoostSettlementBindingV1.settlementBindingHash`.

When public settlement is enabled, `CampaignSettlementLeafV1.runtimeProfile.profileId` MUST equal `BOOST_LOCAL_AREA_MATCHING`, and `runtimeProfile.profileBindingHash` MUST equal `BoostSettlementBindingV1.settlementBindingHash`.

## 9) Verification Procedure

A verifier processing a Boost settlement MUST:

1. Verify the `CampaignRuleV1` and recompute `campaignParamsHash`.
2. Verify `BoostRosterPolicyV1.rosterPolicyHash` and ensure it matches `CampaignRuleV1.settlement.runtimeProfile.profilePolicyHash`.
3. Verify the promoter `AudienceQualificationV1` referenced by `PromoterQueueSlotV1.promoterQualificationHash`.
4. Verify each promoter anchor Spend Attestation Token and its canonical market fields used by the local policy.
5. Verify the buyer `VerifiedConversionV1` and buyer Spend Attestation Token.
6. Verify `LocalAreaBoostMatchV1` against the roster snapshot, local-market policy, and FIFO rule.
7. Verify `BoostSlotConsumptionV1` consumes the selected active slot exactly once.
8. Recompute `BoostSettlementBindingV1.settlementBindingHash`.
9. Verify the campaign `ConversionApprovalV1` binds the Boost settlement binding hash.
10. Verify reward issuance and, if enabled, campaign public settlement commitment.

## 10) Privacy and Disclosure

Boost artifacts are runtime settlement artifacts, not portable identity credentials.

Public artifacts SHOULD reveal only:

- campaign and profile identifiers
- hash references to qualification, conversion, match, and consumption artifacts
- coarse market references when required for public accounting
- payout totals already required by the settlement layer

Public artifacts MUST NOT reveal raw receipts, raw Spend Tokens, wallet addresses, app-user identifiers, or uncommitted precise geography.

## 11) Admin and Publish Mapping

Admin and operator surfaces define campaign policy. The publish bridge MAY compile operator drafts into:

- a `CampaignRuleV1` for campaign proof composition
- a `BoostRosterPolicyV1` when the campaign uses local-area Boost matching
- offer-delivery payloads when wallets need campaign discovery or proof submission surfaces

Runtime Boost matching consumes those compiled artifacts. It does not reinterpret draft UI state as protocol truth.
