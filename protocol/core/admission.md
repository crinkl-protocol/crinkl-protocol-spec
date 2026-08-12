---
status: draft
layer: lifecycle
version: v1
normative: true
---

# Record Admission

Attestation issuance produces a signed claim. Admission is the lifecycle stage where signed claims become part of the shared record that downstream value movement may rely on.

Verification is private. Admission is public.

A Verification Service reads commerce evidence inside the privacy boundary and signs attestations. Proof Validators admit the resulting claims to the record without reading evidence. Neither party holds both powers.

Terms are defined in `../../governance/glossary.md`.

## Roles

### Verification Service

The party that receives commerce evidence, evaluates it under protocol rules inside the privacy boundary, and signs Spend Attestations and Spend Attestation Tokens.

The Verification Service role names the operator of the existing spend-stream and token-issuer trust roots (`../purpose/threat-model.md`). It does not introduce a new trust root category.

- A Verification Service MUST terminate raw evidence at its own privacy boundary (`../protocol/core/privacy-boundaries.md`).
- A Verification Service MUST sign attestations under keys authorized by the applicable trust root mapping.
- In protocol v1, deployments operate a single Verification Service under the configured issuer set. Additional Verification Services are not live on the alpha network; operating them requires the verification-service registry (RESERVED below).

### Proof Validator

A party that independently re-verifies public protocol statements and co-signs deterministic results so that claims can be admitted to the record.

The role is open by conformance and economic exposure through the authority registry. PriceChain Labs is currently the sole reference operator on the alpha network. Registry membership and quorum participation are not economically bonded or staked; those mechanics are deferred to Phase 5 and are not live.

Proof Validators operate on public material only:

- A Proof Validator MUST NOT receive raw receipts, receipt images, OCR text, user identity, private witness material, or private purchase history.
- A Proof Validator MUST verify a statement from public inputs, public artifact commitments, signed registry and assignment records, and policy bindings alone.
- A Proof Validator MUST sign only the exact deterministic result it checked.

Validator membership, selection, and quorum are governed by authority-signed registry and assignment artifacts (`ValidatorRegistrySnapshotV1`, `ValidatorAssignmentV1`), as consumed by the finality trust root in `../protocol/applications/economics/density-burn.md`.

## Division of Power (Normative)

- The party that reads evidence MUST NOT unilaterally create network acceptance. A Verification Service signature is a proposal, never acceptance.
- The parties that create network acceptance MUST NOT require raw evidence. Admission checks operate on signed public claims and commitments only.
- For this v1 statement-coverage mechanism, network acceptance exists only as
  its existing Finality Certificate: a quorum of valid selected-validator
  signatures over the identical deterministic result, under a named registry
  snapshot, validator assignment, and quorum rule. This does not define the
  target Campaign `ValidatorCertificate` or give the word “finality” a global
  state meaning.
- The quorum rule for v1 finality is strict BFT supermajority over the selected committee: `floor(2N/3) + 1` signatures, where `N` is the selected-validator count.
- Eligibility is not duty. Each statement is assigned to a bounded selected committee; no admission path may require all registered validators to coordinate for one statement. Non-selected validators observe and replay certificates asynchronously.
- The Verification Service key set and the validator set MUST be disjoint, so the division of power cannot collapse to one key (root separation, `../protocol/applications/economics/density-burn.md`).

## Admission States

| State | Meaning |
|---|---|
| Attested | A Spend Attestation exists: the Verification Service signed the claim. The claim is a proposal toward the shared record. |
| Admitted | A validator-finalized statement covers the attestation's canonical head: the claim is part of the shared record. |

Attested is not Admitted. A signed attestation that no finalized statement covers remains a Verification Service claim, with only the assurances of the token-issuer trust root.

## Admission Mechanism (v1: Statement Coverage)

Protocol v1 admits attestations at statement granularity, not per-token.

A Spend Attestation is **admitted** when a validator-finalized statement covers it:

1. A public statement (for example `QUALIFIED_GMV_BURN_EPOCH_V1`) commits to a leaf set of canonical spend heads (`spendHeadSetRoot` or the statement's equivalent committed leaf root).
2. Selected Proof Validators independently recompute the statement from its committed public leaves — roots, totals, eligibility hashes, and nullifier scope — and reject on any mismatch or replay.
3. A Finality Certificate aggregates the quorum of identical signed results.
4. Every attestation whose canonical head is included in the finalized statement's committed leaf set is admitted, with inclusion provable by Merkle path against the committed root (`../portability/verifier-requirements.md`).

Admission coverage is checkpoint-granular by design: one certificate admits the batch of claims the statement commits to. Per-token streaming admission is not required by v1 and MUST NOT be presumed by downstream consumers.

Uniqueness is an admission constraint. A statement MUST carry nullifier domain and scope bindings, and validators MUST enforce replay protection before signing, so that the same purchase cannot be admitted more than once within a scope (`../../governance/glossary.md#nullifier`).

## What Admission Asserts (Bounded Scope)

Admission is trusted to assert:

- that a quorum of selected, registered Proof Validators independently recomputed the statement from committed public material and co-signed the identical result;
- that the covered attestations are well-formed, signed by authorized keys, committed exactly once within their nullifier scope, and consistent with the statement's declared totals and roots.

Admission is NOT trusted to assert:

- that any covered purchase occurred in the world. Origination truth roots at the Verification Service that read the evidence; validators verify correctness, not ground truth;
- payout authority, production chain finality, legal settlement, or economic backing;
- the honesty of a Verification Service beyond what its committed output reveals.

This boundary follows the same bounded-scope discipline as every trust root in `../purpose/threat-model.md`.

## Downstream Consumption (Normative)

- Record-level reserve depletion, burn, and Verified GMV consumed as a protocol
  figure MUST consume the exact validator-accepted evidence required by their
  named procedures, never an operator counter
  (`../protocol/applications/economics/density-burn.md`).
- A target Campaign runtime MUST verify `ValidatorCertificateV1` for each
  `ProofOfMatch` consumed by a `CampaignOutcome`. That certificate establishes
  proof acceptance only. Economic admission, Reward Obligation creation, and
  settlement each require their own committed policy and authoritative state;
  the certificate does not authorize them.
- Reward accrual MAY act on Attested claims under the active reward policy.
- Reward claimability — the point where value leaves the system to a wallet — SHOULD be gated on admission coverage of the underlying attestation.

**Deployment note (non-normative):** a deployment that holds rewards for a fixed fraud-review window satisfies the claimability gate by ensuring the hold window is not shorter than the admission checkpoint cadence, so that a claimable reward always rests on an admitted attestation.

## Campaign target boundary

The v1 admission of a Spend Attestation's canonical head, the verification of a
`ProofOfMatch`, and any Campaign activation gate are different procedures.

- A Campaign authority signature is the default authority for
  `CampaignEpochV1`; this specification does not require a generic validator
  vote over every Epoch.
- Target `PROOF_OF_MATCH_VERIFICATION` produces a `ValidatorCertificate` over
  one exact proof hash with `stateTransition = NONE`.
- The certificate does not update a canonical nullifier registry. A relying
  registry or ledger must name and execute any atomic replay transition.
- The certificate does not perform assignment, economic admission, Outcome
  construction, Reward Obligation creation, reserve, or settlement.
- Existing campaign-specific validator procedures are implementation evidence,
  not Campaign protocol predecessors. The validator refactor must remove or
  narrow them unless it demonstrates a distinct activation/non-equivocation
  consumer.

See [`../applications/campaigns/README.md`](../applications/campaigns/README.md)
and the
[`validator handoff`](../../governance/proof-validator-campaign-refactor-handoff.md).

## Negative Invariants (Normative)

- The protocol MUST NOT allow a Verification Service signature alone to move record-level value.
- The protocol MUST NOT require Proof Validators to access raw evidence, private operator databases, or mutable API responses to admit a statement.
- The protocol MUST NOT treat validator liveness, attendance, or heartbeat evidence as admission work.
- The protocol MUST NOT accept a Finality Certificate whose signers are not selected for the statement's assignment, active in the named registry snapshot, and signing with active keys.
- The protocol MUST NOT admit the same nullifier twice within one scope.

## Verification-Service Accountability (RESERVED)

The following surfaces are reserved for a future protocol version and MUST NOT be presumed live:

- **Verification-service registry** — an authority-signed registry of Verification Services, their signing keys, and their admission status, mirroring the validator registry.
- **Adversarial audit probes** — validator-originated crafted submissions (deliberate duplicates, cross-wallet collisions, malformed evidence, boundary cases) measuring a service's rejection behavior on a public integrity surface.
- **Disbelief status** — a validator-governed service status under which a service's attestations are no longer admitted. Disbelief removes a service's product without seizing anything; its claims simply stop entering the record.

Until these surfaces exist, deployments operate a single configured Verification Service, and admission constrains that service's committed output rather than selecting among competing services.

## Related

- `attestation-issuance.md` — the stage before admission.
- `../purpose/threat-model.md` — trust roots and bounded scopes.
- `../protocol/applications/economics/density-burn.md` — the finality trust root and joint-root consumption rules.
- `../portability/verifier-requirements.md` — Merkle inclusion procedure for coverage proofs.
