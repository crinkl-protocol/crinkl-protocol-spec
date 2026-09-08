---
title: The Data-Density Reserve
status: draft
layer: reward-settlement
version: v1
normative: false
spec_version: "1.0.0-rc.8 (pending)"
supersedes: "The Data-Density Reserve v8.2 revision 3 — Crinkl Brain tokenomics/data-density-reserve.md, 2026-09-08"
source_commit: e5ad392c8501cef9e41ed636d3b28deb56a599da
---

# The Data-Density Reserve

CRINKL is a fixed-supply token whose reward reserve depletes as qualified commerce accumulates. This document is the economic-design narrative for that reserve: the machine-readable constants it cites live in [`parameters.json`](parameters.json) and its schema, [`schemas/data_density_reserve_parameters_v1.schema.json`](schemas/data_density_reserve_parameters_v1.schema.json). It is non-normative economic-design prose, not a protocol validity rule; the network's normative supply-accounting mechanism is [Density Burn](density-burn.md), and this document supplies that mechanism's economic rationale and calibration.

> **Revision status — 8 September 2026.** This document specifies the updated economic design. Density Burn v0.2.0 source candidates have been prepared and reviewed; full Solana build and devnet upgrade remain pending. Campaign-fee buybacks are separate settlement work and are not implemented by the reserve burn program. Their fee fraction and fee basis remain to be specified before activation. This document does not claim those mechanisms are deployed.

## Abstract

CRINKL is a fixed-supply token whose reward reserve depletes as qualified commerce accumulates. Verified Commerce Density (VCD), for this schedule, is cumulative qualified GMV alone (`vcd_definition`). A capped logarithmic schedule determines how much may leave the 70,000,000-token reserve (`allocation.shared_pool_tokens`). Each tranche funds CRINKL-elected receipt rewards first; the remainder is permanently burned.

Paid business activity has a separate role. An agreed portion of earned, settled campaign fees is designated to buy circulating CRINKL on the market and burn the purchased tokens. Revenue does not accelerate reserve depletion. This separates the budget for building purchase evidence from purchases funded by demand for that evidence.

Buyers contribute purchase evidence and choose rewards without having to buy or lock CRINKL. Brands can fund campaigns in USDC (`campaign_escrow_currency`). The proposed fee-funded return flow connects paid campaigns to token purchases without requiring brands to choose CRINKL as their funding currency.

## 01 — The asset

Commerce data today comes in two kinds, broken in opposite ways: abundant but unverifiable data (panels, surveys, modeled attribution — accuracy no independent party can audit, and data the user cannot carry to another service), and verified but unshareable data (walled gardens, card networks — real purchase data that exists but is locked inside retailers and processors, bound to identity).

A receipt qualified by the CRINKL network is a third kind: cryptographically verified, identity-free, and publicly attestable.

Raw receipts stay private. What becomes publicly verifiable is what they produce: proof validity, aggregate Verified Commerce Density, and settlement artifacts. Verification services interpret receipts and issue signed spend proofs; proof validators check admissibility, proof integrity, uniqueness, and settlement. PriceChain Labs operates the current reference verification service, and the network is designed to admit additional independent providers and proof validators. The protocol measures commerce that already exists and converts the measurement into token state.

### The causal chain

1. Verified receipts accumulate into **Verified Commerce Density (VCD)** — a single dollar-denominated measure of proven commerce.
2. Rising VCD advances a bounded depletion schedule **D(VCD)** (`depletion_curve`), releasing a tranche from a finite 70M reserve (`allocation.shared_pool_tokens`).
3. Every tranche resolves into exactly two outcomes: **user rewards or permanent burn**.
4. Therefore verified commerce becomes deterministic pressure on a fixed supply.

The reserve calculation is deterministic for accepted inputs. Current input acceptance and execution authority are described separately (see §10, point 5, and the staged admission material referenced there).

## 02 — One number: Verified Commerce Density

For reserve depletion:

**VCD = cumulative qualified GMV** (`vcd_definition`)

Qualified GMV is the dollar value of admitted purchase evidence accepted under the network's verification and uniqueness rules. The same purchase must not add GMV again merely because it participates in multiple campaigns. Verification-service submission alone is not sufficient to authorize a reserve tranche.

Users, receipts per user, and average receipt value can be used as adoption-model assumptions. The schedule consumes accepted GMV; it does not infer actual commerce from an adoption forecast.

### Revenue has a separate role

Settled revenue does not enter VCD. The previous **33× revenue multiplier is removed** from the reserve model (`revenue_multiplier`, now `null` — see `revenue_multiplier_note`). A campaign may produce new qualified purchase evidence and settled fees, but they affect different mechanisms: accepted purchase GMV advances the reserve schedule; the designated fee share funds market purchases and burns outside that reserve.

Before paid campaigns and the fee-funded execution path operate, that second mechanism produces no buybacks. Commercial-capacity estimates are not spendable revenue.

## 03 — Fixed supply and allocation

CRINKL has a hard cap of **100,000,000 tokens** (`total_supply`), minted once at genesis. No minting function exists; there is no protocol path to additional supply, under any condition. Receipt rewards move tokens from the pool into circulation. Burns remove tokens from existence. Fee-funded buybacks acquire circulating tokens for permanent destruction, not for replenishing the reserve. Supply is monotonically non-increasing for the life of the protocol — it can only stay flat or fall.

Allocation (`allocation`):

- **Shared Reward-Burn Pool:** 70,000,000 CRINKL — 70% (`allocation.shared_pool_tokens`). Sole source of reserve-funded receipt rewards and the only allocation the depletion schedule burns from; campaign-funded buyer payouts are separate.
- **Proof Validator Network:** 10,000,000 CRINKL — 10% (`allocation.proof_validator_network_tokens`). Incentivizes proof validators that check proof integrity, uniqueness, and settlement.
- **PriceChain Labs Treasury:** 10,000,000 CRINKL — 10% (`allocation.pricechain_treasury_tokens`). Protocol development, operations, strategic reserve.
- **Market Maker / Liquidity:** 10,000,000 CRINKL — 10% (`allocation.market_maker_liquidity_tokens`). Secondary-market depth and orderly price discovery.
- **Total:** 100,000,000 CRINKL — 100% (`total_supply`). Fixed supply — no minting.

The issuer's allocation is a line item on the same receipt as everyone else's: 10%, disclosed, and never replenished. Seventy percent of all supply that will ever exist is reserved for the two exits — earned by users or burned.

Two burns are accounted for separately. **Reserve burns** are the residual of reserve tranches after CRINKL receipt rewards. **Campaign-fee burns** destroy circulating tokens purchased with the designated share of settled fees (`campaign_fee_burn`). Campaign-fee burns do not draw from the reserve, do not count against its 70M budget, and do not advance its depletion schedule. This fee-funded mechanism replaces the previous funding-currency-dependent network-share burn; the two must not be stacked on the same fee allocation.

### Where the 70M comes from

The Shared Reward-Burn Pool is the published 80M rewards-and-conversion escrow minus 10M carved out for proof validators (the Proof Validator Network bucket above). Consolidating the rewards budget and the burn reserve into one number is deliberate: the burn and the reward share the same index and the same curve, so they can never become two competing schedules. They are two outflows from one tank.

**Design invariant:** cumulative reserve burns + cumulative reserve emissions ≤ 70,000,000 CRINKL (`allocation.shared_pool_tokens`). Additional deposits cannot raise this lifetime limit. The split depends on reward demand and elections: full reserve retirement does not imply 70M burned, because emitted rewards count toward the same budget.

## 04 — The machine

Let **G** denote cumulative qualified GMV in dollars. The reserve's cumulative depletion entitlement is:

**D(G) = min(70,000,000, c × ln(1 + G / K))** (`depletion_curve.formula`)

The existing calibration is retained (`depletion_curve.c`, `depletion_curve.K_usd`):

- **c = 5,633,706.605660 CRINKL** (approximately 5,633,706.61).
- **K = $2,008,032.13**.
- **G ≈ $1B:** approximately 35M CRINKL, half the reserve.
- **G ≈ $500B:** approximately 70M CRINKL, the reserve limit.

The logarithm itself is unbounded. The explicit minimum enforces the ceiling; the curve does not approach 70M asymptotically. Below the cap, marginal depletion per additional dollar declines. Once the cap is reached, further GMV cannot authorize additional reserve outflow.

The milestones now refer to qualified GMV alone, not GMV plus weighted revenue. Retaining the constants does not retain the previous calendar-year projections.

Approximate analytical reference points, not measurements of executed burns (`calibration_milestones`):

| Cumulative qualified GMV | Depletion entitlement |
|---|---:|
| $2.4M | 4.43M CRINKL |
| $100M | 22.13M CRINKL |
| $1B | 35.00M CRINKL |
| $10B | 47.96M CRINKL |
| $100B | 60.93M CRINKL |
| $500B | approximately 70.00M CRINKL |

Execution uses integer fixed-point arithmetic and six-decimal token base units. With the retained calibration, the integer curve at exactly $500B is **69,999,999.995828 CRINKL**, slightly below the cap (`calibration_milestones`, last row). The exact ceiling is 70,000,000,000,000 base units (`decimals`, `depletion_curve.cap_tokens`). This exact figure and the conformance vector that checks it are described in [§ Conformance below](#conformance).

D(G) is combined reserve depletion entitlement, not a burn total. Actual outflow is also limited by available reserve balance.

## 04A — One pool, two exits

Each accepted epoch makes the next tranche available. Historical emissions and burns remain part of the lifetime accounting:

```text
already spent = cumulative reserve emissions + cumulative reserve burns
tranche       = min(available pool balance, max(0, D(G_new) - already spent))
emission      = min(CRINKL reward demand in tokens, tranche)
reserve burn  = tranche - emission
```

When the reserve has met all prior entitlement, this equals the difference between consecutive capped curve values. If prior funding was insufficient, later funding can satisfy unpaid entitlement, but never increase the lifetime ceiling. Once cumulative reserve outflow reaches 70M, all later tranches are zero even if more tokens are deposited.

An in-place program upgrade preserves the existing burned and emitted counters. For compatibility, the stored raw curve value can remain uncapped; the cap is applied to executable entitlement. Preserving that accounting does not require recreating previously burned tokens.

### Exit 1 — Burn

Tokens permanently destroyed, reducing total supply forever. The burn is the residual of each depletion tranche after rewards are paid.

### Exit 2 — Reward emission

Tokens allocated toward USD-denominated receipt rewards, subject to tranche capacity. The reserve program funds the configured rewards escrow; individual user payout is a separate step.

This is the central mechanism-design choice. A burn from a sealed, never-spendable reserve is a costless signal. A burn from the same budget that funds rewards is a costly one: every burned token is a reward the pool could have paid. Because emission is paid first and burn is the residual (`receipt_reward.ordering`), the two exits compete for one fixed budget — heavy receipt volume emits more of each tranche, light reward demand burns it nearly whole.

The curve and split are recomputable from accepted inputs, reward policy, elections, and the attested conversion price. This determinism is not a claim of permissionless execution today: the reviewed implementation requires an issuer signature and a pinned validator quorum; upgrade authority remains retained on the inspected devnet deployment. The authority roadmap is separate from this economic change.

## 05 — The reward

Verification services set the reward per verified receipt — currently **$0.10** (`receipt_reward.usd_reference_rate`), denominated in USD regardless of token price. The rate is service policy (`receipt_reward.set_by`), priced to the market's demand for receipts, not a protocol constant. CRINKL reward demand is converted at the attested token price, so token demand per receipt falls as that price rises. Actual reserve emission is capped by the available tranche; a fixed USD policy rate is not a guarantee of an uncapped pool payout. Reward tokens enter circulation only when earned against proven commerce — there is no time-based vesting, no cliff, no unlock. Emission is work made liquid.

The current rate is flat per receipt. Because the rate is service policy, a verification service may instead weight rewards by coverage — recurring evidence across buyers, merchants, categories, markets, and time — so that the receipts that add most to useful density earn most, rather than every upload earning the same. Reward policy changes what each receipt earns; it does not change the schedule. D(VCD) reads dollars of proven commerce, and a coverage-weighted policy only changes how a tranche is divided among the receipts that produced it.

### The CRINKL / BTC election

Users choose the currency of their reward (`receipt_reward.election`), and that single election governs the burn/emit mix and who pays:

- **CRINKL-elected rewards** are paid by the protocol from the Shared Reward-Burn Pool, whichever verification service admitted the receipt. They consume part of the depletion tranche and reduce the residual burn.
- **BTC-elected rewards** are paid in bitcoin by the verification service that admitted the receipt, from that service's own funds — today, the PriceChain Labs treasury. They are an off-pool, hard-currency cost that draws nothing from the 70M.

For the same accepted GMV and available pool balance, the election does not change depletion entitlement. BTC-elected receipts add no CRINKL reward demand, leaving more of a tranche available for residual burn when other CRINKL reward demand does not already exhaust it. There is no separate guaranteed per-receipt reserve slice.

The election also divides the cost of a false admission. A receipt that should not have been admitted and elects BTC costs the admitting service real bitcoin. One that elects CRINKL costs the pool. The service's own-funds exposure is therefore the BTC election; the pool's exposure is bounded by admission (§02) and discussed in §10.

The previous year-four election tables used the revenue-weighted v8 model and have been withdrawn pending a GMV-only model rerun. The reward policy and funding election are unchanged; their future aggregate burn/emission mix is not established by the old projections.

For a simple split illustration, if an epoch has a 100-CRINKL tranche and CRINKL reward demand of 60 tokens, 60 go to the rewards escrow and 40 burn. If demand is at least 100, the full tranche emits and the reserve burn is zero. BTC payments remain outside that calculation and outside the pool.

## 06 — Commercial capacity

Verified commerce is the network's economic substrate, but verification alone does not produce revenue. Revenue arises when services use that proof supply for paid campaigns, affiliate commerce, measurement, attribution, and settlement.

Not every qualified receipt will be monetized. Some paid outcomes may generate substantially less than 1% of their GMV; others, including affiliate transactions and performance campaigns, may generate substantially more. Across those uses, the model applies **1% of Qualified GMV as an illustrative mature-network revenue equivalent** (`revenue_equivalent_illustrative`).

**revenue equivalent = 1% × qualified GMV**

Illustrative reference:

- $100M qualified GMV → $1M revenue equivalent
- $1B → $10M
- $10B → $100M
- $100B → $1B

This is not revenue automatically earned from every receipt. It is not a guaranteed take rate or a forecast. It is a commercial-capacity reference for what a sufficiently utilized verified-commerce network could support across multiple paid uses.

Neither illustrative revenue equivalent nor actual settled revenue enters VCD under this revision. Only the designated share of eligible earned, settled campaign fees funds the separate buyback mechanism (`campaign_fee_burn`). Its percentage and accounting basis must be defined before activation; no percentage is implied by the 1% commercial-capacity reference.

## 07 — Where the tokens end up

The genesis allocation is unchanged. Over the reserve's life, up to 70M CRINKL is either emitted as receipt rewards or burned. Their exact split depends on accepted GMV, reward policy, token prices, elections, and available funding.

The earlier ~43M emitted / ~27M burned end state was a model output, not a guaranteed allocation. It is withdrawn as a projection for this revision until the GMV-only model and fee-funded return flow are rerun. Majority user ownership remains a possible outcome, not an invariant of the reserve formula.

The 10M proof-validator allocation, 10M liquidity allocation, and 10M PriceChain treasury allocation remain unchanged. Their distribution schedules are not introduced or accelerated here.

Reserve burns reduce potential future circulating supply. They do not, by themselves, remove tokens already trading or establish demand. Campaign-fee buybacks purchase circulating tokens and burn them separately. Neither mechanism guarantees token appreciation or a particular future election mix.

## 08 — The return flow

Receipt rewards help build purchase evidence that brands can use for acquisition, targeting, measurement, attribution, and outcome-based campaigns. Consumers can participate without buying or locking CRINKL.

**Campaign escrow remains denominated in USDC** (`campaign_escrow_currency`). Brands can buy accepted outcomes without holding CRINKL. Under the proposed fee-funded mechanism, an agreed portion of earned, settled network campaign fees buys circulating CRINKL on the open market, and the tokens actually acquired are permanently burned.

**buyback budget = agreed fee fraction × eligible settled campaign fees**

The fee fraction and the basis for eligible fees — including treatment of costs and refunds — remain to be specified before activation (`campaign_fee_burn.fee_fraction`, `campaign_fee_burn.basis`, both `null`; `campaign_fee_burn.status`). Campaign reward principal is not silently included in the fee budget. The remaining fees are available for the network's other obligations under its settlement rules; this revision does not allocate all fee revenue to burns.

The mechanism applies across supported campaign funding paths rather than depending on a brand electing CRINKL. It replaces the earlier rule that burned the network's entire share only on CRINKL-funded campaigns. Optional CRINKL funding and its buyer payouts remain service-design decisions. The previous discount and discovery priority are not assumed in the revised economic model; whether either remains as a separate service policy is an explicit open decision. Neither is needed to establish the fee-funded return flow.

These purchases and burns are outside the reserve burn program. They neither draw reserve tokens nor increase qualified GMV or its depletion entitlement. A designated fee budget is not an executed buyback: reporting must distinguish allocated funds, completed purchases, and tokens actually burned.

The loop:

**Buyers contribute verified purchase evidence → receipt rewards support participation → brands pay for useful campaign outcomes → a defined share of settled fees buys and burns circulating CRINKL.**

New accepted purchase GMV continues to advance the separate capped reserve schedule. Counting a purchase in multiple campaign outcomes must not count its GMV repeatedly.

This retains the original adoption distinction: buyers supply evidence; paying businesses fund the proposed market purchases. Independent verification services and validators follow the existing staged admission and accountability roadmap.

## 09 — Worked scenario

At **$1B cumulative qualified GMV**, the retained curve authorizes approximately **35M CRINKL** of total reserve depletion, subject to available pool balance. Actual reserve burns equal executed depletion minus cumulative reserve emissions.

Revenue does not change that figure. For example, $1B of qualified GMV with no settled revenue and $1B of qualified GMV with settled campaign fees have the same reserve entitlement. In the second case, the agreed fee share may separately fund market purchases and burns once that settlement path is implemented.

No year-of-arrival, receipt count, terminal ownership split, or buyback volume is asserted here. Those require updated adoption, reward-election, price, fee-allocation, and execution assumptions. The v8 revenue-weighted year-four scenario is not carried forward.

## 10 — Risks & considerations

1. **Low token price increases reward demand.** With USD-denominated rewards, a lower token price requires more CRINKL to meet the same policy amount. Emission can absorb more of each tranche, but cannot accelerate the GMV-only depletion schedule or exceed the tranche. Reward demand can exceed available entitlement; that shortfall must not be represented as a guaranteed pool payout.

2. **BTC election as treasury-funded acquisition cost.** BTC-elected rewards are a hard-currency expense of the admitting verification service — today, the treasury. They draw nothing from the pool and can increase residual reserve burn by reducing CRINKL reward demand. The cost sits off the pool charts and should be budgeted as an acquisition line: users will rationally elect BTC more in a downturn, making this draw largest precisely when the treasury can least fund it.

3. **Burn is a residual, and must be read as one.** The schedule burn figure is only legible alongside total depletion, reward election, emitted CRINKL, and BTC-paid rewards. Together those fully explain any burn rate; alone, the burn is not a standalone health signal. Campaign-fee burns and their actual purchase costs are separate figures and should be reported separately.

4. **Calibration and paid demand remain distinct.** Removing the revenue multiplier removes that source of reserve acceleration. The existing curve constants remain, now applied to qualified GMV alone. Dollar volume does not establish useful coverage or repeat brand demand; previous revenue-weighted projections require a new model run.

5. **Pool exposure to admissions.** CRINKL-elected rewards are paid by the protocol whichever verification service admitted the receipt. The pool's protection is admission: a receipt enters qualified GMV and draws a tranche only after proof validators have proven it. Today PriceChain Labs is the only verification service and validators verify reported commerce at the aggregate level, so the pool is only ever paying for the reference service's own admissions, and that service carries the BTC-election cost of its own mistakes. Admitting an independent verification service is a staged transition with two requirements, both of which must be met before that service's receipts draw pool emission: its output is subject to adversarial validator probing, and it has posted a stake that it loses for admissions that fail probing. Probing detects; the stake makes the failure cost the service rather than the pool. False accepted GMV can improperly advance reserve entitlement; low token prices can shift more of that entitlement into emissions. The cap bounds lifetime outflow but does not establish input integrity. Validator reputation and stake are planned for the same transition and are not yet specified.

6. **Fee-funded burns compete with operating needs.** The designated fee share reduces cash available for other obligations. Its basis and rate must be sustainable after buyer payments, service delivery, and applicable costs. Market liquidity and execution determine how many tokens are actually purchased; a fee budget alone is not a burn or a price guarantee.

## 11 — Parameter reference

The authoritative machine-readable form of every parameter below is [`parameters.json`](parameters.json), conformant to [`schemas/data_density_reserve_parameters_v1.schema.json`](schemas/data_density_reserve_parameters_v1.schema.json).

- **Total supply:** 100,000,000 CRINKL; no new minting (`total_supply`).
- **Shared reserve:** 70,000,000 CRINKL lifetime combined receipt-reward emission and reserve-burn ceiling (`allocation.shared_pool_tokens`).
- **Reserve index:** VCD = cumulative qualified GMV alone (`vcd_definition`).
- **Depletion:** min(70M, c × ln(1 + G/K)) (`depletion_curve`).
- **c:** 5,633,706.605660 CRINKL; existing calibration retained (`depletion_curve.c`).
- **K:** $2,008,032.13 (`depletion_curve.K_usd`).
- **Calibration milestones:** approximately 35M entitlement at $1B qualified GMV; approximately 70M at $500B, with integer rounding as stated in §04 (`calibration_milestones`).
- **Revenue multiplier:** removed from the reserve calculation (`revenue_multiplier: null`).
- **Receipt reward policy:** $0.10 USD reference rate, set by verification service; actual pool emission is tranche-capped (`receipt_reward.usd_reference_rate`, `receipt_reward.set_by`).
- **Reward funding:** CRINKL election draws from the reserve; BTC election is paid by the admitting service (`receipt_reward.election`).
- **Reward ordering:** emission first; reserve burn is the residual (`receipt_reward.ordering`).
- **Campaign escrow:** USDC; no CRINKL holding required to buy outcomes (`campaign_escrow_currency`).
- **Campaign-fee burn:** market purchase and burn of circulating CRINKL from a defined fee share, outside the reserve program and the 70M cap (`campaign_fee_burn`).
- **Fee fraction and eligible-fee basis:** not yet specified; required before activation (`campaign_fee_burn.fee_fraction`, `campaign_fee_burn.basis`, both `null`).
- **Independent service admission:** existing staged validator probing and stake requirements; no roadmap acceleration in this revision.
- **Revenue equivalent:** 1% of qualified GMV remains an illustrative commercial-capacity reference, not a fee allocation or forecast (`revenue_equivalent_illustrative`).
- **Launch price:** $0.10 remains a reference assumption, not a supported price (`launch_price_reference_usd`).

The approximate curve reference points in this revision are analytical calculations using the retained constants. The previous v8 engine's revenue-weighted election, adoption-timing, and terminal-split projections have not been regenerated and are not claimed as outputs of this revised model. This document describes economic design; it does not establish deployment, profitability, or token-price performance.

This specification is not financial advice or an offer of any CRINKL token or other asset.

## Conformance

The depletion curve's reference points, including the exact fixed-point value at $500B, are checked by the `economics.dataDensityReserve.depletionCurve.v1` conformance vector (see [`conformance/vectors/v1/vectors/economics.dataDensityReserve.depletionCurve.v1.json`](../../../conformance/vectors/v1/vectors/economics.dataDensityReserve.depletionCurve.v1.json)) and its standalone evaluator, [`scripts/check_data_density_reserve_curve.mjs`](../../../scripts/check_data_density_reserve_curve.mjs).
