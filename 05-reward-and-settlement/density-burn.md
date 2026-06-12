---
status: draft
layer: reward-settlement
version: v1
normative: true
---

# Density Burn

> "Verified spend density must be provable on-chain as a single monotonic figure — and publishing that figure must cost the issuer future emissions."

Density Burn is a supply-accounting mechanism that consumes CRINKL tokens from the **Shared Reward–Burn Pool** as a deterministic function of cumulative qualified network activity. It replaces the prior GMV-indexed supply *release* model: where the old model emitted escrowed tokens in proportion to GMV, Density Burn destroys pool tokens in proportion to qualified GMV — from the **same pool that funds user reward emissions**. Every burned token is a token that would otherwise have remained available for future reward emission.

This shared-pool property is load-bearing and MUST NOT be weakened: a burn drawn from a reserve with no alternative fate carries no economic information. The burn is credible precisely because it consumes the protocol's own emission budget.

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

### Shared Reward–Burn Pool (SRBP)

A single program-owned (PDA) token account holding the protocol's reward emission budget.

- Initial funding: the former rewards escrow less the validator allocation (provisionally 70,000,000 CRINKL = 80M − 10M validators; see Migration below).
- Exactly **two** exits, both protocol-defined:
  1. **Reward emission** — transfers governed by the reward policy layer (reward-layer.md, policy-layer.md).
  2. **Density burn** — irreversible burns governed by this document.
- NO withdrawal instruction, NO emergency-withdraw path, NO upgrade authority after parameter freeze. Any program exposing a third exit from the SRBP is non-conformant.

### Burn Input `A`

The cumulative qualified activity measure, in integer USD cents:

```text
A = QG + λ · SR
```

- `QG` — cumulative **Qualified GMV**: finalized spend totals that pass `QualifiedGmvRuleSetV1` (below) at the epoch's finality cutoff.
- `SR` — cumulative **settled campaign revenue**: sponsor funds actually received and recognized via a paid-settlement/debit artifact. The campaign settlement layer currently excludes sponsor pricing, funding, and payout rails from proof scope (campaign-settlement-gcd.md); therefore `SR` MUST equal `0` in every epoch until a normative paid-settlement artifact exists in this spec. Implementations MUST NOT substitute settlement *commitments* for settled revenue.
- `λ` (lambda) — the revenue weight, expressing how many dollars of raw spend-through one dollar of paid revenue is equivalent to. Provisional value: `33` (an implied ~3% take-rate equivalence).

`A` is monotonically non-decreasing. Corrections to historical spends roll forward into later epochs (see Lifecycle); they never restate a consumed epoch.

### Density curve `B(A)`

The cumulative burn entitlement, in token base units (CRINKL has 6 decimals):

```text
B(A) = floor( c · ln(1 + A / K) )
```

Provisional parameters (frozen as deployment constants after recalibration; see Parameters):

| Parameter | Provisional value | Meaning |
|---|---|---|
| `c` | 5,460,000 CRINKL | curve scale |
| `K` | $52,500,000 (in cents) | density half-scale: input at which marginal burn has decayed to half its initial rate is reached near `K` |
| `λ` | 33 | revenue weight inside `A` |

Required properties (normative — any recalibrated curve MUST preserve all four):

1. **Monotone:** `B` is non-decreasing in `A`.
2. **Concave:** marginal burn per dollar strictly decreases as `A` grows — early density is weighted most ("density" is the design intent, not decoration).
3. **Bounded:** cumulative burn can never exceed the SRBP balance; entitlement beyond the balance is forfeited, not deferred (see Pool semantics). The curve's slow growth additionally bounds the damage of any input inflation: even unbounded fake input asymptotically burns only what the pool holds.
4. **Deterministic:** computed in fixed-point integer arithmetic with floor-only rounding on the *cumulative* value. Per-epoch burns are differences of cumulative values, never independently rounded.

Reference magnitudes under provisional parameters (illustrative; bit-exact golden vectors are produced by the reference implementation before freeze):

| `A` | `B(A)` approx | Marginal burn (tokens per $1 GMV) |
|---|---|---|
| $0 | 0 | 0.104 |
| $250M | 9.56M | 0.018 |
| $290M | 10.24M | 0.016 |
| $1B | 16.37M | 0.0052 |
| $5B | 24.93M | 0.0011 |
| $500B | ~50.0M | ~0.00001 |

At `A = 0`, $1 of settled revenue burns `λ · c / K ≈ 3.43` tokens.

### QualifiedGmvRuleSetV1

A versioned, hash-pinned rule set defining which finalized spends count toward `QG`. It MUST cover, at minimum:

- duplicate-leaf rejection (a spend head contributes to `A` at most once, ever, across all epochs);
- eligibility (structural validity per ../01-core/verification-state.md);
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

  ruleSetHash: "sha256:" + Hash,      // QualifiedGmvRuleSetV1 pin

  qualified: {
    currency: "USD",
    gmvCents: Amount,                 // QG contribution of this window
    settledRevenueCents: Amount,      // SR contribution; MUST be "0" until paid-settlement artifacts are normative
    spendCount: Integer
  },

  spendHeadSetRoot: "sha256:" + Hash, // Merkle root of counted spend heads

  cumulative: {
    inputBeforeCents: Amount,         // A before this epoch
    inputAfterCents: Amount,          // A after this epoch
    burnBeforeBaseUnits: Amount,      // B(A_before)
    burnAfterBaseUnits: Amount,       // B(A_after)
    burnDeltaBaseUnits: Amount        // burnAfter − burnBefore
  },

  prevEpochHash: "sha256:" + Hash,    // hash chain; genesis epoch uses the zero hash

  signatures: { issuedBy: AuthorityId, publicKey: Base64, tokenHash: Hash, signature: Base64 }
}
```

### Consumed-state semantics (normative)

- An epoch is **PENDING** from posting until its burn executes on-chain, and **CONSUMED** thereafter.
- A PENDING epoch MAY be superseded by a corrected epoch for the same `window.date` (greater signing time wins, mirroring gmv-token.md supersession). A CONSUMED epoch MUST NOT be superseded, revised, or re-posted — burning is irreversible, so its input must be too.
- Each `window.date` is consumed at most once. The on-chain program MUST reject a second consumption for the same window and MUST verify `inputBeforeCents` / `burnBeforeBaseUnits` against its own cumulative state, so epochs can only chain, never fork.
- Post-consumption corrections to underlying spends are expressed only as adjustments inside later epochs' qualified totals (downward adjustments floor at zero for the affected window's contribution; `A` never decreases).

## Epoch lifecycle (normative)

1. **Window closes** (UTC day ends).
2. **Observation period** of `T_final` (provisional: 14 days) elapses. Corrections, revocations, and enforcement actions during this period are observable per correction-and-revocation semantics.
3. **Derivation:** the issuer derives qualified totals from the canonical protocol stream — NEVER from public aggregate GET endpoints — applying the pinned `QualifiedGmvRuleSetV1`.
4. **Reconciliation gate:** derived totals are reconciled against (a) the day's latest `VerifiedGmvTokenV1` and (b) the cumulative public GMV projection. Unexplained drift between sources BLOCKS posting.
5. **Sign and post** the epoch (PENDING).
6. **Execute burn:** the on-chain program verifies the issuer signature, chain linkage, cumulative-state match, and window uniqueness, then burns exactly `burnDeltaBaseUnits` from the SRBP, capped at the pool balance. Epoch becomes CONSUMED.

## Pool semantics (normative)

- **Burn precedence:** for a given epoch window, the burn executes before reward-emission claims attributable to that window are processed. The burn is senior to emission — emissions may not drain the pool ahead of an already-finalized burn entitlement.
- **Exhaustion:** executed burn = `min(burnDeltaBaseUnits, poolBalance)`. When the pool reaches zero, both exits halt permanently. Unexecuted entitlement is forfeited, never owed.
- **On-chain state:** the program maintains `A_cum`, `B_cum`, last consumed window, and last epoch hash. All four are publicly readable; `B_cum` is the canonical density index.

## Parameters and recalibration (normative once frozen)

`c`, `K`, `λ`, and `T_final` are deployment constants, immutable after freeze. Before freeze, `c` and `K` MUST be recalibrated jointly against the reward emission schedule so that the **deflation crossover** — the input level at which the marginal burn rate exceeds the marginal emission rate — occurs at an explicitly chosen and documented adoption level. The provisional values above were calibrated for a standalone 50M reserve and are expected to change for the shared pool.

Golden vectors at `A ∈ {0, $250M, $290M, $1B, $5B, $500B}` plus both crossover-adjacent points MUST be generated from the reference fixed-point implementation and added to ../07-conformance/vectors.md before any on-chain consumption.

## Interaction with reward emission (non-normative)

Reward policy denominates rewards in USD. Token-denominated emission per receipt therefore varies inversely with token price, and pool longevity is endogenous: the same density index that consumes the pool also informs the market that prices the emission. The shared pool makes the two flows compete for one balance — fast verified growth permanently reduces the maximum tokens that can ever be emitted. This race is the designed behavior, not a hazard to be engineered away.

## Per-spend burn attribution (non-normative)

Because each epoch commits to `spendHeadSetRoot`, an issuer can furnish a per-spend inclusion proof that a specific spend was counted in a specific consumed epoch. A user can therefore prove "this spend contributed to this burn" without revealing identity and without the epoch revealing anything per-user. Surfaces MAY expose this as a shareable artifact; the epoch itself carries no per-user data.

## Migration from the supply release model (non-normative)

Density Burn supersedes the GMV-indexed supply release model (80M escrow, rate-based release). Migration requirements:

- The historical off-chain "released" ledger is archived and its balance assigned to an explicit legacy bucket; no retroactive on-chain movement is implied (the old escrow shows no outbound movement to reverse).
- The validator allocation (provisionally 10M) is carved out before SRBP funding.
- The SRBP is funded only after the program is audited and golden vectors pass.
- Public tokenomics surfaces describing the release model MUST be replaced before the first epoch is consumed.

## Conformance (to be added to 07-conformance)

- Curve vectors: `B(A)` at the golden inputs, bit-exact.
- Epoch chain vectors: valid chain, forked-chain rejection, duplicate-window rejection, cumulative-state mismatch rejection.
- Rule-set vectors: duplicate leaf, enforcement hold, pre-finality spend, high-total policy, rolled-forward correction.
- Pool vectors: burn precedence over same-window emission, exhaustion capping, post-exhaustion halt.
- Non-zero `settledRevenueCents` MUST be rejected while the paid-settlement artifact remains undefined.
