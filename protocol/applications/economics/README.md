---
status: draft
layer: reward-settlement
version: v1
normative: false
---

# Economics

This directory defines the Reward Layer and its settlement bindings ([`reward-layer.md`](reward-layer.md), [`policy-layer.md`](policy-layer.md), [`settlement-bindings.md`](settlement-bindings.md)), the aggregate accounting artifacts derived from Spend Attestations ([`gmv-token.md`](gmv-token.md), [`distribution-token.md`](distribution-token.md)), the normative supply-accounting mechanism that consumes the Data-Density Reserve ([`density-burn.md`](density-burn.md), with its design rationale in [`density-burn-rationale.md`](density-burn-rationale.md)), and the signed policy and election objects that bind reward computation to an auditable hash ([`issuer-policy-commitment.md`](issuer-policy-commitment.md), [`election-commitment.md`](election-commitment.md)). [`data-density-reserve.md`](data-density-reserve.md) is the economic-design narrative and calibration source for the Density Burn mechanism — genesis allocation, the depletion curve, the receipt-reward election, and the campaign-fee return flow — versioned with this specification rather than as a separately numbered tokenomics paper (see [`../../../governance/versioning.md`](../../../governance/versioning.md)); its machine-readable parameters are [`parameters.json`](parameters.json), conformant to [`schemas/data_density_reserve_parameters_v1.schema.json`](schemas/data_density_reserve_parameters_v1.schema.json). Canonical Campaign liability and resolution are defined by the Campaign architecture ([`../campaigns/`](../campaigns/)), not here.
