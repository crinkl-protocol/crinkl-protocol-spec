---
title: Campaign Direct Buyer Reward Profile
status: released
release: 1.0.0-rc.3
conformance-suite: 2
---

# Campaign Direct Buyer Reward Profile

This released profile publishes the same sponsor-neutral direct buyer-reward
profile adopted in the internal Crinkl Protocol workbench. Its exact engineering
source is `crinkl-protocol` commit
`8c641f57201c75bac12819a0f903ae6105c7f3c3`.

The public package is authenticated by the authority-accepted `v1.0.0-rc.3` tag
and release-manifest digest. Publication does not itself authorize a Campaign
compiler, validator admission, funding, launch, or settlement.

## Profile composition

The profile is exactly:

```text
one immutable CampaignEpochV1
+ rewardPolicyRef resolving to one CampaignDirectBuyerRewardPolicyV1
+ one exact conversion definition and attribution policy from that Epoch
+ one separately resolved outcome-evidence profile
+ one buyer reward-terms reference
= one direct buyer-reward policy composition
```

It does not create a second Campaign object or a second Campaign Epoch. The
direct buyer-reward policy is an optional policy selected by the canonical
`CampaignEpochV1.rewardPolicyRef` seam.

The strict schema and byte-pinned package are published at
[`../../conformance/profiles/campaign-direct-buyer-reward-v1/`](../../conformance/profiles/campaign-direct-buyer-reward-v1/).

## Reward meaning

The policy fixes one buyer reward leg and no promoter or referrer split. Exact
reward terms and exact outcome-evidence rules remain content-addressed
references. A verifier must resolve those references and the exact Campaign
Epoch; missing or unsupported material fails closed or remains
`INDETERMINATE` under the relying profile.

The reward recipient must be bound to the accepted qualifying buyer outcome.
The object creates no stable person, wallet, household, device, or
cross-Campaign identifier.

## Commercial-role separation

The profile is sponsor-neutral. Operator, affiliate, target merchant, payer,
funder, authorized brand representative, and sponsor remain separate business
roles. None is inferred from the reward-policy shape.

Affiliate tracking is also separate. A tracked link, coupon, affiliate order,
commission, or affiliate payout is neither required for nor established by the
buyer reward. Affiliate reporting cannot substitute for the Campaign's exact
conversion, evidence, attribution, timing, correction, and recipient rules.

## Privacy boundary

Merchant names, product names, source URLs, affiliate URLs, coupons, commission
rates, creative, images, buyer identities, funding-party identities, and sponsor
identities are not required in this public object. Exact target and conversion
meaning resolve through committed references and the relying authorization
boundary. Predictable plaintext hashes do not provide confidentiality.

## Campaign Epoch identity

This profile requires the adopted engineering `CampaignEpochV1` schema with:

```text
schema id: crinkl://protocol/schemas/campaign_epoch_v1
sha256:    019628fcb7d2b218cf0104cffa393d41f418047598e6b2e35afb0d239f46e033
```

The older public experimental schema at
`schemas/experimental/campaign-epoch.v1.schema.json` has the same display title
but different bytes and meaning. It remains preserved as historical draft
material and is excluded from this profile. Title-only resolution is
prohibited.

The signed objects retain their embedded `protocolVersion = 1.0.0-rc.1`; the
public repository release label does not rewrite signed wire bytes.

## Lifecycle boundary

This reward profile does not define Campaign pause, close, or early-stop
authority. Campaign product lifecycle and immutable Campaign Epoch validity are
separate concerns. A product decision may prohibit new activity even while an
Epoch remains time-valid, but product activity can never extend or repair an
expired, future, missing, or invalid Epoch.

Any future signed lifecycle-control artifact requires its own authority model,
source/freshness rules, conformance suite, and runtime integration. It must not
be bundled into the reward-policy profile merely because the business UI lets
an operator stop a Campaign.

## Experiment, funding, and settlement boundary

The profile is orthogonal to `CampaignExperimentPolicyV1`. Assignment does not
establish exposure, missing exposure stays `INDETERMINATE`, and incrementality
is a cohort- or market-level result rather than a per-conversion property.

`CampaignEpochV1.fundingTermsRef` and `settlementPolicyRef` remain separate.
This profile does not prove payment, deposit, reserve sufficiency, onchain
escrow, reward authorization, payout, refund, reconciliation, validator
finality, or chain execution.

## Release and runtime boundary

The package pins six exact artifacts: the reward-policy schema, canonical Epoch
schema dependency, conformance vector, deterministic generator, verifier, and
release-reconciliation contract. The source candidate remains unavailable to a
compiler until an authority-accepted `v1.0.0-rc.3` tag and release-manifest
digest identify this `RELEASED` manifest. The release still provides no compiler
or runtime implementation.

Publication and launch remain separate. Even after publication, a Campaign
cannot launch until its runtime, evidence sources, distributed Proof Validator
profile, selected-validator finality policy, funding, and settlement gates are
independently available.
