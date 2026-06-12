---
status: draft
layer: reward-settlement
version: v1
normative: false
---

# Density Burn Rationale — Why One Pool, Not Two

This document records why the Density Burn design merged the Data Density Burn Reserve (50M) and the User Rewards pool (20M) into a single Shared Reward–Burn Pool (70M), replacing the original two-bucket allocation. It is non-normative; the mechanism itself is defined in density-burn.md.

## The original design

```text
50,000,000 — Data Density Burn Reserve   (sealed; only exit: burn)
20,000,000 — User Rewards                (sealed; only exit: emission)
```

Each bucket immutable, single-exit, independent. The burn reserve consumes along the density curve; the reward pool emits per reward policy. Neither touches the other.

## The flaw, found by removal test

Run the standard reduction on the burn itself:

> Remove every burn event and replace the 50M reserve with an immutably locked account. What changes economically?

Nothing. Under the sealed design, the 50M can never circulate **whether or not it burns**. Maximum circulating supply is fixed at 50M the moment the program deploys. Each burn moves tokens from "locked forever" to "destroyed" — two states no market participant can distinguish, because neither state's tokens can ever be held, sold, or emitted.

A burn creates scarcity only relative to a counterfactual in which the burned tokens would otherwise have circulated. The prior supply-release model *was* that counterfactual: the 80M escrow had a live, GMV-driven release path. The sealed two-bucket design deleted the release path for the 50M and kept the burn — which deleted the burn's economic meaning.

The killing detail: the critique "the burn is fake; the float was always 50M" is not FUD against the sealed design. It is *correct*. A mechanism whose honest description refutes its own purpose cannot anchor a long-lived narrative.

## What the burn actually is — and why that made the flaw matter more, not less

The burn is a **Schelling point**: a single, monotonic, immutable, non-repudiable on-chain figure that compresses "is this network's verified spend real and growing?" into one number anyone can coordinate on. That index function is legitimate and is the design intent — *data density, provable on-chain*.

But an index moves markets only as long as it is believed, and signaling theory is unambiguous about what sustains belief: **a signal is credible in proportion to what it costs the sender.** Burning tokens the issuer could never sell, emit, or otherwise use costs the issuer nothing. A costless signal backed by a factually true refutation is the weakest possible foundation for a coordination point. Float-neutral reserve burns have a consistently poor record of holding price for exactly this reason — not because markets don't see the index, but because they see it is free to print.

So the sealed design's problem was not that the Schelling-point theory was wrong. It was that the sealed design was the weakest possible implementation of it.

## The fix: make the signal costly

Merge the buckets. One pool, two exits:

```text
70,000,000 — Shared Reward–Burn Pool
              exit 1: reward emission (per reward policy)
              exit 2: density burn   (per density curve)
              no third exit, ever
```

Now every burned token is a token that would otherwise have remained available for future reward emission. The burn consumes the protocol's own user-acquisition budget, in public, in proportion to verified spend density. Four things change at once:

1. **The index is unchanged.** Same curve, same concavity, same daily heartbeat, same single on-chain number (`B_cum`). Nothing about the Schelling point is lost.
2. **The signal becomes costly.** The issuer provably forfeits emission capacity with every epoch. That is a real, measurable cost — the property that makes signals believable.
3. **The refutation dies.** "The burn is fake" is now simply false: every burn measurably reduces the maximum tokens that can ever be emitted.
4. **The belief loop gains a mechanical backstop.** Rewards are denominated in USD, so token-denominated emission varies inversely with price; pool longevity is endogenous to the same index the burn publishes. Under the sealed design that loop ran on belief alone. Under the shared pool, if belief wavers, mechanics remain: fast growth still permanently shrinks eventual float.

## What the race means

The merged pool turns a static allocation into a contest the protocol cannot rig:

- **Fast verified growth** → the burn front-runs emissions; substantially more than 50M may never reach circulation; rewards become scarcer per token while the index that scarcified them is the same one telling the market why.
- **Slow growth** → emissions draw the pool down over years and the burn consumes what remains.

Either path is honest. The split between burned and emitted is determined by verified spend, not by the issuer — which is also the only claim the published tokenomics needs to make.

## What is preserved, what is given up

**Preserved:** the 50/20 split survives as a *calibration target*. Curve constants are chosen so that at target adoption cumulative burn approaches ~50M, leaving ~20M for emission. The published allocation remains truthful as expected values.

**Given up:** the enforced boundary between the buckets — deliberately, because the boundary was the thing that made the burn vacuous. Also given up: the comfort of a fixed reward budget. The reward pool can be eaten from above by its own success. That is the cost of the signal, and the cost is the point.

## Consequences that bind the implementation

Making the burn economically real re-arms the attacks that vacuousness used to absorb. These move from advisory to mandatory:

- **Finality-locked burn input** (`QualifiedGmvBurnEpochV1`, final-before-consume): an economically meaningful burn against a supersedable input is a type error with real money attached.
- **Self-dealing bounds:** the curve-scale choice (K = $52.5M, not $22M) now binds, because manufactured input genuinely destroys emission capacity and genuinely signals. The bounded, concave curve is the principal damage cap.
- **Burn seniority:** emission claims for a window cannot front-run that window's finalized burn entitlement, or the costly-signal property leaks.
- **Settled revenue stays at zero** until a paid-settlement artifact exists. A costly signal fed by unverifiable revenue would reintroduce the original credibility hole through the side door.

## One-line summary

A burn from a sealed reserve is a free signal with a true refutation; a burn from the emission budget is a costly signal with none — same index, same curve, one pool.
