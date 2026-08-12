# Campaign V1 schema candidates

Status: `SPECIFIED_NOT_IMPLEMENTED`.

These are the first canonical schema candidates for the unimplemented Campaign
object family. They are not listed in a released manifest and do not establish
runtime support. No discarded Campaign draft is a supported predecessor, so
these schemas require no aliases, adapters, or inherited version numbers.

Spend Token schemas and the SOFT-to-HARD verification pipeline are outside this
directory and unchanged.

| Schema | Family decision |
|---|---|
| `campaign_epoch_v1.schema.json` | first immutable signed Campaign rule and economic-policy object |
| `proof_of_match_v1.schema.json` | first canonical serialized ProofOfMatch envelope |
| `validator_certificate_v1.schema.json` | first certificate restricted to `PROOF_OF_MATCH_VERIFICATION` |
| `assignment_record_v1.schema.json` | portable only for a named cross-system, dispute, or independent-consumer use |
| `campaign_outcome_v1.schema.json` | first narrow Outcome composition |
| `reward_obligation_v1.schema.json` | first recipient-scoped Campaign liability family |
| `settlement_record_v1.schema.json` | first liability-resolution record |

## Common content references and signatures

Unless a schema says otherwise, an artifact reference is:

```text
"sha256:" + lowercase_hex(SHA-256(RFC8785(complete artifact bytes)))
```

For signed objects, compute the unsigned canonical bytes by omitting the entire
top-level `signatures` member. `signatures.objectHash` is the lowercase SHA-256
hex digest without the `sha256:` prefix. Ed25519 signs the raw 32 digest bytes.
The external reference is `sha256:` plus `objectHash`.

`ProofOfMatchV1` has no additional object signature: its subject hash is the
artifact reference over the complete envelope. Its `proof.proofBytesHash`
separately authenticates the decoded ZK proof bytes.

`ValidatorCertificateV1` signatures sign the raw 32 bytes identified by
`decisionHash`. The decision-hash preimage and semantic checks are fixed by the
validator handoff in
[`../../../governance/proof-validator-campaign-refactor-handoff.md`](../../../governance/proof-validator-campaign-refactor-handoff.md).

JSON Schema cannot enforce reference resolution, hash equality across fields,
signature authority, time ordering, proof verification, deterministic
assignment, atomic capacity admission, or nullifier uniqueness. Every
conforming implementation must run the normative semantic procedures in the
Campaign architecture and applicable profile in addition to schema validation.
