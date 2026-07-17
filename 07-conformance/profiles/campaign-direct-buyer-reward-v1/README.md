# Campaign Direct Buyer Reward Release Profile

Maturity: `released`. This profile is included in the published `v1.0.0-rc.3`
conformance suite `2`.

The package vendors the exact adopted-engineering reward-policy schema,
adopted-engineering `CampaignEpochV1` dependency, deterministic vector,
generator, checker, and release-reconciliation contract from `crinkl-protocol`
commit `8c641f57201c75bac12819a0f903ae6105c7f3c3`. The manifest pins all six
vendored artifacts by SHA-256. Public candidate semantics and maturity are
stated in [`../../../06-extensions/campaign-direct-buyer-reward-profile.md`](../../../06-extensions/campaign-direct-buyer-reward-profile.md).

The similarly named public experimental schema at `schemas/experimental/campaign-epoch.v1.schema.json` is not wire-compatible with the vendored adopted-engineering Epoch schema and MUST NOT be substituted. The reconciliation contract preserves both byte sets and requires resolution by exact schema ID and SHA-256; the common display title has no resolving authority.

Run the self-contained profile checks from the repository root:

```bash
python3 07-conformance/profiles/campaign-direct-buyer-reward-v1/scripts/check_campaign_direct_reward_profile_vectors.py
python3 07-conformance/profiles/campaign-direct-buyer-reward-v1/scripts/generate_campaign_direct_reward_profile_vectors.py --check
```

These commands require Python `jsonschema` and `cryptography`. Passing them proves only deterministic released-artifact interoperability. It does not establish a live Campaign compiler, product-purchase evidence, a validator statement/profile, selected-committee finality, funding, escrow, settlement, chain execution, runtime, deployment, or production availability.

The released package contains the exact profile entry and executable verifier binding.
The signed object bytes retain their embedded `protocolVersion = 1.0.0-rc.1`; the
repository release label does not silently rewrite wire semantics. A relying consumer
must authenticate the authority-accepted `v1.0.0-rc.3` tag and release-manifest digest;
this repository release does not itself provide a Campaign compiler.

Publication and launch remain separate. Publishing this profile does not make the Campaign
runtime or distributed validator admission profile available; those remain explicit launch
requirements.
