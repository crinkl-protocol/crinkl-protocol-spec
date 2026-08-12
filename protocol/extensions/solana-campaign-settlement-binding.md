---
status: experimental
layer: extension
version: v1
normative: true
---

# Solana Campaign Settlement Binding

> **Compatibility status:** this V1 extension binds the legacy campaign
> settlement GCD and preserves its Anchor account, instruction, event, and PDA
> names. In particular, the on-chain account named `CampaignCommitment` is not
> the target canonical campaign object and does not compete with
> `CampaignEpoch`. This extension does not yet define a target
> `SettlementRecord` binding.

This document maps the campaign settlement GCD in
`../applications/economics/campaign-settlement-gcd.md` to a Solana Anchor
program. It defines implementation names, PDA seeds, instruction bindings, event
bindings, `txRef` shape, and deployment registry requirements.

## Boundary

The protocol primitive is chain-neutral:

```text
CampaignRuleV1
CampaignEpochV1
CampaignSettlementLeafV1
CampaignSettlementBatchV1
CAMPAIGN_SETTLEMENT_COMMITTED
```

The Solana binding defines only how those legacy objects are committed on
Solana. It does not define campaign creation policy, sponsor funding, economic
admission, FIFO matching, promoter queues, payout rails, creator eligibility,
or token-holder rules.

Neither `publish_campaign_commitment` nor `commit_settlement_batch` verifies a
`ProofOfMatch`, issues a `ValidatorCertificate`, creates a
`RewardObligation`, or proves its payment. Solana transaction finality is chain
finality for the named account write, not Proof Validator quorum acceptance.

## Interface Artifacts

Anchor programs expose a machine-readable IDL describing instructions, accounts,
and types. Solana Program Derived Addresses (PDAs) are deterministic account
addresses derived from a program id and seed bytes.

Normative references:

- Anchor IDL: <https://www.anchor-lang.com/docs/basics/idl>
- Solana PDAs: <https://solana.com/docs/core/pda>

For this binding, the human-readable source of truth is this document. The
machine-readable implementation interface is the Anchor IDL generated from the
deployed program build.

## Program Surface

Anchor program name:

```text
campaign_settlement
```

Required account types:

```text
ProgramConfig
CampaignCommitment
SettlementBatchCommitment
```

Required instruction names:

```text
initialize_config
rotate_authority
publish_campaign_commitment
commit_settlement_batch
```

Required emitted event names:

```text
ConfigInitialized
AuthorityRotated
CampaignCommitmentPublished
SettlementBatchCommitted
```

## Hash Encoding

Portable protocol artifacts encode hashes as:

```text
"sha256:" + lowercase hex
```

Solana instruction arguments use decoded 32-byte hash digests:

```text
[u8; 32]
```

Clients MUST decode portable hash strings before passing them to the program and
MUST reject hashes that are not `sha256` lowercase hex strings.

## PDA Seeds

All PDA seeds are byte strings. Hash values are decoded 32-byte digests, not
ASCII `"sha256:"` strings.

```text
ProgramConfig PDA:
  [b"config"]

CampaignCommitment PDA:
  [b"campaign", campaign_params_hash, rule_set_hash]

SettlementBatchCommitment PDA:
  [b"settlement", campaign_params_hash, rule_set_hash, settlement_batch_id_hash]
```

The PDA bump MUST be stored in the corresponding account.

## Account Mapping

### ProgramConfig

Required fields:

```text
authority: Pubkey
authority_version: u64
bump: u8
```

`authority` is the only signer allowed to rotate authority, publish campaign
commitments, or commit settlement batches.

### CampaignCommitment

`CampaignCommitment` below is an immutable V1 Anchor account type and instruction
surface. It MUST remain named as published for compatibility. New portable
campaign specifications MUST use `CampaignEpoch`; an adapter must state the
exact Epoch fields and hashes represented by this legacy account.

Required fields:

```text
campaign_id_hash: [u8; 32]
epoch_id_hash: [u8; 32]
rule_set_hash: [u8; 32]
campaign_params_hash: [u8; 32]
verifier: Pubkey
starts_at: i64
ends_at: i64
payout_asset_hash: [u8; 32]
payout_policy_hash: [u8; 32]
schema_version: u8
created_slot: u64
bump: u8
```

Mapping:

| Protocol field | Solana field |
|---|---|
| `CampaignRuleV1.campaignId` | `campaign_id_hash` |
| `CampaignEpochV1.epochId` | `epoch_id_hash` |
| `CampaignRuleV1.hashes.ruleSetHash` | `rule_set_hash` |
| `CampaignRuleV1.hashes.campaignParamsHash` | `campaign_params_hash` |
| `CampaignRuleV1.verifier` | `verifier` |
| `CampaignEpochV1.effectiveFrom` | `starts_at` |
| `CampaignEpochV1.effectiveTo` | `ends_at` |
| `CampaignRuleV1.publicTerms.payoutAsset` | `payout_asset_hash` |
| `CampaignRuleV1.hashes.rewardPolicyHash` | `payout_policy_hash` |

### SettlementBatchCommitment

Required fields:

```text
settlement_batch_id_hash: [u8; 32]
campaign_id_hash: [u8; 32]
epoch_id_hash: [u8; 32]
rule_set_hash: [u8; 32]
campaign_params_hash: [u8; 32]
root: [u8; 32]
leaf_count: u32
total_payout_amount: u64
payout_asset_hash: [u8; 32]
schema_version: u8
committer: Pubkey
committed_slot: u64
bump: u8
```

Mapping:

| Protocol field | Solana field |
|---|---|
| `CampaignSettlementBatchV1.settlementBatchId` | `settlement_batch_id_hash` |
| `CampaignSettlementBatchV1.campaignId` | `campaign_id_hash` |
| `CampaignSettlementBatchV1.epochId` | `epoch_id_hash` |
| `CampaignSettlementBatchV1.ruleSetHash` | `rule_set_hash` |
| `CampaignSettlementBatchV1.campaignParamsHash` | `campaign_params_hash` |
| `CampaignSettlementBatchV1.root` | `root` |
| `CampaignSettlementBatchV1.leafCount` | `leaf_count` |
| `CampaignSettlementBatchV1.totalPayoutAmount` | `total_payout_amount` |
| `CampaignSettlementBatchV1.payoutAsset` | `payout_asset_hash` |

## Instruction Requirements

### initialize_config

- authority MUST NOT be the default public key
- config PDA MUST use `[b"config"]`
- initial `authority_version` MUST be `1`

### rotate_authority

- current authority MUST sign
- new authority MUST NOT be the default public key
- `authority_version` MUST increment

### publish_campaign_commitment

- configured authority MUST sign
- schema version MUST match the program schema version
- all hash arguments MUST be nonzero
- verifier public key MUST NOT be default
- `starts_at < ends_at`
- campaign PDA MUST use `[b"campaign", campaign_params_hash, rule_set_hash]`

### commit_settlement_batch

- configured authority MUST sign
- schema version MUST match the program schema version
- all hash arguments MUST be nonzero
- `leaf_count > 0`
- settlement PDA MUST use
  `[b"settlement", campaign_params_hash, rule_set_hash, settlement_batch_id_hash]`
- supplied `campaign_params_hash` MUST match the campaign commitment
- supplied `epoch_id_hash` MUST match the campaign commitment
- supplied `rule_set_hash` MUST match the campaign commitment

## Event Mapping

`SettlementBatchCommitted` is the Solana evidence for
`CAMPAIGN_SETTLEMENT_COMMITTED`.

It is supporting evidence for a target `SettlementRecord` only when a later
adopted binding also identifies the exact `RewardObligation`, resolution status,
amount, asset, authoritative settlement rail, and any successor or dispute
record. The V1 event alone does not provide that mapping.

The System-Stream event payload MUST include:

```text
settlementBatchId
campaignId
epochId
ruleSetHash
campaignParamsHash
root
leafCount
totalPayoutAmount
payoutAsset
schemaVersion
txRef
committedAt
```

`txRef` MUST point to the Solana transaction that executed
`commit_settlement_batch`.

## txRef Encoding

Solana campaign settlement `txRef` values use:

```text
solana:<cluster>:program:<programId>:slot:<slot>:tx:<signature>:ix:<instructionName>
```

Examples of `<cluster>`:

```text
devnet
mainnet-beta
localnet
```

Verifiers SHOULD reject a `txRef` when:

- the cluster is not the expected deployment cluster
- the program id is not the registered campaign settlement program id
- the transaction does not include the named instruction
- the instruction does not write the expected commitment account
- finality is below the deployment's required threshold

## Deployment Registry

Each deployment MUST publish a registry record containing:

```text
cluster
programId
programDataAccount
upgradeAuthority
idlHash
programBinaryHash
gitCommit
schemaVersion
programAuthority
systemStreamAuthorityId
deployedSlot
finalityThreshold
```

Devnet and mainnet deployments MUST have separate registry records.

The deployment registry is where concrete program ids live. The protocol spec
defines names and bindings; it does not hard-code every future deployment
address.

## Security Tests Required By This Binding

Implementations SHOULD maintain tests that prove:

- only the configured authority can publish campaign commitments
- only the configured authority can publish settlement batches
- old authority is rejected after rotation
- zero hashes are rejected
- invalid campaign windows are rejected
- duplicate campaign commitment PDAs cannot overwrite the frozen rule
- duplicate settlement batch PDAs cannot overwrite a settlement root
- settlement roots detached from the frozen epoch are rejected
- settlement roots detached from the frozen rule set are rejected
- settlement roots detached from the frozen campaign params are rejected
- public commitments contain hashes and aggregate values only, not private buyer data

Static analysis, low-level SVM tests, and stateful fuzz/stress tests SHOULD be
used as separate evidence layers. A clean scan is evidence for that scan only; it
is not proof that the program is secure.

## Non-Goals

The Solana binding MUST NOT encode:

- campaign creation permission policy
- sponsor funding mechanics
- FIFO or promoter matching policy
- creator eligibility
- payout execution rails
- raw conversion data
- private buyer data
- arbitrary campaign DSL composition

## Target migration boundary

This V1 extension remains usable for its exact published commitment purpose.
Target conformance requires a new version or separate adopted profile that maps
`CampaignEpoch`, `CampaignOutcome`, `RewardObligation`, and
`SettlementRecord` without renaming or repurposing the V1 accounts. The target
profile must also distinguish economic-admission state from settlement and must
not assign Proof Validators authority to reserve or move funds.
