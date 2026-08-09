---
status: draft
layer: predicate
version: v1
normative: true
---

# Campaign Spend Proof Primitives

> **Status: draft v1 optional extension - campaign rule composition**
>
> This document defines how campaign rules compose existing Crinkl proof surfaces into marketer-recognizable commerce outcomes without changing canonical Spend Token semantics.
>
> Implementation status: terminology and primitive families are proposed for v1; public campaign settlement anchoring is frozen by `../05-reward-and-settlement/campaign-settlement-gcd.md`.
>
> Experimental schemas: candidate machine-readable schemas for CampaignEpoch, CampaignAmendment, and FundingTranche live in `../schemas/experimental/`. They are non-core predicate/campaign extension schemas and are not required for Core Spend Attestation validity.
>
> **Publication boundary:** the CampaignEpoch shape and schema on this page are the earlier `v1.0.0-rc.2` experimental candidate, not the exact signed adopted engineering `CampaignEpochV1`. Implementations of the Campaign Experiment Profile MUST use the exact adopted engineering artifacts described by [`../06-extensions/campaign-experiment-profile.md`](../06-extensions/campaign-experiment-profile.md). Similar names do not imply wire compatibility.

## 1) Scope and Boundary

Campaign Spend Proof Primitives are finite proof families used to express campaign rules over identity-free Spend Attestation Tokens.

This extension composes:

- `SpendAttestationTokenV1` from `../03-portability/spend-attestation-token.md`
- `SpendZkStatementProofV1` and private witness envelopes from `../06-extensions/zk-proof-extension.md`
- `statementId`, `scopeId`, and `nullifier` from `../06-extensions/zk-foundation.md`
- reward issuance and reward commitments from `../05-reward-and-settlement/reward-layer.md` and `../05-reward-and-settlement/settlement-bindings.md`
- store/category/market references from `../06-extensions/store-registry.md`
- optional merchant authority claims from `../06-extensions/merchant-authority.md`

This extension does **not**:

- introduce a new core `tokenType`
- change `SpendAttestationTokenV1`
- define a global buyer profile or identity graph
- define reward math, budgets, or sponsor pricing as protocol validity rules
- require public disclosure of raw receipts, wallet identity, or sensitive market geography
- prove incrementality or lift without an explicit control/holdout policy

Campaigns are not custom logic. Campaigns are parameterized rules composed from six finite Campaign Spend Proof Primitives.

## 2) Marketing Terms and Protocol Terms

The protocol terms below are normative. Marketing-facing terms are aliases for operator, sponsor, and product surfaces. Marketing aliases MUST NOT change verification semantics.

| Protocol primitive | Marketing-facing term | Meaning |
|---|---|---|
| Spend Validity | Verified Purchase | A valid, verified commerce event exists. |
| Buyer State | Audience State | A holder's state relative to a campaign scope and lookback window. |
| Frequency / Intensity | Purchase Frequency / Spend Intensity | How often, how much, or how recently qualifying behavior occurred. |
| Category / Competitive Relationship | Category / Competitive Set | The relationship between spend behavior and a brand, category, competitor, or adjacent set. |
| Market / Context | Market Targeting / Context | The market, channel, store cluster, time window, or campaign context in which the rule applies. |
| Outcome / Conversion | Verified Outcome / Verified Conversion | The required commerce outcome occurred and can be evaluated for settlement. |

Derived marketing labels such as "new-to-brand", "repeat buyer", "lapsed buyer", "conquest audience", and "retained buyer" are values produced by primitive composition. They are not new primitive families.

## 3) Common Proof Constraints

Every Campaign Spend Proof Primitive MUST be evaluated inside an explicit scope.

The scope MUST bind:

- `campaignId`
- verifier or settlement authority
- statement or primitive definition hash
- applicable time window
- replay boundary

Any proof used for campaign qualification or conversion MUST bind, directly or through referenced artifacts:

- `spendTokenHash`
- `lineage.headEventHash`
- `statementId` or primitive definition hash
- `scopeId`
- proof mode
- public outputs required by the primitive

Any payout-bearing campaign flow MUST include a scope-specific `nullifier` so the verifier or settlement authority can prevent duplicate payment without requiring a stable wallet identifier.

## 3a) CampaignEpoch Primitive

A **Campaign** is a mutable parent container for sponsor objective, campaign type, market scope, and epoch history. A Campaign does not itself define final eligibility.

Campaign eligibility is defined only by immutable **CampaignEpoch** records. A Campaign may evolve only by appending epochs; no amendment may retroactively alter the rules, funding terms, target merchant set, timing rule, proof results, or earned rewards of a prior epoch.

### Discovery and merchant sets

- **AnchorBrand** activity MAY help discover a **CandidateSet**.
- **CandidateSet** discovery is not campaign eligibility.
- A reviewed CandidateSet becomes a **TargetMerchantSet**.
- A TargetMerchantSet contains approved **EligibleMerchant** entries for an epoch.
- The approved TargetMerchantSet for an active CampaignEpoch may change only by creating a new epoch.
- TargetMerchantSet changes require a new `targetMerchantSetRoot` or `targetMerchantSetHash`.

### CampaignEpoch

A CampaignEpoch is an immutable, append-only, funded rule window.

```text
CampaignEpochV1 {
  campaignId: Identifier,
  epochId: Identifier,
  epochVersion: Integer,
  effectiveFrom: TimestampISO,
  effectiveTo?: TimestampISO,
  timingRule: "SPEND_TIMESTAMP" | "ATTESTATION_TIMESTAMP" | "CLAIM_TIMESTAMP",
  predicateId?: Identifier,
  predicateHash: "sha256:" + Hash,
  ruleSetHash: "sha256:" + Hash,
  candidateSetHash?: "sha256:" + Hash,
  targetMerchantSetRoot?: Hash,
  targetMerchantSetHash?: "sha256:" + Hash,
  rewardRuleHash: "sha256:" + Hash,
  fundingTrancheId: Identifier,
  claimLevel: "OBSERVED" | "ATTRIBUTED" | "INCREMENTAL",
  previousEpochId?: Identifier,
  campaignAuthority?: CampaignAuthorityV1,
  issuerAuthority: Identifier,
  createdAt: TimestampISO
}
```

`ClaimLevel` meanings:

- `OBSERVED` means verified spend occurred under the epoch rule.
- `ATTRIBUTED` means spend matched attribution conditions defined by the epoch.
- `INCREMENTAL` requires a baseline, holdout, or incrementality method specified by the epoch.

`RuleSetHash` is the canonical hash over predicate, target merchant set reference/root, reward rule, claim level, effective window, timing rule, funding reference, and `campaignAuthority` when present. It MUST be computed with RFC 8785 canonical JSON and SHA-256 over the epoch rule material, excluding signatures and transport-only metadata.

`campaignAuthority` is optional for operator and system campaigns. If a campaign or epoch declares merchant-official authority (`CampaignAuthorityV1.authorityType = "VERIFIED_MERCHANT"`), the field is REQUIRED and MUST validate under `../06-extensions/merchant-authority.md`.

`FundingTranche` is a budget allocation bound to a specific CampaignEpoch. A tranche may fund rewards only under the rule set it was committed to. Budget increases are represented by child tranche records; the original tranche amount MUST NOT be mutated.

```text
FundingTrancheV1 {
  fundingTrancheId: Identifier,
  parentFundingTrancheId?: Identifier,
  campaignId: Identifier,
  epochId: Identifier,
  ruleSetHash: "sha256:" + Hash,
  amount: String(Integer >= 0),
  asset: String,
  createdAt: TimestampISO
}
```

### CampaignAmendment

A CampaignAmendment is a forward-only event that closes or supersedes a prior epoch and appends a new CampaignEpoch. It MUST NOT mutate prior epochs.

```text
CampaignAmendmentV1 {
  campaignId: Identifier,
  previousEpochId: Identifier,
  nextEpochId: Identifier,
  amendmentHash: "sha256:" + Hash,
  ruleSetHash: "sha256:" + Hash,
  effectiveFrom: TimestampISO,
  issuerAuthority: Identifier,
  createdAt: TimestampISO,
  reason?: String
}
```

`amendmentHash` MUST be computed over `CampaignAmendmentV1` with `amendmentHash` and transport-only metadata omitted.

Candidate future system-stream event:

```text
CAMPAIGN_EPOCH_APPENDED {
  campaignId: Identifier,
  previousEpochId: Identifier,
  nextEpochId: Identifier,
  amendmentHash: "sha256:" + Hash,
  ruleSetHash: "sha256:" + Hash,
  effectiveFrom: TimestampISO,
  issuerAuthority: Identifier,
  createdAt: TimestampISO
}
```

`CAMPAIGN_EPOCH_APPENDED` is a future candidate system-stream event. It is not part of the current Core event catalog or NATS binding. If activated later, it should use the System-Stream Event Envelope in `../01-core/spend-event.md`.

Normative rules:

- CampaignEpoch records are append-only.
- Prior epochs remain verifiable after amendment.
- CampaignAmendment applies prospectively only.
- A sponsor MUST NOT lower, remove, or invalidate rewards already earned under an earlier epoch.
- A verifier MUST evaluate a spend against exactly one CampaignEpoch.
- Epoch selection MUST use the declared `timingRule`.
- If `timingRule` is missing, the CampaignEpoch is invalid.
- Reward rules may change only by creating a new epoch with a new `rewardRuleHash`.
- Budget top-ups MAY attach to the same epoch only through child FundingTranche records bound to the same `campaignId`, `epochId`, and `ruleSetHash`.
- Unspent budget MAY roll forward only if the prior epoch funding policy permits it.
- Earned rewards are immutable once committed.
- Campaign history remains auditable as a sequence of epochs.
- `claimLevel = "INCREMENTAL"` is invalid unless the epoch rule material specifies a baseline, holdout, or incrementality method.
- The experimental `claimLevel = "INCREMENTAL"` candidate does not make any individual receipt, Spend Attestation, conversion, or Epoch intrinsically incremental. Under the Campaign Experiment Profile, incrementality is a cohort- or market-level result under a frozen method; the exact adopted Epoch supplies only its maximum conversion-claim ceiling.
- A campaign that presents itself as merchant-official MUST bind `CampaignAuthorityV1` into the immutable rule material for the epoch.
- A verifier MUST reject a merchant-official campaign when the referenced merchant claim is missing, expired, revoked, not `VERIFIED`, or does not cover the campaign target merchant set.

### Epoch amendment example

Campaign: Coffee campaign in CBSA 31080.

Epoch 1:

- `AnchorBrand`: Starbucks
- `targetMerchantSetRoot`: `root_A`
- reward: 500 points
- `claimLevel`: `OBSERVED`
- `timingRule`: `SPEND_TIMESTAMP`
- `effectiveFrom`: May 1
- `effectiveTo`: May 15

If the sponsor wants to raise the reward to 750 points and remove one EligibleMerchant, Epoch 1 MUST NOT be edited.

Epoch 2:

- `previousEpochId`: Epoch 1
- `targetMerchantSetRoot`: `root_B`
- reward: 750 points
- `timingRule`: `SPEND_TIMESTAMP`
- `effectiveFrom`: May 16
- `effectiveTo`: May 31

Receipts from May 1 through May 15 remain evaluated under Epoch 1. Receipts from May 16 onward are evaluated under Epoch 2.

## 4) Primitive Families

### 4.1 Spend Validity

Marketing term: **Verified Purchase**.

Spend Validity proves that a referenced Spend Attestation Token represents a valid commerce event under the verifier's acceptance policy.

Minimum checks:

1. Verify the Spend Attestation Token per `../03-portability/spend-attestation-token.md`.
2. Verify issuer authority for the signing key.
3. Verify `canonical.status` is accepted by the campaign rule.
4. Verify freshness policy if the campaign requires latest-head evidence.

Typical public or committed fields:

- `spendTokenHash`
- `lineage.headEventHash`
- verification tier
- store or brand reference
- category reference
- amount bucket or commitment
- timestamp bucket or commitment
- market/context commitment

Spend Validity is the atomic primitive. Every other primitive depends on one or more valid spend references.

### 4.2 Buyer State

Marketing term: **Audience State**.

Buyer State classifies a proof subject relative to a campaign scope, rule, and lookback window.

Valid state labels are campaign-derived outputs, for example:

- `NEW_TO_BRAND`
- `REPEAT`
- `ACTIVE`
- `LAPSED`
- `RETURNING`
- `EXISTING`
- `COMPETITOR_BUYER`
- `CONVERTED`
- `RETAINED`

Normative constraints:

- Buyer state MUST be scoped to a campaign, verifier, rule, and time window.
- Buyer state MUST NOT be treated as a global protocol profile.
- "New-to-brand" means first observed within the declared scope and lookback, not globally new for all time.
- Buyer state proofs SHOULD use commitments, nullifiers, or ZK statements when public disclosure would reveal sensitive spend history.

### 4.3 Frequency / Intensity

Marketing terms: **Purchase Frequency** and **Spend Intensity**.

Frequency / Intensity measures the strength of behavior inside a scope.

Examples:

- at least 2 purchases in 30 days
- 5 category purchases in 90 days
- at least USD 50 of category spend
- high-frequency buyer
- high-value buyer
- recent buyer

Normative constraints:

- Count and amount thresholds MUST declare their lookback window.
- Threshold proofs MUST bind to the campaign scope.
- If individual Spend Tokens are not disclosed, the proof MUST expose only the minimum public output needed for verification, such as `count >= N` or `sum >= threshold`.
- Nullifiers used for replay protection MUST be scope-specific.

### 4.4 Category / Competitive Relationship

Marketing terms: **Category**, **Competitive Set**, and **Conquest Audience**.

Category / Competitive Relationship defines what the spend behavior relates to.

Examples:

- category buyer
- competitor buyer but not sponsor buyer
- adjacent-category buyer
- competitor spender
- adjacent-category spender
- brand switcher
- conquest target

Normative constraints:

- Store/category/brand sets SHOULD be represented by deterministic identifiers, sorted allowlists, or committed set roots.
- When category membership depends on a registry, the verifier SHOULD reference a signed Store Registry snapshot or a campaign-defined allowlist root.
- Competitive relationships MUST be expressed as campaign rule parameters, not as token mutations.
- If a campaign hides the competitive set, the proof MUST bind to the committed set root used by the verifier.

### 4.5 Market / Context

Marketing terms: **Market Targeting**, **Geo Targeting**, and **Campaign Context**.

Market / Context constrains where, when, and under what campaign context a proof qualifies.

Examples:

- CBSA
- city or region bucket
- store cluster
- retailer or channel
- campaign window
- launch market
- time bucket

Normative constraints:

- Market/context claims MUST be scoped to the campaign rule.
- Sensitive geography SHOULD be committed or proven privately rather than publicly disclosed.
- Public settlement MAY reveal a coarse market bucket when needed for budget, queue, or local-market accounting.
- Market/context commitments MUST NOT become stable identity-linked purchase history.

### 4.6 Outcome / Conversion

Marketing terms: **Verified Outcome** and **Verified Conversion**.

Outcome / Conversion proves the required commerce event happened after the campaign rule was active.

Examples:

- first verified receipt submitted
- qualifying purchase occurred
- repeat purchase happened
- lapsed buyer returned
- new Spend Attestation Token was issued
- campaign match approved
- reward settlement triggered

Normative constraints:

- A verified conversion MUST be represented by a new or referenced `SpendAttestationTokenV1` whose canonical status satisfies the campaign's conversion rule.
- The conversion Spend Token MUST be produced by the normal hard-verification flow. Campaign qualification MUST NOT mint a Spend Token.
- The conversion proof MUST bind to the campaign rule, qualification scope, conversion window, and conversion spend token hash.
- Settlement MAY proceed only after conversion approval.

## 5) Campaign Rule Artifact

A Campaign Rule is a canonical, hash-identifiable rule composed from Campaign Spend Proof Primitives.

```text
CampaignRuleV1 {
  schemaVersion: 1,
  protocolVersion: Version,

  campaignId: Identifier,
  sponsor: {
    sponsorId: Identifier,
    brandId?: Identifier
  },
  verifier: {
    verifierId: Identifier,
    authorizedIssuerIds?: [Identifier]
  },
  campaignAuthority?: CampaignAuthorityV1,

  publicTerms: {
    startsAt: TimestampISO,
    endsAt: TimestampISO,
    payoutAmount?: String(Integer >= 0),
    payoutAsset?: "POINTS" | "BTC" | "CRINKL" | String,
    budgetRef?: Identifier
  },

  audience: {
    marketingName?: String,          // e.g. "Category conquest audience"
    requiredPrimitives: [CampaignSpendProofPrimitiveRequirementV1]
  },

  conversion: {
    marketingName?: String,          // e.g. "First verified sponsor purchase"
    requiredPrimitives: [CampaignSpendProofPrimitiveRequirementV1],
    requiredNewSpend?: {
      minimumVerification: "HARD_VERIFIED",
      acceptedStatuses?: [String],   // allowed values: "HARD_VERIFIED", "CORRECTED"
      mustOccurAfterQualification: true,
      storeHash?: "sha256:" + Hash,
      storeSetRoot?: Hash,
      categoryId?: Identifier,
      marketScope?: String
    }
  },

  settlement: {
    rewardPolicyId?: "sha256:" + Hash,
    settlementPolicyId?: "sha256:" + Hash,
    replayScope: RedemptionScopeV1,
    publicCommitment?: {
      enabled: Boolean,
      chainId: Identifier,
      commitmentSchema: "CAMPAIGN_SETTLEMENT_LEAF_V1",
      authorizedCommitter: Identifier
    }
  },

  hashes: {
    audienceHash: "sha256:" + Hash,
    conversionHash: "sha256:" + Hash,
    rewardPolicyHash?: "sha256:" + Hash,
    campaignAuthorityHash?: "sha256:" + Hash,
    ruleSetHash: "sha256:" + Hash,
    campaignParamsHash: "sha256:" + Hash
  }
}
```

`campaignParamsHash` MUST be computed over `CampaignRuleV1` with `hashes.campaignParamsHash`, signatures, and transport-only metadata omitted.

`audienceHash` MUST be computed over `audience`. `conversionHash` MUST be computed over `conversion`. `rewardPolicyHash` MUST be computed over the referenced reward policy artifact when present. `campaignAuthorityHash` MUST be computed over `campaignAuthority` when present. `ruleSetHash` MUST match the selected `CampaignEpochV1.ruleSetHash`. All hashes use RFC 8785 canonical JSON and SHA-256 encoded as `"sha256:" + lowercase hex`.

`CampaignAuthorityV1` is defined by `../06-extensions/merchant-authority.md`. Its absence does not invalidate operator or system campaigns. Its absence MUST invalidate campaigns whose declared authority type is merchant-official or `VERIFIED_MERCHANT`.

`minimumVerification: "HARD_VERIFIED"` means the conversion spend must have passed the hard-verification pipeline. A verifier MAY accept `CORRECTED` as a later canonical hard-verification head when the campaign rule includes `CORRECTED` in `acceptedStatuses`.

`CampaignSpendProofPrimitiveRequirementV1` is a requirement descriptor:

```text
CampaignSpendProofPrimitiveRequirementV1 {
  primitive:
    "SPEND_VALIDITY" |
    "SCOPED_BUYER_STATE" |
    "FREQUENCY_INTENSITY" |
    "CATEGORY_COMPETITIVE_RELATIONSHIP" |
    "MARKET_CONTEXT" |
    "OUTCOME_CONVERSION",

  marketingAlias?: String,
  proofMode: "DISCLOSED_TOKENS" | "ZK_PROOF" | "COMMITTED_AGGREGATE",
  statementId?: "sha256:" + Hash,
  statement?: Object,
  publicOutputs: [String],
  privateInputsDescription?: String,
  lookbackWindowDays?: Integer,
  conversionWindowDays?: Integer
}
```

Unknown primitive names MUST be rejected by conforming verifiers.

## 6) Proof, Match, and Settlement Artifacts

The campaign flow is expressed in terms of the protocol object model
(`../08-governance/glossary.md`, `../README.md#protocol-objects`): a **Spend
Predicate** is evaluated and produces a **Proof of Match**; a Proof of Match
that reaches finality may settle. Audience Qualification, Verified
Conversion, and Conversion Approval are roles and states of that flow, not
separate serialized objects. Only `CampaignRuleV1`/`CampaignEpochV1` (§3a,
§5), `CampaignSettlementLeafV1`, and `CAMPAIGN_SETTLEMENT_COMMITTED` (§6.5)
are named artifacts below.

### 6.1 Audience Qualification

Marketing term: **Audience Qualification**.

Audience Qualification is not a separate object. It is the audience-scope
role of Proof of Match: the result of evaluating the campaign's audience
Spend Predicate — the composed `audience.requiredPrimitives` from
`CampaignRuleV1` (§5) — against one or more Spend Attestations, scoped to
exactly one `CampaignEpoch`.

Every audience-scope Proof of Match MUST carry, directly or by binding:

- `campaignId`, `epochId`, `ruleSetHash`, `campaignParamsHash` — the campaign
  and epoch scope required by §3
- `scopeId`, `nullifier` — the scope and replay bindings required by §3
- `proofMode` — as declared on the matched `CampaignSpendProofPrimitiveRequirementV1` entries (§5)
- the evaluated evidence for each matched primitive requirement (previously
  the `primitiveProofs` field) — the Proof of Match's evidentiary content for
  the composed `audience.requiredPrimitives` list
- `campaignAuthorityHash`, when the campaign or epoch declares
  `CampaignAuthorityV1` (§3a, §5)

Evaluating the audience predicate MUST NOT mint a Spend Token. It only
proves qualification for a campaign scope.

The audience-scope match timestamp and its own content hash (referenced
elsewhere in this document and in `CampaignSettlementLeafV1` as
`qualificationHash`) are Proof of Match fields. Proof of Match has no
formalized field shape or canonical hash computation rule in this repository
yet (`proof-of-match.md` is prose-only, and it is not currently marked
`(schema pending, OM4)` in `README.md` alongside `SpendPredicate` even though
no shape exists) — see the open point in this slice's PR body. Until Proof
of Match is formalized, `qualificationHash` is a verifier/issuer-committed
reference, not a value this document defines a recomputation rule for.

### 6.2 Verified Conversion

Marketing term: **Verified Conversion**.

Verified Conversion is not a separate object. It is the conversion-scope
role of Proof of Match: the result of evaluating the campaign's conversion
Spend Predicate — the composed `conversion.requiredPrimitives` from
`CampaignRuleV1` (§5) — against the conversion Spend Attestation Token,
scoped to the same `CampaignEpoch` as the audience-scope match.

Every conversion-scope Proof of Match MUST carry, directly or by binding:

- `campaignId`, `epochId`, `ruleSetHash`, `campaignParamsHash` — as in §6.1
- `qualificationHash` — binding this match to the audience-scope Proof of
  Match it follows
- `conversionSpendTokenHash`, `conversionHeadEventHash` — the §3 spend
  binding (`spendTokenHash`, `lineage.headEventHash`) for the conversion
  Spend Attestation Token
- `conversionNullifier` — the §3 scope-specific replay binding for this role
- `campaignAuthorityHash`, when declared (as in §6.1)

The `conversionSpendTokenHash` MUST reference a Spend Attestation Token
issued by the normal verification pipeline. The campaign does not create a
special Spend Token type.

As in §6.1, the conversion-scope match timestamp and its own content hash
(`conversionHash` downstream) are Proof of Match fields with no formalized
shape yet; see the open point in this slice's PR body. `conversionHash` here
names the conversion-scope match result and MUST NOT be confused with
`CampaignRuleV1.hashes.conversionHash` (§5), which hashes the rule's
`conversion` requirement definition, not a match result — this naming reuse
predates this slice and is flagged as a separate open point.

### 6.3 Conversion Approval

Marketing term: **Conversion Approval**.

Conversion Approval is not a separate object. It is a **state**: the
audience-scope and conversion-scope Proof of Match for this campaign flow
have reached finality — admitted to the shared record by a Finality
Certificate (a quorum of selected Proof Validators co-signing the identical
deterministic result) per `../02-proof-lifecycle/admission.md`. Settlement
MAY proceed only once this state is reached; an Attested-only match (signed
but not yet Admitted, per the same admission states) MUST NOT settle.

The fields the old `ConversionApprovalV1` draft carried map onto surviving
artifacts as follows:

- `campaignId`, `epochId`, `ruleSetHash`, `campaignParamsHash`,
  `qualificationHash`, `conversionHash`, `conversionSpendTokenHash`,
  `conversionHeadEventHash`, `campaignAuthorityHash` — the campaign binding
  fields the finalized statement covers (§6.1, §6.2); unchanged.
- `payout.amount`, `payout.asset`, `settlementScopeId`,
  `settlementNullifier` — carried forward unchanged into
  `CampaignSettlementLeafV1` (§6.5) and `campaign-settlement-gcd.md`.
  Conversion Approval does not define a competing payout or nullifier
  surface.
- `approvedBy`, `approvedAt` — this purpose is now served jointly by the
  campaign's declared verifier authority (`CampaignRuleV1.verifier.verifierId`,
  §5) for who the finalized statement is scoped to, and the Finality
  Certificate's quorum of selected-validator signatures and finalization
  time (`../02-proof-lifecycle/admission.md`) for who admitted it. There is
  no single-signer "approver" role.
- `signatures.publicKey` / `signatures.signature` — superseded by the
  Finality Certificate's quorum-signature envelope
  (`../02-proof-lifecycle/admission.md`); a single verifier Ed25519
  signature no longer creates network acceptance on its own.
- `signatures.approvalHash` — this is the same `approvalHash` field required
  by the frozen `CampaignSettlementLeafV1` (§6.5, `campaign-settlement-gcd.md`).
  It survives unchanged on the wire. Its definition changes: `approvalHash`
  MUST now be read as the hash of the Finality Certificate (or the finalized
  statement it certifies) that admitted this campaign's Proof of Match, not
  the hash of a bespoke `ConversionApprovalV1` object.
- `schemaVersion` — not applicable; there is no bespoke object shape left to
  version.

### 6.4 Payout Settlement

Marketing term: **Payout Settlement**.

Payout Settlement is the economic consequence of a valid Conversion Approval
(the finality state defined in §6.3). Settlement MAY be represented by
Reward Ledger events, Reward Commitment Tokens, or chain-specific settlement
accounts. This extension does not replace the Reward Layer or Commitment
Layer.

Settlement MUST bind, directly or by hash reference:

- `campaignId`
- `epochId`
- `ruleSetHash`
- `campaignParamsHash`
- `qualificationHash`
- `conversionHash`
- `conversionSpendTokenHash`
- `campaignAuthorityHash` when present in the governing campaign rule
- payout amount and asset
- settlement nullifier
- `approvalHash` — the Finality Certificate hash admitting the campaign's
  Proof of Match to record-level finality (§6.3)

### 6.5 Campaign Settlement Commitment

Marketing term: **Public Settlement**.

Campaign Settlement Commitment is the public/on-chain settlement surface for
payout-bearing campaigns. It commits cleared conversions once Conversion
Approval (§6.3) is reached, without publishing raw audience proof inputs,
wallet identity, raw receipt data, or sensitive market details.

This is not a token. It is a system-stream commitment event plus a Merkle root that MAY be anchored on-chain through the Commitment Layer's chain-binding conventions.

Each committed leaf represents one cleared campaign conversion:

```text
CampaignSettlementLeafV1 {
  schemaVersion: 1,
  leafType: "CAMPAIGN_SETTLEMENT_LEAF",
  settlementId: Identifier,
  campaignId: Identifier,
  epochId: Identifier,
  ruleSetHash: "sha256:" + Hash,
  campaignParamsHash: "sha256:" + Hash,
  qualificationHash: "sha256:" + Hash,
  conversionHash: "sha256:" + Hash,
  conversionSpendTokenHash: "sha256:" + Hash,
  conversionHeadEventHash: Hash,
  approvalHash: "sha256:" + Hash,
  campaignAuthorityHash?: "sha256:" + Hash,

  payout: {
    amount: String(Integer >= 0),
    asset: "POINTS" | "BTC" | "CRINKL" | String
  },

  settlementScopeId: "sha256:" + Hash,
  settlementNullifier: "sha256:" + Hash,
  clearedAt: TimestampISO
}
```

`CampaignSettlementLeafV1` is hashed with the same Merkle conventions as commitment leaves unless a chain binding specifies a stricter domain separator. Verifiers MUST reject leaves that omit `approvalHash`, `conversionSpendTokenHash`, or `settlementNullifier`.

Campaign settlement batches are committed with a system-stream event:

```text
CAMPAIGN_SETTLEMENT_COMMITTED {
  settlementBatchId: Identifier,
  campaignId: Identifier,
  epochId: Identifier,
  ruleSetHash: "sha256:" + Hash,
  campaignParamsHash: "sha256:" + Hash,
  root: Hash,
  leafCount: Integer,
  totalPayoutAmount: String(Integer >= 0),
  payoutAsset: "POINTS" | "BTC" | "CRINKL" | String,
  schemaVersion: "campaign-settlement-v1",
  txRef: String,
  committedAt: TimestampISO
}
```

The system event envelope supplies `chainId`, `signedBy`, `prevHash`, `eventHash`, and the authority signature as defined in `../01-core/spend-event.md`.

Normative constraints:

- `campaignId` and `campaignParamsHash` MUST match the `CampaignRuleV1` that authorized settlement.
- `epochId` and `ruleSetHash` MUST match the CampaignEpoch that authorized the ProofOfMatch.
- `root` MUST be computed over `CampaignSettlementLeafV1` leaves for that campaign settlement batch.
- `leafCount` MUST equal the number of committed leaves.
- `totalPayoutAmount` and `payoutAsset` MUST equal the sum and asset class represented by the committed leaves.
- `txRef` MUST reference the public chain anchor for `root` under the deployment's chain binding.
- `settlementNullifier` MUST be campaign-scoped and MUST NOT be a stable wallet, account, or user identifier.
- Public settlement leaves MUST NOT contain raw receipt artifacts, raw Spend Tokens, wallet addresses, user identifiers, or uncommitted sensitive geography.
- A deployment that stores only `root` on-chain MUST publish enough system-stream history for third parties to recover `campaignId`, `campaignParamsHash`, `schemaVersion`, `signedBy`, `committedAt`, and authority validity.

## 7) Verification Procedure

A verifier processing a Campaign Rule MUST:

1. Recompute `campaignParamsHash` from `CampaignRuleV1`.
2. Select exactly one CampaignEpoch using the epoch `timingRule`; reject missing `timingRule` or ambiguous epoch matches.
3. Recompute `ruleSetHash` from the selected CampaignEpoch rule material.
4. Verify each primitive requirement uses a supported primitive name and proof mode.
5. If `CampaignAuthorityV1.authorityType = "VERIFIED_MERCHANT"`, verify the merchant claim attestation under `../06-extensions/merchant-authority.md` and reject missing, expired, revoked, unverified, or scope-mismatched claims.
6. Verify Audience Qualification:
   - verify all referenced Spend Tokens and proofs
   - verify `scopeId` and `nullifier` binding
   - reject replayed qualification nullifiers within the campaign scope
7. Verify Verified Conversion:
   - verify the conversion Spend Attestation Token per `../03-portability/spend-attestation-token.md`
   - verify `conversionSpendTokenHash` and `conversionHeadEventHash`
   - verify the conversion occurred inside the campaign conversion window
   - verify it occurred after audience qualification when required
   - reject replayed conversion or settlement nullifiers
8. Verify payout terms against the selected CampaignEpoch.
9. Confirm the campaign's audience-scope and conversion-scope Proof of Match have reached finality — Conversion Approval, per §6.3 — via Finality Certificate admission under `../02-proof-lifecycle/admission.md`. An Attested-only match MUST NOT proceed to settlement.
10. Settle through the Reward Layer and, when enabled, the Commitment Layer.
11. If `settlement.publicCommitment.enabled` is true:
   - compute `CampaignSettlementLeafV1` from the approved conversion
   - include it in a campaign settlement batch root
   - emit `CAMPAIGN_SETTLEMENT_COMMITTED`
   - verify the system-stream authority and on-chain `txRef` before treating the public settlement as final

## 8) Privacy and Scoped Proof Memory

Campaign implementations MUST NOT rely only on client-side token storage for replay safety or buyer-state integrity.

Campaign implementations also MUST NOT create a global identity-linked purchase repository.

The correct campaign memory model is scoped proof memory:

- holders keep identity-free Spend Tokens and private witness envelopes as positive evidence
- verifiers keep only the minimum campaign-scoped nullifiers, commitments, and approval hashes required for replay prevention and settlement audit
- buyer-state labels are derived only within explicit campaign scopes and time windows
- raw receipt artifacts SHOULD expire according to deployment retention policy
- durable settlement records SHOULD reference hashes and commitments rather than raw receipt data or stable identity
- public settlement commitments SHOULD reveal only campaign-level settlement facts and hash references, not audience proof inputs or holder identity

## 9) Relationship to Offer Delivery

`../06-extensions/offer-delivery-profile.md` defines an offer-delivery profile: campaign message, holder proof submission, rollout/only-once proof, and encrypted grant or rejection. It is useful for presenting or unlocking offers.

This document defines the campaign proof composition and verified conversion settlement surface. Offer delivery MAY use these primitives, but offer delivery is not the campaign settlement primitive.

## 10) Example: New-to-Brand Conquest Campaign

Marketing name: **New-to-Brand Conquest Campaign**.

Sponsor: `sponsor_brand`.

Audience: **Category conquest audience**.

Audience Qualification:

- Spend Validity: verified competitor Spend Tokens
- Frequency / Intensity: at least 2 qualifying purchases
- Category / Competitive Relationship: sponsor-defined competitor set
- Market / Context: CBSA scope and 30-day lookback
- Buyer State: competitor buyer within campaign scope

Verified Conversion:

- Outcome / Conversion: first verified sponsor-brand purchase after qualification
- Spend Validity: conversion Spend Token is `HARD_VERIFIED`
- Market / Context: conversion occurs inside campaign window and market scope

Conversion Approval:

- the campaign's Proof of Match — covering `campaignParamsHash`, `qualificationHash`, `conversionHash`, `conversionSpendTokenHash`, payout amount, and settlement nullifier — reaches finality via Finality Certificate admission

Payout Settlement:

- settlement issues the reward and may later be proven through Reward Commitment Token inclusion
- public settlement commits the campaign conversion root through `CAMPAIGN_SETTLEMENT_COMMITTED`

Critical invariant:

```text
Audience qualification does not mint a Spend Token.
Verified conversion mints or references the new Spend Token.
Settlement pays only after conversion approval.
```
