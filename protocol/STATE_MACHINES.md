# State Machines

Two independent state machines govern spend lifecycle: one for verification (attestation), one for rewards (economic outputs). They operate in parallel but are explicitly decoupled—spend corrections don't trigger reward clawbacks.

Terms are defined in GLOSSARY.md and used normatively throughout this specification.

## Verification State Machine (Attestation Ledger)

```
UPLOADED ──→ SOFT_VERIFIED ──→ HARD_VERIFIED ──→ CORRECTED*
   │              │               │               │
   └──────────────┴───────────────┴───────────────┴──→ INVALIDATED
```

`CORRECTED*` indicates that multiple corrections may occur (a chain of `SPEND_CORRECTED` events); the head remains in the corrected class.

| State | Definition |
|-------|------------|
| UPLOADED | Initial state; no verification performed |
| SOFT_VERIFIED | Soft verification completed with an eligible status for downstream use (not canonical Spend) |
| HARD_VERIFIED | Canonical Spend produced at the current head |
| CORRECTED | Canonical Spend produced at the current head, superseding prior canonical interpretation |
| INVALIDATED | No valid Spend derivable at the current head; terminal for spend truth |

### Head semantics and finality (normative)

- The protocol defines a single **canonical head** per `spendId`: the unique event reachable by following `prevHash` links from the head back to bootstrap (see `EVENTS.md#ordering-rules`).
- `HARD_VERIFIED`, `CORRECTED`, and `INVALIDATED` are **attestation head classes** (a description of the current head), not retroactive edits.
- `HARD_VERIFIED` and `CORRECTED` are terminal **for now** (they define a canonical Spend at the head), but may be superseded by later `SPEND_CORRECTED` or `SPEND_INVALIDATED` events.
- Corrections and invalidations are **append-only**: they supersede by moving the head forward; they MUST NOT rewrite or delete prior events.
- `INVALIDATED` is terminal for spend truth: after a `SPEND_INVALIDATED` head, no later event may reintroduce a valid canonical Spend for the same `spendId` without a new protocol concept/version explicitly defining reinstatement.

### Allowed Transitions

| From | To | Preconditions |
|------|-----|---------------|
| UPLOADED | SOFT_VERIFIED | `SPEND_SOFT_VERIFIED.softVerificationStatus = SOFT_VERIFIED` |
| UPLOADED | INVALIDATED | `SPEND_INVALIDATED` emitted (no valid Spend derivable) |
| SOFT_VERIFIED | HARD_VERIFIED | `SPEND_HARD_VERIFIED` emitted (canonical fields present) |
| SOFT_VERIFIED | INVALIDATED | `SPEND_INVALIDATED` emitted. If duplicate suspicion is confirmed at hard verification (e.g., `riskFlags` contains `potential_duplicate`), verifier MUST emit `SPEND_INVALIDATED` or `SPEND_CORRECTED`, not `SPEND_HARD_VERIFIED`. |
| HARD_VERIFIED | CORRECTED | `SPEND_CORRECTED` emitted (supersedes canonical interpretation) |
| HARD_VERIFIED | INVALIDATED | `SPEND_INVALIDATED` emitted (supersedes canonical interpretation) |
| CORRECTED | CORRECTED | additional `SPEND_CORRECTED` emitted (further supersession) |
| CORRECTED | INVALIDATED | `SPEND_INVALIDATED` emitted (terminal) |

Illegal transitions are rejected.

**Undefined transitions (normative):** any transition not listed above MUST be rejected with `InvalidTransition` (see `EVENTS.md#error-types`).

**Correction semantics (normative):** `SPEND_CORRECTED` appends a new head that supersedes the prior canonical interpretation while preserving append-only history.

**Soft verification non-transition (normative):** `SPEND_SOFT_VERIFIED` events with `softVerificationStatus != SOFT_VERIFIED` MUST NOT advance the verification state; the derived state remains `UPLOADED` and is considered ineligible for reward issuance.

**Review request non-transition (normative):** `SPEND_REVIEW_REQUESTED` is informational. It MUST NOT advance, reopen, or supersede attestation state, and it MUST NOT reintroduce a valid Spend after an `INVALIDATED` head.

## Reward State Machine (Reward Ledger)

```
NO_REWARD ──→ PROVISIONAL_REWARD_ISSUED ──→ FINAL_REWARD_ISSUED
     │                                              ▲
     └──────────────────────────────────────────────┘
```

| State | Definition |
|-------|------------|
| NO_REWARD | Default; no reward issued |
| PROVISIONAL_REWARD_ISSUED | Reward issued on SOFT_VERIFIED |
| FINAL_REWARD_ISSUED | Reward issued on HARD_VERIFIED |

### Allowed Transitions

| From | To | Preconditions |
|------|-----|---------------|
| NO_REWARD | PROVISIONAL_REWARD_ISSUED | At issuance time, current spend head class is `SOFT_VERIFIED`, `HARD_VERIFIED`, or `CORRECTED` (and not `INVALIDATED`) |
| NO_REWARD | FINAL_REWARD_ISSUED | At issuance time, current spend head class is `HARD_VERIFIED` or `CORRECTED` (skip provisional) |
| PROVISIONAL_REWARD_ISSUED | FINAL_REWARD_ISSUED | At issuance time, current spend head class is `HARD_VERIFIED` or `CORRECTED` |

**Issuance binding (normative):** reward issuance events are spend-stream events. `REWARD_*_ISSUED.prevHash` MUST equal the then-current spend-stream head `eventHash` for the `spendId` (see `EVENTS.md#cross-fsm-ordering-constraints-normative`).

Reward entries are immutable—no clawbacks, no adjustments, even for fraud.

## Cross-Ledger Rules

1. Provisional reward requires spend ≥ SOFT_VERIFIED
2. Final reward requires spend ≥ HARD_VERIFIED
3. Spend invalidation does NOT alter prior rewards
4. Corrections do not automatically trigger rewards; any additional rewards require explicit issuance events

**Immutability:** Reward Ledger entries are never deleted or modified, even if the underlying spend is invalidated or corrected. This separation ensures financial finality independent of attestation corrections.

## State Persistence

State machines are **event-sourced**:
- Current state is derived by replaying events from genesis
- No separate "state database" exists at the protocol level
- Implementations MAY cache derived state for performance but MUST be able to reconstruct it from events

See EVENTS.md for event schemas and replay semantics.

## Replay Invariant

Replaying all ledger events in causal order (respecting `prevHash` chains) MUST produce identical final state as live processing, given the same protocol version.

## Token Outputs (Derived from State)

Tokens are derived outputs—they represent ledger state in portable form but don't introduce new state transitions:

- A **Spend Attestation Token** is derivable once a spend head class is `HARD_VERIFIED`, `CORRECTED`, or `INVALIDATED` and consists of a privacy-safe, portable **snapshot** of that head (see `TOKENS.md`). If later events change the head (e.g., `SPEND_CORRECTED`), a new token MUST be issued; old tokens remain valid historical artifacts but no longer represent the latest head.
- A **Reward Commitment Token** is derivable once a reward batch has been anchored on-chain (`REWARD_BATCH_COMMITTED` event exists in the system-stream) and consists of the commitment event history plus a Merkle inclusion proof for that recipient's rewards in the batch.
