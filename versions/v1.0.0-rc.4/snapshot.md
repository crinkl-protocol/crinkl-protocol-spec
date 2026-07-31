# Crinkl Protocol v1.0.0-rc.4 Release Snapshot

Status: `RELEASED`

The exact finalization transitions, authorization, pre-tag gates, post-tag
gates, and rollback rules are machine-readable in
[`finalization.json`](finalization.json).

## Version surfaces

- Public repository release: `1.0.0-rc.4`.
- Conformance suite version: `2`.
- Default Crinkl Platform binding `protocolVersion`: `1.0.0-rc.2`.
- Spend Attestation Token V2 embedded `protocolVersion`: `1.0.0-rc.1`.
- Supported wire protocol versions: `1.0.0-rc.1` and `1.0.0-rc.2`.

These values are intentionally distinct. This release does not relabel or
rewrite signed wire objects.

## Published profile

`token.spendAttestation.holderBinding.v2` publishes an optional signed
per-Spend Ed25519 public-key commitment and a verifier-authenticated fresh
challenge-response proof. The package pins the adopted vector and executable
checker byte-for-byte to `crinkl-protocol` commit
`5019e41bdeb924449363aa3b538eaa5b3b6ee4dc`.

The profile includes one valid case and seven negative decisions covering
wrong key, wrong signature, changed scope, changed request, expiry, replay, and
absent binding. A token without `holderBinding` remains a valid schema-v2
Spend attestation, while holder control remains unavailable.

## Authority boundary

Holder control proves control of one per-Spend key for one exact verifier
challenge. It does not establish a wallet, legal identity, natural person,
cross-Spend linkage, qualification, reward, settlement, runtime deployment,
or validator-network acceptance.

The release does not activate any Crinkl service or client. Application
adoption and deployment remain separately governed.
