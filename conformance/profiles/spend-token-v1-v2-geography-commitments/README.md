---
status: release-candidate
layer: portability
version: v1
normative: true
---

# Spend Attestation Token V1/V2 Geography Commitment Profile

Maturity: `candidate` in the unpublished public `v1.0.0-rc.7` source and
included in conformance suite 4.

This profile publishes byte-pinned adopted-engineering semantics for
`SpendAttestationTokenV1` and `SpendAttestationTokenV2` geography disclosure:

- `zk` is optional;
- when `zk.commitments` exists, `C_store`, `C_total`, and `C_dayIndex` are
  required;
- `C_currency`, `C_geoRegion`, and `C_cbsaCode` are independently optional;
- new privacy-preserving portable issuance omits plaintext
  `canonical.geoRegion` and `canonical.cbsaCode`; and
- valid immutable signed V1/V2 tokens containing legacy plaintext geography
  remain verifiable.

Absence of an optional geographic commitment does not invalidate the Spend
Attestation Token. A proof profile that requires that commitment is unavailable
for that token.

The profile does not prove the underlying physical purchase occurred, activate
a ZK circuit, publish a new Protocol Spec release, or change the immutable
`v1.0.0-rc.4` release.

Run the exact candidate-profile verifier:

```bash
node conformance/profiles/spend-token-v1-v2-geography-commitments/scripts/check_spend_token_geography_commitments.mjs
```
