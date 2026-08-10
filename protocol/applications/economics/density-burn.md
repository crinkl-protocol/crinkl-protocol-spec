---
status: draft
layer: reward-settlement
version: v1
normative: true
---

# Density Burn

> "Verified spend density must be provable on-chain as a single monotonic figure — and publishing that figure must cost the issuer future emissions."

Density Burn is a supply-accounting mechanism that consumes CRINKL tokens from the **Data Density Reserve** as a deterministic function of cumulative qualified network activity. It replaces the prior GMV-indexed supply *release* model: where the old model emitted escrowed tokens in proportion to GMV, Density Burn destroys reserve tokens in proportion to qualified GMV — from the **same reserve that funds user reward emissions**. Every burned token is a token that would otherwise have remained available for future reward emission.

This shared-reserve property is load-bearing and MUST NOT be weakened: a burn drawn from a reserve with no alternative fate carries no economic information. The burn is credible precisely because it consumes the protocol's own emission budget.

**Identity prohibition:** Per the Identity Minimization Invariant (../00-purpose/what-crinkl-proves.md), Density Burn artifacts MUST NOT include wallet identifiers, recipient references, or any data enabling reconstruction of per-user spend patterns. Spends are referenced only via the committed `spendHeadSetRoot` inherited from Verified GMV Token semantics (gmv-token.md).

## Explicit non-claims (normative)

A Density Burn epoch:

- does NOT claim, imply, or promise any token price, market value, or appreciation;
- is NOT a buyback: no tokens are acquired from any market;
- is NOT a redemption right, dividend, or distribution to any holder;
- does NOT imply rewards were issued for the spends it counts (`issuedGMV` semantics remain independent, per gmv-token.md);
- does NOT claim the counted spends are valid forever; it claims they satisfied a specific, hash-pinned rule set at a specific finality cutoff.

The burn is an index of verified spend density and a forfeiture of future emission capacity. Nothing more is claimed.

## Definitions

### Data Density Reserve (DDR)

A single program-owned (PDA) token account holding the protocol's reward emission budget.

- Initial funding: the former rewards escrow less the validator allocation (provisionally 70,000,000 CRINKL = 80M − 10M validators; see Migration below).
- Exactly **two** exits, both protocol-defined:
  1. **Reward emission** — transfers governed by the reward policy layer (reward-layer.md, policy-layer.md).
  2. **Density burn** — irreversible burns governed by this document.
- NO withdrawal instruction, NO emergency-withdraw path, NO upgrade authority after parameter freeze. Any program exposing a third exit from the DDR is non-conformant.

### Burn Input `A`

The cumulative qualified activity measure, in integer USD cents:

```text
A = QG + λ · SR
```

- `QG` — cumulative **Qualified GMV**: finalized spend totals that pass `QualifiedGmvRuleSetV1` (below) at the epoch's finality cutoff.
- `SR` — cumulative **settled campaign revenue**: sponsor funds actually received and recognized via a paid-settlement/debit artifact. The campaign settlement layer currently excludes sponsor pricing, funding, and payout rails from proof scope (campaign-settlement-gcd.md); therefore `SR` MUST equal `0` in every epoch until a normative paid-settlement artifact exists in this spec. Implementations MUST NOT substitute settlement *commitments* for settled revenue.
- `λ` (lambda) — the revenue weight, expressing how many dollars of raw spend-through one dollar of paid revenue is equivalent to. Provisional value: `33` (an implied ~3% take-rate equivalence).

`A` is monotonically non-decreasing. Corrections to historical spends roll forward into later epochs (see Lifecycle); they never restate a consumed epoch.

### Depletion schedule `D(A)`

The cumulative TOTAL depletion of the reserve — burn plus reward emission together — in token base units (CRINKL has 6 decimals):

```text
D(A) = floor( c · ln(1 + A / K) )
```

`D` is a schedule, not a burn amount: it fixes how much has left the reserve once
cumulative qualified input reaches `A`, independent of token price. Each
epoch's tranche `D(A_new) − D(A_old)` is split atomically between the reward
emission ask (USD-denominated, converted at the posted price, capped by the
tranche) and the burn (the residual). Price moves the split; it can never move
the depletion path. This is what makes the calibration targets meaningful
while the token has no market price.

Calibrated parameters (closed form from the depletion targets; frozen as deployment constants):

| Parameter | Value | Meaning |
|---|---|---|
| `c` | 5,633,706,605,995 base units (≈5.6337M CRINKL) | schedule scale = 70M / ln(1 + $500B/K) |
| `K` | 200,803,213 cents ($2,008,032.13) | = 10^18/(5·10^11 − 2·10^9) dollars, the unique K with D($1B) = ½·D($500B) |
| `λ` | 33 | revenue weight inside `A` |

Calibration targets (normative): `D($1B) = 50%` of the funded reserve;
`D($500B) = 100%`. The closed form follows from requiring
`(1 + 10^9/K)² = 1 + 5·10^11/K`.

Required properties (normative — any recalibrated schedule MUST preserve all four):

1. **Monotone:** `D` is non-decreasing in `A`.
2. **Concave:** marginal depletion per dollar strictly decreases as `A` grows — early density is weighted most ("density" is the design intent, not decoration).
3. **Bounded:** cumulative depletion can never exceed the DDR balance; schedule beyond the balance is forfeited, not deferred (see Data Density Reserve semantics). The slow growth additionally bounds the damage of any input inflation: even unbounded fake input asymptotically depletes only what the reserve holds.
4. **Deterministic:** computed in fixed-point integer arithmetic with floor-only rounding on the *cumulative* value. Per-epoch tranches are differences of cumulative values, never independently rounded.

Reference magnitudes under calibrated parameters (verified on-chain in the localnet sweep):

| `A` | `D(A)` | Depleted |
|---|---|---|
| $1.95M (live 2026-06-12) | 3.83M | 5.46% |
| $100M | 22.13M | 31.6% |
| $1B | 35.00M | **50.00%** |
| $10B | 47.96M | 68.5% |
| $100B | 60.93M | 87.0% |
| $500B | 70.00M | **100.00%** |

### QualifiedGmvRuleSetV1

A versioned, hash-pinned rule set defining which finalized spends count toward `QG`. It MUST cover, at minimum:

- duplicate-leaf rejection (a spend head contributes to `A` at most once, ever, across all epochs);
- eligibility (structural validity per ../protocol/core/verification-state.md);
- fraud/enforcement holds (spends under active enforcement at the finality cutoff are excluded; if later cleared they roll forward);
- finality (only spends whose canonical head is older than the epoch's `finalityCutoff` are countable);
- high-total policy (today an inline platform policy; it MUST be expressed here as versioned rules with conformance vectors before any epoch is consumed on-chain).

The rule set's canonical hash (`ruleSetHash`) is embedded in every epoch. Changing any rule produces a new rule-set version and hash; epochs signed under different rule sets are not comparable and verifiers MUST surface the version.

## QualifiedGmvBurnEpochV1 (portable shape, normative)

The burn-consumable artifact. It is distinct from `VerifiedGmvTokenV1`: GMV tokens are supersedable as-of snapshots; burn epochs are **final-before-consume**.

```text
QualifiedGmvBurnEpochV1 {
  tokenType: "QUALIFIED_GMV_BURN_EPOCH",
  schemaVersion: 1,
  protocolVersion: String,            // single canonical version surface

  window: { type: "UTC_DAY", date: DateISO },

  finalityCutoff: TimestampISO,       // >= window end + T_final
  correctionCutoff: TimestampISO,     // last instant corrections were observable

  ruleSetHash: "sha256:" + Hash,      // QualifiedGmvRuleSetV1 pin (GMV qualification rules)
  policyHash: "sha256:" + Hash,       // IssuerPolicyCommitment hash (Phase 1) — binds usd_per_receipt + crinkl_price BY VALUE; proves the reward without a trusted read

  qualified: {
    currency: "USD",
    gmvCents: Amount,                 // QG contribution of this window
    settledRevenueCents: Amount,      // SR contribution; MUST be "0" until paid-settlement artifacts are normative
    spendCount: Integer
  },

  spendHeadSetRoot: "sha256:" + Hash, // Merkle root of counted spend heads

  // Reserved forward fields — present in the shape and the commitment preimage
  // from V1 so layout stays stable as later phases land; NON-LIVE until then,
  // encoded as 32 zero bytes (the zero hash) while null.
  spendElectionRoot: "sha256:" + Hash | null, // Phase 3 — per-spend reward election (btc/crinkl/alternate/none); enables GMV cross-check + claim derivation
  claimRoot: "sha256:" + Hash | null,         // Phase 4 — root of CRINKL/alternate claim commitments funded from this epoch's emission

  cumulative: {
    inputBeforeCents: Amount,             // A before this epoch
    inputAfterCents: Amount,              // A after this epoch
    depletionBeforeBaseUnits: Amount,     // D(A_before) — TOTAL pool depletion (burn + emission)
    depletionAfterBaseUnits: Amount,      // D(A_after)
    depletionDeltaBaseUnits: Amount       // tranche = D(A_after) − D(A_before); split atomically into emission + burn at execute
  },

  // Atomic split of this epoch's tranche (depletionDeltaBaseUnits), recorded for
  // auditability. emission + burn == depletionDeltaBaseUnits, always.
  split: {
    rewardAskUsdCents: Amount,            // issuer-policy reward ask in USD cents, resolved from policyHash
    rewardEmissionBaseUnits: Amount,      // emission = min( rewardAsk ÷ posted_price, depletionDelta )
    burnBaseUnits: Amount                 // burn = depletionDelta − emission (the residual)
  },

  prevEpochHash: "sha256:" + Hash,    // hash chain; genesis epoch uses the zero hash

  signatures: { issuedBy: AuthorityId, publicKey: Base64, tokenHash: Hash, signature: Base64 },

  finality: {                         // ProofFinalizationCertificateV1 over the epoch commitment
    validatorSetSeq: Integer,         // pinned-set rotation sequence the quorum was formed under
    threshold: Integer,               // M required of the pinned set
    signatures: [ { publicKey: Base64, signature: Base64 } ]  // ed25519 over the commitment hash
  }
}
```

## GMV finality trust root (normative)

**Decision 2026-06-12 (Alvin):** GMV finality for burn consumption is **joint** — a platform root AND a proof-validator root. Neither alone may move the reserve.

1. **Platform root.** The consumption transaction MUST be signed by the issuer key pinned in on-chain program config (the attestation-gateway authority).
2. **Proof-validator root.** The transaction MUST carry at least `threshold` distinct ed25519 signatures from the pinned proof-validator set over the **epoch commitment hash** — the on-chain form of `ProofFinalizationCertificateV1`.

Rules, each load-bearing:

- **The commitment hash MUST be recomputed on-chain** from the posted instruction fields (domain tag `CRINKL_DENSITY_BURN_EPOCH_V1`, then `windowDay`, `finalityCutoff`, `correctionCutoff`, `gmvCents`, `settledRevenueCents`, `spendCount`, `spendHeadSetRoot`, `spendElectionRoot`, `ruleSetHash`, `policyHash`, `claimRoot`, `prevEpochHash`, `inputBeforeCents`, `depletionBeforeBaseUnits`; SHA-256; little-endian integers). Every certified CLAIM is in the preimage — including `spendCount` and the two cutoffs — so displayed metadata cannot diverge from the certified hash. The reserved roots `spendElectionRoot` and `claimRoot` are part of the preimage from V1 — encoded as 32 zero bytes while null (Phases 3/4) — so they transition from sentinel to real hash with no preimage-version change. A signature over any hash the program did not recompute MUST NOT count — the quorum vouches for the GMV figure itself, never for an opaque hash.
- **Output cumulative fields are recomputed, not bound.** `inputAfterCents`, `depletionAfterBaseUnits`, `depletionDeltaBaseUnits`, and the `split` (emission/burn) are NOT in the preimage: the program derives them deterministically from the bound `inputBeforeCents` + `depletionBeforeBaseUnits` + the bound inputs (`gmvCents`, `settledRevenueCents`) + the schedule + the posted price. Binding `before` anchors the chain; binding outputs too would be redundant and could only introduce a divergence the program would have to reject anyway.
- **Finality metadata is not in the preimage, by design.** `validatorSetSeq`, `threshold`, and `finality.signatures` describe the signature envelope, not the claim. The program enforces them against the pinned validator-set in program state (a stronger check than self-attested values would be); they cannot be bound in the very commitment they sign.
- **Validator-set pinning.** The trusted validator set lives in program state, rotated only by a distinct validator-set authority. The certificate carries no information about its own validator set; embedded-key / self-referential certificate trust is non-conformant (proof-validator security audit, trust-model reconciliation 2026-06-10).
- **Root separation.** The issuer key MUST NOT be a member of the validator set, so the joint root can never collapse to one key. The validator-set authority SHOULD be operationally distinct from the issuer.
- **Initialization gating.** Program initialization MUST be restricted to the program upgrade authority (PDAs are mint-deterministic; an unrestricted initialize is front-runnable).
- **Reward-split inputs are platform-only.** `rewardUsdCents` and the posted token price are signed by the issuer transaction but are NOT part of the oracle-certified commitment: the oracle vouches for GMV finality, not pricing. The depletion schedule is price-invariant by construction, so a corrupted price can only shift the burn/emission split within an already-fixed tranche.

**Maturity caveat (normative for external claims).** The proof-validator role is open by conformance and economic exposure through the authority registry, and PriceChain Labs is currently the sole reference operator on the alpha network. The certificate expresses an identity/threshold quorum; the quorum is not economically bonded or staked. Economic bonding, staking, and slashing are deferred to Phase 5 and are not live. Public surfaces MUST NOT describe the quorum as economically bonded or staked before Phase 5.

### Policy binding (Phase 1 ↔ Phase 2) (normative)

Every epoch carries `policyHash` — the **composite** `IssuerPolicyCommitment` hash
([issuer-policy-commitment.md](issuer-policy-commitment.md)) in force for the
window: `SHA-256(canonical({ group_a_config_hash (on-chain c/K/λ/pool/revenue),
issuer_application_policy_hash (platform usd_per_receipt/crinkl_price/…), identity }))`.
The reward per qualified spend is derived from the **hashed** policy, not from
trusted inputs: `reward_crinkl = policy.usd_per_receipt ÷ policy.crinkl_price`.
Tracing `policyHash` to its component hashes yields the exact values, so the
emission figure is provable with no trusted DB read.

> **NON-LIVE (2026-06-16):** the platform currently emits only the Group-B
> component (`issuer_application_policy_hash`, `crinkl-policy-hash/v2`). The
> composite wrapper binding `group_a_config_hash` + identity is unbuilt, so
> `policyHash` here is NOT yet the full IPC and MUST NOT gate any token movement
> until the composite + on-chain Group A binding ship (Phase 1 completion / Phase 5).

Two trust roots meet in the one commitment and attest different things:

- The **issuer (policy) root** signs the IPC and makes `policyHash` authoritative —
  the reward/price policy is the issuer's to set, and may be a multisig (Phase 6).
- The **proof-validator (finality) root** co-signs the epoch commitment but vouches
  only for GMV finality (`gmvCents`, `spendCount`, `spendHeadSetRoot`), never for
  pricing. It signs over `policyHash` as an opaque member of the bundle; it does
  not certify the policy's values.

This keeps the existing invariant — reward-split inputs are issuer-attested, not
oracle-certified — while making them **provable**: a corrupted price can still
only shift the burn/emission split inside an already-fixed tranche (the depletion
schedule is price-invariant), and now any such shift is detectable by tracing the
committed `policyHash`. `rewardUsdCents` and the posted token price MUST equal the
values resolved from `policyHash`; an epoch whose split inputs disagree with its
committed policy is non-conformant.

### Consumed-state semantics (normative)

- An epoch is **PENDING** from posting until its burn executes on-chain, and **CONSUMED** thereafter.
- A PENDING epoch MAY be superseded by a corrected epoch for the same `window.date` (greater signing time wins, mirroring gmv-token.md supersession). A CONSUMED epoch MUST NOT be superseded, revised, or re-posted — burning is irreversible, so its input must be too.
- Each `window.date` is consumed at most once. The on-chain program MUST reject a second consumption for the same window and MUST verify `inputBeforeCents` / `depletionBeforeBaseUnits` against its own cumulative state, so epochs can only chain, never fork.
- Post-consumption corrections to underlying spends are expressed only as adjustments inside later epochs' qualified totals (downward adjustments floor at zero for the affected window's contribution; `A` never decreases).

## Epoch lifecycle (normative)

1. **Window closes** (UTC day ends).
2. **Observation period** of `T_final` (provisional: 14 days) elapses. Corrections, revocations, and enforcement actions during this period are observable per correction-and-revocation semantics.
3. **Derivation:** the issuer derives qualified totals from the canonical protocol stream — NEVER from public aggregate GET endpoints — applying the pinned `QualifiedGmvRuleSetV1`.
4. **Reconciliation gate:** derived totals are reconciled against (a) the day's latest `VerifiedGmvTokenV1` and (b) the cumulative public GMV projection. Unexplained drift between sources BLOCKS posting.
5. **Sign and post** the epoch (PENDING). The issuer signature and the proof-validator finality certificate (GMV finality trust root, above) are both attached.
6. **Execute tranche:** the on-chain program verifies the issuer signature, the finality-certificate quorum against the pinned validator set, chain linkage, cumulative-state match, and window uniqueness, then recomputes the tranche `depletionDeltaBaseUnits = D(A_after) − D(A_before)` (capped at the reserve balance) and splits it atomically: it routes `rewardEmissionBaseUnits = min(rewardAsk ÷ posted_price, tranche)` to the rewards escrow and BURNS the residual `burnBaseUnits = tranche − emission` from the DDR. Total reserve depletion this epoch equals the tranche regardless of the split. Epoch becomes CONSUMED.

## Data Density Reserve semantics (normative)

- **Atomic tranche split:** each consumed epoch computes the tranche
  `D(A_new) − (burned_cum + emitted_cum)` and splits it in one instruction:
  the reward ask (USD at the posted price) up to the tranche goes to the
  rewards escrow; the residual burns. There is no separate emission
  instruction — rewards can never outrun the schedule, and the burn can never
  be front-run by emissions.
- **Depletion identity:** after every consumed epoch,
  `poolBalance = fundedAmount − min(D(A_cum), fundedAmount)` exactly.
- **Exhaustion:** the tranche is capped at the reserve balance (relevant only
  beyond the $500B calibration point). When the reserve reaches zero, both flows
  halt permanently. Schedule beyond the balance is forfeited, never owed.
- **On-chain state:** the program maintains `A_cum`, `D_cum`, `burned_cum`,
  `emitted_cum`, last consumed window, and last epoch hash. All publicly
  readable; `D_cum` (equivalently the reserve balance) is the canonical density
  index, and the burned/emitted split is the price record.

## Parameter governance and the change-gatekeeper (normative)

The economic parameters `c`, `K`, `λ`, and the `revenue_enabled` gate are **mutable
on-chain configuration**, not frozen constants — but only through a two-step
**timelocked gatekeeper** whose purpose is to make any change that could move
mass tokens publicly visible long enough for honest participants to assess and
thwart an attack. The same gate governs the governance roles themselves.

- **Three-role separation of powers.** The `issuer` posts epochs; a
  `governance_authority` proposes and executes parameter changes; a separate
  `guardian` may ONLY veto a pending change and pause epoch consumption. The
  guardian MUST be a distinct key from the governance authority — its veto is
  worthless if a single compromised key can both propose an attack and suppress
  the veto. Each role is a single key today and MAY become a multisig with no
  protocol change.
- **Two-step timelock.** A change is `propose`d as a full snapshot of the mutable
  config; it becomes executable only after `eta = proposed_at + timelock_delay`.
  The full proposed snapshot and `eta` are emitted on-chain so the entire delay
  window is a public warning. The default delay is **48h**; the program enforces
  a hard floor (provisional **24h**) below which the delay can never be set —
  so the gate cannot be timelocked away to near-zero in one proposal. At most
  one change may be pending at a time.
- **Veto.** The guardian or the governance authority MAY cancel a pending change
  at any point before execution. The delay is the warning; the veto is the
  defense.
- **Pause.** Either the guardian or governance MAY pause `consume_epoch`
  immediately (break-glass freeze of all token movement); only the governance
  authority may unpause. Absent a per-epoch rate cap, the pause is the primary
  control that lets honest participants stop the reserve while assessing a
  suspected attack.
- **Validation at propose time.** Proposed values are validated when queued
  (`c,K > 0`, delay ≥ floor, roles distinct and non-default), so an invalid
  change can neither sit queued nor execute.
- `T_final` and the validator set are governed separately (`T_final` is an
  off-chain observation constant; the validator set has its own authority and
  rotation path).

Before the DDR is funded, `c` and `K` MUST be calibrated jointly against the
reward emission schedule so the **deflation crossover** — the input level at
which marginal burn exceeds marginal emission — occurs at an explicitly chosen,
documented adoption level. Canonical v5 calibration: `c = 5,633,706.605995`,
`K = $2,008,032.13`, pinned by `D($1B) = 50%` and `D($500B) = 100%` of the 70M
reserve. Any later recalibration travels through the gatekeeper above.

Golden vectors at `A ∈ {0, $250M, $290M, $1B, $5B, $500B}` plus both crossover-adjacent points MUST be generated from the reference fixed-point implementation and added to ../07-conformance/vectors.md before any on-chain consumption.

## Interaction with reward emission (non-normative)

Reward policy denominates rewards in USD. Token-denominated emission per receipt therefore varies inversely with token price, and reserve longevity is endogenous: the same density index that consumes the reserve also informs the market that prices the emission. The Data Density Reserve makes the two flows compete for one balance — fast verified growth permanently reduces the maximum tokens that can ever be emitted. This race is the designed behavior, not a hazard to be engineered away.

## Per-spend burn attribution (non-normative)

Because each epoch commits to `spendHeadSetRoot`, an issuer can furnish a per-spend inclusion proof that a specific spend was counted in a specific consumed epoch. A user can therefore prove "this spend contributed to this burn" without revealing identity and without the epoch revealing anything per-user. Surfaces MAY expose this as a shareable artifact; the epoch itself carries no per-user data.

## Migration from the supply release model (non-normative)

Density Burn supersedes the GMV-indexed supply release model (80M escrow, rate-based release). Migration requirements:

- The historical off-chain "released" ledger is archived and its balance assigned to an explicit legacy bucket; no retroactive on-chain movement is implied (the old escrow shows no outbound movement to reverse).
- The validator allocation (provisionally 10M) is carved out before DDR funding.
- The DDR is funded only after the program is audited and golden vectors pass.
- Public tokenomics surfaces describing the release model MUST be replaced before the first epoch is consumed.

## Conformance (to be added to 07-conformance)

- Curve vectors: `B(A)` at the golden inputs, bit-exact.
- Epoch chain vectors: valid chain, forked-chain rejection, duplicate-window rejection, cumulative-state mismatch rejection.
- Rule-set vectors: duplicate leaf, enforcement hold, pre-finality spend, high-total policy, rolled-forward correction.
- Data Density Reserve vectors: burn precedence over same-window emission, exhaustion capping, post-exhaustion halt.
- Non-zero `settledRevenueCents` MUST be rejected while the paid-settlement artifact remains undefined.
- Gatekeeper vectors: propose by non-governance rejected; sub-floor delay rejected; non-distinct roles rejected; execute-before-`eta` rejected; second concurrent proposal rejected; guardian veto and governance self-cancel clear the queue; `consume_epoch` rejected while paused; guardian-unpause rejected (governance only); revenue enablement reaches `A` only after a consumed epoch following a successfully executed enable.
- Trust-root vectors: missing certificate, below-threshold certificate, duplicate signatures from one validator counted once, signatures from unpinned keys, quorum over a non-recomputed hash, post-rotation rejection of the previous committee, issuer-in-validator-set rejection, non-upgrade-authority initialization rejection.
