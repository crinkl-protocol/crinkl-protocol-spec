# Issuer Policy Commitment (IPC) — schema & hash rules

> Status: DRAFT for implementation (Phase 1 of the tokenomics foundation plan).
> Anchor: Crinkl tokenomics foundation refactor plan (internal governance).
> Economics are settled — this file defines the **object, its canonical encoding,
> its value-binding hash, and its signature envelope**, nothing more.

## Purpose
The IPC is the **single signed, hash-addressed object** that holds **every
token-affecting parameter**. Its hash is the `policy_hash` referenced in the
`qualified-gmv-burn-epoch-v0` statement (Phase 2) and committed in the density-burn
epoch (Phase 5). Tracing the hash **proves the exact policy** a reward/burn was
computed under — values are bound into the hash (not references), so the proof
needs **no trusted DB read**.

## Object

**Group A — protocol tokenomics (network-governed, per `mint`):**
- `c_base_units`, `k_cents`, `lambda`, `revenue_enabled`
- `pool_fund_units` (70M)
- `aggregation_rule`
- `bounds`: `max_c`, `max_lambda`, `min_K`, `min_committee`, `min_threshold`

**Group B — issuer application policy (issuer-governed, per `(issuer, mint)`):**
- `usd_per_receipt`
- `crinkl_price` + `price_source` (policy / oracle / TWAP; with staleness bound,
  emergency override, dispute rule per the mainnet price-source policy, §6.5)
- `referral_*_points` (+ per-tier), caps (`max_receipts_per_day`, referral caps)
- `review_submission_points`, `correction_bonus_points`, `boost_points`
- `bonus_category_ruleset_hash`, `coin_tier_ruleset_hash`

**Group C — identity & versioning:**
- `issuer`, `mint`
- `policy_version`, `effective_from`, `prev_policy_hash` (chains versions)

> Single issuer today (Crinkl) → one IPC, one `policy_hash`. Multi-issuer (Phase 7)
> splits Group A into a shared per-`mint` commitment (PTC) + per-issuer Group B;
> `policy_hash` then = `hash(ptc_hash, ipc_hash)`. The schema below is forward-
> compatible with that split.

## Canonical encoding (normative)
- Deterministic: **sorted keys**, **fixed-decimal** encoding for every numeric
  value (no float drift), ruleset tables referenced by their **own content-hash**
  (entries sorted, fixed decimals).
- **All values bound by VALUE** — `usd_per_receipt`, `crinkl_price`, `c`/`K`/`λ`,
  `pool_fund_units` are hashed as their literal values, **not** as a mutable
  reference id. (This is the fix for today's `crinkl_policy_hash`, which binds
  `reserve_checkpoint_id` — a reference — so tracing it requires a trusted DB
  read. Bind the values, or content-address the checkpoint and bind that hash.)

## Hash (normative)
`policy_hash = SHA-256(canonical(IPC body))`. Pure content-addressing; identical
bytes → identical hash; any value change → new hash.

## Signature envelope (normative)
- The IPC is **signed by the issuer authority root** over `policy_hash` — single
  key now, Squads multisig later, **no schema change**.
- Group A (protocol) fields change only via the **timelocked** path; Group B
  (issuer) fields via the issuer authority root.
- A verifier accepts an IPC **iff** the signature verifies against the issuer's
  current key in the **authorized-issuer registry** (a public trust root,
  `../TOKENS.md`).

## How settlement uses it
- The `qualified-gmv-burn-epoch-v0` statement (Phase 2) carries `policy_hash`.
- `reward = policy.usd_per_receipt ÷ policy.crinkl_price` (from the hashed policy);
  the burn uses Group A (`c`/`K`/`λ`/`pool`).
- Tracing `policy_hash` → the IPC → the exact values **proves** the reward/burn —
  no value is trusted, all are committed.

## Consumed by later phases
- Phase 2: `policy_hash` enters the statement descriptor + the per-leaf eligibility check.
- Phase 4: the claim root binds `policy_hash` + `policy_version`.
- Phase 5: the epoch commits `policy_hash`; reward/burn read Group A/B from it.

## Open (follow-ups, not blockers)
- Exact mainnet `price_source` policy (§6.5: fixed / TWAP / oracle + staleness + override + dispute).
- The precise field types/byte layout (finalize alongside Phase 2's leaf schema so encodings match).
