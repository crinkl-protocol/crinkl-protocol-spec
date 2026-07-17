# Crinkl Protocol v1.0.0-rc.3 Release Candidate Snapshot

Status: `RELEASE_CANDIDATE_NOT_PUBLISHED`

The exact finalization transitions, required authorization, pre-tag gates, post-tag
gates, and rollback rules are machine-readable in [`finalization.json`](finalization.json).

This snapshot identifies the source candidate for public repository release
`v1.0.0-rc.3` and conformance suite version `2`. It is not an authenticated release.

## Version surfaces

- Public repository release candidate: `1.0.0-rc.3`.
- Conformance suite version: `2`.
- Default Crinkl Platform binding `protocolVersion`: `1.0.0-rc.2`.
- Direct buyer-reward signed object `protocolVersion`: `1.0.0-rc.1`.
- Supported wire protocol versions declared by this package: `1.0.0-rc.1` and
  `1.0.0-rc.2`.

These values are intentionally distinct. The release candidate does not relabel or
rewrite signed wire objects.

## Added profile

`campaign.directBuyerReward.profileV1` is present in the suite-2 source manifest and
is executed through the manifest-bound Python verifier in
`07-conformance/profiles/campaign-direct-buyer-reward-v1/`.

The package pins six artifacts by SHA-256: two strict schemas, one conformance vector,
one checker, one deterministic generator, and one release-reconciliation contract. The
adopted engineering and legacy experimental Campaign Epoch schemas retain distinct exact
IDs and byte hashes; title-only resolution is prohibited.

## Publication and launch boundary

The profile is not released until a reviewed final release commit changes the release
status to `RELEASED`, an authority-accepted `v1.0.0-rc.3` tag identifies that exact commit,
and the exact release-manifest digest is accepted by the relying consumer.

Protocol publication does not establish Campaign runtime, product-outcome evidence,
distributed validator admission, funding, escrow, settlement, deployment, or production
availability. Those remain independent relying-action and launch gates.
