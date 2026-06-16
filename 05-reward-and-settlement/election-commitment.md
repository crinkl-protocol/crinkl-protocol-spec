# Per-spend reward election — schemas (normative)

> Status: DRAFT for implementation (Phase 3 of the tokenomics foundation plan).
> Anchor: Crinkl tokenomics foundation refactor plan (internal governance).
> Locks the preimages users sign and validators recompute **before** any PWA
> capture writes signed bytes. Changing any preimage here is a new schema version.

The per-spend election commits, for every qualified spend in an epoch, which
reward the user elected (btc/crinkl/alternate/none). All four are committed in the
`spendElectionRoot` (see [density-burn.md](density-burn.md)) so the GMV cross-check
is complete; crinkl/alternate are *claim* commitments, btc/none *non-claim*.

## ElectionLeafV1 (normative)
The Merkle leaf, one per qualified spend. Matches `shared-rs::ElectionLeafV1` /
`@crinkl/shared-ts` `ElectionLeafV1`; **field order is load-bearing** (Borsh,
little-endian; `[u8;32]` raw, `u64` 8-byte LE, `u8` 1 byte), hashed with blake3.

```text
ElectionLeafV1 {
  issuer:          [u8;32],   // authorized-issuer id (Pubkey)
  mint:            [u8;32],   // CRINKL mint (Pubkey)
  spend_ref_hash:  [u8;32],   // blake3 of the spend/proof reference (see derivation)
  amount_cents:    u64,       // qualified spend amount; leaves sum to total_gmv_cents
  election:        u8,        // 0=NONE, 1=BTC, 2=CRINKL, 3=ALTERNATE
  nullifier:       [u8;32],   // per-spend nullifier (double-claim prevention)
  epoch:           u64,
}
leaf_hash = blake3(borsh(ElectionLeafV1))
```

## Shared derivations & domains (normative)
Both the PWA authorization and the batcher consume-path MUST use these, so a
signed authorization, the committed leaf, and the validator recomputation agree:

- **Election mapping:** `none→0, btc→1, crinkl→2, alternate→3`.
- **`spend_ref_hash`** = `blake3("crinkl-spend-ref/v1" ‖ spend_id_utf8)`.
- **`nullifier_domain`** = the ASCII string `"crinkl-election-nullifier/v1"`.
- **`nullifier`** = `blake3(nullifier_domain ‖ issuer ‖ mint ‖ spend_id_utf8 ‖ epoch_le8)`.
- **`epoch`** = the GMV statement window the spend falls in (UTC day → epoch index;
  same windowing as `QualifiedGmvBurnEpochV1.window`).
- **Canonical encoding** for signed/hashed JSON objects below: sorted keys,
  fixed-decimal numerics, `[u8;32]` as lowercase hex, matching the IPC convention.

## ClaimElectionAuthorizationV1 (normative)
A user-signed authorization required for any **claim** election leaf — i.e.
`election == CRINKL` or `election == ALTERNATE` (the two claim commitments; btc/none
are non-claim and need no signature). The issuer/validator MUST reject a CRINKL or
ALTERNATE leaf not covered by a valid, in-window authorization. Signed by the
user's `wallet` (ed25519 for Solana; verified via the ed25519 introspection helper).

```text
ClaimElectionAuthorizationV1 {
  schema:                "crinkl-claim-election-auth/v1",  // domain separation + version
  chain:                 String,   // e.g. "solana"
  cluster:               String,   // e.g. "mainnet-beta" / "devnet"
  wallet:                Pubkey,   // the signer; MUST equal the elector wallet
  issuer:                Pubkey,
  mint:                  Pubkey,
  election:              "CRINKL" | "ALTERNATE",  // the claim election being authorized
  claim_destination:     Pubkey,   // where the claimed reward is claimable
  policy_hash:           Hash,     // the IPC policy_hash in force
  policy_version:        String,   // bound alongside policy_hash (defense in depth)
  epoch:                 u64,      // the epoch/window covered
  spend_ref_hash:        [u8;32],  // the spend covered; the 32-ZERO sentinel = a
                                   //   window-standing auth (covers all of the
                                   //   wallet's leaves of this election in
                                   //   [issued_at,expiry] under policy_hash + epoch)
  nullifier_domain:      "crinkl-election-nullifier/v1",  // must match the leaf derivation
  issued_at:             TimestampISO,
  expiry:                TimestampISO,           // hard validity bound
}
signed_message  = the human-readable template (below) — the UTF-8 bytes the wallet signs
authorization_id = sha256(utf8(signed_message))   // INTERNAL dedup/replay key only — NOT a protocol
                                                   //   identifier (the on-chain leaf binds blake3
                                                   //   spend_ref_hash + nullifier, derived separately
                                                   //   by the batcher). sha256 because the gateway has
                                                   //   no blake3; if ever protocol-exposed, switch to blake3.
signature        = ed25519(wallet, utf8(signed_message))
```

**Signed message format (normative).** A fixed, human-readable, DETERMINISTIC
template (SIWE-style): a plain-language intro, then every field labeled — friendly
to sign, yet the verifier recomputes it byte-for-byte. Lines joined by `\n`, no
trailing spaces. Each top section is separated by ONE blank line. `<label>` =
`"CRINKL"` for CRINKL, `"Bitcoin and CRINKL (Mix)"` for ALTERNATE. `<valid_from>` /
`<valid_to>` are the friendly UTC dates of `issued_at` / `expiry` (`"<Mon> <D>, <YYYY>"`,
e.g. `"Jun 16, 2026"`, derived deterministically from the ISO timestamps — display
only; the binding `issued_at` / `expiry` are the raw ISO strings in the verification
block):

```text
Crinkl — authorize your reward

I authorize Crinkl to reward my verified spend as <label>, claimable to my wallet.

Claim to: <claim_destination>

Valid: <valid_from> to <valid_to>

Network: <chain>:<cluster>

— verification (do not edit) —
schema: <schema>
election: <election>
wallet: <wallet>
issuer: <issuer>
mint: <mint>
policy_hash: <policy_hash>
policy_version: <policy_version>
epoch: <epoch>
issued_at: <issued_at>
expiry: <expiry>
nullifier_domain: <nullifier_domain>
spend_ref_hash: <spend_ref_hash>
```

Every field is present (bound): the intro + friendly `Valid:` line are display, the
labeled `— verification —` block is the binding (raw `election`, `wallet`, and the
raw-ISO `issued_at` / `expiry` are bound there, not just the friendly `<label>` /
date line). The verifier reconstructs this exact string from the stored fields and
checks the ed25519 signature over its UTF-8 bytes — never a pre-hash, never an opaque
blob. **The reference impl is canonical** and this spec is kept byte-identical to it:
`crinkl-pwa-next` `lib/rewardElectionSignature.ts` `canonicalClaimElectionMessage`
(and gateway `attestation-gateway/.../electionAuthRoutes.ts`, byte-for-byte equal).

**Validity (normative):** a CRINKL or ALTERNATE leaf is accepted iff a stored
authorization (a) verifies against `wallet`, (b) matches the leaf's `election`,
`issuer`, `mint`, `chain`, `cluster`, and `policy_hash`, (c) is within
`[issued_at, expiry]`, and (d) covers the leaf's `spend_ref_hash` **and** `epoch`
per its mode:
- **single-spend** — auth `spend_ref_hash` equals the leaf's `spend_ref_hash`: the
  auth's `epoch` MUST equal the leaf's `epoch` (exact).
- **window-standing** — auth `spend_ref_hash` is the 32-zero sentinel: the auth
  covers every epoch in `[auth.epoch, floor(expiry / 86400)]`, i.e. one signature
  authorizes the wallet's CRINKL/ALTERNATE leaves of this `election` + `policy_hash`
  across that whole window (the "future rewards" UX). The leaf is accepted iff its
  `epoch` falls in that range (and `policy_hash` still matches — a policy change
  mid-window yields a different `policy_hash`, so leaves under the new policy are
  NOT covered and require a fresh authorization).

The signed message is the canonical body — never an opaque hash the verifier did not
recompute.

> **Granularity note:** a single-spend authorization (binds the leaf's
> `spend_ref_hash`) is the strongest evidence; a window-standing authorization
> (zero sentinel) trades per-spend granularity for one signature per
> election/policy/epoch window — better UX, weaker per-spend non-repudiation. The
> PWA SHOULD default to window-standing when the user sets the *preference*; the
> consume-path MAY require single-spend for high-value spends (policy decision).

## ElectionRootConsumeInputV1 (normative)
How the batcher turns the platform's per-spend election rows into `ElectionLeafV1`
+ posts the root. Defines the contract the (production-DB) claim path must satisfy.

**Source rows:** per qualified spend in the epoch, from
`platform.reward_preference_snapshots` (the primary `REWARD_FINAL_ISSUED` snapshot,
`is_primary`) joined to the spend's qualified `amount_cents`:

```text
ElectionRowV1 {
  spend_id:       String,
  wallet_ref:     String,
  preference:     "none"|"btc"|"alternate"|"crinkl",
  policy_version: String,
  amount_cents:   u64,        // joined from the spend/receipt record
  occurred_at:    TimestampISO,
}
```

**Derivation (row → ElectionLeafV1):**
- `election`        = map(preference) per "Shared derivations".
- `issuer` / `mint` = issuer/mint from batcher config (the authorized-issuer + CRINKL mint).
- `spend_ref_hash`  = `blake3("crinkl-spend-ref/v1" ‖ spend_id)`.
- `amount_cents`    = `ElectionRowV1.amount_cents` (Σ over the epoch == `total_gmv_cents`).
- `epoch`           = window-of(`occurred_at`).
- `nullifier`       = `blake3("crinkl-election-nullifier/v1" ‖ issuer ‖ mint ‖ spend_id ‖ epoch_le8)`.

**Rules (normative):**
- A claim row (`election == CRINKL` or `ALTERNATE`) MUST have a valid
  `ClaimElectionAuthorizationV1` (above) covering it, else it is excluded and
  surfaced as an exception (never silently dropped or downgraded). btc/none rows
  need no authorization.
- **Replay tracking:** each consumed row is marked posted (an onchain-tracking
  column on the snapshots, mirroring `points_canonical_v2.onchain_status`); a spend
  appears in at most one epoch's election root. The claim RPC leases rows
  atomically (mirror `claim_points_for_batch_json`).
- The root is `merkleRoot(rows.map(leaf_hash))` over **all** rows in the epoch
  (btc/none included); posted once via `init_election_root` with
  `total_gmv_cents = Σ amount_cents` and `eligible_spend_count = rows.length`.

## Consumed by later phases
- Phase 4: `claim_root` derives from the crinkl/alternate subset of these leaves.
- Phase 5: the burn epoch commits `spendElectionRoot`; validators recompute the
  leaves from the published rows (DA) and check `Σ amount_cents == total_gmv_cents`.

## Open (follow-ups, not blockers)
- Exact UTC-day → epoch index function (finalize alongside `QualifiedGmvBurnEpochV1.window`).
- Whether high-value spends require single-spend authorization (policy decision).
