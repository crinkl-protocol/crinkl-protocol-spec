---
status: draft
layer: reference
version: v1
normative: false
protocol: 1.0.0-rc.2
revision: 2026-07-16
supersedes: Standalone CRINKL Tokenomics White Paper series (v1–v8, 2025–2026), archived
---

# CRINKL Tokenomics — Reference

> **Authority note.** This document is a non-normative narrative view of the CRINKL
> token economy. The normative definitions live in
> [`05-reward-and-settlement/`](../../05-reward-and-settlement/), principally
> [`density-burn.md`](../../05-reward-and-settlement/density-burn.md),
> [`issuer-policy-commitment.md`](../../05-reward-and-settlement/issuer-policy-commitment.md),
> [`policy-layer.md`](../../05-reward-and-settlement/policy-layer.md), and
> [`election-commitment.md`](../../05-reward-and-settlement/election-commitment.md).
> **Where this document and the spec disagree, the spec wins** (see
> [`08-governance/change-process.md`](../../08-governance/change-process.md), Authority
> Hierarchy). Business-policy statements in this document are deployment disclosures by
> PriceChain Labs, not protocol rules; they are labeled as such.

## Abstract

CRINKL is a fixed-supply token driven by a single measurement: cumulative qualified
network activity — cryptographically verified, identity-free evidence that real-world
commerce occurred. As that measurement grows, a 70,000,000-token Shared Reward–Burn
Pool depletes on a deterministic schedule. Tokens leave the pool in exactly two ways:
earned by the users whose receipts created the evidence, or permanently burned.
Nothing is minted, and the pool itself releases nothing on a clock — the only clock in
the release schedule is commerce.

Run to completion, the mechanism hands majority ownership of the network to the people
who proved its commerce, and leaves brands one way to reach them at end state:
campaigns funded in CRINKL, acquired from the users who earned it.

## 1. The measurement

The spec's canonical burn input (density-burn.md § Burn Input `A`) is:

```
A = QG + λ · SR
```

- `QG` — cumulative **Qualified GMV**: finalized spend totals passing the hash-pinned
  `QualifiedGmvRuleSetV1` at each epoch's finality cutoff.
- `SR` — cumulative **settled campaign revenue**. Normatively `SR = 0` in every epoch
  until a paid-settlement artifact exists in the spec; settlement *commitments* never
  count.
- `λ` — the revenue weight (33): one dollar of settled revenue counts as thirty-three
  dollars of pass-through GMV, pricing committed economic activity above raw volume
  (~3% take-rate equivalence).

The earlier marketing name for `A` was **Verified Commerce Density (VCD)**. This
document retains "density" as narrative shorthand; the spec's `A` is canonical.

`A` is monotonically non-decreasing, denominated in integer USD cents, and derived
from the canonical protocol stream — never from public aggregate endpoints.

## 2. Fixed supply and allocation *(business disclosure)*

Total supply is 100,000,000 CRINKL, minted once at genesis. No minting function
exists. Supply is monotonically non-increasing for the life of the protocol.

| Allocation | Tokens | Share | Mandate |
|---|---|---|---|
| Shared Reward–Burn Pool (SRBP) | 70,000,000 | 70% | Sole source of reward emission; the only burnable supply |
| Oracle Proof Network | 10,000,000 | 10% | Validator incentives (staking/slashing: Phase 5) |
| PriceChain Labs Treasury | 10,000,000 | 10% | Operations & reserve — **3-year vesting schedule, in place by beta launch** |
| Market Maker / Liquidity | 10,000,000 | 10% | Secondary-market depth |

The SRBP figure is the former 80M rewards escrow less the 10M validator carve-out
(density-burn.md § Migration). The pool is a program-owned account with **exactly two
exits** — reward emission and density burn. No withdrawal instruction, no
emergency-withdraw path. Any program exposing a third exit is non-conformant.

## 3. The machine

The depletion schedule (normative in density-burn.md) maps cumulative input to
cumulative **total** pool depletion — burn plus emission together:

```
D(A) = floor( c · ln(1 + A / K) )
```

| Parameter | Value | Meaning |
|---|---|---|
| `c` | ≈ 5,633,706.6 CRINKL | Schedule scale = 70M / ln(1 + $500B/K) |
| `K` | $2,008,032.13 | Curve knee; the unique K with D($1B) = ½·D($500B) |
| `λ` | 33 | Revenue weight inside `A` |

Calibration anchors (normative): **D($1B) = 50%** of the funded pool;
**D($500B) = 100%**. Required properties of any recalibration: monotone, concave,
bounded, deterministic (fixed-point integer arithmetic, floor-only rounding on the
cumulative value).

### Parameter governance — stated plainly

`c`, `K`, `λ`, and the `revenue_enabled` gate are **mutable on-chain configuration**,
changeable only through the spec's two-step timelocked gatekeeper (density-burn.md
§ Parameter governance): propose → 48h public timelock (hard floor 24h) → execute,
with a distinct **guardian** key holding veto and pause powers, three-role separation
(issuer / governance authority / guardian), and at most one pending change at a time.

Earlier standalone editions of this paper said "no one holds a lever over the
schedule." The accurate statement is: **the shape of the machine is fixed — its
calibration is mutable only through a public, delayed, vetoable process.** The pool
size, the two-exit rule, the rewards-first split, and the required curve properties
are structural invariants outside the gatekeeper's reach.

## 4. One pool, two exits

Each consumed epoch computes the tranche `D(A_new) − D(A_old)` and splits it
**atomically** (density-burn.md § Pool semantics):

```
emission = min( reward ask ÷ posted price , tranche )
burn     = tranche − emission
```

Emission is paid first; the burn is the residual. Because both exits draw one budget,
every burned token is a reward the pool could have paid — a costly signal. Price moves
the split; it can never move the depletion path.

Per the spec's **explicit non-claims**: a density-burn epoch is **not a buyback** (no
tokens are acquired from any market), not a redemption right, not a dividend, and
implies no price claim. Any market purchases by verification services (see § 6) are
business activity, categorically distinct from the burn.

## 5. The reward

Rewards are denominated in USD and set by **verification-service policy, not
protocol** — currently $0.10 per qualified receipt at the PriceChain-operated service.
Each service prices its own rate: it must incentivize receipt supply to have proofs
and campaigns to sell, and it bears the real cost of acquisition. The rate and posted
token price are bound by the hash-committed `IssuerPolicyCommitment`
(issuer-policy-commitment.md), so `reward_crinkl = usd_per_receipt ÷ crinkl_price` is
provable without any trusted database read.

- **Payout election.** Earners elect CRINKL or BTC per reward
  (election-commitment.md; on-chain `spendElectionRoot`: Phase 3). BTC-elected rewards
  are paid off-pool in hard currency by the paying verification service; the
  corresponding pool slice burns instead of emits. The election changes the mix, never
  the total.
- **Earner reward vesting** *(planned, parameters TBD)*: earned rewards will vest
  before becoming liquid. This amends prior editions' "no vesting, no cliff, no
  unlock" language. Release from the pool remains activity-gated; the vest applies to
  liquidity. Open items: vest symmetry across the CRINKL/BTC election, and whether
  granted-but-unvested rewards count against the pool identity at grant or at vest.

## 6. Demand and the return flow

**Depletion era (current).** Brands may fund campaigns in USD or USDC. The ingesting
verification service retains that revenue to fund operations and growth, and decides —
at its own discretion, with no protocol-set rate — how much to recycle into
open-market CRINKL buybacks. Such purchases are business activity, not protocol burn.

**End state.** At full retirement, campaigns are funded only in CRINKL, acquired on
the open market — where the sellers are, by construction, the users and validators who
earned it. Ownership transfers along the way: validators and the market maker
distribute into the market during the density burn, and the issuer's own allocation is
vesting-constrained.

*Open item:* because D(A) approaches 70M asymptotically, "full retirement" is not
reached in finite time below the $500B density target. The sunset trigger for fiat
campaign funding (a depletion percentage or density milestone) is not yet specified.

## 7. Commercial capacity *(illustrative, non-normative)*

Across paid uses combined, the model applies **1% of Qualified GMV** as an
illustrative mature-network revenue equivalent. It is not a take rate, a forecast, or
revenue automatically earned. Only revenue that is actually settled enters `A`, and
only after `revenue_enabled` is executed through the gatekeeper and a paid-settlement
artifact is normative.

## 8. End state

At full retirement on default drivers: ≈43M CRINKL earned by users receipt-by-receipt;
≈27M permanently burned (supply 100M → ≈73M); 10M distributed to validators; 10M
distributed by the market maker; 10M held by the issuer (post-vest, ± market activity).
The majority owners of the network are the people who proved its commerce — by
construction, not policy.

## 9. Roadmap *(forward-looking, not commitments)*

| Item | Status | Spec anchor |
|---|---|---|
| Composite IssuerPolicyCommitment binding (Group A + B) | Phase 1 completion | issuer-policy-commitment.md |
| Per-spend reward election on-chain | Phase 3 (`spendElectionRoot`) | density-burn.md |
| Claim commitments funded from epochs | Phase 4 (`claimRoot`) | density-burn.md |
| Validator token staking/slashing | Phase 5 — planned for mainnet | density-burn.md § Maturity caveat |
| Issuer multisig | Phase 6 | density-burn.md |
| Verification-service staking for slashing | Under consideration (mainnet) | — |
| Earner reward vesting | Planned; parameters TBD | § 5 above |
| Issuer treasury 3-year vest | Committed; in place by beta | § 2 above |
| CBSA population-gated rewards | Under consideration (possibly beta): per-tranche reward budgets apportioned across US CBSAs by population; a CBSA's share emits once it crosses activation thresholds (~150 wallets · 10 receipts/month). Dormant-slice treatment (burn vs. roll) TBD | — |

## 10. Risks & considerations

1. **Low token price accelerates emission.** USD-fixed rewards emit more CRINKL per
   receipt as price falls; the pool drains fastest when the project is weakest.
   Dampers: earner vesting delays the resulting sell pressure (not the drain), and
   reward rates are service policy, repriceable downward.
2. **BTC election is a hard-currency acquisition cost** borne by the paying
   verification service — largest in downturns, invisible on pool charts.
3. **Burn is a residual** and is only legible alongside total depletion, election mix,
   emitted CRINKL, and BTC-paid rewards. Never a standalone health signal.
4. **Sensitivity to λ.** Once revenue is live, λ dominates `A`; λ is also inside the
   gatekeeper's mutable set. Small revisions materially reshape the deflation path.
5. **Input-inflation bound.** The concave, bounded schedule caps the damage of any
   fake-input attack: even unbounded fraudulent input asymptotically depletes only
   what the pool holds (density-burn.md, required property 3).

## Parameter reference

| Parameter | Value | Class |
|---|---|---|
| Total supply | 100,000,000 | Structural invariant |
| Shared pool (SRBP) | 70,000,000 | Structural invariant (two exits only) |
| Split rule | Emission-first; burn = residual | Structural invariant |
| Curve properties | Monotone · concave · bounded · deterministic | Structural invariant |
| `c` | ≈ 5,633,706.6 CRINKL | Mutable via timelocked gatekeeper |
| `K` | $2,008,032.13 | Mutable via timelocked gatekeeper |
| `λ` | 33 | Mutable via timelocked gatekeeper |
| `revenue_enabled` | off (SR must equal 0) | Mutable via timelocked gatekeeper |
| Reward per receipt | $0.10 (current) | Verification-service policy (IPC-bound) |
| Posted token price | per IPC | Verification-service policy (IPC-bound) |
| `T_final` | 14 days (provisional) | Off-chain observation constant |
| Issuer treasury vest | 3 years from beta | Business commitment |

---

*All normative semantics: [`05-reward-and-settlement/density-burn.md`](../../05-reward-and-settlement/density-burn.md).
This document is a reference narrative and is not an offer, solicitation, or financial
advice. Scenario figures are illustrative projections under stated default drivers.*
